"""
Motor de decision.
Determina la decision final, plan, y condicionamientos.

ORDEN DE PRIORIDAD CORRECTO (fix de pisada D2 vs D3):
  1. MOP 3 -> SIEMPRE revision especial (incluye perfiles delgados)
  2. Consultas masivas (10+) -> cotitular
  3. Riesgo alto (no MOP3 ya cubierto)
  4. Score ROJO
  5. Excede capacidad con prob baja
  6. MOP 2 -> condicionado
  7. Riesgo medio con prob baja
  8. Probabilidad alta -> aprobado
  9. Probabilidad media -> pre aprobado
  10. Probabilidad baja-media -> mejorable
  11. Default -> alternativa
"""
from dataclasses import dataclass, field
from typing import List
from .inputs import InputsAnalisis
from .perfil_engine import Riesgos
from .trace import Trace


@dataclass(frozen=True)
class DecisionData:
    """Resultado del decisionador."""
    decision: str
    plan: str
    condicionamientos: List[str] = field(default_factory=list)
    requiere_cotitular: bool = False
    mensaje_cliente: str = ""
    mensaje_asesor: str = ""


# ════════════════════════════════════════════════════════════════
# MAPEO PLAN -> SEMAFORO
# Ya no se usa string-matching frágil sobre la decision
# ════════════════════════════════════════════════════════════════
SEMAFORO_POR_PLAN = {
    "AUTOMATICO":          "verde",
    "DIRECTO":             "verde",
    "SE_VA_A_ANALISIS":    "amarillo",
    "CONDICIONADO":        "amarillo",
    "CONDICIONADO_MOP2":   "amarillo",
    "AJUSTAR_PLAZO":       "amarillo",
    "RESCATE":             "naranja",
    "REVISION_FINANCIERA": "naranja",
    "COTITULAR":           "naranja",
    "ALTERNATIVA":         "rojo",
    "REVISION":            "naranja",
}


def mapear_semaforo(plan: str) -> str:
    """Devuelve color de semaforo segun plan."""
    return SEMAFORO_POR_PLAN.get(plan, "naranja")


# ════════════════════════════════════════════════════════════════
# DECISIONADOR PRINCIPAL
# ════════════════════════════════════════════════════════════════
def decidir(
    inputs: InputsAnalisis,
    riesgos: Riesgos,
    perfil: str,
    score_color: str,
    prob: int,
    excede: bool,
    trace: Trace,
) -> DecisionData:
    """
    Determina la decision final con prioridades correctas.

    El orden de las ramas SI importa: la primera que matchea gana.
    """

    # ─── Prioridad 1: MOP 3 (revision especial) ──────────────────
    # SIEMPRE va aqui, sin importar perfil ni riesgo
    if inputs.atrasos_mop == 3:
        trace.disparar("D1")
        return DecisionData(
            decision="REVISION ESPECIAL FINANCIERA",
            plan="REVISION_FINANCIERA",
            condicionamientos=[
                "REVISION ESPECIAL FINANCIERA",
                "COTITULAR LINEA DIRECTA",
                "NO APLICA CREDINISSAN",
            ],
            requiere_cotitular=True,
            mensaje_cliente=(
                "Tu perfil requiere revision directa con la financiera "
                "para evaluar alternativas especiales."
            ),
            mensaje_asesor=(
                "MOP 3 detectado: Enviar folio a revision especial. "
                "CrediNissan no aplica. Buscar alternativa directa con "
                "financiera o cotitular linea directa con buen historial."
            ),
        )

    # ─── Prioridad 2: Consultas masivas ──────────────────────────
    if inputs.consultas >= 10:
        trace.disparar("D2")
        return DecisionData(
            decision="ESTRATEGIA ALTERNATIVA",
            plan="COTITULAR",
            condicionamientos=["COTITULAR OBLIGATORIO"],
            requiere_cotitular=True,
            mensaje_cliente=(
                "Tu perfil necesita el apoyo de un cotitular para avanzar."
            ),
            mensaje_asesor=(
                "10+ consultas en buro. Cotitular obligatorio."
            ),
        )

    # ─── Prioridad 3: Riesgo alto sin perfil fuerte ──────────────
    if riesgos.riesgo_alto and perfil != "FUERTE":
        trace.disparar("D3")
        return DecisionData(
            decision="ESTRATEGIA ALTERNATIVA",
            plan="ALTERNATIVA",
            condicionamientos=[
                "SUBIR ENGANCHE",
                "COMPROBAR INGRESOS",
                "COTITULAR",
            ],
            requiere_cotitular=True,
            mensaje_cliente=(
                "Tu perfil puede avanzar mediante una alternativa "
                "de financiamiento."
            ),
            mensaje_asesor=(
                "Riesgo alto: subir enganche >=10% / comprobar ingresos / "
                "buscar cotitular."
            ),
        )

    # ─── Prioridad 4: Score ROJO ─────────────────────────────────
    if score_color == "ROJO":
        trace.disparar("D4")
        return DecisionData(
            decision="ESTRATEGIA ALTERNATIVA",
            plan="COTITULAR",
            condicionamientos=["COTITULAR FUERTE", "MAYOR ENGANCHE"],
            requiere_cotitular=True,
            mensaje_cliente=(
                "Tu perfil actualmente requiere una alternativa "
                "de financiamiento."
            ),
            mensaje_asesor=(
                "Cotitular fuerte / Subir enganche / "
                "Evitar consultas en buro."
            ),
        )

    # ─── Prioridad 5: Excede capacidad con prob baja ─────────────
    if excede and prob < 70:
        trace.disparar("D5")
        return DecisionData(
            decision="AJUSTE NECESARIO",
            plan="AJUSTAR_PLAZO",
            condicionamientos=["AMPLIAR PLAZO", "VALIDAR INGRESOS"],
            mensaje_cliente=(
                "La mensualidad puede ajustarse para mejorar tu perfil."
            ),
            mensaje_asesor=(
                "Ampliar plazo / Reducir monto / Validar ingresos."
            ),
        )

    # ─── Prioridad 6: MOP 2 (condicionado) ───────────────────────
    if inputs.atrasos_mop == 2:
        trace.disparar("D6")
        return DecisionData(
            decision="APROBABLE CONDICIONADO",
            plan="CONDICIONADO_MOP2",
            condicionamientos=[
                "PONERSE AL CORRIENTE SI APLICA",
                "MAYOR ENGANCHE 25%+",
                "O COTITULAR LINEA DIRECTA",
            ],
            requiere_cotitular=True,
            mensaje_cliente=(
                "Tu perfil avanza pero requiere condicionamientos especificos."
            ),
            mensaje_asesor=(
                "MOP 2 (31-60d): Si la deuda sigue activa, ponerse al "
                "corriente antes. Si ya fue pasada, condicionar con mayor "
                "enganche o cotitular."
            ),
        )

    # ─── Prioridad 7: Riesgo medio con prob baja ─────────────────
    if riesgos.riesgo_medio and prob < 60:
        trace.disparar("D7")
        return DecisionData(
            decision="PERFIL CON OPORTUNIDAD",
            plan="RESCATE",
            condicionamientos=[
                "MAYOR ENGANCHE",
                "COTITULAR",
                "COMPROBAR INGRESOS Y/O INVESTIGACION FISICA",
            ],
            requiere_cotitular=True,
            mensaje_cliente=(
                "Tu perfil tiene alta posibilidad de avanzar "
                "ajustando puntos clave."
            ),
            mensaje_asesor=(
                "Enganche >=25% / Cotitular linea directa / "
                "Evitar mas consultas."
            ),
        )

    # ─── Prioridad 8: Probabilidad alta (>=70) ───────────────────
    if prob >= 70:
        if riesgos.riesgo_medio:
            trace.disparar("D8")
            return DecisionData(
                decision="APROBADO EN ANALISIS DE FINANCIERA",
                plan="SE_VA_A_ANALISIS",
                condicionamientos=[
                    "VALIDACION DE INGRESOS",
                    "INVESTIGACION TELEFONICA",
                ],
                mensaje_cliente=(
                    "Tu perfil es viable y puede avanzar a "
                    "proceso de aprobacion."
                ),
                mensaje_asesor=(
                    "Validacion de ingresos / Investigacion telefonica."
                ),
            )
        trace.disparar("D8")
        return DecisionData(
            decision="APROBADO",
            plan="AUTOMATICO",
            condicionamientos=[],
            mensaje_cliente=(
                "Tu perfil cumple los criterios para avanzar en automatico."
            ),
            mensaje_asesor="Perfil limpio. Proceder directo.",
        )

    # ─── Prioridad 9: Probabilidad media (50-69) ─────────────────
    if prob >= 50:
        # Calcular enganche_pct para sub-rama
        enganche_pct = (
            (inputs.enganche / inputs.precio) * 100
            if inputs.precio > 0 else 0
        )
        if enganche_pct < 20 or riesgos.riesgo_medio:
            trace.disparar("D9")
            return DecisionData(
                decision="APROBABLE CON AJUSTES",
                plan="CONDICIONADO",
                condicionamientos=[
                    "MAYOR ENGANCHE",
                    "VALIDACION FINANCIERA",
                ],
                mensaje_cliente=(
                    "Tu perfil es viable realizando algunos ajustes."
                ),
                mensaje_asesor=(
                    "Subir enganche +15pts / Validacion por financiera."
                ),
            )
        trace.disparar("D9")
        return DecisionData(
            decision="PRE APROBADO",
            plan="DIRECTO",
            condicionamientos=[],
            mensaje_cliente="Tu perfil es favorable para avanzar.",
            mensaje_asesor="Perfil estable. Proceder.",
        )

    # ─── Prioridad 10: Probabilidad baja-media (35-49) ──────────
    if prob >= 35:
        trace.disparar("D10")
        return DecisionData(
            decision="PERFIL MEJORABLE",
            plan="COTITULAR",
            condicionamientos=[
                "COTITULAR",
                "COMPROBAR INGRESOS",
                "MEJORAR ENGANCHE",
            ],
            requiere_cotitular=True,
            mensaje_cliente=(
                "Tu perfil puede fortalecerse con apoyo adicional."
            ),
            mensaje_asesor=(
                "Cotitular fuerte / Comprobar ingresos / Mejorar enganche."
            ),
        )

    # ─── Prioridad 11: Default ───────────────────────────────────
    trace.disparar("D11")
    return DecisionData(
        decision="ESTRATEGIA ALTERNATIVA",
        plan="ALTERNATIVA",
        condicionamientos=[
            "FINANCIERA FLEXIBLE",
            "REESTRUCTURA DE PERFIL",
        ],
        mensaje_cliente=(
            "Tu perfil puede avanzar mediante una alternativa "
            "de financiamiento."
        ),
        mensaje_asesor="Financiera flexible / Reestructura de perfil.",
    )