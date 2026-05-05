"""
AutoScore AI — Motor de Decision Crediticio v2
==============================================

Motor deterministico, auditable y modular.
Punto de entrada unico: core.motor.analizar(inputs)

Mismo input -> mismo output, siempre.
"""

from .inputs import InputsAnalisis
from .resultado import ResultadoMotor
from .motor import analizar

__version__ = "2.0.0"
__all__ = ["InputsAnalisis", "ResultadoMotor", "analizar"]