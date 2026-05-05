"""
Evaluador de presion financiera actual. v3.0

Dimension que el motor v2 no tenia:
  Score historico = como pago EN EL PASADO
  Presion financiera = como esta su carga de deuda HOY

Un cliente puede tener historial impecable (MOP 1 siempre)
y aun asi estar financieramente tensionado hoy:
  - tarjetas al tope
  - multiples creditos abiertos
  - buscando mas credito activamente

Esto es exactamente lo que la financiera detecta en el buro
y que el motor antes no capturaba.

RESPONSABILIDAD UNICA:
  Mide tension financiera actual.
  NO evalua historial de pagos (eso es score_engine).
  NO evalua profundidad historica (eso es madurez).
  NO evalua PTI de la operacion nueva (eso es pti).
"""
from dataclasses import dataclass, field
from typing import List
from .inputs import InputsAnalisis
from .trace import Trace as Trace


@dataclass(frozen=True)
class PresionFinanciera:
    """
    Resultado de la evaluacion de presion financiera.

    nivel:                  BAJA / MEDIA / ALTA / CRITICA
    utilizacion_alta:       True si usa >60% del credito revolvente
    endeudamiento_elevado:  True si tiene muchos productos activos
    busqueda_activa:        True si consultas recientes indican busqueda
    bloquea_automatico:     True si la presion impide proceso automatico
    requiere_validacion:    True si se necesita revisar deuda real
    condicionamientos:      Lista de condicionamientos especificos
    razon:                  Explicacion tecnica para el asesor
    """
    nivel: str
    utilizacion_alta: bool
    endeudamiento_elevado: bool
    busqueda_activa: bool
    bloquea_automatico: bool
    requiere_validacion: bool
    condicionamientos: List[str]
    razon: str


def evaluar_presion(inputs: InputsAnalisis, trace: Trace) -> PresionFinanciera:
    """
    Evalua la presion financiera actual del cliente.

    Fuentes de presion:
      1. Utilizacion de lineas revolventes (tarjetas al tope)
      2. Numero de productos activos (muchos compromisos)
      3. Consultas recientes (busqueda activa de credito)
      4. Nivel de deuda declarado por el asesor
    """
    puntos_presion = 0
    senales = []
    condicionamientos: List[str] = []

    # ─── Fuente 1: Utilizacion revolvente ────────────────────────
    # Dato mas importante. Indica que tan cerca esta del limite.
    utilizacion_alta = False

    if inputs.utilizacion_revolvente > 0:
        # Tenemos dato real
        if inputs.utilizacion_revolvente >= 80:
            puntos_presion += 4
            utilizacion_alta = True
            senales.append(f"Utilizacion revolvente critica ({inputs.utilizacion_revolvente}%)")
            condicionamientos.append("LIQUIDAR O REDUCIR DEUDA REVOLVENTE ANTES DE SOLICITAR")
            trace.disparar("PR1_CRITICA")
        elif inputs.utilizacion_revolvente >= 60:
            puntos_presion += 3
            utilizacion_alta = True
            senales.append(f"Utilizacion revolvente alta ({inputs.utilizacion_revolvente}%)")
            condicionamientos.append("REDUCIR UTILIZACION DE TARJETAS AL 50% O MENOS")
            trace.disparar("PR1_ALTA")
        elif inputs.utilizacion_revolvente >= 40:
            puntos_presion += 1
            senales.append(f"Utilizacion revolvente media ({inputs.utilizacion_revolvente}%)")
            trace.disparar("PR1_MEDIA")
        else:
            trace.disparar("PR1_BAJA")
    else:
        # Sin dato: inferir desde tarjetas que tiene
        # Si tiene tarjetas pero no sabemos utilizacion,
        # asumimos riesgo conservador moderado
        if inputs.tarjeta_alta == 1 or inputs.tarjeta_baja == 1:
            puntos_presion += 1  # riesgo moderado por desconocimiento
            trace.disparar("PR1_INFERIDA")
        utilizacion_alta = False  # no podemos confirmar

    # ─── Fuente 2: Productos activos (endeudamiento actual) ──────
    endeudamiento_elevado = False

    if inputs.productos_activos >= 4:
        puntos_presion += 3
        endeudamiento_elevado = True
        senales.append(f"{inputs.productos_activos} creditos activos simultaneos")
        condicionamientos.append("CONSOLIDAR O LIQUIDAR CREDITOS ANTES DE SOLICITAR")
        trace.disparar("PR2_ELEVADO")
    elif inputs.productos_activos == 3:
        puntos_presion += 2
        endeudamiento_elevado = True
        senales.append(f"{inputs.productos_activos} creditos activos")
        trace.disparar("PR2_MEDIO")
    elif inputs.productos_activos == 2:
        puntos_presion += 1
        senales.append(f"{inputs.productos_activos} creditos activos")
        trace.disparar("PR2_BAJO")
    elif inputs.productos_activos == 1:
        trace.disparar("PR2_MINIMO")

    # ─── Fuente 3: Consultas recientes (busqueda activa) ─────────
    busqueda_activa = False

    # Usar consultas_recientes si disponible, sino usar consultas como proxy
    consultas_eval = (
        inputs.consultas_recientes
        if inputs.consultas_recientes > 0
        else inputs.consultas
    )

    if consultas_eval >= 5:
        puntos_presion += 2
        busqueda_activa = True
        senales.append(f"{consultas_eval} consultas recientes (busqueda activa de credito)")
        condicionamientos.append("ESPERAR 3-6 MESES PARA REDUCIR CONSULTAS EN BURO")
        trace.disparar("PR3_ALTA")
    elif consultas_eval >= 3:
        puntos_presion += 1
        senales.append(f"{consultas_eval} consultas (actividad crediticia reciente)")
        trace.disparar("PR3_MEDIA")
    else:
        trace.disparar("PR3_BAJA")

    # ─── Fuente 4: Nivel de deuda declarado por asesor ───────────
    if inputs.nivel_deuda_actual == 3:   # alta
        puntos_presion += 3
        senales.append("Carga de deuda alta (evaluacion del asesor)")
        condicionamientos.append("REVISAR Y DOCUMENTAR COMPROMISOS FINANCIEROS ACTUALES")
        trace.disparar("PR4_ALTA")
    elif inputs.nivel_deuda_actual == 2:  # media
        puntos_presion += 2
        senales.append("Carga de deuda media")
        trace.disparar("PR4_MEDIA")
    elif inputs.nivel_deuda_actual == 1:  # baja
        puntos_presion += 0
        trace.disparar("PR4_BAJA")
    # 0 = ninguna, no suma

    # ─── Determinar nivel de presion ─────────────────────────────
    if puntos_presion >= 7:
        nivel = "CRITICA"
    elif puntos_presion >= 4:
        nivel = "ALTA"
    elif puntos_presion >= 2:
        nivel = "MEDIA"
    else:
        nivel = "BAJA"

    # ─── Determinar si bloquea AUTOMATICO ────────────────────────
    # CRITICA: siempre bloquea
    # ALTA:    bloquea si combinada con tarjetas activas
    # MEDIA:   no bloquea pero requiere validacion
    bloquea_automatico = nivel in ("CRITICA", "ALTA")
    requiere_validacion = nivel in ("CRITICA", "ALTA", "MEDIA")

    if bloquea_automatico:
        trace.disparar("PR_BLOQUEA_AUTO")

    # ─── Construir razon explicativa ─────────────────────────────
    if not senales:
        razon = "Sin senales de presion financiera detectadas"
    else:
        razon = "Presion financiera detectada: " + " | ".join(senales)

    return PresionFinanciera(
        nivel=nivel,
        utilizacion_alta=utilizacion_alta,
        endeudamiento_elevado=endeudamiento_elevado,
        busqueda_activa=busqueda_activa,
        bloquea_automatico=bloquea_automatico,
        requiere_validacion=requiere_validacion,
        condicionamientos=condicionamientos,
        razon=razon,
    )