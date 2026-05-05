"""
Detector de riesgos.
Marca riesgo_alto y riesgo_medio segun el perfil del cliente.
"""
from dataclasses import dataclass
from .inputs import InputsAnalisis
from .trace import Trace


@dataclass(frozen=True)
class Riesgos:
    """Banderas de riesgo detectadas."""
    riesgo_alto: bool
    riesgo_medio: bool


def detectar_riesgos(
    inputs: InputsAnalisis,
    enganche_pct: float,
    trace: Trace,
) -> Riesgos:
    """
    Evalua todos los factores de riesgo.

    Riesgo alto:
      - MOP 3 (atrasos +61 dias)
      - 8+ consultas en buro
      - Tipo ingreso = No comprueba
      - Enganche < 10% del precio

    Riesgo medio:
      - MOP 2 (atrasos 31-60 dias)
      - 5-7 consultas
      - Tipo ingreso = Independiente
      - Enganche entre 10% y 20%
    """
    riesgo_alto = False
    riesgo_medio = False

    # Atrasos
    if inputs.atrasos_mop == 3:
        riesgo_alto = True
        trace.disparar("R1")
    elif inputs.atrasos_mop == 2:
        riesgo_medio = True
        trace.disparar("R2")

    # Consultas
    if inputs.consultas >= 8:
        riesgo_alto = True
        trace.disparar("R3")
    elif inputs.consultas >= 5:
        riesgo_medio = True
        trace.disparar("R4")

    # Tipo de ingreso
    if inputs.tipo_ingreso == "Independiente":
        riesgo_medio = True
        trace.disparar("R5")
    elif inputs.tipo_ingreso == "No comprueba":
        riesgo_alto = True
        trace.disparar("R6")

    # Enganche
    if enganche_pct < 10:
        riesgo_alto = True
        trace.disparar("R7")
    elif enganche_pct < 20:
        riesgo_medio = True
        trace.disparar("R8")

    return Riesgos(
        riesgo_alto=riesgo_alto,
        riesgo_medio=riesgo_medio,
    )