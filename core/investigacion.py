"""
Generador de alertas de investigacion.

CRITICO: ahora retorna LISTA, no string.
Antes las 4 alertas se sobrescribian unas a otras.
Ahora pueden coexistir.
"""
from typing import List
from .inputs import InputsAnalisis
from .trace import Trace as Trace


def generar_alertas_investigacion(
    inputs: InputsAnalisis,
    prob: int,
    trace: Trace,
) -> List[str]:
    """
    Genera lista de alertas de investigacion aplicables.

    Las 4 alertas pueden coexistir simultaneamente:
      INV1: No nomina con prob baja
      INV2: Domicilio buro != ID
      INV3: Independiente (siempre)
      INV4: Independiente con negocio en domicilio
    """
    alertas: List[str] = []

    # INV1: No nomina con probabilidad baja
    if inputs.tipo_ingreso != "Nomina" and prob < 45:
        alertas.append("Validacion adicional requerida")
        trace.disparar("INV1")

    # INV2: Domicilio en buro distinto al ID
    if inputs.domicilio_id == 2:
        alertas.append("Validacion de domicilio")
        trace.disparar("INV2")

    # INV3: Independiente siempre requiere validacion de ingresos
    if inputs.tipo_ingreso == "Independiente":
        alertas.append("Validacion de ingresos")
        trace.disparar("INV3")

    # INV4: Independiente con negocio en domicilio (regla de Monica)
    if inputs.tipo_ingreso == "Independiente" and inputs.negocio_casa == 1:
        alertas.append("Requiere validacion fisica")
        trace.disparar("INV4")

    # Si no se disparo ninguna, alerta default
    if not alertas:
        alertas.append("Sin alerta relevante")

    return alertas