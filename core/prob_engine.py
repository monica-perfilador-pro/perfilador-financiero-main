"""
Motor de probabilidad.
Calcula la probabilidad final de aprobacion.

CRITICO: aqui se aplica TODA la logica que muta probabilidad,
incluida la regla de investigacion fisica que antes mutaba
DESPUES de calcular el score color (causaba contradicciones).
"""
from .inputs import InputsAnalisis
from .trace import Trace as Trace


def calcular_probabilidad(
    inputs: InputsAnalisis,
    perfil: str,
    enganche_pct: float,
    trace: Trace,
) -> int:
    """
    Calcula la probabilidad final (5-95%).

    Pipeline:
      1. Probabilidad base segun perfil
      2. Ajustes por enganche
      3. Penalizaciones por consultas
      4. Caps/ajustes por MOP
      5. Bonus por investigacion fisica (independiente con negocio en casa)
      6. Clamp final 5-95
    """
    # Paso 1: probabilidad base segun perfil
    if perfil == "FUERTE":
        prob = 85
        trace.disparar("R23")
    elif perfil == "MEDIO":
        prob = 65
        trace.disparar("R24")
    else:  # DELGADO
        prob = 30
        trace.disparar("R25")

    # Paso 2: ajustes por enganche
    if enganche_pct >= 40:
        prob += 10
        trace.disparar("R26")
    elif enganche_pct >= 25:
        prob += 5
        trace.disparar("R27")

    # Paso 3: penalizaciones por consultas
    if inputs.consultas >= 8:
        prob -= 25
        trace.disparar("R28")
    elif inputs.consultas >= 5:
        prob -= 15
        trace.disparar("R29")
    elif inputs.consultas >= 3:
        prob -= 5
        trace.disparar("R30")

    # Paso 4: caps por MOP
    if inputs.atrasos_mop == 3:
        prob = min(prob, 28)
        trace.disparar("R31")
    elif inputs.atrasos_mop == 2:
        prob -= 10
        trace.disparar("R32")

    # Paso 5: investigacion fisica (independiente con negocio en domicilio)
    # IMPORTANTE: aqui ANTES del clamp y antes de calcular score color.
    # Antes esta regla mutaba prob despues, causando contradicciones.
    if inputs.tipo_ingreso == "Independiente" and inputs.negocio_casa == 1:
        prob = max(prob, 80)
        trace.disparar("R33")

    # Paso 6: clamp final
    prob = max(5, min(95, prob))
    trace.disparar("R34")

    return prob


def determinar_color(prob: int, trace: Trace) -> str:
    """
    Mapea probabilidad a score color.

    >= 80%   AZUL
    70-79%   VERDE
    45-69%   AMARILLO
    35-44%   NARANJA
    < 35%    ROJO
    """
    if prob >= 80:
        trace.disparar("R35")
        return "AZUL"
    if prob >= 70:
        trace.disparar("R36")
        return "VERDE"
    if prob >= 45:
        trace.disparar("R37")
        return "AMARILLO"
    if prob >= 35:
        trace.disparar("R38")
        return "NARANJA"
    trace.disparar("R39")
    return "ROJO"