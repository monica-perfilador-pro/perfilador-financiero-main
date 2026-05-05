"""
Motor de scoring numerico.
Calcula el score crediticio basado en el historial del cliente.
"""
from .inputs import InputsAnalisis
from .trace import Trace as Trace


def calcular_score(inputs: InputsAnalisis, trace: Trace) -> int:
    """
    Calcula el score numerico (puede ser negativo).

    Bonificaciones:
      +5 CrediNissan previo
      +4 Tarjeta limite alto
      +3 Auto previo / Hipoteca bancaria
      +1 Tarjeta basica con ingreso alto / Infonavit

    Penalizaciones:
      -15 MOP 3 (atrasos +61 dias)
      -12 8+ consultas
      -6  5-7 consultas
      -4  MOP 2 (31-60 dias)
      -3  3-4 consultas
    """
    score = 0

    # Bonificaciones positivas
    if inputs.tarjeta_alta == 1:
        score += 4
        trace.disparar("R9")

    if inputs.tarjeta_baja == 1 and inputs.ingreso > 30000:
        score += 1
        trace.disparar("R10")

    if inputs.credinissan == 1:
        score += 5
        trace.disparar("R11")

    if inputs.auto_previo == 1:
        score += 3
        trace.disparar("R12")

    if inputs.hipotecario == 1:
        score += 3
        trace.disparar("R13")
    elif inputs.hipotecario == 2:
        score += 1
        trace.disparar("R14")

    # Penalizaciones por atrasos
    if inputs.atrasos_mop == 2:
        score -= 4
        trace.disparar("R15")
    elif inputs.atrasos_mop == 3:
        score -= 15
        trace.disparar("R16")

    # Penalizaciones por consultas (orden importante: mayor a menor)
    if inputs.consultas >= 8:
        score -= 12
        trace.disparar("R17")
    elif inputs.consultas >= 5:
        score -= 6
        trace.disparar("R18")
    elif inputs.consultas >= 3:
        score -= 3
        trace.disparar("R19")

    return score


def determinar_perfil(score: int, trace: Trace) -> str:
    """
    Mapea el score numerico al perfil interno.

    DELGADO: score <= 0
    MEDIO:   1 <= score <= 6
    FUERTE:  score >= 7
    """
    if score <= 0:
        trace.disparar("R20")
        return "DELGADO"
    if score >= 7:
        trace.disparar("R22")
        return "FUERTE"
    trace.disparar("R21")
    return "MEDIO"