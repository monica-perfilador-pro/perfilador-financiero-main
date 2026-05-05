import streamlit as st
import datetime
import json

# ════════════════════════════════════════════
# PDF SOLICITUD DE CREDITO — para regenerar desde dashboard
# ════════════════════════════════════════════
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
from io import BytesIO
import datetime

W, H = letter  # 612 x 792 pts

# ── PALETA ────────────────────────────────────────────────────────
ROJO        = HexColor("#c3002f")
NEGRO       = HexColor("#111111")
GRIS_OSCURO = HexColor("#333333")
GRIS_MEDIO  = HexColor("#666666")
GRIS_CLARO  = HexColor("#cccccc")
GRIS_FONDO  = HexColor("#f5f5f5")
GRIS_BLOCK  = HexColor("#e8e8e8")  # franjas de seccion

def frect(c, x, y, w, h, color, lw=0):
    c.setFillColor(color)
    c.rect(x, y, w, h, fill=1, stroke=0)

def srect(c, x, y, w, h, color=GRIS_CLARO, lw=0.4):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.rect(x, y, w, h, fill=0, stroke=1)

def txt(c, s, x, y, font, size, color, align="left"):
    c.setFont(font, size)
    c.setFillColor(color)
    if align=="center": c.drawCentredString(x, y, s)
    elif align=="right": c.drawRightString(x, y, s)
    else: c.drawString(x, y, s)

def hline(c, x1, x2, y, color=GRIS_CLARO, lw=0.4):
    c.setStrokeColor(color); c.setLineWidth(lw)
    c.line(x1, y, x2, y)

def section_band(c, y, label, w_total=552):
    """Banda gris con titulo de seccion."""
    frect(c, 30, y-12, w_total, 14, GRIS_BLOCK)
    txt(c, label, 36, y-3, "Helvetica-Bold", 7, NEGRO)

def field(c, x, y, w, h, label, value="", show_border=True):
    """Campo del formulario con etiqueta arriba y valor adentro."""
    if show_border:
        srect(c, x, y-h, w, h, GRIS_CLARO, 0.4)
    # Etiqueta
    txt(c, label, x+3, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    # Valor
    if value:
        txt(c, str(value)[:60], x+4, y-h+4, "Helvetica-Bold", 7, NEGRO)

def checkbox(c, x, y, label, marked=False, size=6):
    """Checkbox con etiqueta."""
    srect(c, x, y, size, size, NEGRO, 0.5)
    if marked:
        txt(c, "x", x+1.2, y+1, "Helvetica-Bold", 6, NEGRO)
    txt(c, label, x+size+3, y+1, "Helvetica", 6, NEGRO)
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
    txt(cv, "SOLICITUD DE CREDITO PERSONA FISICA", 30, H-30, "Helvetica-Bold", 12, NEGRO)
    txt(cv, f"Fecha: {fecha}", W-30, H-30, "Helvetica", 9, NEGRO, "right")
    frect(cv, 30, H-36, 552, 1.5, ROJO)

    # ── DATOS DEL ASESOR Y FUENTE DE VENTA ────────────────────────
    section_band(cv, H-50, "DATOS DEL ASESOR Y FUENTE DE VENTA")
    y = H-54
    field(cv, 30,  y, 220, 18, "Nombre del Asesor",   d.get("asesor",""))
    field(cv, 250, y, 130, 18, "RFC del Asesor",      d.get("rfc_asesor",""))
    # Fuente de venta con checkboxes
    srect(cv, 380, y-18, 202, 18, GRIS_CLARO, 0.4)
    txt(cv, "Fuente de Venta", 383, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 386
    cx += checkbox(cv, cx, y-14, "BDC",      d.get("fuente_venta")=="BDC")
    cx += checkbox(cv, cx, y-14, "PISO",     d.get("fuente_venta")=="PISO")
    cx += checkbox(cv, cx, y-14, "CARTERA",  d.get("fuente_venta")=="CARTERA")

    # ── TIPO DE SOLICITUD ────────────────────────────────────────
    y -= 28
    section_band(cv, y, "TIPO DE SOLICITUD")
    y -= 16
    cx = 36
    cx += checkbox(cv, cx, y, "Credito Simple",      d.get("tipo_credito")=="Simple")
    cx += checkbox(cv, cx, y, "Arrendamiento",        d.get("tipo_credito")=="Arrendamiento")
    cx += checkbox(cv, cx, y, "Credi Taxi",           d.get("tipo_credito")=="Credi Taxi")
    cx += checkbox(cv, cx, y, "Subete",               d.get("tipo_credito")=="Subete")
    cx += checkbox(cv, cx, y, "Correo electronico",   d.get("tipo_credito")=="Correo")
    cx += checkbox(cv, cx, y, "Redes Sociales",       d.get("tipo_credito")=="Redes")

    # ── IDENTIFICACION DEL CLIENTE ───────────────────────────────
    y -= 14
    section_band(cv, y, "IDENTIFICACION DEL CLIENTE")
    y -= 16
    cx = 36
    cx += checkbox(cv, cx, y, "Persona Fisica",                  d.get("tipo_persona")=="PF")
    cx += checkbox(cv, cx, y, "Persona Fisica Actividad Empr.",  d.get("tipo_persona")=="PFAE")
    cx += checkbox(cv, cx, y+0, "Cliente Recompra:",  False, 0)
    cx += checkbox(cv, cx, y, "SI",  d.get("recompra")=="SI")
    cx += checkbox(cv, cx, y, "NO",  d.get("recompra")=="NO")
    cx += checkbox(cv, cx, y+0, "Empleado:", False, 0)
    cx += checkbox(cv, cx, y, "SI",  d.get("empleado")=="SI")
    cx += checkbox(cv, cx, y, "NO",  d.get("empleado")=="NO")

    # ── DATOS DEL ACREDITADO ─────────────────────────────────────
    y -= 14
    section_band(cv, y, "DATOS DEL ACREDITADO")
    y -= 4

    # Fila 1: Apellidos y nombres (4 cols)
    field(cv, 30,  y,  138, 18, "Apellido Paterno",  d.get("apellido_paterno",""))
    field(cv, 168, y,  138, 18, "Apellido Materno",  d.get("apellido_materno",""))
    field(cv, 306, y,  138, 18, "Primer Nombre",     d.get("primer_nombre",""))
    field(cv, 444, y,  138, 18, "Segundo Nombre",    d.get("segundo_nombre",""))

    y -= 22
    # Fila 2: Fecha nacimiento, RFC, CURP, Pais, Estado, Sexo
    field(cv, 30,  y, 78, 18, "Fecha de Nacimiento", d.get("fecha_nacimiento",""))
    field(cv, 108, y, 90, 18, "RFC (con Homoclave)", d.get("rfc_cliente",""))
    field(cv, 198, y, 86, 18, "CURP",                 d.get("curp",""))
    field(cv, 284, y, 90, 18, "Pais de nacimiento",   d.get("pais_nacimiento","Mexico"))
    field(cv, 374, y, 100,18, "Estado de nacimiento", d.get("estado_nacimiento",""))
    # Sexo con checkboxes
    srect(cv, 474, y-18, 108, 18, GRIS_CLARO, 0.4)
    txt(cv, "Sexo", 477, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 480
    cx += checkbox(cv, cx, y-14, "F",  d.get("sexo")=="F")
    cx += checkbox(cv, cx, y-14, "M",  d.get("sexo")=="M")

    y -= 22
    # Fila 3: Nacionalidad, Numero celular, Correo
    srect(cv, 30, y-18, 130, 18, GRIS_CLARO, 0.4)
    txt(cv, "Nacionalidad", 33, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 36
    cx += checkbox(cv, cx, y-14, "Mexicana",   d.get("nacionalidad")=="Mexicana")
    cx += checkbox(cv, cx, y-14, "Extranjera", d.get("nacionalidad")=="Extranjera")

    field(cv, 160, y, 120, 18, "Numero de Celular",  d.get("celular",""))
    field(cv, 280, y, 302, 18, "Correo electronico",  d.get("correo_cliente",""))

    y -= 22
    # Fila 4: Estado civil
    srect(cv, 30, y-18, 552, 18, GRIS_CLARO, 0.4)
    txt(cv, "Estado Civil", 33, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 36
    cx += checkbox(cv, cx, y-14, "Soltero",   d.get("estado_civil")=="Soltero")
    cx += checkbox(cv, cx, y-14, "Casado",    d.get("estado_civil")=="Casado")
    cx += checkbox(cv, cx, y-14, "Divorciado",d.get("estado_civil")=="Divorciado")
    cx += checkbox(cv, cx, y-14, "Viudo",     d.get("estado_civil")=="Viudo")
    cx += checkbox(cv, cx, y-14, "Union Libre",d.get("estado_civil")=="Union Libre")
    cx += 10
    txt(cv, "Regimen:", cx, y-13, "Helvetica-Bold", 5.5, GRIS_OSCURO)
    cx += 30
    cx += checkbox(cv, cx, y-14, "Bienes Separados",  d.get("regimen")=="Bienes Separados")
    cx += checkbox(cv, cx, y-14, "Sociedad Conyugal", d.get("regimen")=="Sociedad Conyugal")

    y -= 22
    # Fila 5: Identificacion
    srect(cv, 30, y-18, 432, 18, GRIS_CLARO, 0.4)
    txt(cv, "Tipo de identificacion", 33, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 36
    cx += checkbox(cv, cx, y-14, "Credencial Votar", d.get("tipo_id")=="INE")
    cx += checkbox(cv, cx, y-14, "Pasaporte",         d.get("tipo_id")=="Pasaporte")
    cx += checkbox(cv, cx, y-14, "Forma Migratoria",  d.get("tipo_id")=="Forma Migratoria")
    cx += checkbox(cv, cx, y-14, "Cedula Profesional",d.get("tipo_id")=="Cedula")
    field(cv, 462, y, 120, 18, "No. de Identificacion", d.get("num_id",""))

    # ── CONYUGE ──────────────────────────────────────────────────
    y -= 32
    section_band(cv, y, "CONYUGE O CONCUBINO(A)")
    y -= 4
    field(cv, 30,  y, 138, 18, "Apellido Paterno",       d.get("c_apellido_paterno",""))
    field(cv, 168, y, 138, 18, "Apellido Materno",       d.get("c_apellido_materno",""))
    field(cv, 306, y, 138, 18, "Primer Nombre",          d.get("c_primer_nombre",""))
    field(cv, 444, y, 80,  18, "Segundo Nombre",         d.get("c_segundo_nombre",""))
    field(cv, 524, y, 58,  18, "Dependientes",           str(d.get("dependientes","")))

    # ── DATOS DEL DOMICILIO ──────────────────────────────────────
    y -= 32
    section_band(cv, y, "DATOS DEL DOMICILIO")
    y -= 4
    # Situacion vivienda
    srect(cv, 30, y-18, 200, 18, GRIS_CLARO, 0.4)
    txt(cv, "Situacion de Vivienda", 33, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 36
    cx += checkbox(cv, cx, y-14, "Propia",      d.get("vivienda")=="Propia")
    cx += checkbox(cv, cx, y-14, "Renta",       d.get("vivienda")=="Renta")
    cx += checkbox(cv, cx, y-14, "Hipoteca",    d.get("vivienda")=="Hipoteca")
    cx += checkbox(cv, cx, y-14, "Familiar",    d.get("vivienda")=="Familiar")

    field(cv, 230, y, 90, 18, "Valor Aproximado",        d.get("valor_vivienda",""))
    field(cv, 320, y, 90, 18, "Valor Renta/Hipoteca",    d.get("valor_renta",""))
    field(cv, 410, y, 86, 18, "Telefono Fijo",           d.get("tel_fijo",""))
    field(cv, 496, y, 86, 18, "Tel. Recados",            d.get("tel_recados",""))

    y -= 22
    # Direccion completa
    field(cv, 30,  y, 250, 18, "Calle, Av. o Via",       d.get("calle",""))
    field(cv, 280, y, 60,  18, "No. Ext.",               d.get("num_ext",""))
    field(cv, 340, y, 60,  18, "No. Int.",               d.get("num_int",""))
    field(cv, 400, y, 110, 18, "Colonia",                d.get("colonia",""))
    field(cv, 510, y, 72,  18, "Pais Residencia",        d.get("pais_residencia","Mexico"))

    y -= 22
    field(cv, 30,  y, 130, 18, "Entre calles",           d.get("entre_calles",""))
    field(cv, 160, y, 100, 18, "Delegacion/Municipio",   d.get("municipio",""))
    field(cv, 260, y, 90,  18, "Ciudad",                 d.get("ciudad",""))
    field(cv, 350, y, 80,  18, "Estado",                 d.get("estado",""))
    field(cv, 430, y, 50,  18, "C.P.",                   d.get("cp",""))
    field(cv, 480, y, 102, 18, "Tiempo Residencia",      d.get("tiempo_residencia",""))

    # ── OCUPACION ────────────────────────────────────────────────
    y -= 32
    section_band(cv, y, "OCUPACION DEL ACREDITADO")
    y -= 4
    srect(cv, 30, y-18, 552, 18, GRIS_CLARO, 0.4)
    txt(cv, "Ocupacion", 33, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 36
    cx += checkbox(cv, cx, y-14, "Empleado S. Privado",      d.get("ocupacion")=="Privado")
    cx += checkbox(cv, cx, y-14, "Empleado S. Publico",      d.get("ocupacion")=="Publico")
    cx += checkbox(cv, cx, y-14, "Independiente",            d.get("ocupacion")=="Independiente")
    cx += checkbox(cv, cx, y-14, "Jubilado",                 d.get("ocupacion")=="Jubilado")
    cx += checkbox(cv, cx, y-14, "Ama de casa",              d.get("ocupacion")=="Ama de casa")
    cx += checkbox(cv, cx, y-14, "Estudiante",               d.get("ocupacion")=="Estudiante")
    cx += checkbox(cv, cx, y-14, "Otro",                     d.get("ocupacion")=="Otro")

    y -= 22
    # Tipo contrato + ingresos
    srect(cv, 30, y-18, 200, 18, GRIS_CLARO, 0.4)
    txt(cv, "Tipo de Contrato", 33, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 36
    cx += checkbox(cv, cx, y-14, "Fijo",      d.get("contrato")=="Fijo")
    cx += checkbox(cv, cx, y-14, "Temporal",  d.get("contrato")=="Temporal")
    field(cv, 230, y, 100, 18, "Ingreso Fijo $",     d.get("ingreso_fijo",""))
    field(cv, 330, y, 90,  18, "Variable $",          d.get("ingreso_variable",""))
    field(cv, 420, y, 80,  18, "Ahorro/Cheques $",    d.get("ahorro",""))
    field(cv, 500, y, 82,  18, "Ingreso Acumulable",  d.get("ingreso_acumulable",""))

    y -= 22
    field(cv, 30,  y, 270, 18, "Nombre de la Empresa",  d.get("empresa",""))
    field(cv, 300, y, 90,  18, "Fecha de Ingreso",       d.get("fecha_ingreso",""))
    srect(cv, 390, y-18, 96, 18, GRIS_CLARO, 0.4)
    txt(cv, "Nacionalidad Empresa", 393, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 396
    cx += checkbox(cv, cx, y-14, "Mex",  d.get("nac_empresa")=="Mexicana")
    cx += checkbox(cv, cx, y-14, "Ext",  d.get("nac_empresa")=="Extranjera")
    srect(cv, 486, y-18, 96, 18, GRIS_CLARO, 0.4)
    txt(cv, "Tipo Empresa", 489, y-3.5, "Helvetica", 5.5, GRIS_OSCURO)
    cx = 492
    cx += checkbox(cv, cx, y-14, "Priv",  d.get("tipo_empresa")=="Privada")
    cx += checkbox(cv, cx, y-14, "Pub",   d.get("tipo_empresa")=="Publica")

    y -= 22
    field(cv, 30,  y, 552, 18, "Descripcion del empleo o actividad",  d.get("descripcion_empleo",""))

    y -= 22
    field(cv, 30,  y, 280, 18, "Actividad Especifica de la Empresa", d.get("actividad_empresa",""))
    field(cv, 310, y, 136, 18, "Telefono Empresa",                    d.get("tel_empresa",""))
    field(cv, 446, y, 136, 18, "Telefono Alterno",                    d.get("tel_alterno",""))

    y -= 22
    field(cv, 30,  y, 200, 18, "Domicilio Empresa - Calle",         d.get("dom_empresa",""))
    field(cv, 230, y, 50,  18, "No. Ext.",                            d.get("emp_num_ext",""))
    field(cv, 280, y, 50,  18, "No. Int.",                            d.get("emp_num_int",""))
    field(cv, 330, y, 90,  18, "Colonia",                             d.get("emp_colonia",""))
    field(cv, 420, y, 80,  18, "Municipio",                           d.get("emp_municipio",""))
    field(cv, 500, y, 50,  18, "Estado",                              d.get("emp_estado",""))
    field(cv, 550, y, 32,  18, "C.P.",                                d.get("emp_cp",""))

    y -= 22
    field(cv, 30,  y, 300, 18, "Antiguedad en el empleo",  d.get("antiguedad_empleo",""))
    field(cv, 330, y, 252, 18, "Nombre del Jefe Inmediato", d.get("jefe_inmediato",""))

    # ── REFERENCIAS PERSONALES ───────────────────────────────────
    y -= 32
    section_band(cv, y, "DATOS GENERALES DE REFERENCIAS")
    y -= 4

    for i in range(1, 4):
        prefijo = f"ref{i}_"
        ref_y = y
        # Numero de referencia
        frect(cv, 30, ref_y-12, 14, 14, ROJO)
        txt(cv, str(i), 37, ref_y-3, "Helvetica-Bold", 8, white, "center")
        # Datos
        field(cv, 46,  ref_y, 110, 14, "Apellido Paterno",  d.get(prefijo+"ap",""))
        field(cv, 156, ref_y, 110, 14, "Apellido Materno",  d.get(prefijo+"am",""))
        field(cv, 266, ref_y, 110, 14, "Primer Nombre",     d.get(prefijo+"nom",""))
        field(cv, 376, ref_y, 110, 14, "Segundo Nombre",    d.get(prefijo+"nom2",""))
        field(cv, 486, ref_y, 96,  14, "Parentesco",        d.get(prefijo+"parentesco",""))

        ref_y -= 14
        field(cv, 46,  ref_y, 86, 14, "Tel. Fijo",         d.get(prefijo+"tel_fijo",""))
        field(cv, 132, ref_y, 86, 14, "Tel. Oficina",      d.get(prefijo+"tel_ofi",""))
        field(cv, 218, ref_y, 86, 14, "Tel. Celular",      d.get(prefijo+"tel_cel",""))
        field(cv, 304, ref_y, 100, 14,"Horario Localizar",  d.get(prefijo+"horario",""))
        field(cv, 404, ref_y, 178, 14, "Lugar Localizacion",d.get(prefijo+"lugar",""))
        y = ref_y - 16

    # Footer pagina 1
    txt(cv, "* Los numeros telefonicos deben ser de 10 digitos", 30, 28, "Helvetica-Oblique", 6.5, GRIS_MEDIO)
    txt(cv, "Pagina 1 de 1", 30, 16, "Helvetica-Bold", 7, NEGRO)
    txt(cv, "AutoScore AI · Aprobacion Inteligente", W-30, 16, "Helvetica-Bold", 7, ROJO, "right")
    frect(cv, 30, 10, 552, 1, ROJO)

    cv.showPage()
    cv.save()
    buf.seek(0)
    return buf


# ════════════════════════════════════════════
# DASHBOARD APP
# ════════════════════════════════════════════

st.set_page_config(page_title="AutoScore AI — Dashboard F&I", page_icon="📊", layout="wide")

# Forzar tema claro
st.markdown('<style>[data-testid="stAppViewContainer"]{background:#fff!important;} iframe{color-scheme:light!important;}</style>', unsafe_allow_html=True)

SHEET_ID   = "1f0oXowVTkuZdtlzw3Cdx5IIJRc9XIU6n0zM-EaXlyAA"
SHEET_NAME = "AutoScore Perfiles"
PASSWORD   = "autoscore2024"

# ── PALETA ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Exo+2:wght@400;500;600&display=swap');
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],
[data-testid="stDataFrame"], [data-testid="stDataFrameResizable"] {
    background: #ffffff !important; color: #111111 !important;
    font-family: 'Exo 2', sans-serif !important;
}
/* Forzar tabla blanca con texto negro */
[data-testid="stDataFrame"] * {
    color: #111111 !important;
    background-color: #ffffff !important;
}
[data-testid="stDataFrame"] th {
    background-color: #f5f5f5 !important;
    color: #c3002f !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #c3002f !important;
}
[data-testid="stDataFrame"] tr:hover td {
    background-color: #fff5f5 !important;
}
iframe[data-testid="stDataFrameResizable"] {
    color-scheme: light !important;
}
.block-container { padding: 1.5rem 2rem !important; max-width: 100% !important; }
/* Header */
/* header limpio */
/* Métricas */
.metric-row { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:20px; }
.metric-card { background:#fff; border:0.5px solid #e0e0e0; border-radius:10px;
    padding:14px 16px; border-top:3px solid #c3002f; }
.metric-label { font-size:0.65rem; color:#888; text-transform:uppercase;
    letter-spacing:0.08em; margin-bottom:4px; }
.metric-value { font-family:'Rajdhani',sans-serif; font-size:1.8rem;
    font-weight:700; color:#111; line-height:1; }
.metric-sub { font-size:0.7rem; color:#aaa; margin-top:3px; }
/* Badges score */
.badge { display:inline-block; padding:3px 10px; border-radius:50px;
    font-size:0.72rem; font-weight:600; letter-spacing:0.04em; }
.badge-AZUL     { background:#eff8ff; color:#0369a1; }
.badge-VERDE    { background:#f0fdf4; color:#166534; }
.badge-AMARILLO { background:#fefce8; color:#854d0e; }
.badge-NARANJA  { background:#fff7ed; color:#9a3412; }
.badge-ROJO     { background:#fff5f5; color:#9f1239; }
/* Tabla */
.stDataFrame { border-radius:10px !important; }
/* Login */
.login-box { max-width:360px; margin:80px auto; background:#fff;
    border:0.5px solid #e0e0e0; border-radius:16px; padding:36px;
    border-top:3px solid #c3002f; }
/* Inputs */
.stTextInput input { border:1px solid #ddd !important; border-radius:8px !important;
    font-size:0.88rem !important; }
.stTextInput input:focus { border-color:#c3002f !important; box-shadow:0 0 0 2px rgba(195,0,47,0.1) !important; }
label,[data-testid="stWidgetLabel"] p {
    color:#c3002f !important; font-size:0.68rem !important;
    font-weight:600 !important; letter-spacing:0.08em !important;
    text-transform:uppercase !important; }
.stButton>button { background:#c3002f !important; color:#fff !important;
    border:none !important; border-radius:50px !important; padding:10px 24px !important;
    font-family:'Rajdhani',sans-serif !important; font-weight:700 !important;
    font-size:0.9rem !important; letter-spacing:0.1em !important;
    width:100% !important; box-shadow:0 2px 12px rgba(195,0,47,0.3) !important; }
.stSelectbox>div>div { border:1px solid #ddd !important; border-radius:8px !important; }
hr { border:none !important; border-top:1px solid #e5e5e5 !important; margin:16px 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── LOGIN ─────────────────────────────────────────────────────────
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("""
    <div style="height:2px;background:#c3002f;margin:-1.5rem -2rem 0;"></div>
    <div class="login-box">
      <div style="text-align:center;margin-bottom:24px;">
        <div style="font-family:'Rajdhani',sans-serif;font-size:1.6rem;
            font-weight:700;color:#111;">AutoScore <span style="color:#c3002f;">AI</span></div>
        <div style="font-size:0.65rem;color:#c3002f;letter-spacing:0.16em;
            text-transform:uppercase;margin-top:4px;">Dashboard F&amp;I</div>
        <div style="font-size:0.75rem;color:#888;margin-top:8px;">
            Solo para uso interno — Gerencia y F&amp;I</div>
      </div>
    """, unsafe_allow_html=True)

    pwd = st.text_input("Contraseña de acceso", type="password", placeholder="••••••••••")
    if st.button("INGRESAR"):
        if pwd == PASSWORD:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# ── CARGAR DATOS ──────────────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes)
        service = build("sheets", "v4", credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{SHEET_NAME}'!A1:R1000"
        ).execute()

        valores = result.get("values", [])
        if len(valores) < 2:
            return []

        headers = valores[0]
        filas   = []
        for row in valores[1:]:
            while len(row) < len(headers):
                row.append("")
            filas.append(dict(zip(headers, row)))
        return filas

    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return []


# ── HEADER ────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:14px;padding:10px 0 8px;">
  <div>
    <div style="font-family:'Rajdhani',sans-serif;font-size:1.4rem;font-weight:700;
        color:#111;letter-spacing:0.08em;">AutoScore <span style="color:#c3002f;">AI</span></div>
    <div style="font-size:0.65rem;color:#c3002f;letter-spacing:0.16em;
        text-transform:uppercase;">Dashboard F&amp;I · Solo uso interno</div>
  </div>
</div>
<div style="height:2px;background:#c3002f;margin-bottom:16px;"></div>
""", unsafe_allow_html=True)

# ── CARGAR Y VALIDAR ──────────────────────────────────────────────
datos = cargar_datos()

if not datos:
    st.markdown("""
    <div style="text-align:center;padding:60px 0;color:#aaa;">
      <div style="font-size:2.5rem;margin-bottom:12px;">📋</div>
      <div style="font-family:'Rajdhani',sans-serif;font-size:1rem;
          text-transform:uppercase;letter-spacing:0.1em;">
          Sin perfiles aún
      </div>
      <div style="font-size:0.78rem;margin-top:8px;">
          Los análisis aparecerán aquí automáticamente
      </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

# ── TABS: HOY / HISTÓRICO ─────────────────────────────────────────
import datetime
hoy_str = datetime.date.today().strftime("%d/%m/%Y")

tab_hoy, tab_hist = st.tabs(["📅 HOY", "📂 HISTÓRICO"])

vista_actual = "HOY"  # Default

# ── FILTROS ───────────────────────────────────────────────────────
f1, f2, f3, f4 = st.columns([2, 2, 2, 1])

asesores = ["Todos"] + sorted(set(d.get("Asesor","") for d in datos if d.get("Asesor","")))
scores   = ["Todos", "AZUL", "VERDE", "AMARILLO", "NARANJA", "ROJO"]

with f1:
    filtro_asesor = st.selectbox("Asesor", asesores)
with f2:
    filtro_score  = st.selectbox("Score", scores)
with f3:
    filtro_fecha  = st.text_input("Buscar cliente o fecha", placeholder="Ej: Juan / 26/04/2026")
with f4:
    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
        st.rerun()

# Aplicar filtros
filtrados = datos
if filtro_asesor != "Todos":
    filtrados = [d for d in filtrados if d.get("Asesor","") == filtro_asesor]
if filtro_score != "Todos":
    filtrados = [d for d in filtrados if d.get("Score","") == filtro_score]
if filtro_fecha:
    q = filtro_fecha.lower()
    filtrados = [d for d in filtrados
                 if q in d.get("Cliente","").lower()
                 or q in d.get("Fecha","").lower()]

# Separar HOY vs HISTÓRICO
filtrados_hoy = [d for d in filtrados if d.get("Fecha","") == hoy_str]
filtrados_hist = [d for d in filtrados if d.get("Fecha","") != hoy_str]

# Función para renderizar tabla de perfiles
def render_perfiles(lista_perfiles, etiqueta):
    if not lista_perfiles:
        st.markdown(f"""
        <div style="text-align:center;padding:40px;color:#aaa;background:#fafafa;
            border-radius:10px;border:1px dashed #ddd;">
          <div style="font-size:1.8rem;margin-bottom:8px;">📋</div>
          <div style="font-size:0.9rem;font-weight:600;">Sin perfiles {etiqueta}</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Métricas para esta vista
    total_v    = len(lista_perfiles)
    aprob_v    = sum(1 for d in lista_perfiles if "APROBADO" in d.get("Decision",""))
    sc_dist_v  = {}
    for d in lista_perfiles:
        sc = d.get("Score","")
        sc_dist_v[sc] = sc_dist_v.get(sc, 0) + 1
    prob_v = []
    for d in lista_perfiles:
        try: prob_v.append(float(d.get("Probabilidad",0)))
        except: pass
    avg_v = round(sum(prob_v)/len(prob_v)) if prob_v else 0
    pct_v = round(aprob_v/total_v*100) if total_v > 0 else 0

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-card">
        <div class="metric-label">Total {etiqueta}</div>
        <div class="metric-value">{total_v}</div>
        <div class="metric-sub">analizados</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Aprobados</div>
        <div class="metric-value" style="color:#166534;">{aprob_v}</div>
        <div class="metric-sub">{pct_v}% del total</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Prob. promedio</div>
        <div class="metric-value">{avg_v}%</div>
        <div class="metric-sub">de aprobación</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Score azul/verde</div>
        <div class="metric-value" style="color:#0369a1;">
            {sc_dist_v.get('AZUL',0) + sc_dist_v.get('VERDE',0)}
        </div>
        <div class="metric-sub">perfiles fuertes</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Requieren acción</div>
        <div class="metric-value" style="color:#c3002f;">
            {sc_dist_v.get('NARANJA',0) + sc_dist_v.get('ROJO',0)}
        </div>
        <div class="metric-sub">naranja + rojo</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabla HTML
    SC_STYLES = {
        "AZUL":     ("background:#eff8ff","color:#0369a1"),
        "VERDE":    ("background:#f0fdf4","color:#166534"),
        "AMARILLO": ("background:#fefce8","color:#854d0e"),
        "NARANJA":  ("background:#fff7ed","color:#9a3412"),
        "ROJO":     ("background:#fff5f5","color:#9f1239"),
    }
    headers = ["Folio","Fecha","Hora","Asesor","Cliente","Teléfono","Score",
               "Prob %","Decisión","Cap. Pago","Mensualidad","Temperatura"]
    rows_html = ""
    for i, d in enumerate(reversed(lista_perfiles)):
        sc = d.get("Score","")
        bg, tc = SC_STYLES.get(sc, ("background:#fff","color:#111"))
        bg_row = "#ffffff" if i % 2 == 0 else "#fafafa"
        try: cap = f'${float(d.get("Capacidad_Pago",0) or 0):,.0f}'
        except: cap = "$0"
        try: men = f'${float(d.get("Mensualidad",0) or 0):,.0f}'
        except: men = "$0"
        score_badge = f'<span style="{bg};{tc};padding:2px 10px;border-radius:50px;font-size:0.72rem;font-weight:600;">{sc}</span>'
        folio_badge = f'<span style="background:#fff5f5;color:#c3002f;padding:2px 8px;border-radius:6px;font-family:Rajdhani,sans-serif;font-weight:700;font-size:0.72rem;border:1px solid #fecdd3;">{d.get("Folio","-")}</span>'
        vals = [
            folio_badge, d.get("Fecha",""), d.get("Hora",""), d.get("Asesor",""),
            d.get("Cliente",""), d.get("Tel_Cliente",""), score_badge,
            str(d.get("Probabilidad","")) + "%", d.get("Decision",""),
            cap, men, d.get("Temp",""),
        ]
        tds = "".join([f'<td style="padding:8px 10px;border-bottom:1px solid #f0f0f0;color:#111;font-size:0.78rem;white-space:nowrap;">{v}</td>' for v in vals])
        rows_html += f'<tr style="background:{bg_row};">{tds}</tr>'
    ths = "".join([f'<th style="padding:10px;background:#fff;color:#c3002f;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;border-bottom:2px solid #c3002f;white-space:nowrap;">{h}</th>' for h in headers])
    tabla_html = f"""
    <div style="overflow-x:auto;border:1px solid #e5e5e5;border-radius:10px;margin-bottom:12px;">
      <table style="width:100%;border-collapse:collapse;background:#fff;">
        <thead><tr>{ths}</tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """
    st.markdown(tabla_html, unsafe_allow_html=True)

# Renderizar tabs
with tab_hoy:
    st.markdown(f"""
    <div style="font-family:'Rajdhani',sans-serif;font-size:0.85rem;font-weight:700;
        color:#c3002f;text-transform:uppercase;letter-spacing:0.1em;margin:14px 0 10px;">
        📅 Perfiles del día — {hoy_str}
    </div>
    """, unsafe_allow_html=True)
    render_perfiles(filtrados_hoy, "hoy")

with tab_hist:
    st.markdown(f"""
    <div style="font-family:'Rajdhani',sans-serif;font-size:0.85rem;font-weight:700;
        color:#c3002f;text-transform:uppercase;letter-spacing:0.1em;margin:14px 0 10px;">
        📂 Histórico — Días anteriores
    </div>
    """, unsafe_allow_html=True)
    render_perfiles(filtrados_hist, "anteriores")

# ── MÉTRICAS RESUMEN GLOBAL (oculto - ya se muestra en cada tab) ───
total    = len(filtrados)
aprobados= sum(1 for d in filtrados if "APROBADO" in d.get("Decision",""))
st.markdown("<hr>", unsafe_allow_html=True)

import pandas as pd

# ── SOLICITUDES DE CREDITO ────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<div style="font-family:'Rajdhani',sans-serif;font-size:0.9rem;font-weight:700;
    color:#c3002f;text-transform:uppercase;letter-spacing:0.1em;margin:18px 0 10px;">
    📋 Solicitudes de Credito
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def cargar_solicitudes():
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly",
                  "https://www.googleapis.com/auth/drive.readonly"]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes)
        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range="'Solicitudes'!A1:X1000"
        ).execute()
        valores = result.get("values", [])
        if len(valores) < 2: return []
        headers = valores[0]
        filas = []
        for row in valores[1:]:
            while len(row) < len(headers): row.append("")
            filas.append(dict(zip(headers, row)))
        return filas
    except Exception as e:
        return []

solicitudes = cargar_solicitudes()

def render_solicitudes(lista_sols, etiqueta_vacio):
    if not lista_sols:
        st.markdown(f"""
        <div style="text-align:center;padding:30px;color:#aaa;background:#fafafa;
            border-radius:10px;border:1px dashed #ddd;">
          <div style="font-size:1.5rem;margin-bottom:8px;">📋</div>
          <div style="font-size:0.85rem;">Sin solicitudes {etiqueta_vacio}</div>
        </div>
        """, unsafe_allow_html=True)
        return

    SC_STYLES_SOL = {
        "AZUL":"background:#eff8ff;color:#0369a1",
        "VERDE":"background:#f0fdf4;color:#166534",
        "AMARILLO":"background:#fefce8;color:#854d0e",
        "NARANJA":"background:#fff7ed;color:#9a3412",
        "ROJO":"background:#fff5f5;color:#9f1239",
    }
    for idx, s in enumerate(reversed(lista_sols)):
        sc = s.get("Score","")
        sc_style = SC_STYLES_SOL.get(sc, "background:#fff;color:#111")
        col0, col1, col2, col3, col4, col5 = st.columns([1.2,2,2,2,1,1])
        with col0:
            st.markdown(f"""
            <div style="font-size:0.72rem;color:#c3002f;font-weight:700;font-family:'Rajdhani',sans-serif;
                background:#fff5f5;padding:4px 8px;border-radius:6px;border:1px solid #fecdd3;
                text-align:center;letter-spacing:0.04em;">
              {s.get('Folio','-')}
            </div>
            """, unsafe_allow_html=True)
        with col1:
            st.markdown(f"""
            <div style="font-size:0.78rem;color:#111;font-weight:600;">{s.get('Cliente','-')}</div>
            <div style="font-size:0.68rem;color:#888;">{s.get('Fecha','-')} · {s.get('Hora','-')}</div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="font-size:0.74rem;color:#111;">{s.get('Asesor','-')}</div>
            <div style="font-size:0.66rem;color:#888;">RFC: {s.get('RFC_Asesor','-')}</div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="font-size:0.74rem;"><span style="background:#fafafa;padding:2px 8px;border-radius:50px;font-weight:600;color:#c3002f;">{s.get('Fuente_Venta','-')}</span></div>
            <div style="font-size:0.66rem;color:#888;margin-top:3px;">{s.get('Tipo_Credito','-')}</div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div style="text-align:center;"><span style="{sc_style};padding:3px 10px;border-radius:50px;font-size:0.7rem;font-weight:600;">{sc or '-'}</span></div>
            <div style="font-size:0.66rem;color:#888;text-align:center;margin-top:3px;">{s.get('Probabilidad','-')}%</div>
            """, unsafe_allow_html=True)
        with col5:
            try:
                datos_json = json.loads(s.get("Datos_JSON","{}"))
                buf_pdf = generar_pdf_solicitud(datos_json)
                st.download_button(
                    "📥 PDF",
                    data=buf_pdf.getvalue(),
                    file_name=f"solicitud_{s.get('Folio','-')}.pdf",
                    mime="application/pdf",
                    key=f"dl_sol_{etiqueta_vacio}_{idx}",
                    use_container_width=True
                )
            except Exception:
                st.markdown("<div style='font-size:0.65rem;color:#aaa;text-align:center;'>Sin PDF</div>", unsafe_allow_html=True)
        st.markdown("<div style='border-bottom:1px solid #eee;margin:6px 0;'></div>", unsafe_allow_html=True)


if not solicitudes:
    st.markdown("""
    <div style="text-align:center;padding:30px;color:#aaa;background:#fafafa;
        border-radius:10px;border:1px dashed #ddd;">
      <div style="font-size:1.5rem;margin-bottom:8px;">📋</div>
      <div style="font-size:0.85rem;">Sin solicitudes generadas aun</div>
      <div style="font-size:0.7rem;color:#bbb;margin-top:6px;">
          Cuando un asesor genere una solicitud, aparecera aqui con su PDF descargable
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Filtros
    sf1, sf2 = st.columns([2,2])
    with sf1: filt_asesor_sol = st.selectbox("Filtrar por asesor",
        ["Todos"] + sorted(set(s.get("Asesor","") for s in solicitudes if s.get("Asesor",""))),
        key="filt_asesor_sol")
    with sf2: filt_fuente = st.selectbox("Filtrar por fuente de venta",
        ["Todas","BDC","PISO","CARTERA"], key="filt_fuente")

    sols_filtradas = solicitudes
    if filt_asesor_sol != "Todos":
        sols_filtradas = [s for s in sols_filtradas if s.get("Asesor","")==filt_asesor_sol]
    if filt_fuente != "Todas":
        sols_filtradas = [s for s in sols_filtradas if s.get("Fuente_Venta","")==filt_fuente]

    sols_hoy  = [s for s in sols_filtradas if s.get("Fecha","")==hoy_str]
    sols_hist = [s for s in sols_filtradas if s.get("Fecha","")!=hoy_str]

    sol_tab_hoy, sol_tab_hist = st.tabs([f"📅 HOY ({len(sols_hoy)})", f"📂 HISTÓRICO ({len(sols_hist)})"])

    with sol_tab_hoy:
        st.markdown(f"""
        <div style="font-family:'Rajdhani',sans-serif;font-size:0.78rem;font-weight:700;
            color:#666;letter-spacing:0.06em;margin:10px 0 6px;">
            Solicitudes generadas hoy — {hoy_str}
        </div>
        """, unsafe_allow_html=True)
        render_solicitudes(sols_hoy, "hoy")

    with sol_tab_hist:
        st.markdown("""
        <div style="font-family:'Rajdhani',sans-serif;font-size:0.78rem;font-weight:700;
            color:#666;letter-spacing:0.06em;margin:10px 0 6px;">
            Solicitudes anteriores
        </div>
        """, unsafe_allow_html=True)
        render_solicitudes(sols_hist, "anteriores")

# ── CERRAR SESIÓN ─────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
_c1, _c2, _c3 = st.columns([3,1,3])
with _c2:
    if st.button("Cerrar sesión"):
        st.session_state.autenticado = False
        st.rerun()

st.markdown("""
<div style="text-align:center;color:#ccc;font-size:0.65rem;margin-top:8px;">
    AutoScore AI — Dashboard F&I · Solo uso interno · Datos protegidos
</div>
""", unsafe_allow_html=True)
