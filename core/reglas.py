"""
Catalogo central de reglas del motor.
Tabla unica de la verdad — toda regla del sistema esta aqui.

Cada regla tiene:
  - id:           identificador unico (R1, R12, D6, INV5)
  - nombre:       legible
  - categoria:    RIESGO / SCORE / PROBABILIDAD / DECISION / INVESTIGACION
  - prioridad:    1=mas alta, 100=mas baja (relevante en DECISION)
  - impacto:      descripcion del efecto
  - explicacion:  por que existe esta regla
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Regla:
    id: str
    nombre: str
    categoria: str
    prioridad: int
    impacto: str
    explicacion: str


# ════════════════════════════════════════════════════════════════
# CATALOGO DE REGLAS
# ════════════════════════════════════════════════════════════════
CATALOGO_REGLAS = [
    # ─── BLOQUE A — DETECCION DE RIESGOS ─────────────────────────
    Regla("R1",  "atrasos_mop3_riesgo_alto",   "RIESGO", 10,
          "riesgo_alto = True",
          "MOP 3 (+61 dias) indica historial crediticio severamente deteriorado"),
    Regla("R2",  "atrasos_mop2_riesgo_medio",  "RIESGO", 11,
          "riesgo_medio = True",
          "MOP 2 (31-60 dias) indica atrasos moderados que requieren atencion"),
    Regla("R3",  "consultas_8_riesgo_alto",    "RIESGO", 12,
          "riesgo_alto = True",
          "8+ consultas en buro indican busqueda agresiva de credito"),
    Regla("R4",  "consultas_5_riesgo_medio",   "RIESGO", 13,
          "riesgo_medio = True",
          "5-7 consultas son aceptables pero requieren validacion"),
    Regla("R5",  "independiente_riesgo_medio", "RIESGO", 14,
          "riesgo_medio = True",
          "Independientes requieren validacion adicional de ingresos"),
    Regla("R6",  "no_comprueba_riesgo_alto",   "RIESGO", 15,
          "riesgo_alto = True",
          "Sin comprobacion de ingresos no se puede validar capacidad"),
    Regla("R7",  "enganche_bajo_riesgo_alto",  "RIESGO", 16,
          "riesgo_alto = True",
          "Enganche menor al 10% indica falta de capacidad inicial"),
    Regla("R8",  "enganche_medio_riesgo",      "RIESGO", 17,
          "riesgo_medio = True",
          "Enganche entre 10-20% es minimo para perfiles regulares"),

    # ─── BLOQUE B — SCORE NUMERICO ───────────────────────────────
    Regla("R9",  "tarjeta_alta_plus_4",        "SCORE", 20,
          "score += 4",
          "Tarjeta con limite >100K indica buen historial crediticio"),
    Regla("R10", "tarjeta_baja_ingreso_alto",  "SCORE", 21,
          "score += 1",
          "Tarjeta basica con ingreso alto suma poco al perfil"),
    Regla("R11", "credinissan_plus_5",         "SCORE", 22,
          "score += 5",
          "CrediNissan previo es el mejor predictor de aprobacion"),
    Regla("R12", "auto_previo_plus_3",         "SCORE", 23,
          "score += 3",
          "Credito automotriz previo demuestra capacidad de pago en bienes durables"),
    Regla("R13", "hipoteca_bancaria_plus_3",   "SCORE", 24,
          "score += 3",
          "Hipoteca bancaria es el credito mas robusto del historial"),
    Regla("R14", "hipoteca_infonavit_plus_1",  "SCORE", 25,
          "score += 1",
          "Infonavit es positivo pero menos que hipoteca bancaria"),
    Regla("R15", "atrasos_mop2_resta_4",       "SCORE", 26,
          "score -= 4",
          "MOP 2 reduce el score por atraso reciente"),
    Regla("R16", "atrasos_mop3_resta_15",      "SCORE", 27,
          "score -= 15",
          "MOP 3 castiga severamente el score por atraso grave"),
    Regla("R17", "consultas_8_resta_12",       "SCORE", 28,
          "score -= 12",
          "8+ consultas penaliza fuerte por busqueda desesperada"),
    Regla("R18", "consultas_5_resta_6",        "SCORE", 29,
          "score -= 6",
          "5-7 consultas penaliza moderadamente"),
    Regla("R19", "consultas_3_resta_3",        "SCORE", 30,
          "score -= 3",
          "3-4 consultas penaliza levemente"),

    # ─── BLOQUE C — PERFIL Y PROBABILIDAD ────────────────────────
    Regla("R20", "perfil_delgado_score_neg",   "PERFIL", 31,
          "perfil = DELGADO",
          "Score <= 0 indica perfil sin antecedentes positivos"),
    Regla("R21", "perfil_medio_score_1_6",     "PERFIL", 32,
          "perfil = MEDIO",
          "Score 1-6 indica perfil con algunos elementos positivos"),
    Regla("R22", "perfil_fuerte_score_7plus",  "PERFIL", 33,
          "perfil = FUERTE",
          "Score 7+ indica perfil con historial robusto"),
    Regla("R23", "prob_base_fuerte_85",        "PROBABILIDAD", 40,
          "prob = 85",
          "Perfil FUERTE inicia con 85% de probabilidad"),
    Regla("R24", "prob_base_medio_65",         "PROBABILIDAD", 41,
          "prob = 65",
          "Perfil MEDIO inicia con 65% de probabilidad"),
    Regla("R25", "prob_base_delgado_30",       "PROBABILIDAD", 42,
          "prob = 30",
          "Perfil DELGADO inicia con 30% de probabilidad"),
    Regla("R26", "prob_engan_40_plus_10",      "PROBABILIDAD", 43,
          "prob += 10",
          "Enganche >=40% del precio aumenta significativamente la aprobacion"),
    Regla("R27", "prob_engan_25_plus_5",       "PROBABILIDAD", 44,
          "prob += 5",
          "Enganche >=25% del precio mejora la aprobacion"),
    Regla("R28", "prob_consultas_8_resta_25",  "PROBABILIDAD", 45,
          "prob -= 25",
          "8+ consultas reducen drasticamente la probabilidad"),
    Regla("R29", "prob_consultas_5_resta_15",  "PROBABILIDAD", 46,
          "prob -= 15",
          "5-7 consultas reducen moderadamente la probabilidad"),
    Regla("R30", "prob_consultas_3_resta_5",   "PROBABILIDAD", 47,
          "prob -= 5",
          "3-4 consultas reducen levemente la probabilidad"),
    Regla("R31", "prob_mop3_cap_28",           "PROBABILIDAD", 48,
          "prob = min(prob, 28)",
          "MOP 3 limita la probabilidad maxima a 28% (revision especial)"),
    Regla("R32", "prob_mop2_resta_10",         "PROBABILIDAD", 49,
          "prob -= 10",
          "MOP 2 reduce probabilidad por atraso reciente"),
    Regla("R33", "prob_inv_fisica_min_80",    "PROBABILIDAD", 50,
          "prob = max(prob, 80)",
          "Independiente con negocio en domicilio sube prob por confirmacion fisica"),
    Regla("R34", "prob_clamp_5_95",            "PROBABILIDAD", 51,
          "prob = max(5, min(95, prob))",
          "Limita probabilidad final entre 5% y 95%"),

    # ─── BLOQUE D — SCORE COLOR ──────────────────────────────────
    Regla("R35", "sc_azul_prob_80",            "COLOR", 60,
          "score_color = AZUL",
          "Probabilidad >=80% es perfil AZUL (alta aprobacion)"),
    Regla("R36", "sc_verde_prob_70",           "COLOR", 61,
          "score_color = VERDE",
          "Probabilidad 70-79% es perfil VERDE (buena aprobacion)"),
    Regla("R37", "sc_amarillo_prob_45",        "COLOR", 62,
          "score_color = AMARILLO",
          "Probabilidad 45-69% es perfil AMARILLO (validacion adicional)"),
    Regla("R38", "sc_naranja_prob_35",         "COLOR", 63,
          "score_color = NARANJA",
          "Probabilidad 35-44% es perfil NARANJA (areas de oportunidad)"),
    Regla("R39", "sc_rojo_prob_baja",          "COLOR", 64,
          "score_color = ROJO",
          "Probabilidad <35% es perfil ROJO (estrategia alternativa)"),

    # ─── BLOQUE E — DECISIONADO (orden de prioridad importante) ──
    Regla("D1",  "dec_mop3_revision",          "DECISION", 1,
          "decision = REVISION ESPECIAL FINANCIERA",
          "MOP 3 SIEMPRE va a revision especial, no aplica CrediNissan"),
    Regla("D2",  "dec_consultas_10_cotitular", "DECISION", 2,
          "decision = ESTRATEGIA ALTERNATIVA + COTITULAR OBLIGATORIO",
          "10+ consultas obligan a cotitular para aprobacion"),
    Regla("D3",  "dec_riesgo_alto_no_fuerte",  "DECISION", 3,
          "decision = ESTRATEGIA ALTERNATIVA",
          "Riesgo alto sin perfil fuerte requiere alternativa"),
    Regla("D4",  "dec_score_rojo",             "DECISION", 4,
          "decision = ESTRATEGIA ALTERNATIVA + COTITULAR FUERTE",
          "Score ROJO requiere cotitular fuerte y mayor enganche"),
    Regla("D5",  "dec_excede_prob_baja",       "DECISION", 5,
          "decision = AJUSTE NECESARIO",
          "Mensualidad excede capacidad y probabilidad <70%, ajustar plazo"),
    Regla("D6",  "dec_mop2_condicionado",      "DECISION", 6,
          "decision = APROBABLE CONDICIONADO",
          "MOP 2 es aprobable con mayor enganche o cotitular"),
    Regla("D7",  "dec_riesgo_medio_prob_baja", "DECISION", 7,
          "decision = PERFIL CON OPORTUNIDAD",
          "Riesgo medio con probabilidad <60% se puede rescatar"),
    Regla("D8",  "dec_aprobado_prob_70",       "DECISION", 8,
          "decision = APROBADO o APROBADO EN ANALISIS",
          "Probabilidad >=70% es aprobacion (con o sin riesgo medio)"),
    Regla("D9",  "dec_pre_aprobado_prob_50",   "DECISION", 9,
          "decision = APROBABLE CON AJUSTES o PRE APROBADO",
          "Probabilidad 50-69% requiere ajustes o es pre-aprobado"),
    Regla("D10", "dec_mejorable_prob_35",      "DECISION", 10,
          "decision = PERFIL MEJORABLE",
          "Probabilidad 35-49% requiere apoyo adicional"),
    Regla("D11", "dec_default_alternativa",    "DECISION", 11,
          "decision = ESTRATEGIA ALTERNATIVA",
          "Caso por defecto: requiere financiera flexible"),

    # ─── BLOQUE F — ALERTAS DE INVESTIGACION ─────────────────────
    Regla("INV1","alerta_no_nomina_prob_baja", "INVESTIGACION", 70,
          "alertas += 'Validacion adicional requerida'",
          "No-nomina con prob <45 requiere validacion extra"),
    Regla("INV2","alerta_domicilio_no_id",     "INVESTIGACION", 71,
          "alertas += 'Validacion de domicilio'",
          "Domicilio en buro distinto al ID requiere validacion"),
    Regla("INV3","alerta_independiente_ing",   "INVESTIGACION", 72,
          "alertas += 'Validacion de ingresos'",
          "Independiente siempre requiere validacion de ingresos"),
    Regla("INV4","alerta_negocio_casa_fisica", "INVESTIGACION", 73,
          "alertas += 'Requiere validacion fisica'",
          "Independiente con negocio en domicilio requiere visita fisica"),
]


def buscar_regla(regla_id: str) -> Regla | None:
    """Devuelve la regla por su ID. None si no existe."""
    for r in CATALOGO_REGLAS:
        if r.id == regla_id:
            return r
    return None