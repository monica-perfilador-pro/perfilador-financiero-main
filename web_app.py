import streamlit as st
from io import BytesIO
import sys, os

# ── MOTOR v3.1 ────────────────────────────────────────────────────
# Agrega la carpeta raíz al path para que core/ sea encontrado
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

try:
    from core.inputs import InputsAnalisis
    from core.motor import analizar as _analizar_motor
    MOTOR_V3_DISPONIBLE = True
except ImportError:
    MOTOR_V3_DISPONIBLE = False

# ── GOOGLE SHEETS ────────────────────────────────────────────────
def guardar_perfil_sheets(datos: dict, folio: str = None) -> str:
    """Guarda perfil en Google Sheets con folio unico. Retorna el folio."""
    import datetime
    if not folio:
        try:
            folio = generar_folio_perfil()
        except Exception:
            folio = None
    if not folio:
        folio = f"PER-{datetime.datetime.now().year}-{datetime.datetime.now().strftime('%H%M%S')}"
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        SHEET_ID   = "1f0oXowVTkuZdtlzw3Cdx5IIJRc9XIU6n0zM-EaXlyAA"
        SHEET_NAME = "AutoScore Perfiles"
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes)
        service = build("sheets", "v4", credentials=creds)

        ahora = datetime.datetime.now()
        fila = [
            folio,
            ahora.strftime("%d/%m/%Y"), ahora.strftime("%H:%M:%S"),
            datos.get("asesor",""), datos.get("telefono_asesor",""),
            datos.get("nombre",""), datos.get("telefono",""),
            datos.get("sc",""), datos.get("prob",0),
            datos.get("decision",""), datos.get("cap_pago",0),
            datos.get("mensualidad",0),
            round(float(datos.get("enganche_pct",0) or 0), 1),
            datos.get("temp",""), datos.get("inv",""),
            ", ".join(datos.get("condicionamientos",[])),
            datos.get("plan",""),
            datos.get("ingreso",0), datos.get("tipo_ingreso",""),
        ]
        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=f"'{SHEET_NAME}'!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [fila]}
        ).execute()
        return folio
    except Exception:
        return folio  # Devuelve el folio aunque falle Sheets


def generar_folio_unico() -> str:
    """Genera un folio unico tipo SOL-AAAA-NNNN consultando el Sheet."""
    import datetime
    año = datetime.datetime.now().year
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        SHEET_ID  = "1f0oXowVTkuZdtlzw3Cdx5IIJRc9XIU6n0zM-EaXlyAA"
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes)
        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="'Solicitudes'!A2:A10000"
        ).execute()
        valores = result.get("values", [])
        # Contar folios del año actual
        prefijo = f"SOL-{año}-"
        contador = sum(1 for r in valores if r and r[0].startswith(prefijo))
        return f"{prefijo}{contador+1:04d}"
    except Exception:
        # Fallback: timestamp si falla Sheets
        ts = datetime.datetime.now().strftime("%H%M%S")
        return f"SOL-{año}-{ts}"


def buscar_solicitud_por_folio(folio: str) -> "dict | None":
    """Busca una solicitud por folio y retorna los datos para precargar el form."""
    import json
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        SHEET_ID  = "1f0oXowVTkuZdtlzw3Cdx5IIJRc9XIU6n0zM-EaXlyAA"
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly",
                  "https://www.googleapis.com/auth/drive.readonly"]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes)
        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="'Solicitudes'!A1:Z10000"
        ).execute()
        valores = result.get("values", [])
        if len(valores) < 2:
            return None
        headers = valores[0]
        for row in valores[1:]:
            while len(row) < len(headers):
                row.append("")
            registro = dict(zip(headers, row))
            if registro.get("Folio","").strip().upper() == folio.strip().upper():
                # Parsear el JSON con todos los datos
                try:
                    datos = json.loads(registro.get("Datos_JSON","{}"))
                    datos["__folio"]    = registro.get("Folio","")
                    datos["__fecha"]    = registro.get("Fecha","")
                    datos["__hora"]     = registro.get("Hora","")
                    datos["__row_idx"]  = valores.index(row) + 1
                    return datos
                except Exception:
                    return None
        return None
    except Exception:
        return None


def actualizar_solicitud_sheets(folio: str, datos: dict) -> bool:
    """Actualiza una solicitud existente identificada por folio."""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        import datetime, json
        SHEET_ID  = "1f0oXowVTkuZdtlzw3Cdx5IIJRc9XIU6n0zM-EaXlyAA"
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes)
        service = build("sheets", "v4", credentials=creds)

        # Buscar la fila del folio
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range="'Solicitudes'!A1:A10000"
        ).execute()
        valores = result.get("values", [])
        row_idx = None
        for i, row in enumerate(valores):
            if row and row[0].strip().upper() == folio.strip().upper():
                row_idx = i + 1
                break
        if not row_idx:
            return False

        ahora = datetime.datetime.now()
        fila = [
            folio,
            ahora.strftime("%d/%m/%Y"), ahora.strftime("%H:%M:%S"),
            datos.get("asesor",""), datos.get("rfc_asesor",""), datos.get("fuente_venta",""),
            datos.get("nombre_completo",""), datos.get("rfc_cliente",""), datos.get("curp",""),
            datos.get("celular",""), datos.get("correo_cliente",""),
            datos.get("score_sc",""), datos.get("score_prob",0), datos.get("decision",""),
            datos.get("tipo_credito",""), datos.get("tipo_persona",""),
            datos.get("estado_civil",""), datos.get("vivienda",""),
            datos.get("ciudad",""), datos.get("estado",""),
            datos.get("ocupacion",""), datos.get("empresa",""),
            datos.get("ingreso_fijo",""), datos.get("antiguedad_empleo",""),
            json.dumps(datos, ensure_ascii=False)
        ]
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'Solicitudes'!A{row_idx}",
            valueInputOption="RAW",
            body={"values": [fila]}
        ).execute()
        return True
    except Exception:
        return False


def generar_folio_perfil() -> str:
    """Genera folio unico tipo PER-AAAA-NNNN para analisis."""
    import datetime
    año = datetime.datetime.now().year
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        SHEET_ID  = "1f0oXowVTkuZdtlzw3Cdx5IIJRc9XIU6n0zM-EaXlyAA"
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes)
        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="\'AutoScore Perfiles\'!A2:A10000"
        ).execute()
        valores = result.get("values", [])
        prefijo = f"PER-{año}-"
        contador = sum(1 for r in valores if r and r[0].startswith(prefijo))
        return f"{prefijo}{contador+1:04d}"
    except Exception:
        ts = datetime.datetime.now().strftime("%H%M%S")
        return f"PER-{año}-{ts}"


def buscar_perfil_duplicado(telefono: str, nombre: str) -> dict:
    """Busca si existe perfil del mismo cliente en las ultimas 24h."""
    import datetime
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        SHEET_ID  = "1f0oXowVTkuZdtlzw3Cdx5IIJRc9XIU6n0zM-EaXlyAA"
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly",
                  "https://www.googleapis.com/auth/drive.readonly"]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes)
        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range="\'AutoScore Perfiles\'!A1:S10000"
        ).execute()
        valores = result.get("values", [])
        if len(valores) < 2:
            return None
        headers = valores[0]
        hoy = datetime.date.today()
        ayer = hoy - datetime.timedelta(days=1)

        # Buscar de mas reciente a mas antiguo
        for row in reversed(valores[1:]):
            while len(row) < len(headers):
                row.append("")
            registro = dict(zip(headers, row))
            tel_reg = (registro.get("Tel_Cliente","") or "").strip()
            nom_reg = (registro.get("Cliente","") or "").strip().upper()
            fecha_reg = registro.get("Fecha","")

            # Coincide por telefono o por nombre
            coincide = False
            if telefono and tel_reg and telefono.strip() == tel_reg:
                coincide = True
            elif nombre and nom_reg and nombre.strip().upper() == nom_reg:
                coincide = True

            if coincide:
                # Verificar si es de las ultimas 24h
                try:
                    f_parts = fecha_reg.split("/")
                    f_obj = datetime.date(int(f_parts[2]), int(f_parts[1]), int(f_parts[0]))
                    if f_obj >= ayer:
                        return registro
                except Exception:
                    pass
        return None
    except Exception:
        return None


def actualizar_perfil_sheets(folio: str, datos: dict) -> bool:
    """Actualiza un perfil existente identificado por folio."""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        import datetime
        SHEET_ID  = "1f0oXowVTkuZdtlzw3Cdx5IIJRc9XIU6n0zM-EaXlyAA"
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes)
        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range="\'AutoScore Perfiles\'!A1:A10000"
        ).execute()
        valores = result.get("values", [])
        row_idx = None
        for i, row in enumerate(valores):
            if row and row[0].strip().upper() == folio.strip().upper():
                row_idx = i + 1
                break
        if not row_idx:
            return False

        ahora = datetime.datetime.now()
        fila = [
            folio,
            ahora.strftime("%d/%m/%Y"), ahora.strftime("%H:%M:%S"),
            datos.get("asesor",""), datos.get("telefono_asesor",""),
            datos.get("nombre",""), datos.get("telefono",""),
            datos.get("sc",""), datos.get("prob",0),
            datos.get("decision",""), datos.get("cap_pago",0),
            datos.get("mensualidad",0),
            round(float(datos.get("enganche_pct",0) or 0), 1),
            datos.get("temp",""), datos.get("inv",""),
            ", ".join(datos.get("condicionamientos",[])),
            datos.get("plan",""),
            datos.get("ingreso",0), datos.get("tipo_ingreso",""),
        ]
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"\'AutoScore Perfiles\'!A{row_idx}",
            valueInputOption="RAW",
            body={"values": [fila]}
        ).execute()
        return True
    except Exception:
        return False


def guardar_solicitud_sheets(datos: dict, folio: str = None):
    """Guarda solicitud nueva en hoja 'Solicitudes' con folio unico."""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        import datetime, json

        SHEET_ID    = "1f0oXowVTkuZdtlzw3Cdx5IIJRc9XIU6n0zM-EaXlyAA"
        SHEET_SOL   = "Solicitudes"
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes)
        service = build("sheets", "v4", credentials=creds)

        if not folio:
            folio = generar_folio_unico()

        ahora = datetime.datetime.now()
        fila = [
            folio,
            ahora.strftime("%d/%m/%Y"), ahora.strftime("%H:%M:%S"),
            datos.get("asesor",""), datos.get("rfc_asesor",""), datos.get("fuente_venta",""),
            datos.get("nombre_completo",""), datos.get("rfc_cliente",""), datos.get("curp",""),
            datos.get("celular",""), datos.get("correo_cliente",""),
            datos.get("score_sc",""), datos.get("score_prob",0), datos.get("decision",""),
            datos.get("tipo_credito",""), datos.get("tipo_persona",""),
            datos.get("estado_civil",""), datos.get("vivienda",""),
            datos.get("ciudad",""), datos.get("estado",""),
            datos.get("ocupacion",""), datos.get("empresa",""),
            datos.get("ingreso_fijo",""), datos.get("antiguedad_empleo",""),
            json.dumps(datos, ensure_ascii=False)
        ]
        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=f"'{SHEET_SOL}'!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [fila]}
        ).execute()
        return folio
    except Exception:
        return None
import base64
import os

def get_logo_b64():
    """Carga el logo como base64 para usar en HTML."""
    for name in ["AUTOSCOREIA.png", "logo_new.png", "logo.png"]:
        if os.path.exists(name):
            with open(name, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    return ""

# ══════════════════════════════════════════
# PDF CLIENTE — disenio minimalista premium
# ════════════════════════════════════════════
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from io import BytesIO
import datetime

W, H = letter  # type: ignore  # 612 x 792 pts
M    = 44      # margen lateral
CW   = W - 2*M  # ancho contenido = 524 pts

# ── PALETA ──────────────────────────────────────────────────────
ROJO        = HexColor("#c3002f")
NEGRO       = HexColor("#111111")
GRIS_OSCURO = HexColor("#444444")
GRIS_MEDIO  = HexColor("#888888")
GRIS_CLARO  = HexColor("#e5e5e5")
GRIS_FONDO  = HexColor("#f8f8f8")
BLANCO      = HexColor("#ffffff")

SC_COLOR  = {"AZUL":"#38bdf8","VERDE":"#22c55e","AMARILLO":"#eab308","NARANJA":"#f97316","ROJO":"#c3002f"}
SC_BG     = {"AZUL":"#eff8ff","VERDE":"#f0fdf4","AMARILLO":"#fefce8","NARANJA":"#fff7ed","ROJO":"#fff5f5"}
SC_TXT    = {"AZUL":"#0369a1","VERDE":"#166534","AMARILLO":"#854d0e","NARANJA":"#9a3412","ROJO":"#9f1239"}
SC_BORDE  = {"AZUL":"#bfdbfe","VERDE":"#bbf7d0","AMARILLO":"#fde68a","NARANJA":"#fed7aa","ROJO":"#fecdd3"}

MSGS = {
    "AZUL": {
        "titulo":   "Tu camino hacia tu auto esta listo",
        "cuerpo":   "Felicitaciones. Tu historial financiero refleja responsabilidad y compromiso, exactamente lo que las instituciones buscan. Eres candidato prioritario para obtener las mejores condiciones de financiamiento disponibles en el mercado.",
        "plan_lbl": None, "plan": [],
        "urgencia": "Las unidades con mejores condiciones se apartan con anticipacion. No dejes pasar esta oportunidad.",
        "decision": "APROBADO — Perfil limpio, proceder directo",
        "badge":    "SCORE AZUL",
    },
    "VERDE": {
        "titulo":   "Tu financiamiento esta al alcance",
        "cuerpo":   "Tu situacion financiera muestra solidez y buenos antecedentes crediticios. Con el proceso correcto tienes altas posibilidades de obtener tu vehiculo en las condiciones que necesitas. Estamos listos para acompanarte en cada paso del camino.",
        "plan_lbl": None, "plan": [],
        "urgencia": "Asegurar tu unidad ahora te garantiza el precio y la disponibilidad. El mercado cambia rapidamente.",
        "decision": "APROBADO EN ANALISIS — Validaciones normales",
        "badge":    "SCORE VERDE",
    },
    "AMARILLO": {
        "titulo":   "Tu auto esta mas cerca de lo que crees",
        "cuerpo":   "Hemos analizado tu situacion y tenemos buenas noticias: existen caminos concretos para que puedas llevarte tu vehiculo. Con ajustes menores en tu solicitud, tu perfil puede fortalecerse significativamente.",
        "plan_lbl": "LO QUE PUEDE MEJORAR TU PERFIL:",
        "plan":     ["Subir enganche al 25%+", "Validacion de ingresos", "Evitar consultas en buro", "Integrar cotitular de ser necesario"],
        "urgencia": "Cada dia de espera puede significar cambios en tasas y disponibilidad de unidades.",
        "decision": "APROBABLE CON AJUSTES — Validacion por financiera",
        "badge":    "SCORE AMARILLO",
    },
    "NARANJA": {
        "titulo":   "No es un no, es un 'todavia no'",
        "cuerpo":   "Contamos con opciones de financiamiento disenadas especificamente para perfiles como el tuyo. No es un no, es un camino diferente — y tenemos ese camino trazado para llevarte a donde quieres llegar.",
        "plan_lbl": "OPCIONES DISPONIBLES PARA TI:",
        "plan":     ["Financiera alternativa flexible", "Cotitular linea directa", "Mayor enganche inicial", "Plazo extendido disponible"],
        "urgencia": "El momento de actuar es ahora, antes de que cambien las condiciones del mercado.",
        "decision": "PERFIL CON OPORTUNIDAD — Estrategia alternativa",
        "badge":    "SCORE NARANJA",
    },
    "ROJO": {
        "titulo":   "Encontramos la ruta para tu auto",
        "cuerpo":   "Entendemos que cada situacion financiera es unica y tiene su historia. Lo importante no es donde estas hoy, sino hacia donde vas. Hemos disenado un plan especifico para ti que, paso a paso, te acercara a tener el vehiculo que necesitas.",
        "plan_lbl": "TU PLAN DE ACCION CONCRETO:",
        "plan":     ["Subir enganche al 20%+", "Integrar cotitular fuerte", "Evitar consultas en buro", "Hablar con tu asesor hoy mismo"],
        "urgencia": "Dar el primer paso hoy te pone en ventaja para el momento correcto. Tu asesor esta listo.",
        "decision": "PLAN DE ACCION PERSONALIZADO — Tu solucion existe",
        "badge":    "PERFIL EN PROCESO",
    },
}

# ── HELPERS ─────────────────────────────────────────────────────
def frect(c, x, y, w, h, color, r=0):
    c.setFillColor(color if isinstance(color, type(ROJO)) else HexColor(color))
    if r: c.roundRect(x, y, w, h, r, fill=1, stroke=0)
    else: c.rect(x, y, w, h, fill=1, stroke=0)

def srect(c, x, y, w, h, color, lw=0.5, r=0):
    c.setStrokeColor(color if isinstance(color, type(ROJO)) else HexColor(color))
    c.setLineWidth(lw)
    if r: c.roundRect(x, y, w, h, r, fill=0, stroke=1)
    else: c.rect(x, y, w, h, fill=0, stroke=1)

def txt(c, s, x, y, font, size, color, align="left"):
    c.setFont(font, size)
    c.setFillColor(color if isinstance(color, type(ROJO)) else HexColor(color))
    if align=="center": c.drawCentredString(x, y, s)
    elif align=="right": c.drawRightString(x, y, s)
    else: c.drawString(x, y, s)

def hline(c, x1, x2, y, color=None, lw=0.5):
    c.setStrokeColor(color or GRIS_CLARO)
    c.setLineWidth(lw)
    c.line(x1, y, x2, y)

def wrap_text(c, text, x, y, max_w, font, size, color, leading=13):
    """Dibuja texto con word-wrap, retorna y final."""
    c.setFont(font, size)
    c.setFillColor(color if isinstance(color, type(ROJO)) else HexColor(color))
    words = text.split()
    line_buf = ""
    cy = y
    for w in words:
        test = (line_buf + " " + w).strip()
        if c.stringWidth(test, font, size) <= max_w:
            line_buf = test
        else:
            c.drawString(x, cy, line_buf)
            cy -= leading
            line_buf = w
    if line_buf:
        c.drawString(x, cy, line_buf)
    return cy - leading


# ── GENERADOR PRINCIPAL ─────────────────────────────────────────
def generar_pdf_cliente(datos: dict) -> BytesIO:
    buf = BytesIO()
    cv  = canvas.Canvas(buf, pagesize=letter)
    cv.setTitle("AutoScore AI — Analisis de Financiamiento")

    sc      = datos.get("sc", "AMARILLO")
    msg     = MSGS.get(sc, MSGS["AMARILLO"])
    col     = HexColor(SC_COLOR[sc])
    nombre  = (datos.get("nombre") or "Cliente").upper()
    prob    = datos.get("prob", 0)
    cap     = datos.get("cap_pago", 0)
    men     = datos.get("mensualidad", 0)
    asesor  = datos.get("asesor", "") or ""
    tel_a   = datos.get("telefono_asesor", "") or ""
    correo_a= datos.get("correo_asesor", "") or ""
    docs    = datos.get("docs", ["INE", "Comprobante de domicilio"])
    fecha   = datetime.date.today().strftime("%d/%m/%Y")

    # ════════════════════════════════════════════════
    # SECCIÓN 1 — HEADER  (y: 792 → 700)
    # ════════════════════════════════════════════════
    # Fondo blanco
    frect(cv, 0, 0, W, H, BLANCO)
    frect(cv, 0, 0, W, H, GRIS_FONDO)

    # Franja header negra
    frect(cv, 0, H-70, W, 70, NEGRO)
    # Línea roja top
    frect(cv, 0, H-3, W, 3, ROJO)

    # Logo texto en header
    txt(cv, "AutoScore", M, H-32, "Helvetica-Bold", 20, BLANCO)
    w_as = cv.stringWidth("AutoScore", "Helvetica-Bold", 20)
    txt(cv, " AI", M+w_as, H-32, "Helvetica-Bold", 20, ROJO)
    txt(cv, "APROBACION INTELIGENTE", M, H-48, "Helvetica", 8, HexColor("#888888"))
    txt(cv, fecha, W-M, H-32, "Helvetica", 9, HexColor("#888888"), "right")
    txt(cv, "Analisis de Financiamiento Automotriz", W-M, H-46, "Helvetica", 8, HexColor("#666666"), "right")

    # ════════════════════════════════════════════════
    # SECCIÓN 2 — NOMBRE + PROBABILIDAD  (y: 700 → 620)
    # ════════════════════════════════════════════════
    y = H - 90

    # Nombre cliente grande
    txt(cv, nombre, M, y, "Helvetica-Bold", 18, NEGRO)
    frect(cv, M, y-6, 50, 2, ROJO)

    # Círculo probabilidad — lado derecho
    cx_c, cy_c, r_c = W-M-45, y-22, 34
    frect(cv, cx_c-r_c-6, cy_c-r_c-6, (r_c+6)*2, (r_c+6)*2, BLANCO, r=r_c+6)
    srect(cv, cx_c-r_c-6, cy_c-r_c-6, (r_c+6)*2, (r_c+6)*2, GRIS_CLARO, r=r_c+6)
    # Arco fondo
    cv.setStrokeColor(GRIS_CLARO); cv.setLineWidth(6)
    cv.arc(cx_c-r_c, cy_c-r_c, cx_c+r_c, cy_c+r_c, startAng=0, extent=180)
    # Arco progreso
    cv.setStrokeColor(col); cv.setLineWidth(6)
    cv.arc(cx_c-r_c, cy_c-r_c, cx_c+r_c, cy_c+r_c, startAng=0, extent=min(180, prob*1.8))
    txt(cv, "PROB.", cx_c, cy_c+10, "Helvetica", 7, GRIS_MEDIO, "center")
    txt(cv, f"{prob}%", cx_c, cy_c-8, "Helvetica-Bold", 18, NEGRO, "center")

    y -= 22
    txt(cv, "Estimado(a),", M, y, "Helvetica", 9, GRIS_MEDIO)

    # ════════════════════════════════════════════════
    # SECCIÓN 3 — DECISIÓN BANNER  (y: ~640 → 600)
    # ════════════════════════════════════════════════
    y -= 24
    frect(cv, M, y-28, CW, 32, HexColor(SC_BG[sc]), r=5)
    srect(cv, M, y-28, CW, 32, HexColor(SC_BORDE[sc]), r=5)
    frect(cv, M, y-28, 4, 32, col, r=2)
    txt(cv, msg["decision"], M+14, y-8, "Helvetica-Bold", 10, HexColor(SC_TXT[sc]))
    # Badge
    bw = cv.stringWidth(msg["badge"], "Helvetica-Bold", 7) + 16
    frect(cv, M+14, y-24, bw, 13, col, r=6)
    txt(cv, msg["badge"], M+22, y-17, "Helvetica-Bold", 7, BLANCO)

    # ════════════════════════════════════════════════
    # SECCIÓN 4 — MÉTRICAS 2 COLUMNAS  (y: ~570 → 520)
    # ════════════════════════════════════════════════
    y -= 46
    hline(cv, M, W-M, y+8)

    col_w = CW // 2 - 8
    # Caja 1 — Capacidad de pago
    frect(cv, M, y-42, col_w, 46, BLANCO, r=5)
    srect(cv, M, y-42, col_w, 46, GRIS_CLARO, r=5)
    frect(cv, M, y-42, col_w, 3, col, r=2)
    txt(cv, "CAPACIDAD DE PAGO", M+10, y-12, "Helvetica", 7, GRIS_MEDIO)
    txt(cv, f"${cap:,.0f}", M+10, y-30, "Helvetica-Bold", 16, NEGRO)

    # Caja 2 — Mensualidad o meta enganche
    x2 = M + col_w + 16
    frect(cv, x2, y-42, col_w, 46, BLANCO, r=5)
    srect(cv, x2, y-42, col_w, 46, GRIS_CLARO, r=5)
    frect(cv, x2, y-42, col_w, 3, col, r=2)
    if sc in ("ROJO","NARANJA"):
        txt(cv, "META ENGANCHE", x2+10, y-12, "Helvetica", 7, GRIS_MEDIO)
        txt(cv, "20-25% del precio", x2+10, y-30, "Helvetica-Bold", 11, col)
    else:
        txt(cv, "MENSUALIDAD ESTIMADA", x2+10, y-12, "Helvetica", 7, GRIS_MEDIO)
        txt(cv, f"${men:,.0f}", x2+10, y-30, "Helvetica-Bold", 16, NEGRO)

    # ════════════════════════════════════════════════
    # SECCIÓN 5 — MENSAJE EMOCIONAL  (y: ~470 → 380)
    # ════════════════════════════════════════════════
    y -= 60
    hline(cv, M, W-M, y+6)
    y -= 6

    # Título emocional
    txt(cv, msg["titulo"], M, y, "Helvetica-Bold", 13, NEGRO)
    frect(cv, M, y-5, 42, 2, col)
    y -= 20

    # Cuerpo del mensaje — word wrap en ancho completo
    y = wrap_text(cv, msg["cuerpo"], M, y, CW, "Helvetica", 9.5, GRIS_OSCURO, leading=15)
    y -= 10

    # ════════════════════════════════════════════════
    # SECCIÓN 6 — PLAN DE ACCIÓN (si aplica)  (y: ~360 → 290)
    # ════════════════════════════════════════════════
    if msg["plan_lbl"] and msg["plan"]:
        box_h = 16 + len(msg["plan"]) * 16 + 14
        frect(cv, M, y-box_h, CW, box_h, HexColor(SC_BG[sc]), r=5)
        srect(cv, M, y-box_h, CW, box_h, HexColor(SC_BORDE[sc]), r=5)
        txt(cv, msg["plan_lbl"], M+12, y-14, "Helvetica-Bold", 8, HexColor(SC_TXT[sc]))
        # Items en 2 columnas
        items = msg["plan"]
        half  = (len(items)+1)//2
        for i, item in enumerate(items[:half]):
            iy = y - 28 - i*16
            txt(cv, f"+ {item}", M+12, iy, "Helvetica", 8.5, GRIS_OSCURO)
        for i, item in enumerate(items[half:]):
            iy = y - 28 - i*16
            txt(cv, f"+ {item}", M+12+CW//2, iy, "Helvetica", 8.5, GRIS_OSCURO)
        y -= box_h + 12

    # ════════════════════════════════════════════════
    # SECCIÓN 7 — DOCUMENTOS  (y: ~280 → 240)
    # ════════════════════════════════════════════════
    txt(cv, "DOCUMENTACION REQUERIDA", M, y, "Helvetica-Bold", 8, ROJO)
    y -= 12
    chip_x = M
    for doc in docs[:6]:
        dw = cv.stringWidth(doc, "Helvetica", 8) + 18
        if chip_x + dw > W-M:
            chip_x = M; y -= 16
        frect(cv, chip_x, y-12, dw, 14, HexColor(SC_BG[sc]), r=4)
        srect(cv, chip_x, y-12, dw, 14, HexColor(SC_BORDE[sc]), r=4)
        txt(cv, doc, chip_x+9, y-4, "Helvetica", 8, HexColor(SC_TXT[sc]))
        chip_x += dw + 8
    y -= 26

    # ════════════════════════════════════════════════
    # SECCIÓN 8 — URGENCIA  (y: ~210 → 180)
    # ════════════════════════════════════════════════
    frect(cv, M, y-24, CW, 26, HexColor(SC_BG[sc]), r=5)
    srect(cv, M, y-24, CW, 26, HexColor(SC_BORDE[sc]), r=5)
    txt(cv, msg["urgencia"], M+CW//2, y-10, "Helvetica-Oblique", 8.5,
        HexColor(SC_TXT[sc]), "center")
    y -= 36

    # ════════════════════════════════════════════════
    # SECCIÓN 9 — CTA APARTAR UNIDAD (TODOS los scores)
    # ════════════════════════════════════════════════
    frect(cv, M, y-36, CW, 38, ROJO, r=6)
    txt(cv, "ASEGURA TU UNIDAD HOY", M+CW//2, y-12,
        "Helvetica-Bold", 11, BLANCO, "center")
    txt(cv, "Solicita tu apartado con un deposito de $5,000", M+CW//2, y-24,
        "Helvetica", 8.5, HexColor("#ffcccc"), "center")
    txt(cv, "Las unidades disponibles se asignan por orden de llegada", M+CW//2, y-34,
        "Helvetica", 7.5, HexColor("#ffaaaa"), "center")
    y -= 48

    # ════════════════════════════════════════════════
    # SECCIÓN 10 — CUENTA BBVA  (y: ~130 → 110)
    # ════════════════════════════════════════════════
    frect(cv, M, y-26, CW, 28, NEGRO, r=5)
    txt(cv, "BBVA  |  DAOSA SA DE CV  |  012320001250476847",
        M+CW//2, y-11, "Helvetica-Bold", 9, BLANCO, "center")
    txt(cv, "Incluye en el concepto tu nombre completo y envia comprobante a tu asesor",
        M+CW//2, y-21, "Helvetica", 7, HexColor("#888888"), "center")
    y -= 38

    # ════════════════════════════════════════════════
    # FOOTER — ASESOR + LEGAL  (y: ~70 → 20)
    # ════════════════════════════════════════════════
    hline(cv, M, W-M, y)
    y -= 14

    # Asesor izquierda
    txt(cv, asesor or "Asesor AutoScore AI", M, y, "Helvetica-Bold", 9, NEGRO)
    if tel_a:
        txt(cv, f"Tel: {tel_a}", M, y-12, "Helvetica", 8, GRIS_MEDIO)
    if correo_a:
        txt(cv, correo_a, M+100, y-12, "Helvetica", 8, GRIS_MEDIO)

    # Legal derecha
    txt(cv, "Este documento es de caracter informativo.",
        W-M, y, "Helvetica", 7, HexColor("#cccccc"), "right")
    txt(cv, "La aprobacion final depende de la evaluacion de la institucion financiera.",
        W-M, y-10, "Helvetica", 7, HexColor("#cccccc"), "right")

    # Línea bottom roja
    frect(cv, 0, 0, W, 4, ROJO)

    cv.showPage()
    cv.save()
    buf.seek(0)
    return buf



# ════════════════════════════════════════════
# PDF SOLICITUD DE CREDITO — 1 hoja editable
# ════════════════════════════════════════════
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
from io import BytesIO
import datetime

W, H = letter  # type: ignore  # 612 x 792 pts

# ── PALETA ────────────────────────────────────────────────────────
ROJO        = HexColor("#c3002f")
NEGRO       = HexColor("#111111")
GRIS_OSCURO = HexColor("#333333")
GRIS_MEDIO  = HexColor("#666666")
GRIS_CLARO  = HexColor("#cccccc")
GRIS_FONDO  = HexColor("#f5f5f5")
GRIS_BLOCK  = HexColor("#e8e8e8")  # franjas de seccion

def s_frect(c, x, y, w, h, color, lw=0):
    c.setFillColor(color)
    c.rect(x, y, w, h, fill=1, stroke=0)

def s_srect(c, x, y, w, h, color=GRIS_CLARO, lw=0.4):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.rect(x, y, w, h, fill=0, stroke=1)

def s_txt(c, s, x, y, font, size, color, align="left"):
    c.setFont(font, size)
    c.setFillColor(color)
    if align=="center": c.drawCentredString(x, y, s)
    elif align=="right": c.drawRightString(x, y, s)
    else: c.drawString(x, y, s)

def s_hline(c, x1, x2, y, color=GRIS_CLARO, lw=0.4):
    c.setStrokeColor(color); c.setLineWidth(lw)
    c.line(x1, y, x2, y)

def s_section_band(c, y, label, w_total=552):
    """Banda gris con titulo de seccion."""
    s_frect(c, 30, y-12, w_total, 14, GRIS_BLOCK)
    s_txt(c, label, 36, y-3, "Helvetica-Bold", 7, NEGRO)

def s_field(c, x, y, w, h, label, value="", show_border=True):
    """Campo del formulario con etiqueta arriba y valor adentro."""
    if show_border:
        s_srect(c, x, y-h, w, h, GRIS_CLARO, 0.4)
    # Etiqueta
    s_txt(c, label, x+3, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    # Valor
    if value:
        s_txt(c, str(value)[:60], x+4, y-h+4, "Helvetica-Bold", 7, NEGRO)

def s_checkbox(c, x, y, label, marked=False, size=6):
    """Checkbox con etiqueta."""
    s_srect(c, x, y, size, size, NEGRO, 0.5)
    if marked:
        s_txt(c, "x", x+1.2, y+1, "Helvetica-Bold", 6, NEGRO)
    s_txt(c, label, x+size+3, y+1, "Helvetica", 6, NEGRO)
    return c.stringWidth(label, "Helvetica", 6) + size + 8

def generar_pdf_solicitud(d: dict) -> BytesIO:
    """
    Genera el PDF de solicitud de credito persona fisica.
    Recibe dict con todos los campos del formulario expandido.
    """
    buf = BytesIO()
    cv  = canvas.Canvas(buf, pagesize=letter)
    cv.setTitle("Solicitud de Credito - AutoScore AI")

    fecha = datetime.date.today().strftime("%d / %m / %Y")

    # ════════════════════════════════════════════════════════════
    # PAGINA 1
    # ════════════════════════════════════════════════════════════

    # ── HEADER ───────────────────────────────────────────────────
    s_txt(cv, "SOLICITUD DE CREDITO PERSONA FISICA", 30, H-30, "Helvetica-Bold", 12, NEGRO)
    s_txt(cv, f"Fecha: {fecha}", W-30, H-30, "Helvetica", 9, NEGRO, "right")
    s_frect(cv, 30, H-36, 552, 1.5, ROJO)

    # ── DATOS DEL ASESOR Y FUENTE DE VENTA ────────────────────────
    s_section_band(cv, H-50, "DATOS DEL ASESOR Y FUENTE DE VENTA")
    y = H-54
    s_field(cv, 30,  y, 220, 18, "Nombre del Asesor",   d.get("asesor",""))
    s_field(cv, 250, y, 130, 18, "RFC del Asesor",      d.get("rfc_asesor",""))
    # Fuente de venta con checkboxes
    s_srect(cv, 380, y-18, 202, 18, GRIS_CLARO, 0.4)
    s_txt(cv, "Fuente de Venta", 383, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 386
    cx += s_checkbox(cv, cx, y-14, "BDC",      d.get("fuente_venta")=="BDC")
    cx += s_checkbox(cv, cx, y-14, "PISO",     d.get("fuente_venta")=="PISO")
    cx += s_checkbox(cv, cx, y-14, "CARTERA",  d.get("fuente_venta")=="CARTERA")

    # ── TIPO DE SOLICITUD ────────────────────────────────────────
    y -= 28
    s_section_band(cv, y, "TIPO DE SOLICITUD")
    y -= 16
    cx = 36
    cx += s_checkbox(cv, cx, y, "Credito Simple",      d.get("tipo_credito")=="Simple")
    cx += s_checkbox(cv, cx, y, "Arrendamiento",        d.get("tipo_credito")=="Arrendamiento")
    cx += s_checkbox(cv, cx, y, "Credi Taxi",           d.get("tipo_credito")=="Credi Taxi")
    cx += s_checkbox(cv, cx, y, "Subete",               d.get("tipo_credito")=="Subete")
    cx += s_checkbox(cv, cx, y, "Correo electronico",   d.get("tipo_credito")=="Correo")
    cx += s_checkbox(cv, cx, y, "Redes Sociales",       d.get("tipo_credito")=="Redes")

    # ── IDENTIFICACION DEL CLIENTE ───────────────────────────────
    y -= 14
    s_section_band(cv, y, "IDENTIFICACION DEL CLIENTE")
    y -= 16
    cx = 36
    cx += s_checkbox(cv, cx, y, "Persona Fisica",                  d.get("tipo_persona")=="PF")
    cx += s_checkbox(cv, cx, y, "Persona Fisica Actividad Empr.",  d.get("tipo_persona")=="PFAE")
    cx += s_checkbox(cv, cx, y+0, "Cliente Recompra:",  False, 0)
    cx += s_checkbox(cv, cx, y, "SI",  d.get("recompra")=="SI")
    cx += s_checkbox(cv, cx, y, "NO",  d.get("recompra")=="NO")
    cx += s_checkbox(cv, cx, y+0, "Empleado:", False, 0)
    cx += s_checkbox(cv, cx, y, "SI",  d.get("empleado")=="SI")
    cx += s_checkbox(cv, cx, y, "NO",  d.get("empleado")=="NO")

    # ── DATOS DEL ACREDITADO ─────────────────────────────────────
    y -= 14
    s_section_band(cv, y, "DATOS DEL ACREDITADO")
    y -= 4

    # Fila 1: Apellidos y nombres (4 cols)
    s_field(cv, 30,  y,  138, 18, "Apellido Paterno",  d.get("apellido_paterno",""))
    s_field(cv, 168, y,  138, 18, "Apellido Materno",  d.get("apellido_materno",""))
    s_field(cv, 306, y,  138, 18, "Primer Nombre",     d.get("primer_nombre",""))
    s_field(cv, 444, y,  138, 18, "Segundo Nombre",    d.get("segundo_nombre",""))

    y -= 22
    # Fila 2: Fecha nacimiento, RFC, CURP, Pais, Estado, Sexo
    s_field(cv, 30,  y, 78, 18, "Fecha de Nacimiento", d.get("fecha_nacimiento",""))
    s_field(cv, 108, y, 90, 18, "RFC (con Homoclave)", d.get("rfc_cliente",""))
    s_field(cv, 198, y, 86, 18, "CURP",                 d.get("curp",""))
    s_field(cv, 284, y, 90, 18, "Pais de nacimiento",   d.get("pais_nacimiento","Mexico"))
    s_field(cv, 374, y, 100,18, "Estado de nacimiento", d.get("estado_nacimiento",""))
    # Sexo con checkboxes
    s_srect(cv, 474, y-18, 108, 18, GRIS_CLARO, 0.4)
    s_txt(cv, "Sexo", 477, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 480
    cx += s_checkbox(cv, cx, y-14, "F",  d.get("sexo")=="F")
    cx += s_checkbox(cv, cx, y-14, "M",  d.get("sexo")=="M")

    y -= 22
    # Fila 3: Nacionalidad, Numero celular, Correo
    s_srect(cv, 30, y-18, 130, 18, GRIS_CLARO, 0.4)
    s_txt(cv, "Nacionalidad", 33, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 36
    cx += s_checkbox(cv, cx, y-14, "Mexicana",   d.get("nacionalidad")=="Mexicana")
    cx += s_checkbox(cv, cx, y-14, "Extranjera", d.get("nacionalidad")=="Extranjera")

    s_field(cv, 160, y, 120, 18, "Numero de Celular",  d.get("celular",""))
    s_field(cv, 280, y, 302, 18, "Correo electronico",  d.get("correo_cliente",""))

    y -= 22
    # Fila 4: Estado civil
    s_srect(cv, 30, y-18, 552, 18, GRIS_CLARO, 0.4)
    s_txt(cv, "Estado Civil", 33, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 36
    cx += s_checkbox(cv, cx, y-14, "Soltero",   d.get("estado_civil")=="Soltero")
    cx += s_checkbox(cv, cx, y-14, "Casado",    d.get("estado_civil")=="Casado")
    cx += s_checkbox(cv, cx, y-14, "Divorciado",d.get("estado_civil")=="Divorciado")
    cx += s_checkbox(cv, cx, y-14, "Viudo",     d.get("estado_civil")=="Viudo")
    cx += s_checkbox(cv, cx, y-14, "Union Libre",d.get("estado_civil")=="Union Libre")
    cx += 10
    s_txt(cv, "Regimen:", cx, y-13, "Helvetica-Bold", 5.5, GRIS_OSCURO)
    cx += 30
    cx += s_checkbox(cv, cx, y-14, "Bienes Separados",  d.get("regimen")=="Bienes Separados")
    cx += s_checkbox(cv, cx, y-14, "Sociedad Conyugal", d.get("regimen")=="Sociedad Conyugal")

    y -= 22
    # Fila 5: Identificacion
    s_srect(cv, 30, y-18, 432, 18, GRIS_CLARO, 0.4)
    s_txt(cv, "Tipo de identificacion", 33, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 36
    cx += s_checkbox(cv, cx, y-14, "Credencial Votar", d.get("tipo_id")=="INE")
    cx += s_checkbox(cv, cx, y-14, "Pasaporte",         d.get("tipo_id")=="Pasaporte")
    cx += s_checkbox(cv, cx, y-14, "Forma Migratoria",  d.get("tipo_id")=="Forma Migratoria")
    cx += s_checkbox(cv, cx, y-14, "Cedula Profesional",d.get("tipo_id")=="Cedula")
    s_field(cv, 462, y, 120, 18, "No. de Identificacion", d.get("num_id",""))

    # ── CONYUGE ──────────────────────────────────────────────────
    y -= 32
    s_section_band(cv, y, "CONYUGE O CONCUBINO(A)")
    y -= 4
    s_field(cv, 30,  y, 138, 18, "Apellido Paterno",       d.get("c_apellido_paterno",""))
    s_field(cv, 168, y, 138, 18, "Apellido Materno",       d.get("c_apellido_materno",""))
    s_field(cv, 306, y, 138, 18, "Primer Nombre",          d.get("c_primer_nombre",""))
    s_field(cv, 444, y, 80,  18, "Segundo Nombre",         d.get("c_segundo_nombre",""))
    s_field(cv, 524, y, 58,  18, "Dependientes",           str(d.get("dependientes","")))

    # ── DATOS DEL DOMICILIO ──────────────────────────────────────
    y -= 32
    s_section_band(cv, y, "DATOS DEL DOMICILIO")
    y -= 4
    # Situacion vivienda
    s_srect(cv, 30, y-18, 200, 18, GRIS_CLARO, 0.4)
    s_txt(cv, "Situacion de Vivienda", 33, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 36
    cx += s_checkbox(cv, cx, y-14, "Propia",      d.get("vivienda")=="Propia")
    cx += s_checkbox(cv, cx, y-14, "Renta",       d.get("vivienda")=="Renta")
    cx += s_checkbox(cv, cx, y-14, "Hipoteca",    d.get("vivienda")=="Hipoteca")
    cx += s_checkbox(cv, cx, y-14, "Familiar",    d.get("vivienda")=="Familiar")

    s_field(cv, 230, y, 90, 18, "Valor Aproximado",        d.get("valor_vivienda",""))
    s_field(cv, 320, y, 90, 18, "Valor Renta/Hipoteca",    d.get("valor_renta",""))
    s_field(cv, 410, y, 86, 18, "Telefono Fijo",           d.get("tel_fijo",""))
    s_field(cv, 496, y, 86, 18, "Tel. Recados",            d.get("tel_recados",""))

    y -= 22
    # Direccion completa
    s_field(cv, 30,  y, 250, 18, "Calle, Av. o Via",       d.get("calle",""))
    s_field(cv, 280, y, 60,  18, "No. Ext.",               d.get("num_ext",""))
    s_field(cv, 340, y, 60,  18, "No. Int.",               d.get("num_int",""))
    s_field(cv, 400, y, 110, 18, "Colonia",                d.get("colonia",""))
    s_field(cv, 510, y, 72,  18, "Pais Residencia",        d.get("pais_residencia","Mexico"))

    y -= 22
    s_field(cv, 30,  y, 130, 18, "Entre calles",           d.get("entre_calles",""))
    s_field(cv, 160, y, 100, 18, "Delegacion/Municipio",   d.get("municipio",""))
    s_field(cv, 260, y, 90,  18, "Ciudad",                 d.get("ciudad",""))
    s_field(cv, 350, y, 80,  18, "Estado",                 d.get("estado",""))
    s_field(cv, 430, y, 50,  18, "C.P.",                   d.get("cp",""))
    s_field(cv, 480, y, 102, 18, "Tiempo Residencia",      d.get("tiempo_residencia",""))

    # ── OCUPACION ────────────────────────────────────────────────
    y -= 32
    s_section_band(cv, y, "OCUPACION DEL ACREDITADO")
    y -= 4
    s_srect(cv, 30, y-18, 552, 18, GRIS_CLARO, 0.4)
    s_txt(cv, "Ocupacion", 33, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 36
    cx += s_checkbox(cv, cx, y-14, "Empleado S. Privado",      d.get("ocupacion")=="Privado")
    cx += s_checkbox(cv, cx, y-14, "Empleado S. Publico",      d.get("ocupacion")=="Publico")
    cx += s_checkbox(cv, cx, y-14, "Independiente",            d.get("ocupacion")=="Independiente")
    cx += s_checkbox(cv, cx, y-14, "Jubilado",                 d.get("ocupacion")=="Jubilado")
    cx += s_checkbox(cv, cx, y-14, "Ama de casa",              d.get("ocupacion")=="Ama de casa")
    cx += s_checkbox(cv, cx, y-14, "Estudiante",               d.get("ocupacion")=="Estudiante")
    cx += s_checkbox(cv, cx, y-14, "Otro",                     d.get("ocupacion")=="Otro")

    y -= 22
    # Tipo contrato + ingresos
    s_srect(cv, 30, y-18, 200, 18, GRIS_CLARO, 0.4)
    s_txt(cv, "Tipo de Contrato", 33, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 36
    cx += s_checkbox(cv, cx, y-14, "Fijo",      d.get("contrato")=="Fijo")
    cx += s_checkbox(cv, cx, y-14, "Temporal",  d.get("contrato")=="Temporal")
    s_field(cv, 230, y, 100, 18, "Ingreso Fijo $",     d.get("ingreso_fijo",""))
    s_field(cv, 330, y, 90,  18, "Variable $",          d.get("ingreso_variable",""))
    s_field(cv, 420, y, 80,  18, "Ahorro/Cheques $",    d.get("ahorro",""))
    s_field(cv, 500, y, 82,  18, "Ingreso Acumulable",  d.get("ingreso_acumulable",""))

    y -= 22
    s_field(cv, 30,  y, 270, 18, "Nombre de la Empresa",  d.get("empresa",""))
    s_field(cv, 300, y, 90,  18, "Fecha de Ingreso",       d.get("fecha_ingreso",""))
    s_srect(cv, 390, y-18, 96, 18, GRIS_CLARO, 0.4)
    s_txt(cv, "Nacionalidad Empresa", 393, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 396
    cx += s_checkbox(cv, cx, y-14, "Mex",  d.get("nac_empresa")=="Mexicana")
    cx += s_checkbox(cv, cx, y-14, "Ext",  d.get("nac_empresa")=="Extranjera")
    s_srect(cv, 486, y-18, 96, 18, GRIS_CLARO, 0.4)
    s_txt(cv, "Tipo Empresa", 489, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 492
    cx += s_checkbox(cv, cx, y-14, "Priv",  d.get("tipo_empresa")=="Privada")
    cx += s_checkbox(cv, cx, y-14, "Pub",   d.get("tipo_empresa")=="Publica")

    y -= 22
    s_field(cv, 30,  y, 552, 18, "Descripcion del empleo o actividad",  d.get("descripcion_empleo",""))

    y -= 22
    s_field(cv, 30,  y, 280, 18, "Actividad Especifica de la Empresa", d.get("actividad_empresa",""))
    s_field(cv, 310, y, 136, 18, "Telefono Empresa",                    d.get("tel_empresa",""))
    s_field(cv, 446, y, 136, 18, "Telefono Alterno",                    d.get("tel_alterno",""))

    y -= 22
    s_field(cv, 30,  y, 200, 18, "Domicilio Empresa - Calle",         d.get("dom_empresa",""))
    s_field(cv, 230, y, 50,  18, "No. Ext.",                            d.get("emp_num_ext",""))
    s_field(cv, 280, y, 50,  18, "No. Int.",                            d.get("emp_num_int",""))
    s_field(cv, 330, y, 90,  18, "Colonia",                             d.get("emp_colonia",""))
    s_field(cv, 420, y, 80,  18, "Municipio",                           d.get("emp_municipio",""))
    s_field(cv, 500, y, 50,  18, "Estado",                              d.get("emp_estado",""))
    s_field(cv, 550, y, 32,  18, "C.P.",                                d.get("emp_cp",""))

    y -= 22
    s_field(cv, 30,  y, 300, 18, "Antiguedad en el empleo",  d.get("antiguedad_empleo",""))
    s_field(cv, 330, y, 252, 18, "Nombre del Jefe Inmediato", d.get("jefe_inmediato",""))

    # ── REFERENCIAS PERSONALES ───────────────────────────────────
    y -= 32
    s_section_band(cv, y, "DATOS GENERALES DE REFERENCIAS")
    y -= 4

    for i in range(1, 4):
        prefijo = f"ref{i}_"
        ref_y = y
        # Numero de referencia
        s_frect(cv, 30, ref_y-12, 14, 14, ROJO)
        s_txt(cv, str(i), 37, ref_y-3, "Helvetica-Bold", 8, white, "center")
        # PROBLEMA 3: nombre completo en un campo ancho + parentesco
        s_field(cv, 46,  ref_y, 330, 14, "Nombre Completo",    d.get(prefijo+"nombre_completo",""))
        s_field(cv, 376, ref_y, 206, 14, "Parentesco",         d.get(prefijo+"parentesco",""))

        ref_y -= 14
        s_field(cv, 46,  ref_y, 130, 14, "Tel. Celular",       d.get(prefijo+"tel_cel",""))
        s_field(cv, 176, ref_y, 100, 14, "Horario Localizar",  d.get(prefijo+"horario",""))
        s_field(cv, 276, ref_y, 306, 14, "Lugar Localizacion", d.get(prefijo+"lugar",""))
        y = ref_y - 16

    # Footer pagina 1
    s_txt(cv, "* Los numeros telefonicos deben ser de 10 digitos", 30, 28, "Helvetica-Oblique", 6.5, GRIS_MEDIO)
    s_txt(cv, "Pagina 1 de 1", 30, 16, "Helvetica-Bold", 7, NEGRO)
    s_txt(cv, "AutoScore AI · Aprobacion Inteligente", W-30, 16, "Helvetica-Bold", 7, ROJO, "right")
    s_frect(cv, 30, 10, 552, 1, ROJO)

    cv.showPage()
    cv.save()
    buf.seek(0)
    return buf


# APP PRINCIPAL
# ══════════════════════════════════════════
st.set_page_config(page_title="AutoScore AI", page_icon="🚗", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Exo+2:wght@300;400;500;600;700&display=swap');

/* ══════════════════════════════════════════
   NISSAN BRAND PALETTE
   Rojo #c3002f · Negro #000 · Blanco #fff
   Gris form #f5f5f5 · Gris card #1a1a1a
══════════════════════════════════════════ */

/* ─── BASE ─────────────────────────────── */
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"], section.main {
    background: #ffffff !important;
    color: #111 !important;
}
[data-testid="stAppViewContainer"]::before {
    content: ""; position: fixed; inset: 0;
    background-image:
        linear-gradient(rgba(195,0,47,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(195,0,47,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none; z-index: 0;
}
.block-container {
    position: relative; z-index: 1;
    padding: 1rem 0 2rem 0 !important;
    max-width: 100% !important;
}
/* Panel derecho — scroll independiente para no cortar contenido */
/* Ambas columnas arrancan desde el mismo punto vertical */
[data-testid="stHorizontalBlock"] {
    align-items: flex-start !important;
}
/* Separación entre sec-label y primer input */
.sec-label + div,
.sec-label + [data-testid="stHorizontalBlock"] {
    margin-top: 8px !important;
}
*, *::before, *::after {
    font-family: 'Exo 2', sans-serif !important;
    box-sizing: border-box;
}

/* ─── TOPBAR ────────────────────────────── */
.topbar-wrap { display: none; }
.topbar-title {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.4rem; font-weight: 700;
    color: #ffffff; letter-spacing: 0.1em; line-height: 1;
}
.topbar-sub {
    color: #c3002f; font-size: 0.6rem;
    letter-spacing: 0.18em; text-transform: uppercase; margin-top: 2px;
}
.topbar-divider {
    display: inline-block; width: 1px; height: 34px;
    background: #222; margin: 0 14px; vertical-align: middle;
}
.topbar-desc { color: #555; font-size: 0.68rem; letter-spacing: 0.04em; }
.topbar-badge {
    background: rgba(195,0,47,0.12);
    border: 1px solid rgba(195,0,47,0.3);
    border-radius: 50px; padding: 4px 12px;
    font-size: 0.6rem; color: #c3002f;
    letter-spacing: 0.1em; text-transform: uppercase; font-weight: 600;
}

/* ─── SECTION LABEL ─────────────────────── */
.sec-label {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.68rem; font-weight: 700;
    color: #c3002f; text-transform: uppercase;
    letter-spacing: 0.14em; margin: 22px 0 10px;
    display: flex; align-items: center; gap: 7px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(195,0,47,0.2);
}
.sec-label:first-child { margin-top: 16px; }

/* ─── PANEL FORMULARIO — gris claro ──────── */
[data-testid="column"]:first-child .sec-label {
    color: #c3002f !important;
    border-bottom-color: rgba(195,0,47,0.2) !important;
}
[data-testid="column"]:first-child label,
[data-testid="column"]:first-child [data-testid="stWidgetLabel"] p {
    color: #c3002f !important;
}
[data-testid="column"]:last-child label,
[data-testid="column"]:last-child [data-testid="stWidgetLabel"] p {
    color: #555 !important;
}

/* ─── INPUTS ────────────────────────────── */
.stTextInput input, .stNumberInput input {
    background: #ffffff !important;
    color: #111 !important;
    border: 1px solid #ddd !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    font-size: 0.82rem !important;
    width: 100% !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #c3002f !important;
    box-shadow: 0 0 0 2px rgba(195,0,47,0.12) !important;
}
.stTextInput input::placeholder, .stNumberInput input::placeholder {
    color: #bbb !important;
}
.stSelectbox > div > div {
    background: #ffffff !important;
    color: #111 !important;
    border: 1px solid #ddd !important;
    border-radius: 8px !important;
    padding: 2px 8px !important;
    font-size: 0.82rem !important;
}
label, [data-testid="stWidgetLabel"] p {
    color: #c3002f !important;
    font-size: 0.65rem !important; font-weight: 600 !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
    margin-bottom: 2px !important;
}
.stNumberInput button {
    background: #f5f5f5 !important;
    border: 1px solid #ddd !important;
    color: #c3002f !important; border-radius: 6px !important;
    padding: 2px 8px !important; width: auto !important; margin: 0 !important;
}
/* Grid pattern solo en fondo gris — no en panels */
[data-testid="stAppViewContainer"]::before { display: none !important; }
div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
/* Dentro del form de solicitud, referencias necesitan más espacio */
[data-testid="stForm"] div[data-testid="stVerticalBlock"] { gap: 0.4rem !important; }

/* ─── BOTÓN PRINCIPAL ────────────────────── */
.stFormSubmitButton > button, .stButton > button {
    width: 100% !important;
    background: #c3002f !important;
    color: #fff !important; border: none !important;
    border-radius: 50px !important; padding: 12px 24px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.95rem !important; font-weight: 700 !important;
    letter-spacing: 0.13em !important; text-transform: uppercase !important;
    box-shadow: 0 4px 20px rgba(195,0,47,0.35) !important;
    margin-top: 6px !important;
    transition: transform 0.15s, box-shadow 0.15s, background 0.15s !important;
}
.stFormSubmitButton > button:hover, .stButton > button:hover {
    background: #e8001a !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 28px rgba(195,0,47,0.5) !important;
}

/* ─── ALERTS ──────────────────────────────── */
.stSuccess > div {
    background: #f0fdf4 !important; border: 1px solid #bbf7d0 !important;
    border-radius: 9px !important; color: #166534 !important; font-size: 0.82rem !important;
}
.stWarning > div {
    background: #fffbeb !important; border: 1px solid #fde68a !important;
    border-radius: 9px !important; color: #92400e !important; font-size: 0.82rem !important;
}
.stError > div {
    background: #fff1f2 !important; border: 1px solid #fecdd3 !important;
    border-radius: 9px !important; color: #9f1239 !important; font-size: 0.82rem !important;
}
.stInfo > div {
    background: #f8f9fa !important; border: 1px solid #e2e8f0 !important;
    border-radius: 9px !important; color: #334155 !important; font-size: 0.82rem !important;
}

hr { border:none !important; border-top:1px solid #1a1a1a !important; margin:8px 0 !important; }
.stCaption p { color:#c3002f !important; font-size:0.72rem !important; }

.stLinkButton a {
    background: #1a1a1a !important; border: 1px solid #333 !important;
    color: #fff !important; border-radius: 8px !important;
    font-weight: 600 !important; font-size: 0.8rem !important;
    width: 100% !important; display: block !important;
    text-align: center !important; padding: 9px !important;
}
.stDownloadButton > button {
    background: #c3002f !important;
    border: 1px solid #c3002f !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    width: 100% !important;
    padding: 12px !important;
    letter-spacing: 0.06em !important;
    box-shadow: 0 2px 12px rgba(195,0,47,0.3) !important;
}
.stDownloadButton > button:hover {
    background: #e8001a !important;
    box-shadow: 0 4px 20px rgba(195,0,47,0.5) !important;
}

/* ─── EXPANDER ────────────────────────────── */
[data-testid="stExpander"] {
    background: #111 !important;
    border: 1px solid #222 !important;
    border-radius: 10px !important; overflow: visible !important;
}
[data-testid="stExpander"] details { background: transparent !important; }
[data-testid="stExpander"] details summary {
    background: #111 !important; border-radius: 10px !important;
    padding: 10px 14px !important; cursor: pointer !important;
    position: relative !important; z-index: 1 !important;
}
[data-testid="stExpander"] details summary::marker,
[data-testid="stExpander"] details summary::-webkit-details-marker {
    display: none !important; content: "" !important;
}
[data-testid="stExpander"] details summary p,
[data-testid="stExpander"] details summary div,
[data-testid="stExpander"] details summary span {
    color: #888 !important; font-size: 0.78rem !important;
    font-weight: 600 !important; background: transparent !important;
    border: none !important; box-shadow: none !important;
}
[data-testid="stExpander"] details > div {
    background: #0d0d0d !important;
    border-top: 1px solid #222 !important;
    padding: 12px 14px !important;
    border-radius: 0 0 10px 10px !important;
    position: relative !important; z-index: 0 !important;
}
[data-testid="stExpander"] details > div * { background: transparent !important; box-shadow: none !important; }
[data-testid="stExpander"] svg { color: #555 !important; fill: #555 !important; }

/* ─── RESULTADO UI ────────────────────────── */
.prob-hero {
    display: flex; align-items: flex-end; gap: 10px;
    padding: 16px 20px 12px;
    background: #000;
    border: 1px solid #1a1a1a;
    border-radius: 14px; margin-bottom: 10px;
    position: relative; overflow: hidden;
}
.prob-hero::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: #c3002f;
}
.prob-label { font-size: 0.75rem; color: #aaa; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px; }
.prob-sublabel { font-family: 'Rajdhani', sans-serif !important; font-size: 0.88rem; color: #cbd5e1; letter-spacing: 0.04em; }

.score-badge {
    display: inline-flex; align-items: center; gap: 10px;
    padding: 10px 16px; border-radius: 12px; margin: 6px 0; width: 100%;
}
.score-badge .score-em  { font-size: 1.5rem; }
.score-badge .score-lbl { font-family: 'Rajdhani', sans-serif !important; font-size: 1.1rem; font-weight: 700; letter-spacing: 0.06em; }
.score-badge .score-sub { font-size: 0.75rem; color: #94a3b8; margin-top: 1px; }

.metrics-2 { display: flex; gap: 10px; margin: 8px 0; }
.metric-tile { flex: 1; border-radius: 10px; padding: 10px 14px; }
.metric-tile.blue   { background: #000; border: 1px solid #1a1a1a; }
.metric-tile.purple { background: #1a0006; border: 1px solid rgba(195,0,47,0.25); }
.metric-tile .mt-lbl { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; font-weight: 600; }
.metric-tile.blue   .mt-lbl { color: #7dd3fc; }
.metric-tile.purple .mt-lbl { color: #c3002f; }
.metric-tile .mt-val { font-family: 'Rajdhani', sans-serif !important; font-size: 1.35rem; font-weight: 700; color: #fff; line-height: 1; }

.semaforo {
    display: flex; align-items: center; justify-content: center;
    gap: 10px; padding: 10px 16px; border-radius: 10px;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase; margin: 8px 0;
}
.semaforo.verde    { background:#f0fdf4; border:1px solid #bbf7d0; color:#166534; }
.semaforo.amarillo { background:#fffbeb; border:1px solid #fde68a; color:#92400e; }
.semaforo.naranja  { background:#fff7ed; border:1px solid #fed7aa; color:#9a3412; }
.semaforo.rojo     { background:#fff1f2; border:1px solid #fecdd3; color:#9f1239; }

.msg-cliente {
    background: #0d0d0d; border: 1px solid #1a1a1a;
    border-left: 3px solid #c3002f; border-radius: 0 9px 9px 0;
    padding: 10px 14px; color: #cbd5e1;
    font-size: 0.85rem; line-height: 1.6; margin: 6px 0;
}

.estrategia-box {
    background: #1a0006; border: 1px solid rgba(195,0,47,0.25);
    border-left: 3px solid #c3002f; border-radius: 0 9px 9px 0;
    padding: 10px 14px; color: #f87171;
    font-size: 0.78rem; line-height: 1.6;
}

.sec-label-result {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.68rem; font-weight: 700; color: #555;
    text-transform: uppercase; letter-spacing: 0.14em;
    margin: 10px 0 5px; display: flex; align-items: center; gap: 7px;
    padding-bottom: 5px; border-bottom: 1px solid #1a1a1a;
}

.alerta-chip {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 11px; border-radius: 7px;
    font-size: 0.74rem; font-weight: 600;
    margin: 3px 0; letter-spacing: 0.02em;
}
.alerta-chip.ok  { background:#f0fdf4; border:1px solid #bbf7d0; color:#166534; }
.alerta-chip.bad { background:#fff1f2; border:1px solid #fecdd3; color:#9f1239; }

.cond-box {
    background: #1a0000; border: 1px solid rgba(220,38,38,0.3);
    border-left: 3px solid #dc2626;
    border-radius: 9px; padding: 10px 14px;
    color: #dc2626; font-size: 0.76rem;
    line-height: 1.75; margin: 4px 0; font-weight: 600;
}

.cuenta-box {
    background: #000; border: 1px solid #1a1a1a;
    border-top: 2px solid #c3002f;
    border-radius: 9px; padding: 10px 14px; margin: 4px 0;
}

.security-line {
    text-align: center; color: #333; font-size: 0.68rem;
    letter-spacing: 0.06em; margin-top: 8px;
    display: flex; align-items: center; justify-content: center; gap: 5px;
}

/* Botón notas internas — alineado como fila de alerta */
div[data-testid="stButton"]:has(button[key="btn_estrategia"]) {
    width: 100% !important;
}
div[data-testid="stButton"]:has(button[key="btn_estrategia"]) > button {
    background: #111 !important;
    border: 1px solid #2a2a2a !important;
    color: #555 !important;
    border-radius: 7px !important;
    padding: 6px 11px !important;
    font-size: 0.74rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    text-transform: none !important;
    box-shadow: none !important;
    width: 100% !important;
    text-align: left !important;
    margin: 3px 0 !important;
}
div[data-testid="stButton"]:has(button[key="btn_estrategia"]) > button:hover {
    border-color: rgba(195,0,47,0.4) !important;
    color: #888 !important;
    background: #161616 !important;
    transform: none !important;
    box-shadow: none !important;
}

.panel-left  { border-right: 1px solid #1a1a1a; padding-right: 16px; }
.panel-right { padding-left: 16px; }
</style>
""", unsafe_allow_html=True)

# ── LOGO BASE64 ────────────────────────────────────────────────────
_LOGO_SRC = get_logo_b64()

# ── SESSION STATE ──────────────────────────────────────────────────
for k, v in {
    "resultado": None, "cotitular_activo": False,
    "cotitular_resultado": None, "ingreso": 0.0, "mensualidad": 0.0,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── TOPBAR — solo línea roja, sin logo duplicado ───────────────────
st.markdown("""
<div style="height:3px;background:#c3002f;margin-bottom:12px;"></div>
""", unsafe_allow_html=True)

# ── BANNER PILOTO ─────────────────────────────────────────────────
st.markdown("""
<div style="background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #f59e0b;
    border-radius:8px;padding:8px 16px;margin-bottom:16px;display:flex;align-items:center;gap:10px;">
  <span style="font-size:1rem;">🧪</span>
  <div>
    <span style="font-size:0.74rem;font-weight:700;color:#92400e;">PILOTO INTERNO — Motor v3.1</span>
    <span style="font-size:0.7rem;color:#a16207;margin-left:8px;">
      Herramienta de perfilamiento financiero orientativo.
      El resultado NO sustituye la decisión oficial de la financiera.
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── BUSCADOR GLOBAL DE FOLIO ──────────────────────────────────────
if "datos_precargados" not in st.session_state:
    st.session_state.datos_precargados = {}
if "folio_actual" not in st.session_state:
    st.session_state.folio_actual = None

# Panel fijo siempre visible — layout tipo SaaS
st.markdown("""
<div style="background:#0d0d0d;border:1px solid #1e1e1e;border-left:3px solid #c3002f;
    border-radius:10px;padding:14px 18px 10px;margin-bottom:20px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
    <span style="font-size:0.8rem;">🔍</span>
    <span style="font-family:'Rajdhani',sans-serif;font-size:0.78rem;font-weight:700;
        color:#c3002f;text-transform:uppercase;letter-spacing:0.1em;">
      Buscar solicitud existente
    </span>
    <span style="font-size:0.68rem;color:#555;margin-left:4px;">
      — ingresa el folio para cargar los datos del cliente
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# CSS input folio blanco sobre negro
st.markdown("""
<style>
input[aria-label*="Folio AS-"] {
    background:#1a1a1a!important;color:#fff!important;
    border:1px solid #c3002f!important;border-radius:8px!important;
}
input[aria-label*="Folio AS-"]::placeholder{color:#555!important;}
</style>
""", unsafe_allow_html=True)

_bcol1, _bcol2, _bcol3 = st.columns([4, 1, 1])
with _bcol1:
    folio_global = st.text_input(
        "Folio AS-AAAA-NNNN",
        value=st.session_state.folio_actual or "",
        key="folio_buscar_global",
        placeholder="Ej: AS-2026-0001",
        label_visibility="collapsed",
    )
with _bcol2:
    if st.button("🔍 Buscar", key="btn_buscar_global", use_container_width=True):
        if folio_global.strip():
            datos_enc = buscar_solicitud_por_folio(folio_global.strip())
            if datos_enc:
                st.session_state.datos_precargados = datos_enc
                st.session_state.folio_actual = folio_global.strip().upper()
                st.session_state.mostrar_solicitud = True
                st.success(f"✅ {st.session_state.folio_actual} cargado")
                st.rerun()
            else:
                st.error(f"❌ No encontrado: {folio_global}")
        else:
            st.warning("Ingresa un folio")
with _bcol3:
    # CAMBIO 2 — Botón + NUEVA con lógica completa de limpieza
    if st.button("＋ Nueva", key="btn_nueva_global", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Indicador de modo edición activo
if st.session_state.get("folio_actual"):
    st.markdown(f"""
    <div style="background:#0d1a0d;border:1px solid #166534;border-left:3px solid #22c55e;
        border-radius:7px;padding:6px 14px;margin:-8px 0 16px;font-size:0.74rem;color:#4ade80;">
      ✏️ Editando folio <b style="font-family:'Rajdhani',sans-serif;letter-spacing:0.06em;">
      {st.session_state.folio_actual}</b> — modifica los campos y analiza de nuevo
    </div>
    """, unsafe_allow_html=True)

# ── DOS COLUMNAS ───────────────────────────────────────────────────
col_izq, col_der = st.columns([1, 1], gap="medium")

# ╔══════════════════════════════════╗
# ║      IZQUIERDA — FORMULARIO      ║
# ╚══════════════════════════════════╝
with col_izq:

    # LOGO arriba del formulario
    _fl1, _fl2, _fl3 = st.columns([1, 3, 1])
    with _fl2:
        st.image("AUTOSCOREIA.png", use_container_width=True)
    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

    with st.form("formulario"):

        # ASESOR — ahora dentro del form para alineación consistente
        st.markdown('<div class="sec-label">👤 Datos del Asesor</div>', unsafe_allow_html=True)
        a1, a2 = st.columns(2)
        with a1: asesor = st.text_input("Nombre asesor", placeholder="Nombre completo")
        with a2: rfc    = st.text_input("RFC asesor", placeholder="XAXX010101000")
        b1, b2 = st.columns(2)
        with b1: telefono_asesor = st.text_input("Teléfono asesor", placeholder="55 1234 5678")
        with b2: correo_asesor   = st.text_input("Correo asesor", placeholder="asesor@correo.com")

        # CLIENTE
        st.markdown('<div class="sec-label">👥 Datos del Cliente</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: nombre_cliente = st.text_input("Nombre cliente", placeholder="Nombre completo")
        with c2: telefono       = st.text_input("Teléfono", placeholder="55 9876 5432")
        correo = st.text_input("Correo cliente", placeholder="cliente@correo.com")

        # PERFIL
        st.markdown('<div class="sec-label">📊 Perfil Financiero</div>', unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)
        with p1: edad        = st.number_input("Edad", 18, 73, 18)
        with p2: ingreso     = st.number_input("Ingreso mensual ($)", min_value=6500.0, value=6500.0, step=500.0, format="%.0f")
        with p3: tipo_ingreso= st.selectbox("Tipo de ingreso", ["Nómina","Independiente","No comprueba"])

        q1, q2, q3 = st.columns(3)
        with q1: negocio_casa  = st.selectbox(
            "Negocio en domicilio (solo independientes)", [1,2,0],
            index=2,
            format_func=lambda x:"Sí" if x==1 else ("No" if x==2 else "— No aplica —"),
            help="Aparece como 'No aplica' si el tipo de ingreso no es Independiente. Activa la alerta de investigación física cuando aplica."
        )
        with q2: domicilio     = st.selectbox("Antigüedad domicilio", [1,2,3], format_func=lambda x:["<1 año","1-3 años","+3 años"][x-1])
        with q3: domicilio_buro= st.selectbox("Domicilio = ID", [1,2], format_func=lambda x:"Sí" if x==1 else "No")
        if tipo_ingreso == "Independiente":
            st.caption("ℹ️ Para independientes: indica si el negocio está en su domicilio (activa investigación física)")
        else:
            st.caption("ℹ️ El campo 'Negocio en domicilio' solo aplica para tipo de ingreso Independiente — déjalo en 'No aplica'")

        # VEHÍCULO — sin consultas (se mueven a Historial)
        st.markdown('<div class="sec-label">🚗 Datos del Vehículo</div>', unsafe_allow_html=True)
        v1, v2, v3 = st.columns(3)
        with v1: precio    = st.number_input("Precio ($)", min_value=0.0, format="%0.0f")
        with v2: enganche  = st.number_input("Enganche ($)", min_value=0.0, format="%0.0f")
        with v3: plazo     = st.selectbox("Plazo", [12,24,36,48,60,72])

        # HISTORIAL — consultas aquí, una sola vez
        st.markdown('<div class="sec-label">🏦 Historial Crediticio</div>', unsafe_allow_html=True)
        h1, h2, h3 = st.columns(3)
        with h1: auto        = st.selectbox("Crédito auto previo", [1,2], format_func=lambda x:"Sí" if x==1 else "No")
        with h2: credinissan = st.selectbox("CrediNissan", [1,2], format_func=lambda x:"Sí" if x==1 else "No")
        with h3: hipotecario = st.selectbox("Hipotecario", [1,2,3], format_func=lambda x:["Bancario","Infonavit","No tiene"][x-1])

        i1, i2, i3 = st.columns(3)
        with i1: tarjeta_alta = st.selectbox("Tarjetas >$100K", [1,2], format_func=lambda x:"Sí" if x==1 else "No")
        with i2: tarjeta_baja = st.selectbox("Tarjetas <$100K", [1,2], format_func=lambda x:"Sí" if x==1 else "No")
        with i3: atrasos      = st.selectbox("Atrasos en buró", [1,2,3], format_func=lambda x:["1-30d","31-60d","+61d"][x-1])

        # CONSULTAS — campo único consolidado (reemplaza ambos anteriores)
        st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
        consultas = st.number_input(
            "¿Cuántas consultas recientes tiene en Buró? (últimos 6 meses)",
            min_value=0, max_value=20, value=0,
            help="Busca en el buró las consultas de los últimos 6 meses. Si no puedes distinguirlas del total, usa el número total visible."
        )

        # PERFIL COMPRA
        st.markdown('<div class="sec-label">🔥 Perfil de Compra</div>', unsafe_allow_html=True)
        k1, k2, k3 = st.columns(3)
        with k1: enganche_disp = st.selectbox("¿Tiene enganche?", [1,2], format_func=lambda x:"Sí" if x==1 else "No")
        with k2: compra_mes    = st.selectbox("¿Compra este mes?", [1,2], format_func=lambda x:"Sí" if x==1 else "No")
        with k3: unidad        = st.selectbox("¿Hay unidad?", [1,2], format_func=lambda x:"Sí" if x==1 else "No")

        # SITUACIÓN FINANCIERA ACTUAL (v3.0)
        st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-label">💳 Situación Financiera Actual</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.72rem;color:#666;margin:-4px 0 14px;line-height:1.5;">Ayuda al motor a detectar presión financiera aunque el cliente pague puntual. Puedes apoyarte en el buró impreso.</div>', unsafe_allow_html=True)

        fa1, fa2 = st.columns(2)
        with fa1:
            # CAMBIO 4: pregunta reformulada en lenguaje natural y amigable
            nivel_deuda_actual = st.selectbox(
                "¿Cómo lleva actualmente sus créditos y pagos?",
                options=[0,1,2,3],
                format_func=lambda x:{
                    0:"✅  Sin deudas — perfil limpio",
                    1:"🟢  Deuda baja — pagos cómodos y controlados",
                    2:"🟡  Deuda media — varios créditos pero manejables",
                    3:"🔴  Deuda alta — pagos comprometidos o ajustados",
                }[x],
                help="Pregúntale naturalmente: '¿Cómo llevas tus pagos? ¿Estás al corriente?' Tu criterio como asesor cuenta."
            )
        with fa2:
            productos_activos = st.selectbox(
                "¿Cuántos créditos activos tiene?",
                options=[0,1,2,3,4],
                format_func=lambda x:{0:"Ninguno",1:"1 crédito activo",2:"2 créditos activos",3:"3 créditos activos",4:"4 o más créditos"}[x],
                help="Cuenta tarjetas + hipoteca + autos + personales abiertos HOY en el buró."
            )

        st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
        fa3, fa4 = st.columns(2)
        with fa3:
            utilizacion_revolvente = st.selectbox(
                "¿Cuánto debe en sus tarjetas?",
                options=[0,10,40,70,90],
                format_func=lambda x:{
                    0:"—  No tiene tarjetas",
                    10:"Poco — paga casi completo",
                    40:"La mitad — ~50% del límite",
                    70:"Bastante — más del 60%",
                    90:"Casi al tope — cerca del límite",
                }[x],
                help="Pregúntale: '¿A cuánto del límite traes tus tarjetas?' También aparece en el buró."
            )
        with fa4:
            # consultas_recientes = consultas (mismo campo unificado)
            consultas_recientes = consultas

        # ESTABILIDAD LABORAL E HISTORIAL (v3.1)
        st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-label">💼 Estabilidad Laboral e Historial</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.72rem;color:#666;margin:-4px 0 14px;line-height:1.5;">Dos preguntas que mejoran la precisión del análisis. El asesor puede preguntarlas de manera natural.</div>', unsafe_allow_html=True)

        el1, el2 = st.columns(2)
        with el1:
            antiguedad_empleo = st.selectbox(
                "¿Cuánto lleva en su trabajo actual?",
                options=[4,3,2,1,0],
                format_func=lambda x:{4:"Más de 5 años",3:"De 2 a 5 años",2:"De 6 meses a 2 años",1:"Menos de 6 meses",0:"Jubilado / No aplica"}[x],
                index=1,
                help="No importa la empresa. Solo cuánto tiempo lleva en ese trabajo."
            )
        with el2:
            antiguedad_historial = st.selectbox(
                "¿Desde hace cuánto tiene créditos o tarjetas?",
                options=[4,3,2,1,0],
                format_func=lambda x:{4:"Más de 7 años",3:"De 3 a 7 años",2:"De 1 a 3 años",1:"Menos de 1 año",0:"Sin créditos previos"}[x],
                index=1,
                help="Aproximado está bien. ¿Cuándo abrió su primer crédito o tarjeta?"
            )

        st.markdown("<div style='margin:4px 0'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("✦  ANALIZAR PERFIL FINANCIERO")

# ── LÓGICA — Motor v3.1 ────────────────────────────────────────────
if submitted:
    # ── Mapear tipo_ingreso al formato del motor ──────────────────
    # El form usa "Nómina" con tilde, el motor usa "Nomina" sin tilde
    _tipo_map = {"Nómina": "Nomina", "Independiente": "Independiente", "No comprueba": "No comprueba"}
    tipo_ingreso_motor = _tipo_map.get(tipo_ingreso, "Nomina")

    if MOTOR_V3_DISPONIBLE:
        # ── Construir InputsAnalisis con TODOS los campos del motor v3.1 ──
        _inputs = InputsAnalisis(
            nombre           = nombre_cliente,
            telefono         = telefono,
            correo           = correo,
            edad             = int(edad),
            ingreso          = float(ingreso),
            tipo_ingreso     = tipo_ingreso_motor,
            negocio_casa     = int(negocio_casa),
            antiguedad_dom   = int(domicilio),
            domicilio_id     = int(domicilio_buro),
            precio           = float(precio),
            enganche         = float(enganche),
            plazo            = int(plazo),
            consultas        = int(consultas),
            auto_previo      = int(auto),
            credinissan      = int(credinissan),
            hipotecario      = int(hipotecario),
            tarjeta_alta     = int(tarjeta_alta),
            tarjeta_baja     = int(tarjeta_baja),
            atrasos_mop      = int(atrasos),
            enganche_disp    = int(enganche_disp),
            compra_mes       = int(compra_mes),
            unidad_disp      = int(unidad),
            # v3.0 — presión financiera
            utilizacion_revolvente = int(utilizacion_revolvente),
            productos_activos      = int(productos_activos),
            consultas_recientes    = int(consultas_recientes),
            nivel_deuda_actual     = int(nivel_deuda_actual),
            # v3.1 — estabilidad laboral e historial
            antiguedad_empleo      = int(antiguedad_empleo),
            antiguedad_historial   = int(antiguedad_historial),
            # asesor
            asesor_nombre    = asesor,
            asesor_rfc       = rfc,
            asesor_telefono  = telefono_asesor,
            asesor_correo    = correo_asesor,
        )

        # ── Ejecutar motor v3.1 ────────────────────────────────────
        _r = _analizar_motor(_inputs)

        # ── Mapear resultado del motor al formato de la UI ─────────
        # (la UI usa claves cortas heredadas del sistema anterior)
        prob_col = (
            "#4ade80" if _r.probabilidad >= 70
            else "#facc15" if _r.probabilidad >= 50
            else "#fb923c" if _r.probabilidad >= 35
            else "#f87171"
        )
        # Temperatura con emoji (el motor devuelve sin emoji)
        temp_emoji = {
            "CALIENTE": "🔥 CALIENTE",
            "TIBIO":    "🟡 TIBIO",
            "FRIO":     "❄️ FRÍO",
        }.get(_r.temperatura, _r.temperatura)

        st.session_state.resultado = {
            "sc":    _r.score_color,
            "prob":  _r.probabilidad,
            "prob_col": prob_col,
            "sem":   _r.semaforo,
            "temp":  temp_emoji,
            "inv":   _r.inv,           # alias legado: alertas como texto único
            "decision": _r.decision,
            "plan":  _r.plan,
            "msg_c": _r.mensaje_cliente,
            "msg_a": _r.mensaje_asesor,
            "condicionamientos": list(_r.condicionamientos),
            "alerta_cotitular":     _r.requiere_cotitular,
            "alerta_ingresos":      _r.requiere_validacion_ingresos,
            "alerta_investigacion": _r.requiere_investigacion_fisica,
            "financiera": _r.financiera_sugerida,
            "perfil": _r.perfil_interno,
            "score":  _r.score_puntos,
            "enganche_pct": _r.enganche_pct,
            "nombre": nombre_cliente,
            "telefono": telefono,
            "correo":  correo,
            "asesor":  asesor,
            "telefono_asesor": telefono_asesor,
            "correo_asesor":   correo_asesor,
            "rfc":     rfc,
            "docs":    list(_r.documentos_requeridos),
            "mensualidad": _r.mensualidad_estimada,
            "cap_pago":    _r.capacidad_pago,
            # v3 extras (para PDF y auditoría)
            "reglas_disparadas": _r.reglas_disparadas,
            "version_motor":     _r.version_motor,
        }
        st.session_state.cotitular_activo    = (_r.plan == "COTITULAR")
        st.session_state.cotitular_resultado = None
        st.session_state.ingreso      = ingreso
        st.session_state.mensualidad  = _r.mensualidad_estimada

    else:
        # ── Fallback: motor legado si core/ no está disponible ─────
        st.error("⚠️ Motor v3 no disponible. Verifica que la carpeta core/ esté en el mismo directorio que web_app.py")
        st.stop()

    # Recolectar datos del formulario para edición posterior
    datos_form_completo = {
        "asesor": asesor, "rfc": rfc,
        "telefono_asesor": telefono_asesor, "correo_asesor": correo_asesor,
        "nombre_cliente": nombre_cliente, "telefono": telefono, "correo": correo,
        "edad": int(edad), "ingreso": float(ingreso), "tipo_ingreso": tipo_ingreso,
        "negocio_casa": int(negocio_casa), "domicilio": int(domicilio),
        "domicilio_buro": int(domicilio_buro),
        "precio": float(precio), "enganche": float(enganche),
        "plazo": int(plazo), "consultas": int(consultas),
        "auto": int(auto), "credinissan": int(credinissan),
        "hipotecario": int(hipotecario),
        "tarjeta_alta": int(tarjeta_alta), "tarjeta_baja": int(tarjeta_baja),
        "atrasos": int(atrasos),
        "enganche_disp": int(enganche_disp), "compra_mes": int(compra_mes),
        "unidad": int(unidad),
        # v3.0
        "utilizacion_revolvente": int(utilizacion_revolvente),
        "productos_activos": int(productos_activos),
        "consultas_recientes": int(consultas_recientes),
        "nivel_deuda_actual": int(nivel_deuda_actual),
        # v3.1
        "antiguedad_empleo": int(antiguedad_empleo),
        "antiguedad_historial": int(antiguedad_historial),
    }
    # Detectar perfil duplicado del mismo cliente en últimas 24h
    datos_perfil = {**st.session_state.resultado,
        "ingreso": ingreso, "tipo_ingreso": tipo_ingreso,
        "enganche_pct": st.session_state.resultado.get("enganche_pct", 0),
        "datos_form": datos_form_completo}

    perfil_dup = buscar_perfil_duplicado(telefono, nombre_cliente)
    if perfil_dup and not st.session_state.get("decision_duplicado_tomada"):
        # Guardar info para mostrar el aviso
        st.session_state.perfil_duplicado     = perfil_dup
        st.session_state.datos_perfil_pending = datos_perfil
        st.session_state.decision_duplicado_tomada = False
    else:
        # Guardar normal
        folio_nuevo = guardar_perfil_sheets(datos_perfil)
        if folio_nuevo:
            st.session_state.folio_perfil_actual = folio_nuevo
        # Reset flag
        st.session_state.decision_duplicado_tomada = False
        st.session_state.perfil_duplicado = None

# ── AVISO DE PERFIL DUPLICADO ─────────────────────────────────────
if st.session_state.get("perfil_duplicado"):
    pd_info = st.session_state.perfil_duplicado
    st.markdown(f"""
    <div style="background:#fffbeb;border:2px solid #f59e0b;border-left:5px solid #c3002f;
        border-radius:10px;padding:14px 18px;margin:10px 0;">
      <div style="font-size:0.9rem;color:#92400e;font-weight:700;margin-bottom:6px;">
        ⚠️ Perfil duplicado detectado
      </div>
      <div style="font-size:0.78rem;color:#78350f;line-height:1.6;">
        Ya existe un análisis reciente de este cliente:<br>
        <b>Folio:</b> {pd_info.get('Folio','-')} &nbsp;·&nbsp;
        <b>Fecha:</b> {pd_info.get('Fecha','-')} {pd_info.get('Hora','')} &nbsp;·&nbsp;
        <b>Score:</b> {pd_info.get('Score','-')} ({pd_info.get('Probabilidad','-')}%)
      </div>
      <div style="font-size:0.74rem;color:#a16207;margin-top:8px;font-style:italic;">
        ¿Es el mismo cliente con datos actualizados o un análisis distinto?
      </div>
    </div>
    """, unsafe_allow_html=True)
    cdup1, cdup2, cdup3 = st.columns([1,1,1])
    with cdup1:
        if st.button("💾 Actualizar el existente", use_container_width=True, key="btn_actualizar_dup"):
            folio_existente = pd_info.get("Folio","")
            if folio_existente:
                ok = actualizar_perfil_sheets(folio_existente, st.session_state.datos_perfil_pending)
                if ok:
                    st.session_state.folio_perfil_actual = folio_existente
                    st.success(f"✅ Análisis {folio_existente} actualizado")
                else:
                    st.error("No se pudo actualizar")
            st.session_state.perfil_duplicado = None
            st.session_state.decision_duplicado_tomada = True
            st.rerun()
    with cdup2:
        if st.button("➕ Crear análisis nuevo", use_container_width=True, key="btn_crear_dup"):
            folio_nuevo = guardar_perfil_sheets(st.session_state.datos_perfil_pending)
            if folio_nuevo:
                st.session_state.folio_perfil_actual = folio_nuevo
                st.success(f"✅ Nuevo análisis creado: {folio_nuevo}")
            st.session_state.perfil_duplicado = None
            st.session_state.decision_duplicado_tomada = True
            st.rerun()
    with cdup3:
        if st.button("✖ Descartar", use_container_width=True, key="btn_descartar_dup"):
            st.session_state.perfil_duplicado = None
            st.session_state.datos_perfil_pending = None
            st.session_state.decision_duplicado_tomada = True
            st.info("Análisis no guardado en el sistema")
            st.rerun()

# Mostrar folio del análisis actual si existe
if st.session_state.get("folio_perfil_actual"):
    st.markdown(f"""
    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-left:3px solid #22c55e;
        border-radius:7px;padding:7px 14px;margin:8px 0;font-size:0.78rem;color:#166534;">
      📋 Análisis registrado con folio:
      <b style="font-family:'Rajdhani',sans-serif;color:#c3002f;letter-spacing:0.04em;">
      {st.session_state.folio_perfil_actual}</b>
    </div>
    """, unsafe_allow_html=True)

# ╔══════════════════════════════════════╗
# ║   DERECHA — RESULTADO REESTRUCTURADO ║
# ╚══════════════════════════════════════╝
with col_der:
    # Spacer alineado con logo del panel izquierdo
    if not st.session_state.resultado:
        st.markdown("""
        <div style="height:120px;display:flex;align-items:center;
            justify-content:center;border-bottom:1px solid #1a1a1a;margin-bottom:4px;">
          <div style="font-family:'Rajdhani',sans-serif;font-size:0.65rem;color:#333;
              text-transform:uppercase;letter-spacing:0.12em;">
              AutoScore AI — Panel de Resultados
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="height:120px;display:flex;align-items:center;
            padding-left:4px;border-bottom:1px solid #1a1a1a;margin-bottom:8px;">
          <div style="font-family:'Rajdhani',sans-serif;font-size:0.65rem;color:#444;
              text-transform:uppercase;letter-spacing:0.12em;">
              Resultado del análisis
          </div>
        </div>
        """, unsafe_allow_html=True)

    if not st.session_state.resultado:
        _lc1, _lc2, _lc3 = st.columns([1, 3, 1])
        with _lc2:
            st.image("AUTOSCOREIA.png", use_container_width=True)
        st.markdown("""
        <div style="text-align:center;padding:16px 0 8px;">
          <div style="font-size:1.05rem;font-weight:700;color:#1a1a1a;
              text-transform:uppercase;letter-spacing:0.1em;">
              Resultado del Análisis
          </div>
          <div style="font-size:0.7rem;color:#aaa;letter-spacing:0.06em;
              text-transform:uppercase;margin-top:8px;">
              Completa el formulario y presiona Analizar
          </div>
        </div>""", unsafe_allow_html=True)

    else:
        r = st.session_state.resultado

        SCORE_MAP = {
            "AZUL":     ("🔵","SCORE AZUL",    "#38bdf8","Perfil fuerte — alta probabilidad de aprobación"),
            "VERDE":    ("🟢","SCORE VERDE",   "#22c55e","Buen perfil — condiciones normales"),
            "AMARILLO": ("🟡","SCORE AMARILLO","#eab308","Perfil medio — requiere validación adicional"),
            "NARANJA":  ("🟠","SCORE NARANJA", "#f97316","Perfil con áreas de oportunidad"),
            "ROJO":     ("🔴","SCORE ROJO",    "#ef4444","Perfil requiere estrategia alternativa"),
        }
        em, lbl, col_hex, dsc = SCORE_MAP[r["sc"]]

        # ── 1. DECISIÓN — lo primero y más grande ─────────────
        sem_icon = {'verde':'✅','amarillo':'⚡','naranja':'⚠️','rojo':'🔴'}[r['sem']]
        st.markdown(f"""
        <div class="prob-hero">
          <div style="flex:1;">
            <div class="prob-label">Resultado del análisis</div>
            <div style="font-family:'Rajdhani',sans-serif;font-size:1.6rem;font-weight:700;
                line-height:1.1;margin:4px 0 6px;color:{'#4ade80' if r['sem']=='verde' else '#facc15' if r['sem']=='amarillo' else '#fb923c' if r['sem']=='naranja' else '#f87171'};">
                {sem_icon} {r['decision']}
            </div>
            <div class="prob-sublabel">{r['temp']} &nbsp;·&nbsp; {r['financiera']}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 2. MENSAJE CLIENTE ────────────────────────────────
        if r.get("msg_c"):
            st.markdown(f'<div class="msg-cliente">💡 {r["msg_c"]}</div>', unsafe_allow_html=True)

        # ── 3. PROBABILIDAD + SCORE ───────────────────────────
        rgb = {'AZUL':'56,189,248','VERDE':'34,197,94','AMARILLO':'234,179,8','NARANJA':'249,115,22','ROJO':'239,68,68'}[r['sc']]
        st.markdown(f"""
        <div class="metrics-2" style="margin-top:10px;">
          <div class="metric-tile blue" style="text-align:center;">
            <div class="mt-lbl">Probabilidad de aprobación</div>
            <div class="mt-val" style="color:{r['prob_col']};font-size:2.2rem;">{r['prob']}%</div>
          </div>
          <div class="metric-tile" style="background:rgba({rgb},0.08);border:1px solid {col_hex}33;text-align:center;">
            <div class="mt-lbl" style="color:{col_hex};">Score crediticio</div>
            <div style="font-size:1.6rem;line-height:1.2;margin:4px 0;">{em}</div>
            <div style="font-family:'Rajdhani',sans-serif;font-size:0.88rem;font-weight:700;color:{col_hex};">{lbl}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 4. MENSUALIDAD + CAPACIDAD ────────────────────────
        excede_color = "#f87171" if r["mensualidad"] > r["cap_pago"] else "#e2e8f0"
        st.markdown(f"""
        <div class="metrics-2">
          <div class="metric-tile blue">
            <div class="mt-lbl">Capacidad de pago</div>
            <div class="mt-val">${r['cap_pago']:,.0f}</div>
          </div>
          <div class="metric-tile purple">
            <div class="mt-lbl">Mensualidad estimada</div>
            <div class="mt-val" style="color:{excede_color};">${r['mensualidad']:,.0f}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 5. ALERTAS ────────────────────────────────────────
        st.markdown('<div class="sec-label-result">⚠️ Riesgos detectados</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="alerta-chip {'bad' if r['alerta_cotitular'] else 'ok'}">
            {'🔴' if r['alerta_cotitular'] else '🟢'} COTITULAR &nbsp;—&nbsp;
            {'Requiere cotitular' if r['alerta_cotitular'] else 'Sin alerta'}
        </div>
        <div class="alerta-chip {'bad' if r['alerta_ingresos'] else 'ok'}">
            {'🔴' if r['alerta_ingresos'] else '🟢'} INGRESOS &nbsp;—&nbsp;
            {'Validar ingresos' if r['alerta_ingresos'] else 'Sin alerta'}
        </div>
        <div class="alerta-chip {'bad' if r['alerta_investigacion'] else 'ok'}">
            {'🔴' if r['alerta_investigacion'] else '🟢'} INVESTIGACIÓN &nbsp;—&nbsp; {r['inv']}
        </div>
        """, unsafe_allow_html=True)

        # ── 6. ESTRATEGIA INTERNA — toggle manual (sin st.expander) ──
        if "mostrar_estrategia" not in st.session_state:
            st.session_state.mostrar_estrategia = False

        lbl_btn = "🔒 Notas internas — solo asesor" if not st.session_state.mostrar_estrategia else "🔒 Cerrar notas internas"
        if st.button(lbl_btn, key="btn_estrategia"):
            st.session_state.mostrar_estrategia = not st.session_state.mostrar_estrategia

        if st.session_state.mostrar_estrategia:
            st.markdown(f"""
            <div class="estrategia-box">
                🔴 {r["msg_a"]}<br><br>
                <b>Nivel interno:</b> {r["perfil"]} &nbsp;·&nbsp;
                Score: {r["score"]} pts &nbsp;·&nbsp;
                Enganche: {r["enganche_pct"]:.0f}%
            </div>
            """, unsafe_allow_html=True)

        # ── 7. CONDICIONAMIENTOS ──────────────────────────────
        if r["condicionamientos"]:
            st.markdown('<div class="sec-label-result">📋 Condicionamientos</div>', unsafe_allow_html=True)
            cond_items = "".join([f"• {c}<br>" for c in r["condicionamientos"]])
            st.markdown(f'<div class="cond-box">{cond_items}</div>', unsafe_allow_html=True)

        # ── 8. DOCUMENTACIÓN ─────────────────────────────────
        st.markdown('<div class="sec-label-result">📄 Documentación requerida</div>', unsafe_allow_html=True)
        st.markdown("""
        <style>
        .doc-chip-list { display:flex; flex-wrap:wrap; gap:6px; margin:4px 0; }
        .doc-chip-item {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 5px 12px;
            color: #e2e8f0;
            font-size: 0.78rem;
            font-weight: 500;
        }
        </style>
        """, unsafe_allow_html=True)
        docs_html = "".join([f'<span class="doc-chip-item">📎 {d}</span>' for d in r["docs"]])
        st.markdown(f'<div class="doc-chip-list">{docs_html}</div>', unsafe_allow_html=True)

        # ── 9. SIGUIENTE PASO + CUENTA ────────────────────────
        st.markdown('<div class="sec-label-result">💰 Siguiente paso</div>', unsafe_allow_html=True)
        anticipo = "Solicitar ENGANCHE COMPLETO" if r["plan"]=="DIRECTO" else "Solicitar APARTADO $5,000"
        st.markdown(f"""
        <div class="cuenta-box">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;">
            <div>
              <div style="color:#fcd34d;font-size:0.78rem;font-weight:700;margin-bottom:6px;">👉 {anticipo}</div>
              <div style="font-family:'Rajdhani',sans-serif;font-size:0.88rem;font-weight:700;color:#e2e8f0;">DAOSA SA DE CV — BBVA</div>
              <div style="color:#475569;font-size:0.75rem;margin-top:2px;letter-spacing:0.03em;">012320001250476847</div>
            </div>
            <div style="color:#ef4444;font-size:0.7rem;font-weight:600;text-align:right;
                line-height:1.5;padding:4px 0;">⚠️ Solicita anticipo<br>para asegurar unidad</div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin:6px 0'></div>", unsafe_allow_html=True)
        st.link_button("📊 Abrir Cotizador",
            "https://procotiza.losnrtelepro.com.mx/Procotiza/login.aspx?mns",
            use_container_width=True)

        # ── COTITULAR ─────────────────────────────────────────
        if st.session_state.cotitular_activo:
            st.markdown('<div class="sec-label-result">👥 Análisis de Cotitular</div>', unsafe_allow_html=True)
            with st.form("formulario_cotitular"):
                ct1, ct2 = st.columns(2)
                with ct1: tipo_cot    = st.selectbox("Tipo", ["Línea directa","Conocido"])
                with ct2: ingreso_cot = st.number_input("Ingreso cotitular ($)", min_value=0.0, step=500.0)
                cu1,cu2,cu3 = st.columns(3)
                with cu1: auto_cot         = st.selectbox("Auto previo",  ["Sí","No"])
                with cu2: credinissan_cot  = st.selectbox("CrediNissan",   ["Sí","No"])
                with cu3: hipotecario_cot  = st.selectbox("Hipotecario",   ["No tiene","Infonavit","Bancario"])
                cv1,cv2 = st.columns(2)
                with cv1: tarjeta_alta_cot = st.selectbox("Tarjetas >100K",["Sí","No"])
                with cv2: atrasos_cot      = st.selectbox("Buró",["Sin atrasos","1-30d","31-60d","61+d"])
                submit_cot = st.form_submit_button("✦  EVALUAR COTITULAR")

            if submit_cot:
                sc2=0
                if auto_cot=="Sí":                 sc2+=3
                if credinissan_cot=="Sí":           sc2+=5
                if hipotecario_cot=="Bancario":     sc2+=4
                elif hipotecario_cot=="Infonavit":  sc2+=2
                if tarjeta_alta_cot=="Sí":          sc2+=4
                if atrasos_cot=="Sin atrasos":      sc2+=5
                elif atrasos_cot=="1-30d":          sc2+=2
                elif atrasos_cot=="31-60d":         sc2-=4
                elif atrasos_cot=="61+d":           sc2-=10
                cap_t  = (st.session_state.ingreso + ingreso_cot)*0.3
                men_g  = st.session_state.mensualidad
                buro_c = "BUENO" if sc2>=12 else ("REGULAR" if sc2>=6 else "MALO")
                if tipo_cot=="Conocido" and buro_c!="BUENO":   res_cot="❌ Debe ser línea directa con buen historial"
                elif cap_t>=men_g and buro_c=="BUENO":         res_cot="🟢 APROBADO FINAL"
                elif buro_c=="REGULAR":                        res_cot="🟡 Aún condicionado — mejorar perfil"
                else:                                          res_cot="🔴 Cotitular no viable"
                st.session_state.cotitular_resultado = res_cot

        if st.session_state.cotitular_resultado:
            st.markdown(f"""
            <div class="alerta-chip {'ok' if 'APROBADO' in st.session_state.cotitular_resultado else 'bad'}"
                style="margin-top:4px;font-size:0.82rem;">
                {st.session_state.cotitular_resultado}
            </div>""", unsafe_allow_html=True)


        # ── PDF CLIENTE ─────────────────────────────────────────────
        st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)
        ok = all([r.get("asesor","").strip(), r.get("nombre","").strip(), r.get("telefono","").strip()])
        if not ok:
            st.warning("⚠️ Completa datos de asesor y cliente para generar PDF")
        else:
            buf_pdf = generar_pdf_cliente(r)
            st.download_button(
                "📄 Descargar PDF para el cliente",
                data=buf_pdf.getvalue(),
                file_name=f"autoscore_{(r.get('nombre','cliente') or 'cliente').replace(' ','_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        # ── GENERAR SOLICITUD DE CREDITO ─────────────────────────────
        st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)
        if "mostrar_solicitud" not in st.session_state:
            st.session_state.mostrar_solicitud = False
        lbl_sol = "📋 Generar Solicitud de Credito" if not st.session_state.mostrar_solicitud else "✖ Cerrar formulario de solicitud"
        if st.button(lbl_sol, key="btn_solicitud", use_container_width=True):
            st.session_state.mostrar_solicitud = not st.session_state.mostrar_solicitud
            st.rerun()

        st.markdown('<div class="security-line">🛡️ Datos protegidos y seguros</div>', unsafe_allow_html=True)

# ── FORMULARIO EXPANDIDO DE SOLICITUD ─────────────────────────────
if st.session_state.get("resultado") and st.session_state.get("mostrar_solicitud"):
    r = st.session_state.resultado
    st.markdown("---")
    st.markdown("""
    <div style="background:#000;color:#fff;padding:14px 20px;margin:0 -1rem 16px;
        border-top:3px solid #c3002f;">
      <div style="font-family:'Rajdhani',sans-serif;font-size:1.2rem;font-weight:700;
          letter-spacing:0.08em;">📋 SOLICITUD DE CREDITO — DATOS COMPLEMENTARIOS</div>
      <div style="font-size:0.7rem;color:#888;letter-spacing:0.06em;margin-top:2px;">
          Completa los campos para generar el PDF de solicitud que llegara automaticamente al F&I
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Atajo a datos precargados (el buscador está arriba en la app)
    p = st.session_state.datos_precargados or {}

    with st.form("form_solicitud"):
        # ─── DATOS DEL ASESOR Y FUENTE DE VENTA ───
        st.markdown('<div class="sec-label">👔 Datos del Asesor y Fuente de Venta</div>', unsafe_allow_html=True)
        sa1, sa2, sa3 = st.columns([2,1,1])
        with sa1: nom_asesor_sol = st.text_input("Nombre asesor", value=p.get("asesor",r.get("asesor","")))
        with sa2: rfc_asesor_sol = st.text_input("RFC asesor", value=p.get("rfc_asesor",""), placeholder="XAXX010101000")
        with sa3: fuente_venta = st.selectbox("Fuente de venta", ["BDC","PISO","CARTERA"], index=["BDC","PISO","CARTERA"].index(p.get("fuente_venta","BDC")) if p.get("fuente_venta") in ["BDC","PISO","CARTERA"] else 0)

        # ─── TIPO DE SOLICITUD Y CLIENTE ───
        st.markdown('<div class="sec-label">📝 Tipo de Solicitud</div>', unsafe_allow_html=True)
        tc1, tc2, tc3, tc4 = st.columns(4)
        with tc1: tipo_credito = st.selectbox("Tipo de credito", ["Simple","Arrendamiento","Credi Taxi","Subete"], index=["Simple","Arrendamiento","Credi Taxi","Subete"].index(p.get("tipo_credito","Simple")) if p.get("tipo_credito") in ["Simple","Arrendamiento","Credi Taxi","Subete"] else 0)
        with tc2: tipo_persona = st.selectbox("Tipo persona", ["PF","PFAE"], index=0 if p.get("tipo_persona","PF")=="PF" else 1)
        with tc3: recompra     = st.selectbox("Recompra",     ["NO","SI"], index=1 if p.get("recompra")=="SI" else 0)
        with tc4: empleado     = st.selectbox("Empleado",     ["NO","SI"], index=1 if p.get("empleado")=="SI" else 0)

        # ─── DATOS DEL ACREDITADO ───
        st.markdown('<div class="sec-label">👤 Datos del Acreditado</div>', unsafe_allow_html=True)
        a1, a2, a3, a4 = st.columns(4)
        # Defaults desde datos precargados del Sheet solamente.
        # NO se usan partes del campo "nombre" del perfilamiento porque
        # ese campo viene en orden "Nombre Apellido" y cruza los datos.
        with a1: ap_paterno = st.text_input("Apellido paterno", value=p.get("apellido_paterno",""), placeholder="García")
        with a2: ap_materno = st.text_input("Apellido materno", value=p.get("apellido_materno",""), placeholder="López")
        with a3: pn_nombre  = st.text_input("Primer nombre",    value=p.get("primer_nombre",""),    placeholder="Juan")
        with a4: sn_nombre  = st.text_input("Segundo nombre",   value=p.get("segundo_nombre",""),   placeholder="Carlos")

        b1, b2, b3, b4 = st.columns(4)
        with b1: fecha_nac = st.text_input("Fecha nacimiento", value=p.get("fecha_nacimiento",""), placeholder="DD/MM/AAAA")
        with b2: rfc_cli   = st.text_input("RFC cliente", value=p.get("rfc_cliente",""), placeholder="XXXX000000XXX")
        with b3: curp      = st.text_input("CURP", value=p.get("curp",""), placeholder="XXXX000000XXXXXX00")
        with b4: sexo      = st.selectbox("Sexo", ["M","F"], index=1 if p.get("sexo")=="F" else 0)

        c1, c2, c3 = st.columns(3)
        with c1: pais_nac     = st.text_input("Pais nacimiento", value=p.get("pais_nacimiento","Mexico"))
        with c2: estado_nac   = st.text_input("Estado nacimiento", value=p.get("estado_nacimiento",""))
        with c3: nacionalidad = st.selectbox("Nacionalidad", ["Mexicana","Extranjera"], index=1 if p.get("nacionalidad")=="Extranjera" else 0)

        d1, d2, d3 = st.columns(3)
        with d1: estado_civil = st.selectbox("Estado civil", ["Soltero","Casado","Divorciado","Viudo","Union Libre"], index=["Soltero","Casado","Divorciado","Viudo","Union Libre"].index(p.get("estado_civil","Soltero")) if p.get("estado_civil") in ["Soltero","Casado","Divorciado","Viudo","Union Libre"] else 0)
        with d2: regimen      = st.selectbox("Regimen", ["N/A","Bienes Separados","Sociedad Conyugal"], index=["N/A","Bienes Separados","Sociedad Conyugal"].index(p.get("regimen","N/A")) if p.get("regimen") in ["N/A","Bienes Separados","Sociedad Conyugal"] else 0)
        with d3: tipo_id      = st.selectbox("Tipo ID", ["INE","Pasaporte","Forma Migratoria","Cedula"], index=["INE","Pasaporte","Forma Migratoria","Cedula"].index(p.get("tipo_id","INE")) if p.get("tipo_id") in ["INE","Pasaporte","Forma Migratoria","Cedula"] else 0)
        num_id = st.text_input("Numero de identificacion", value=p.get("num_id",""))

        # ─── DOMICILIO ───
        st.markdown('<div class="sec-label">🏠 Domicilio</div>', unsafe_allow_html=True)
        v1, v2 = st.columns([1,2])
        with v1: vivienda = st.selectbox("Situacion vivienda", ["Propia","Renta","Hipoteca","Familiar"], index=["Propia","Renta","Hipoteca","Familiar"].index(p.get("vivienda","Propia")) if p.get("vivienda") in ["Propia","Renta","Hipoteca","Familiar"] else 0)
        with v2: tiempo_res = st.text_input("Tiempo de residencia", value=p.get("tiempo_residencia",""), placeholder="Ej: 5 anos 3 meses")

        d1, d2, d3 = st.columns([3,1,1])
        with d1: calle    = st.text_input("Calle / Avenida", value=p.get("calle",""))
        with d2: num_ext  = st.text_input("No. Ext", value=p.get("num_ext",""))
        with d3: num_int  = st.text_input("No. Int", value=p.get("num_int",""))

        e1, e2, e3 = st.columns(3)
        with e1: colonia       = st.text_input("Colonia", value=p.get("colonia",""))
        with e2: entre_calles  = st.text_input("Entre calles", value=p.get("entre_calles",""))
        with e3: municipio     = st.text_input("Delegacion/Municipio", value=p.get("municipio",""))

        f1, f2, f3 = st.columns(3)
        with f1: ciudad = st.text_input("Ciudad", value=p.get("ciudad",""))
        with f2: estado = st.text_input("Estado", value=p.get("estado",""))
        with f3: cp     = st.text_input("C.P.", value=p.get("cp",""))

        g1, g2 = st.columns(2)
        with g1: tel_fijo    = st.text_input("Telefono fijo", value=p.get("tel_fijo",""))
        with g2: tel_recados = st.text_input("Telefono para recados", value=p.get("tel_recados",""))

        # ─── OCUPACION ───
        st.markdown('<div class="sec-label">💼 Ocupacion</div>', unsafe_allow_html=True)
        o1, o2, o3 = st.columns(3)
        with o1: ocupacion = st.selectbox("Ocupacion", ["Privado","Publico","Independiente","Jubilado","Ama de casa","Estudiante","Otro"], index=["Privado","Publico","Independiente","Jubilado","Ama de casa","Estudiante","Otro"].index(p.get("ocupacion","Privado")) if p.get("ocupacion") in ["Privado","Publico","Independiente","Jubilado","Ama de casa","Estudiante","Otro"] else 0)
        with o2: contrato  = st.selectbox("Tipo contrato", ["Fijo","Temporal"], index=1 if p.get("contrato")=="Temporal" else 0)
        with o3: antiguedad_emp = st.text_input("Antiguedad empleo", value=p.get("antiguedad_empleo",""))

        emp1, emp2 = st.columns(2)
        with emp1: empresa = st.text_input("Nombre de la empresa", value=p.get("empresa",""))
        with emp2: jefe_inm = st.text_input("Jefe inmediato", value=p.get("jefe_inmediato",""))

        ei1, ei2 = st.columns(2)
        with ei1: fecha_ingreso = st.text_input("Fecha de ingreso a la empresa", value=p.get("fecha_ingreso",""), placeholder="DD/MM/AAAA")
        with ei2: actividad_empresa = st.text_input("Actividad especifica de la empresa", value=p.get("actividad_empresa",""))

        # CAMBIO 4 — autollenado ingresos según tipo
        _tipo_sol = r.get("tipo_ingreso", "")
        _ingreso_val = str(r.get("ingreso",""))
        _default_fijo = _ingreso_val if "omina" in _tipo_sol or _tipo_sol == "Nómina" else "0"
        _default_var  = _ingreso_val if _tipo_sol == "Independiente" else "0"

        ing1, ing2, ing3, ing4 = st.columns(4)
        with ing1: ing_fijo         = st.text_input("Ingreso fijo $",       value=p.get("ingreso_fijo",     _default_fijo))
        with ing2: ing_variable     = st.text_input("Ingreso variable $",   value=p.get("ingreso_variable", _default_var))
        with ing3: ahorro           = st.text_input("Ahorro/Cheques $",     value=p.get("ahorro",""))
        with ing4: ing_acumulable   = st.text_input("Ingreso acumulable $", value=p.get("ingreso_acumulable",""))

        ne1, ne2 = st.columns(2)
        with ne1: nac_empresa  = st.selectbox("Nacionalidad empresa", ["Mexicana","Extranjera"], index=1 if p.get("nac_empresa")=="Extranjera" else 0)
        with ne2: tipo_empresa = st.selectbox("Tipo empresa",         ["Privada","Publica"],     index=1 if p.get("tipo_empresa")=="Publica" else 0)

        tel_emp1, tel_emp2 = st.columns(2)
        with tel_emp1: tel_empresa = st.text_input("Telefono empresa", value=p.get("tel_empresa",""))
        with tel_emp2: tel_alterno = st.text_input("Telefono alterno", value=p.get("tel_alterno",""))

        descripcion_empleo = st.text_input("Descripcion del empleo o actividad", value=p.get("descripcion_empleo",""))

        # DOMICILIO EMPRESA — campos faltantes (ERROR 1)
        st.markdown('<div style="font-size:0.72rem;color:#c3002f;font-weight:600;margin-top:12px;">Domicilio de la empresa</div>', unsafe_allow_html=True)
        de1, de2, de3 = st.columns([3,1,1])
        with de1: dom_empresa  = st.text_input("Calle / Avenida (empresa)", value=p.get("dom_empresa",""))
        with de2: emp_num_ext  = st.text_input("No. Ext (emp)", value=p.get("emp_num_ext",""))
        with de3: emp_num_int  = st.text_input("No. Int (emp)", value=p.get("emp_num_int",""))

        df1, df2, df3, df4 = st.columns(4)
        with df1: emp_colonia   = st.text_input("Colonia (emp)",   value=p.get("emp_colonia",""))
        with df2: emp_municipio = st.text_input("Municipio (emp)", value=p.get("emp_municipio",""))
        with df3: emp_estado    = st.text_input("Estado (emp)",    value=p.get("emp_estado",""))
        with df4: emp_cp        = st.text_input("C.P. (emp)",      value=p.get("emp_cp",""))

        # ─── REFERENCIAS PERSONALES ───
        st.markdown('<div class="sec-label">👥 Referencias Personales (3 obligatorias)</div>', unsafe_allow_html=True)
        refs = {}
        for i in range(1, 4):
            # Separador visual limpio entre referencias
            st.markdown(f"""
            <div style="border-top:{'2px solid #c3002f' if i==1 else '1px solid #e5e5e5'};
                margin:{'12px 0 10px' if i==1 else '16px 0 10px'};
                display:flex;align-items:center;gap:8px;">
              <span style="background:#c3002f;color:#fff;font-size:0.68rem;font-weight:700;
                  padding:2px 8px;border-radius:4px;letter-spacing:0.06em;white-space:nowrap;">
                REF {i}
              </span>
            </div>
            """, unsafe_allow_html=True)
            # PROBLEMA 3: nombre completo en un solo campo
            rn1, rn2 = st.columns([3, 1])
            with rn1: refs[f"ref{i}_nombre_completo"] = st.text_input(
                "Nombre completo",
                value=p.get(f"ref{i}_nombre_completo", ""),
                placeholder="Apellido Paterno Apellido Materno Nombre(s)",
                key=f"ref_nombre_{i}"
            )
            with rn2: refs[f"ref{i}_parentesco"] = st.text_input(
                "Parentesco",
                value=p.get(f"ref{i}_parentesco", ""),
                placeholder="Ej: Hermano",
                key=f"ref_par_{i}"
            )
            rt1, rt2, rt3 = st.columns(3)
            with rt1: refs[f"ref{i}_tel_cel"] = st.text_input(
                "Celular",
                value=p.get(f"ref{i}_tel_cel", ""),
                placeholder="10 dígitos",
                key=f"ref_tc_{i}"
            )
            with rt2: refs[f"ref{i}_horario"] = st.text_input(
                "Horario para localizar",
                value=p.get(f"ref{i}_horario", ""),
                placeholder="Ej: 9am-6pm",
                key=f"ref_hr_{i}"
            )
            with rt3: refs[f"ref{i}_lugar"] = st.text_input(
                "Lugar de localización",
                value=p.get(f"ref{i}_lugar", ""),
                placeholder="Ej: Casa / Trabajo",
                key=f"ref_lug_{i}"
            )

        # ─── BOTON GENERAR / ACTUALIZAR ───
        st.markdown("<div style='margin:14px 0'></div>", unsafe_allow_html=True)
        es_actualizacion = bool(st.session_state.folio_actual)
        lbl_submit = "💾 ACTUALIZAR SOLICITUD" if es_actualizacion else "📋 GENERAR PDF DE SOLICITUD"
        submit_sol = st.form_submit_button(lbl_submit, use_container_width=True)

        if submit_sol:
            datos_sol = {
                "asesor": nom_asesor_sol, "rfc_asesor": rfc_asesor_sol, "fuente_venta": fuente_venta,
                "tipo_credito": tipo_credito, "tipo_persona": tipo_persona,
                "recompra": recompra, "empleado": empleado,
                "apellido_paterno": ap_paterno, "apellido_materno": ap_materno,
                "primer_nombre": pn_nombre, "segundo_nombre": sn_nombre,
                "nombre_completo": f"{ap_paterno} {ap_materno} {pn_nombre} {sn_nombre}".strip(),
                "fecha_nacimiento": fecha_nac, "rfc_cliente": rfc_cli, "curp": curp,
                "sexo": sexo, "pais_nacimiento": pais_nac, "estado_nacimiento": estado_nac,
                "nacionalidad": nacionalidad, "estado_civil": estado_civil,
                "regimen": regimen, "tipo_id": tipo_id, "num_id": num_id,
                "celular": r.get("telefono",""), "correo_cliente": r.get("correo",""),
                "vivienda": vivienda, "tiempo_residencia": tiempo_res,
                "calle": calle, "num_ext": num_ext, "num_int": num_int,
                "colonia": colonia, "entre_calles": entre_calles, "municipio": municipio,
                "ciudad": ciudad, "estado": estado, "cp": cp,
                "tel_fijo": tel_fijo, "tel_recados": tel_recados,
                "ocupacion": ocupacion, "contrato": contrato,
                "empresa": empresa, "jefe_inmediato": jefe_inm,
                "antiguedad_empleo": antiguedad_emp,
                "ingreso_fijo": ing_fijo, "ingreso_variable": ing_variable, "ahorro": ahorro,
                "tel_empresa": tel_empresa, "tel_alterno": tel_alterno,
                "descripcion_empleo": descripcion_empleo,
                "actividad_empresa": actividad_empresa,
                "fecha_ingreso": fecha_ingreso,
                "nac_empresa": nac_empresa,
                "tipo_empresa": tipo_empresa,
                "ingreso_acumulable": ing_acumulable,
                "dom_empresa": dom_empresa,
                "emp_num_ext": emp_num_ext,
                "emp_num_int": emp_num_int,
                "emp_colonia": emp_colonia,
                "emp_municipio": emp_municipio,
                "emp_estado": emp_estado,
                "emp_cp": emp_cp,
                **refs,
                "score_sc": r.get("sc",""), "score_prob": r.get("prob",0),
                "decision": r.get("decision",""),
            }
            buf_sol = generar_pdf_solicitud(datos_sol)
            st.session_state.pdf_solicitud_buf = buf_sol.getvalue()
            # Persistir datos_sol para que los campos no queden vacíos en el siguiente rerun
            st.session_state.datos_precargados = datos_sol

            if es_actualizacion:
                # Actualizar fila existente
                ok = actualizar_solicitud_sheets(st.session_state.folio_actual or "", datos_sol)
                if ok:
                    st.session_state.pdf_solicitud_nombre = f"solicitud_{st.session_state.folio_actual or 'nuevo'}_{ap_paterno}".replace(" ","_") + ".pdf"
                    st.success(f"✅ Solicitud {st.session_state.folio_actual or ''} ACTUALIZADA correctamente")
                else:
                    st.warning("⚠️ No se pudo actualizar — se creará una nueva solicitud")
                    folio_nuevo = guardar_solicitud_sheets(datos_sol)
                    if folio_nuevo:
                        st.session_state.folio_actual = folio_nuevo
                        st.session_state.pdf_solicitud_nombre = f"solicitud_{folio_nuevo}.pdf"
            else:
                # Crear nueva solicitud
                folio_nuevo = guardar_solicitud_sheets(datos_sol)
                if folio_nuevo:
                    st.session_state.folio_actual = folio_nuevo
                    st.session_state.pdf_solicitud_nombre = f"solicitud_{folio_nuevo}.pdf"
                    st.markdown(f"""
                    <div style="background:#f0fdf4;border:2px solid #22c55e;border-left:6px solid #c3002f;
                        border-radius:10px;padding:14px 18px;margin:12px 0;">
                      <div style="font-size:0.78rem;color:#166534;font-weight:600;margin-bottom:4px;">
                        ✅ Solicitud creada exitosamente
                      </div>
                      <div style="font-size:1.1rem;color:#111;font-weight:700;font-family:'Rajdhani',sans-serif;letter-spacing:0.06em;">
                        Folio asignado: <span style="color:#c3002f;">{folio_nuevo}</span>
                      </div>
                      <div style="font-size:0.72rem;color:#666;margin-top:6px;">
                        Anota este folio. Sirve para volver a editar esta misma solicitud sin crear una nueva.
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.session_state.pdf_solicitud_nombre = f"solicitud_{ap_paterno}_{pn_nombre}".replace(" ","_") + ".pdf"
                    st.warning("⚠️ PDF generado pero no se pudo guardar en Google Sheets — verifica que la pestaña 'Solicitudes' tenga la columna 'Folio' al inicio")

    # Botón de descarga fuera del form
    if st.session_state.get("pdf_solicitud_buf"):
        st.download_button(
            "📥 Descargar PDF de Solicitud",
            data=st.session_state.pdf_solicitud_buf,
            file_name=st.session_state.pdf_solicitud_nombre,
            mime="application/pdf",
            use_container_width=True,
            key="dl_solicitud"
        )