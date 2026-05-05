"""
Validador de PTI (Payment to Income).

Separacion conceptual critica:
  - Score crediticio = calidad del historial
  - PTI = viabilidad financiera de la operacion

Una operacion puede tener buen score pero estructura financiera inviable.
El motor ahora evalua ambas dimensiones por separado.

PTI = Mensualidad / Ingreso mensual
  < 30%:  ADECUADO (zona verde)
  30-40%: ALTO (zona de atencion)
  > 40%:  EXCESIVO (zona de rechazo)
"""
from dataclasses import dataclass
from .inputs import InputsAnalisis
from .trace import Trace as Trace


@dataclass(frozen=True)
class ResultadoPTI:
    """
    Resultado de la validacion PTI.

    pti_pct:          porcentaje real de la mensualidad vs ingreso
    zona:             ADECUADO / ALTO / EXCESIVO
    excede_capacidad: True si mensualidad > capacidad de pago
    bloquea_automatico: True si la estructura financiera no permite AUTOMATICO
    condicionamientos_pti: condicionamientos especificos de la estructura
    mensaje_asesor:   explicacion tecnica para el asesor
    """
    pti_pct: float
    zona: str
    excede_capacidad: bool
    bloquea_automatico: bool
    condicionamientos_pti: list
    mensaje_asesor: str


def validar_pti(
    mensualidad: float,
    capacidad_pago: float,
    ingreso: float,
    enganche_pct: float,
    trace: Trace,
) -> ResultadoPTI:
    """
    Valida la estructura financiera de la operacion.

    Genera condicionamientos contextuales e inteligentes:
    - NO sugiere subir enganche si ya es alto
    - NO sugiere ampliar plazo si ya es maximo
    - SI identifica el problema raiz de la estructura
    """
    condicionamientos: list = []
    razones_bloqueo = []

    # ─── Calcular PTI real ────────────────────────────────────────
    pti_pct = round((mensualidad / ingreso * 100), 1) if ingreso > 0 else 100.0

    # ─── Clasificar zona PTI ──────────────────────────────────────
    if pti_pct <= 30:
        zona = "ADECUADO"
        trace.disparar("PTI1")
    elif pti_pct <= 40:
        zona = "ALTO"
        trace.disparar("PTI2")
    else:
        zona = "EXCESIVO"
        trace.disparar("PTI3")

    # ─── Evaluar si excede capacidad de pago ─────────────────────
    excede_capacidad = mensualidad > capacidad_pago

    # ─── Determinar si bloquea AUTOMATICO ───────────────────────
    # Regla PTI-A: Mensualidad excede capacidad -> NO AUTOMATICO
    if excede_capacidad:
        razones_bloqueo.append(
            f"Mensualidad ${mensualidad:,.0f} excede capacidad ${capacidad_pago:,.0f}"
        )
        trace.disparar("PTI_A")

    # Regla PTI-B: PTI excesivo -> NO AUTOMATICO
    if zona == "EXCESIVO":
        razones_bloqueo.append(
            f"PTI {pti_pct}% supera el maximo recomendado (40%)"
        )
        trace.disparar("PTI_B")

    bloquea_automatico = len(razones_bloqueo) > 0

    # ─── Generar condicionamientos CONTEXTUALES ───────────────────
    # Aqui es donde evitamos sugerencias ilogicas.
    # Solo sugerimos lo que tiene sentido financiero real.

    if excede_capacidad or zona in ("ALTO", "EXCESIVO"):

        # REGLA DE ORO: No sugerir subir enganche si ya es alto
        if enganche_pct < 25:
            condicionamientos.append("SUBIR ENGANCHE AL 25%+")
            trace.disparar("PTI_C1")
        elif enganche_pct < 35:
            condicionamientos.append("CONSIDERAR MAYOR ENGANCHE (25-35%)")
            trace.disparar("PTI_C2")
        # Si enganche >= 35%: NO sugerimos subir enganche (ya es alto)

        # Siempre sugerir ajustar plazo si la mensualidad excede
        if excede_capacidad:
            condicionamientos.append("AMPLIAR PLAZO O REDUCIR MONTO")
            trace.disparar("PTI_C3")

        # Si ingresos son el problema
        if pti_pct > 40:
            condicionamientos.append("VALIDAR INGRESOS ADICIONALES")
            trace.disparar("PTI_C4")

        # Cotitular como opcion para mejorar PTI
        if excede_capacidad and enganche_pct >= 35:
            # Si ya tiene buen enganche y aun excede,
            # el problema es ingreso -> cotitular
            condicionamientos.append("COTITULAR PARA SUMAR INGRESOS")
            trace.disparar("PTI_C5")

    # ─── Mensaje tecnico para el asesor ──────────────────────────
    if not razones_bloqueo:
        mensaje = (
            f"Estructura financiera adecuada. "
            f"PTI: {pti_pct}% (dentro del rango recomendado)."
        )
    else:
        base = (
            f"Estructura financiera requiere ajuste. "
            f"PTI: {pti_pct}%. "
        )
        detalle = " | ".join(razones_bloqueo)
        mensaje = base + detalle

    return ResultadoPTI(
        pti_pct=pti_pct,
        zona=zona,
        excede_capacidad=excede_capacidad,
        bloquea_automatico=bloquea_automatico,
        condicionamientos_pti=condicionamientos,
        mensaje_asesor=mensaje,
    )