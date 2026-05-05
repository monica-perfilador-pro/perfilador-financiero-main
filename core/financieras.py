"""
Asignacion de financiera sugerida y documentacion requerida.
"""
from typing import List
from .inputs import InputsAnalisis


def determinar_financiera(plan: str) -> str:
    """
    Mapea plan a financiera sugerida.

    Automatico:    Caso ideal (CrediNissan/Banca tradicional)
    Condicionado:  Requiere validacion adicional
    Especial:      Requiere revision con financiera (alternativas)
    """
    if plan in {"AUTOMATICO", "DIRECTO"}:
        return "Automatico"
    if plan in {"SE_VA_A_ANALISIS", "CONDICIONADO", "CONDICIONADO_MOP2"}:
        return "Condicionado"
    return "Revision especial"


def determinar_documentos(plan: str, inputs: InputsAnalisis) -> List[str]:
    """
    Determina documentos requeridos segun el plan y tipo de ingreso.
    """
    docs = ["INE", "Comprobante de domicilio"]

    if plan == "DIRECTO":
        return ["INE", "Comprobante", "Cotizacion"]

    if plan in {"COTITULAR", "REVISION_FINANCIERA"}:
        docs.append("Cotitular obligatorio")

    if inputs.tipo_ingreso == "Nomina":
        docs.extend(["Nomina", "Estado de cuenta"])
    else:
        docs.append("Estados de cuenta")

    return docs