"""
Guia de preguntas para asesores — variables nuevas v3.0

Este archivo documenta EXACTAMENTE como formular las nuevas preguntas
en la UI de Streamlit para que los asesores las entiendan sin necesidad
de formacion financiera.

Principio: el motor puede ser sofisticado, las preguntas deben ser simples.
Lenguaje: comercial, no tecnico. Natural, no intimidante.

Variables nuevas:
  - utilizacion_revolvente  (0-100%)
  - productos_activos       (0-10)
  - consultas_recientes     (0-20)
  - nivel_deuda_actual      (0/1/2/3)
"""


# ════════════════════════════════════════════════════════════════
# COMO MOSTRAR ESTAS PREGUNTAS EN EL FORMULARIO
# (para copiar directamente al web_app.py o form_perfil.py)
# ════════════════════════════════════════════════════════════════

PREGUNTAS_UI = {

    # ─── Utilizacion revolvente ──────────────────────────────────
    "utilizacion_revolvente": {
        "label": "¿Cuánto debe en sus tarjetas actualmente?",
        "tipo": "selectbox",
        "opciones": [
            (0,  "— No tiene tarjetas de crédito"),
            (10, "Poco — las paga completo o casi completo"),
            (40, "La mitad — debe alrededor del 50% del límite"),
            (70, "Bastante — debe más del 60% del límite"),
            (90, "Casi al tope — cerca del límite o lo supera"),
        ],
        "tooltip": (
            "Pregúntale al cliente: '¿Tienes tarjetas de crédito? "
            "¿Más o menos cuánto debes en relación a tu límite?' "
            "También puedes verlo en el estado de cuenta o en el buró."
        ),
        "por_que_importa": (
            "Las financieras revisan esto en el buró. "
            "Si el cliente ya debe mucho en tarjetas, aunque pague puntual, "
            "la financiera puede pensar que ya está muy comprometido financieramente."
        ),
        "ejemplo_conversacion": (
            "Asesor: 'Oye, ¿tienes tarjetas de crédito? "
            "¿Más o menos a cuánto del límite las traes?'\n"
            "Cliente responde → asesor selecciona la opción más cercana."
        ),
    },

    # ─── Productos activos ───────────────────────────────────────
    "productos_activos": {
        "label": "¿Cuántos créditos activos tiene el cliente?",
        "tipo": "selectbox",
        "opciones": [
            (0, "Ninguno — sin deudas activas"),
            (1, "1 crédito — solo uno (hipoteca, tarjeta o auto)"),
            (2, "2 créditos — dos compromisos activos"),
            (3, "3 créditos — tres compromisos activos"),
            (4, "4 o más — muchos compromisos simultáneos"),
        ],
        "tooltip": (
            "Cuenta TODOS los créditos que tiene ABIERTOS HOY: "
            "tarjetas + hipoteca + créditos de auto + créditos personales + "
            "créditos de tienda (Coppel, Liverpool, etc.). "
            "Lo puedes ver en el buró impreso."
        ),
        "por_que_importa": (
            "Tener muchos créditos al mismo tiempo, aunque todos estén al corriente, "
            "indica que el cliente ya tiene muchos compromisos financieros. "
            "Agregar uno más puede ser riesgoso para la financiera."
        ),
        "ejemplo_conversacion": (
            "Asesor: 'Viendo su buró — ¿cuántos créditos tiene activos? "
            "Cuéntame la hipoteca, el auto si tiene, las tarjetas...'\n"
            "Cuenta los que tengan saldo o estén abiertos."
        ),
    },

    # ─── Consultas recientes ─────────────────────────────────────
    "consultas_recientes": {
        "label": "¿Cuántas consultas recientes tiene en buró? (últimos 6 meses)",
        "tipo": "number_input",
        "min": 0,
        "max": 20,
        "default": 0,
        "tooltip": (
            "Busca en el buró las consultas de los últimos 6 meses. "
            "Son diferentes a las consultas históricas totales. "
            "Si no puedes distinguirlas, deja en 0 y el motor usa el total."
        ),
        "por_que_importa": (
            "Muchas consultas recientes significan que el cliente ha estado "
            "buscando crédito en varios lados al mismo tiempo. "
            "Esto puede indicar que tiene urgencia de dinero o dificultades financieras."
        ),
        "ejemplo_conversacion": (
            "Asesor: 'En el buró, ¿cuántas veces han revisado su crédito "
            "en los últimos 6 meses? Son las consultas recientes que aparecen.'"
        ),
    },

    # ─── Nivel de deuda actual ───────────────────────────────────
    "nivel_deuda_actual": {
        "label": "En tu opinión, ¿cómo ves la carga de deuda del cliente?",
        "tipo": "selectbox",
        "opciones": [
            (0, "Sin deudas — perfil limpio, sin compromisos"),
            (1, "Deuda baja — uno o dos créditos manejables"),
            (2, "Deuda media — varios créditos pero los controla"),
            (3, "Deuda alta — muchos compromisos o cerca del límite"),
        ],
        "tooltip": (
            "Esta es tu evaluación como asesor después de ver el buró. "
            "No necesitas ser exacto — es tu impresión general "
            "sobre qué tan cargado financieramente está el cliente."
        ),
        "por_que_importa": (
            "Tu experiencia como asesor cuenta. A veces el buró no refleja "
            "todo — hay deudas informales o compromisos que el cliente menciona. "
            "Esta pregunta captura tu criterio profesional."
        ),
        "ejemplo_conversacion": (
            "Asesor: 'Considerando todo lo que viste en el buró y lo que "
            "te contó el cliente, ¿cómo calificas su carga de deuda en general?'"
        ),
    },
}


# ════════════════════════════════════════════════════════════════
# SECCION EN LA UI — como agrupar estas preguntas
# ════════════════════════════════════════════════════════════════

SECCION_UI = {
    "titulo": "💳 Situación Financiera Actual",
    "subtitulo": (
        "Estas preguntas ayudan a detectar si el cliente "
        "tiene mucha deuda en este momento, aunque pague puntual."
    ),
    "nota_asesor": (
        "ℹ️ Tip: Puedes obtener esta información revisando "
        "el buró de crédito junto con el cliente. "
        "No es necesario ser exacto — elige la opción más cercana."
    ),
    "campos": [
        "nivel_deuda_actual",      # primero la facil (tu criterio)
        "productos_activos",       # segundo (cuantos creditos)
        "utilizacion_revolvente",  # tercero (tarjetas)
        "consultas_recientes",     # ultimo (mas tecnico)
    ],
    "obligatorio": False,  # todas tienen defaults — no bloquean el analisis
}


# ════════════════════════════════════════════════════════════════
# CODIGO STREAMLIT LISTO PARA PEGAR EN FORM_PERFIL.PY
# ════════════════════════════════════════════════════════════════
CODIGO_STREAMLIT = '''
# ─── SECCIÓN NUEVA: Situación Financiera Actual ───────────────
st.markdown(\'\'\'
<div class="sec-label">💳 Situación Financiera Actual</div>
<div style="font-size:0.72rem;color:#888;margin:-6px 0 12px;">
  Ayuda al motor a detectar si el cliente tiene mucha deuda hoy,
  aunque pague puntual. Puedes verlo en el buró impreso.
</div>
\'\'\', unsafe_allow_html=True)

dfa1, dfa2 = st.columns(2)

with dfa1:
    nivel_deuda_actual = st.selectbox(
        "¿Cómo ves la carga de deuda del cliente?",
        options=[0, 1, 2, 3],
        format_func=lambda x: {
            0: "Sin deudas — perfil limpio",
            1: "Deuda baja — uno o dos créditos manejables",
            2: "Deuda media — varios pero los controla",
            3: "Deuda alta — muchos compromisos o al límite",
        }[x],
        help=(
            "Tu evaluación como asesor después de ver el buró. "
            "No necesitas ser exacto."
        )
    )

with dfa2:
    productos_activos = st.selectbox(
        "¿Cuántos créditos activos tiene?",
        options=[0, 1, 2, 3, 4],
        format_func=lambda x: {
            0: "Ninguno",
            1: "1 crédito",
            2: "2 créditos",
            3: "3 créditos",
            4: "4 o más",
        }[x],
        help=(
            "Cuenta tarjetas + hipoteca + autos + créditos personales "
            "que estén abiertos HOY en el buró."
        )
    )

dfa3, dfa4 = st.columns(2)

with dfa3:
    utilizacion_revolvente = st.selectbox(
        "¿Cuánto debe en sus tarjetas?",
        options=[0, 10, 40, 70, 90],
        format_func=lambda x: {
            0:  "— No tiene tarjetas",
            10: "Poco — paga casi completo",
            40: "La mitad — ~50% del límite",
            70: "Bastante — más del 60%",
            90: "Casi al tope — cerca del límite",
        }[x],
        help=(
            "Pregúntale: '¿A cuánto del límite traes tus tarjetas?' "
            "También aparece en el buró como porcentaje de utilización."
        )
    )

with dfa4:
    consultas_recientes = st.number_input(
        "Consultas recientes en buró (últimos 6 meses)",
        min_value=0, max_value=20, value=0,
        help=(
            "Busca en el buró las consultas de los últimos 6 meses. "
            "Si no puedes identificarlas, deja en 0."
        )
    )
'''


# ════════════════════════════════════════════════════════════════
# GUIA DE INTERPRETACION PARA EL ASESOR
# (para mostrar como tooltip o en entrenamiento)
# ════════════════════════════════════════════════════════════════
GUIA_INTERPRETACION = {
    "utilizacion_revolvente": {
        "verde":    "0-40% — Usa bien su crédito revolvente",
        "amarillo": "41-60% — Nivel medio, aceptable",
        "naranja":  "61-80% — Usa mucho del límite, señal de atención",
        "rojo":     "81-100% — Al tope, indica presión financiera",
    },
    "productos_activos": {
        "verde":    "0-1 — Sin compromisos o muy pocos",
        "amarillo": "2 — Dos créditos es manejable",
        "naranja":  "3 — Tres ya es bastante",
        "rojo":     "4+ — Demasiados compromisos simultáneos",
    },
    "consultas_recientes": {
        "verde":    "0-1 — Sin búsqueda activa de crédito",
        "amarillo": "2-3 — Alguna actividad reciente",
        "naranja":  "4-5 — Busca crédito activamente",
        "rojo":     "6+ — Busqueda desesperada, señal importante",
    },
    "nivel_deuda_actual": {
        "verde":    "0-1 — Sin deudas o muy pocas",
        "amarillo": "2 — Carga media, manejable",
        "rojo":     "3 — Carga alta, revisar con cuidado",
    },
}