"""
sandbox.py — Módulo de pruebas del motor AutoScore AI v3.1

Usa este archivo para probar perfiles ANTES de mandar cambios al webapp.

GUÍA RÁPIDA DE CODIGOS:
─────────────────────────────────────────────────────────────────

VARIABLES ORIGINALES:
  tipo_ingreso:       "Nomina" | "Independiente" | "No comprueba"
  negocio_casa:       0=No aplica  1=Sí  2=No
  antiguedad_dom:     1=<1 año     2=1-3 años   3=+3 años
  domicilio_id:       1=Sí coincide con ID   2=No coincide
  hipotecario:        1=Bancario   2=Infonavit  3=No tiene
  tarjeta_alta:       1=Sí (>100K) 2=No
  tarjeta_baja:       1=Sí (<100K) 2=No
  atrasos_mop:        1=Al corriente/1-30d   2=31-60d   3=+61d
  auto_previo:        1=Sí  2=No
  credinissan:        1=Sí  2=No
  enganche_disp:      1=Sí  2=No
  compra_mes:         1=Sí  2=No
  unidad_disp:        1=Sí  2=No

VARIABLES NUEVAS v3.0 — PRESIÓN FINANCIERA:
  utilizacion_revolvente:  0=sin tarjetas  10=paga casi todo  40=~50% límite
                           70=más del 60%  90=casi al tope
  productos_activos:       0=ninguno  1=uno  2=dos  3=tres  4=cuatro o más
  consultas_recientes:     número de consultas últimos 6 meses (0 si no sabes)
  nivel_deuda_actual:      0=sin deudas  1=baja  2=media  3=alta

VARIABLES NUEVAS v3.1 — ESTABILIDAD LABORAL E HISTORIAL:
  antiguedad_empleo:    0=jubilado/N.A.  1=<6 meses  2=6m-2años
                        3=2-5 años       4=+5 años
  antiguedad_historial: 0=sin créditos   1=<1 año    2=1-3 años
                        3=3-7 años       4=+7 años

─────────────────────────────────────────────────────────────────
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.inputs import InputsAnalisis
from core.motor import analizar


# ════════════════════════════════════════════════════════════════
# PERFIL A PROBAR — modifica estos valores
# ════════════════════════════════════════════════════════════════
inputs = InputsAnalisis(
    # ─── Cliente ─────────────────────────────────────────────────
    nombre          = "Cliente Test",
    telefono        = "5555555555",
    correo          = "test@test.com",
    edad            = 35,

    # ─── Perfil financiero ───────────────────────────────────────
    ingreso         = 40000,
    tipo_ingreso    = "Nomina",        # "Nomina" | "Independiente" | "No comprueba"
    negocio_casa    = 2,               # 0=N/A  1=Sí  2=No
    antiguedad_dom  = 3,               # 1=<1año  2=1-3años  3=+3años
    domicilio_id    = 1,               # 1=Sí coincide  2=No coincide

    # ─── Vehículo ────────────────────────────────────────────────
    precio          = 290000,
    enganche        = 85000,
    plazo           = 72,              # 12 | 24 | 36 | 48 | 60 | 72

    # ─── Buró ────────────────────────────────────────────────────
    consultas       = 3,
    auto_previo     = 2,               # 1=Sí  2=No
    credinissan     = 2,               # 1=Sí  2=No
    hipotecario     = 2,               # 1=Bancario  2=Infonavit  3=No tiene
    tarjeta_alta    = 1,               # 1=Sí (>100K)  2=No
    tarjeta_baja    = 1,               # 1=Sí (<100K)  2=No
    atrasos_mop     = 1,               # 1=OK/1-30d  2=31-60d  3=+61d

    # ─── Perfil de compra ────────────────────────────────────────
    enganche_disp   = 1,               # 1=Sí  2=No
    compra_mes      = 1,               # 1=Sí  2=No
    unidad_disp     = 1,               # 1=Sí  2=No

    # ─── Presión financiera (v3.0) ───────────────────────────────
    utilizacion_revolvente  = 0,   # 0=sin tarj  10=poco  40=mitad  70=bastante  90=tope
    productos_activos       = 0,   # 0=ninguno  1=uno  2=dos  3=tres  4=cuatro+
    consultas_recientes     = 0,   # consultas últimos 6 meses (0=no sé)
    nivel_deuda_actual      = 0,   # 0=ninguna  1=baja  2=media  3=alta

    # ─── Estabilidad laboral e historial (v3.1) ──────────────────
    antiguedad_empleo       = 3,   # 0=N.A.  1=<6m  2=6m-2a  3=2-5a  4=+5a
    antiguedad_historial    = 2,   # 0=sin créd  1=<1a  2=1-3a  3=3-7a  4=+7a
)


# ════════════════════════════════════════════════════════════════
# EJECUTAR MOTOR Y MOSTRAR RESULTADO
# ════════════════════════════════════════════════════════════════
resultado = analizar(inputs)

# Enganche % calculado
enganche_pct = (inputs.enganche / inputs.precio * 100) if inputs.precio > 0 else 0


print()
print("╔══════════════════════════════════════════════════════════╗")
print("║          AutoScore AI — Resultado del Análisis           ║")
print("╚══════════════════════════════════════════════════════════╝")

print(f"\n{'DECISIÓN':<22} {resultado.decision}")
print(f"{'PLAN':<22} {resultado.plan}")
print(f"{'SCORE COLOR':<22} {resultado.score_color}")
print(f"{'PROBABILIDAD':<22} {resultado.probabilidad}%")
print(f"{'SEMÁFORO':<22} {resultado.semaforo.upper()}")
print(f"{'TEMPERATURA':<22} {resultado.temperatura}")
print(f"{'FINANCIERA':<22} {resultado.financiera_sugerida}")

print(f"\n─── Métricas financieras ────────────────────────────────────")
print(f"{'Score puntos':<22} {resultado.score_puntos}")
print(f"{'Perfil interno':<22} {resultado.perfil_interno}")
print(f"{'Enganche %':<22} {enganche_pct:.1f}%")
print(f"{'Capacidad de pago':<22} ${resultado.capacidad_pago:,.0f}")
print(f"{'Mensualidad estimada':<22} ${resultado.mensualidad_estimada:,.0f}")
print(f"{'Excede capacidad':<22} {'⚠️  SÍ' if resultado.excede_capacidad else '✅ No'}")
print(f"{'PTI aproximado':<22} {resultado.mensualidad_estimada/inputs.ingreso*100:.1f}%")

print(f"\n─── Alertas y condicionamientos ─────────────────────────────")

if resultado.condicionamientos:
    print("Condicionamientos:")
    for c in resultado.condicionamientos:
        print(f"  • {c}")
else:
    print("Condicionamientos:      Ninguno")

print(f"\nAlertas investigación:")
for a in resultado.alertas_investigacion:
    print(f"  • {a}")

print(f"\n─── Mensajes ────────────────────────────────────────────────")
print(f"Para el cliente:")
print(f"  {resultado.mensaje_cliente or '(sin mensaje)'}")
print(f"\nPara el asesor:")
print(f"  {resultado.mensaje_asesor or '(sin mensaje)'}")

print(f"\n─── Banderas ────────────────────────────────────────────────")
print(f"{'Requiere cotitular':<28} {'Sí' if resultado.requiere_cotitular else 'No'}")
print(f"{'Requiere validación ingresos':<28} {'Sí' if resultado.requiere_validacion_ingresos else 'No'}")
print(f"{'Requiere investigación física':<28} {'Sí' if resultado.requiere_investigacion_fisica else 'No'}")

print(f"\n─── Documentos requeridos ───────────────────────────────────")
for d in resultado.documentos_requeridos:
    print(f"  • {d}")

print(f"\n─── Auditoría — reglas disparadas ───────────────────────────")
reglas = resultado.reglas_disparadas
print(f"Total: {len(reglas)} reglas")

# Agrupar por prefijo
grupos = {
    "Riesgo (R1-R8)":    [r for r in reglas if r.startswith("R") and int(r.split("_")[0][1:]) <= 8 if r[1:].split("_")[0].isdigit()],
    "Score (R9-R19)":    [r for r in reglas if r.startswith("R") and r[1:].split("_")[0].isdigit() and 9 <= int(r[1:].split("_")[0]) <= 19],
    "Perfil/Prob (R20+)":[r for r in reglas if r.startswith("R") and r[1:].split("_")[0].isdigit() and int(r[1:].split("_")[0]) >= 20],
    "Madurez (M/MA)":    [r for r in reglas if r.startswith("M")],
    "PTI":               [r for r in reglas if r.startswith("PTI")],
    "Presión (PR)":      [r for r in reglas if r.startswith("PR")],
    "Estabilidad (EST)": [r for r in reglas if r.startswith("EST")],
    "Decisión (D)":      [r for r in reglas if r.startswith("D")],
    "Post-decision":     [r for r in reglas if r.startswith("POST")],
}
for grupo, regs in grupos.items():
    if regs:
        print(f"  {grupo}: {', '.join(regs)}")

print(f"\n  Versión motor: {resultado.version_motor}")
print(f"  Timestamp: {resultado.timestamp[:19]}")
print()
print("══════════════════════════════════════════════════════════════")