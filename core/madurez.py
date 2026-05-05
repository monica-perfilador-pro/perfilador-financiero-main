"""
Evaluador de madurez crediticia.

Separacion conceptual critica:
  - Score crediticio = historial de pagos (limpio o sucio)
  - Madurez crediticia = profundidad, experiencia y estabilidad del historial

Un perfil puede tener historial LIMPIO pero DELGADO.
El motor ahora distingue ambas dimensiones.
"""
from dataclasses import dataclass
from .inputs import InputsAnalisis
from .trace import Trace as Trace


@dataclass(frozen=True)
class MadurezCrediticia:
    """
    Resultado del evaluador de madurez.

    nivel:       ALTA / MEDIA / BAJA
    profundidad: PROFUNDO / BASICO / DELGADO
    es_joven_independiente: bandera critica
    tiene_estructura_minima: al menos un producto de credito formal
    limitante_automatico: True si el perfil NO califica para AUTOMATICO
    razon_limitante: texto explicativo para el asesor
    """
    nivel: str
    profundidad: str
    es_joven_independiente: bool
    tiene_estructura_minima: bool
    limitante_automatico: bool
    razon_limitante: str


def evaluar_madurez(inputs: InputsAnalisis, trace: Trace) -> MadurezCrediticia:
    """
    Evalua la madurez crediticia del perfil.

    Dimensiones evaluadas:
      1. Profundidad del historial (cuantos productos de credito tiene)
      2. Antiguedad del historial (desde cuando los tiene — v3.1)
      3. Estabilidad del perfil (edad + tipo ingreso + tiempo domicilio)
      4. Experiencia bancaria real (tipos de credito usados)

    v3.1: La antiguedad del historial amplifica o modera la profundidad.
    Una tarjeta de 10 años vale mas que una tarjeta de 3 meses.
    """
    puntos_profundidad = 0
    puntos_estabilidad = 0
    razones_limitante = []

    # ─── Dimension 1: Profundidad historica ──────────────────────
    if inputs.credinissan == 1:
        puntos_profundidad += 3
        trace.disparar("M1")

    if inputs.auto_previo == 1:
        puntos_profundidad += 2
        trace.disparar("M2")

    if inputs.hipotecario in (1, 2):
        puntos_profundidad += 3
        trace.disparar("M3")

    if inputs.tarjeta_alta == 1:
        puntos_profundidad += 2
        trace.disparar("M4")

    if inputs.tarjeta_baja == 1:
        puntos_profundidad += 1
        trace.disparar("M5")

    profundidad_base = (
        "PROFUNDO" if puntos_profundidad >= 5
        else "BASICO" if puntos_profundidad >= 2
        else "DELGADO"
    )

    # ─── Dimension 2: Antiguedad del historial (v3.1) ────────────
    # La antiguedad amplifica o modera la profundidad base.
    # Sin antiguedad o con historial muy reciente, un perfil
    # "con tarjetas" puede ser tan riesgoso como uno sin nada.

    if inputs.antiguedad_historial == 0:
        # Sin historial crediticio en absoluto
        profundidad_efectiva = "DELGADO"
        trace.disparar("M9_SIN_HIST")
    elif inputs.antiguedad_historial == 1:
        # Menos de 1 año — historial nuevo
        if profundidad_base == "PROFUNDO":
            profundidad_efectiva = "BASICO"    # baja un nivel
        else:
            profundidad_efectiva = "DELGADO"   # baja a minimo
        trace.disparar("M9_RECIENTE")
    elif inputs.antiguedad_historial >= 3:
        # 3+ años — historial maduro amplifica
        puntos_amplificados = puntos_profundidad + 2
        profundidad_efectiva = (
            "PROFUNDO" if puntos_amplificados >= 5
            else "BASICO" if puntos_amplificados >= 2
            else "DELGADO"
        )
        trace.disparar("M9_MADURO")
    else:
        # 1-3 años — sin amplificacion ni reduccion
        profundidad_efectiva = profundidad_base
        trace.disparar("M9_MEDIO")

    # ─── Dimension 3: Estabilidad del perfil ─────────────────────
    if inputs.antiguedad_dom == 3:
        puntos_estabilidad += 2
        trace.disparar("M6")
    elif inputs.antiguedad_dom == 2:
        puntos_estabilidad += 1
        trace.disparar("M7")

    if inputs.tipo_ingreso == "Nomina":
        puntos_estabilidad += 2
        trace.disparar("M8")
    elif inputs.tipo_ingreso == "No comprueba":
        puntos_estabilidad -= 1

    # ─── Calcular nivel de madurez ────────────────────────────────
    puntos_prof_efectivos = (
        5 if profundidad_efectiva == "PROFUNDO"
        else 3 if profundidad_efectiva == "BASICO"
        else 0
    )
    total = puntos_prof_efectivos + puntos_estabilidad

    if total >= 7:
        nivel = "ALTA"
    elif total >= 3:
        nivel = "MEDIA"
    else:
        nivel = "BAJA"

    tiene_estructura_minima = puntos_profundidad >= 1

    es_joven_independiente = (
        inputs.edad <= 25
        and inputs.tipo_ingreso == "Independiente"
    )

    # ─── Reglas limitantes de AUTOMATICO ─────────────────────────
    limitante_automatico = False

    # MA1: Joven independiente nunca automatico
    if es_joven_independiente:
        limitante_automatico = True
        razones_limitante.append("Perfil joven independiente: estabilidad no comprobada")
        trace.disparar("MA1")

    # MA2: Sin estructura formal ninguna
    if profundidad_base == "DELGADO" and not tiene_estructura_minima:
        limitante_automatico = True
        razones_limitante.append("Historial sin profundidad crediticia formal")
        trace.disparar("MA2")

    # MA3: Madurez baja
    if nivel == "BAJA":
        limitante_automatico = True
        razones_limitante.append("Madurez crediticia insuficiente para proceso automatico")
        trace.disparar("MA3")

    # MA4: Muy joven con historial delgado o basico
    if inputs.edad <= 22 and profundidad_efectiva in ("DELGADO", "BASICO"):
        limitante_automatico = True
        razones_limitante.append("Edad y profundidad crediticia insuficiente para automatico")
        trace.disparar("MA4")

    # MA5: Sin historial en absoluto (v3.1)
    if inputs.antiguedad_historial == 0:
        limitante_automatico = True
        razones_limitante.append("Sin historial crediticio previo")
        trace.disparar("MA5")

    # MA6: Historial muy reciente (<1 año) y no profundo (v3.1)
    if inputs.antiguedad_historial == 1 and profundidad_base != "PROFUNDO":
        limitante_automatico = True
        razones_limitante.append("Historial crediticio menor a 1 año")
        trace.disparar("MA6")

    razon_final = (
        " / ".join(razones_limitante)
        if razones_limitante
        else "Madurez crediticia adecuada"
    )

    return MadurezCrediticia(
        nivel=nivel,
        profundidad=profundidad_efectiva,
        es_joven_independiente=es_joven_independiente,
        tiene_estructura_minima=tiene_estructura_minima,
        limitante_automatico=limitante_automatico,
        razon_limitante=razon_final,
    )