"""
Evaluador de estabilidad estructural del perfil. v3.0

Dimension que el motor v2 no tenia:
  Estabilidad = factores que hacen el perfil mas o menos predecible
                a largo plazo, independientemente de su historial.

El caso que detecto Monica:
  edad=56, plazo=72 → termina a los 62 años
  Las financieras endurecen cuando el credito termina cerca
  de la edad de retiro, porque los ingresos pueden caer.

RESPONSABILIDAD UNICA:
  Mide riesgos estructurales de largo plazo.
  NO evalua historial (score_engine).
  NO evalua profundidad historica (madurez).
  NO evalua presion actual (presion).
  NO evalua PTI de la operacion (pti).

Lo que evalua:
  1. Edad al terminar el plazo (riesgo de retiro)
  2. Tipo de ingreso vs estabilidad del empleo
  3. Antiguedad en domicilio (proxy de estabilidad de vida)
"""
from dataclasses import dataclass, field
from typing import List
from .inputs import InputsAnalisis
from .trace import Trace as Trace


# Umbrales de edad al terminar el credito
EDAD_FIN_OK        = 60   # menos de 60: sin restriccion
EDAD_FIN_ATENCION  = 65   # 60-64: requiere atencion
EDAD_FIN_LIMITE    = 70   # 65-69: endurece condiciones
                          # 70+:   bloquea automatico


@dataclass(frozen=True)
class EstabilidadPerfil:
    """
    Resultado de la evaluacion de estabilidad estructural.

    nivel:               ALTA / MEDIA / BAJA
    edad_al_terminar:    edad + (plazo / 12)
    riesgo_edad_plazo:   OK / ATENCION / ALTO / CRITICO
    plazo_maximo_rec:    plazo recomendado para este perfil de edad
    ingreso_estable:     True si el tipo de ingreso es estable
    domicilio_estable:   True si lleva mas de 1 ano en domicilio
    bloquea_automatico:  True si impide proceso automatico
    condicionamientos:   Lista de condicionamientos especificos
    razon:               Explicacion tecnica para el asesor
    """
    nivel: str
    edad_al_terminar: int
    riesgo_edad_plazo: str
    plazo_maximo_rec: int
    ingreso_estable: bool
    domicilio_estable: bool
    bloquea_automatico: bool
    condicionamientos: List[str]
    razon: str


def evaluar_estabilidad(inputs: InputsAnalisis, trace: Trace) -> EstabilidadPerfil:
    """
    Evalua la estabilidad estructural del perfil.

    Factores evaluados:
      1. Edad al terminar el plazo
      2. Estabilidad laboral real (antiguedad_empleo — v3.1)
      3. Estabilidad del ingreso (tipo)
      4. Estabilidad del domicilio

    v3.1: Incorpora antiguedad_empleo como predictor de estabilidad laboral.
    Ajusta EST1_ATENCION para bloquear AUTOMATICO cuando historial no es profundo.
    """
    puntos_riesgo = 0
    senales: List[str] = []
    condicionamientos: List[str] = []

    # ─── Factor 1: Edad al terminar el plazo ─────────────────────
    anos_plazo = inputs.plazo / 12
    edad_fin = int(inputs.edad + anos_plazo)
    plazo_maximo_rec = inputs.plazo

    # Calcular si el historial es profundo para modular ATENCION
    pts_prof = 0
    if inputs.credinissan == 1: pts_prof += 3
    if inputs.auto_previo == 1: pts_prof += 2
    if inputs.hipotecario in (1, 2): pts_prof += 3
    if inputs.tarjeta_alta == 1: pts_prof += 2
    if inputs.tarjeta_baja == 1: pts_prof += 1
    # Amplificar con antiguedad si aplica
    if inputs.antiguedad_historial >= 3:
        pts_prof += 2
    historial_profundo = pts_prof >= 5

    if edad_fin < EDAD_FIN_OK:
        riesgo_edad_plazo = "OK"
        trace.disparar("EST1_OK")

    elif edad_fin < EDAD_FIN_ATENCION:
        riesgo_edad_plazo = "ATENCION"
        puntos_riesgo += 1
        senales.append(f"Termina credito a los {edad_fin} anos (pre-retiro)")
        plazo_maximo_rec = max(12, int((EDAD_FIN_OK - inputs.edad) * 12))
        # v3.1: si historial no es profundo, ATENCION suma un punto extra
        # esto permite que con otros factores llegue a bloquear AUTOMATICO
        if not historial_profundo:
            puntos_riesgo += 1
            senales.append("Historial no profundo agrava riesgo de edad")
            trace.disparar("EST1_ATENCION_EXTRA")
        trace.disparar("EST1_ATENCION")

    elif edad_fin < EDAD_FIN_LIMITE:
        riesgo_edad_plazo = "ALTO"
        puntos_riesgo += 2
        senales.append(f"Termina credito a los {edad_fin} anos (cercano a retiro)")
        plazo_maximo_rec = max(12, int((EDAD_FIN_ATENCION - inputs.edad) * 12))
        condicionamientos.append(f"REDUCIR PLAZO — maximo recomendado: {plazo_maximo_rec} meses")
        trace.disparar("EST1_ALTO")

    else:
        riesgo_edad_plazo = "CRITICO"
        puntos_riesgo += 4
        senales.append(f"Termina credito a los {edad_fin} anos (supera limite)")
        plazo_maximo_rec = max(12, int((EDAD_FIN_OK - inputs.edad) * 12))
        condicionamientos.append(f"PLAZO MAXIMO {plazo_maximo_rec} MESES PARA ESTE PERFIL DE EDAD")
        condicionamientos.append("CONSIDERAR COTITULAR MAS JOVEN")
        trace.disparar("EST1_CRITICO")

    # ─── Factor 2: Estabilidad laboral real (v3.1) ───────────────
    # NUEVA DIMENSION: cuánto tiempo lleva en su trabajo actual.
    # La permanencia laboral es el predictor más importante
    # para financieras después del historial crediticio.

    if inputs.antiguedad_empleo == 1:
        # Menos de 6 meses — empleo muy reciente, alta incertidumbre
        puntos_riesgo += 3
        senales.append("Empleo muy reciente (menos de 6 meses)")
        condicionamientos.append("VERIFICAR ESTABILIDAD LABORAL — menos de 6 meses en empleo actual")
        trace.disparar("EST2_MUY_RECIENTE")

    elif inputs.antiguedad_empleo == 2:
        # 6 meses a 2 años — empleo reciente pero funcional
        puntos_riesgo += 1
        senales.append("Empleo reciente (6 meses a 2 años)")
        trace.disparar("EST2_RECIENTE")

    elif inputs.antiguedad_empleo == 3:
        # 2-5 años — estable
        trace.disparar("EST2_ESTABLE")

    elif inputs.antiguedad_empleo == 4:
        # Más de 5 años — muy estable, reduce riesgo general
        puntos_riesgo = max(0, puntos_riesgo - 1)
        trace.disparar("EST2_CONSOLIDADO")

    # 0 = jubilado / no aplica — neutro

    # ─── Factor 3: Estabilidad del ingreso (tipo) ────────────────
    ingreso_estable = True

    if inputs.tipo_ingreso == "No comprueba":
        ingreso_estable = False
        puntos_riesgo += 2
        senales.append("Ingreso no comprobable")
        trace.disparar("EST3_NO_COMPRUEBA")
    elif inputs.tipo_ingreso == "Independiente":
        ingreso_estable = False
        puntos_riesgo += 1
        senales.append("Ingreso independiente — variabilidad potencial")
        trace.disparar("EST3_INDEPENDIENTE")
    else:
        trace.disparar("EST3_NOMINA")

    # ─── Factor 4: Estabilidad del domicilio ─────────────────────
    domicilio_estable = inputs.antiguedad_dom >= 2

    if inputs.antiguedad_dom == 1:
        puntos_riesgo += 1
        senales.append("Domicilio reciente (menos de 1 ano)")
        trace.disparar("EST4_INESTABLE")
    else:
        trace.disparar("EST4_ESTABLE")

    # ─── Determinar nivel de estabilidad ─────────────────────────
    if puntos_riesgo == 0:
        nivel = "ALTA"
    elif puntos_riesgo <= 2:
        nivel = "MEDIA"
    else:
        nivel = "BAJA"

    # ─── Determinar si bloquea AUTOMATICO ────────────────────────
    bloquea_automatico = (
        riesgo_edad_plazo == "CRITICO"                          # edad fin >=70
        or (riesgo_edad_plazo == "ALTO" and not ingreso_estable)  # 65-69 + inestable
        or puntos_riesgo >= 4                                   # multiples factores
        or inputs.antiguedad_empleo == 1                        # v3.1: empleo <6 meses
        or (riesgo_edad_plazo == "ATENCION" and not historial_profundo)  # v3.1: 60-64 + no profundo
    )

    if bloquea_automatico:
        trace.disparar("EST_BLOQUEA_AUTO")

    # ─── Construir razon ─────────────────────────────────────────
    if not senales:
        razon = "Perfil estructuralmente estable"
    else:
        razon = "Factores de estabilidad: " + " | ".join(senales)

    return EstabilidadPerfil(
        nivel=nivel,
        edad_al_terminar=edad_fin,
        riesgo_edad_plazo=riesgo_edad_plazo,
        plazo_maximo_rec=plazo_maximo_rec,
        ingreso_estable=ingreso_estable,
        domicilio_estable=domicilio_estable,
        bloquea_automatico=bloquea_automatico,
        condicionamientos=condicionamientos,
        razon=razon,
    )