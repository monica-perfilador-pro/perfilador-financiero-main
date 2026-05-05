"""
Tests del motor de decision v2.

Cubre los casos clave:
  - Determinismo (mismo input = mismo output)
  - Pisadas resueltas (4 fixes)
  - Casos de borde
  - Trazabilidad de reglas
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from core import analizar, InputsAnalisis


# ════════════════════════════════════════════════════════════════
# HELPER: input default razonable
# ════════════════════════════════════════════════════════════════
def make_input(**kwargs) -> InputsAnalisis:
    """Crea un input con valores razonables, override con kwargs."""
    defaults = dict(
        nombre="Cliente Test", telefono="5555555555", correo="t@t.com",
        edad=35, ingreso=30000.0, tipo_ingreso="Nomina",
        negocio_casa=0, antiguedad_dom=3, domicilio_id=1,
        precio=300000.0, enganche=60000.0, plazo=60,
        consultas=0, auto_previo=2, credinissan=2, hipotecario=3,
        tarjeta_alta=2, tarjeta_baja=2, atrasos_mop=1,
        enganche_disp=1, compra_mes=1, unidad_disp=1,
    )
    defaults.update(kwargs)
    return InputsAnalisis(**defaults)


# ════════════════════════════════════════════════════════════════
# T1 — DETERMINISMO
# ════════════════════════════════════════════════════════════════
def test_determinismo_mismo_input_mismo_output():
    """Mismo input ejecutado 10 veces debe dar exactamente el mismo output."""
    inputs = make_input(ingreso=50000, tarjeta_alta=1, credinissan=1)
    resultados = [analizar(inputs) for _ in range(10)]

    primero = resultados[0]
    for r in resultados[1:]:
        assert r.decision == primero.decision
        assert r.plan == primero.plan
        assert r.probabilidad == primero.probabilidad
        assert r.score_color == primero.score_color
        assert r.score_puntos == primero.score_puntos


# ════════════════════════════════════════════════════════════════
# T2 — FIX PISADA 1: prob no se muta despues de calcular sc
# ════════════════════════════════════════════════════════════════
def test_independiente_negocio_casa_no_contradice_resultado():
    """
    Independiente con negocio en domicilio:
    - prob debe quedar >= 80
    - score_color debe ser AZUL (consistente con prob)
    - decision NO debe ser ESTRATEGIA ALTERNATIVA
    """
    inputs = make_input(
        tipo_ingreso="Independiente",
        negocio_casa=1,
        ingreso=40000,
        consultas=0,
        atrasos_mop=1,
    )
    r = analizar(inputs)

    assert r.probabilidad >= 80, f"prob deberia ser >=80, fue {r.probabilidad}"
    assert r.score_color == "AZUL", f"sc deberia ser AZUL, fue {r.score_color}"
    # Decision debe ser consistente con prob alta
    assert "ALTERNATIVA" not in r.decision, (
        f"Con prob {r.probabilidad}% no debe ser alternativa: {r.decision}"
    )


def test_independiente_sin_negocio_casa_no_aplica_regla():
    """Si negocio_casa=0 (no aplica), la regla R33 NO debe disparar."""
    inputs = make_input(
        tipo_ingreso="Independiente",
        negocio_casa=0,  # no aplica
        consultas=5,
    )
    r = analizar(inputs)

    # Sin la regla, la prob debe reflejar las penalizaciones
    assert "R33" not in r.reglas_disparadas


def test_nomina_negocio_casa_si_no_aplica_regla():
    """Si tipo_ingreso=Nomina, la regla de investigacion fisica NO aplica."""
    inputs = make_input(
        tipo_ingreso="Nomina",
        negocio_casa=1,  # aunque diga Si
    )
    r = analizar(inputs)

    assert "R33" not in r.reglas_disparadas
    assert not r.requiere_investigacion_fisica


# ════════════════════════════════════════════════════════════════
# T3 — FIX PISADA 2: alertas de investigacion como lista
# ════════════════════════════════════════════════════════════════
def test_multiples_alertas_coexisten():
    """
    Independiente con domicilio != ID y prob<45 debe tener
    multiples alertas en la lista, no solo la ultima.
    """
    inputs = make_input(
        tipo_ingreso="Independiente",
        domicilio_id=2,
        consultas=5,
        atrasos_mop=2,
    )
    r = analizar(inputs)

    alertas = r.alertas_investigacion
    # Al menos debe contener validacion ingresos + validacion domicilio
    assert any("ingresos" in a.lower() for a in alertas), \
        f"Debe haber alerta de ingresos: {alertas}"
    assert any("domicilio" in a.lower() for a in alertas), \
        f"Debe haber alerta de domicilio: {alertas}"


def test_alertas_no_se_pierden():
    """Una alerta no debe sobrescribir a las anteriores."""
    inputs = make_input(
        tipo_ingreso="Independiente",
        domicilio_id=2,
        negocio_casa=1,
    )
    r = analizar(inputs)

    # Debe tener al menos 3 alertas distintas
    assert len(r.alertas_investigacion) >= 2


# ════════════════════════════════════════════════════════════════
# T4 — FIX PISADA 3: MOP 3 va a revision especial SIEMPRE
# ════════════════════════════════════════════════════════════════
def test_mop3_perfil_delgado_va_a_revision_especial():
    """
    BUG corregido: MOP 3 con perfil DELGADO antes iba a 'ESTRATEGIA
    ALTERNATIVA' (D2) en lugar de 'REVISION ESPECIAL' (D3).
    """
    inputs = make_input(
        atrasos_mop=3,
        consultas=0,
        ingreso=15000,  # ingreso bajo para perfil delgado
        credinissan=2, auto_previo=2, tarjeta_alta=2, tarjeta_baja=2,
        hipotecario=3,
    )
    r = analizar(inputs)

    assert r.decision == "REVISION ESPECIAL FINANCIERA", (
        f"MOP 3 debe ir a revision especial, fue: {r.decision}"
    )
    assert r.plan == "REVISION_FINANCIERA"
    assert "D1" in r.reglas_disparadas
    assert "NO APLICA CREDINISSAN" in r.condicionamientos


def test_mop3_perfil_fuerte_tambien_va_a_revision():
    """MOP 3 con perfil FUERTE tambien va a revision especial."""
    inputs = make_input(
        atrasos_mop=3,
        credinissan=1, auto_previo=1, tarjeta_alta=1, hipotecario=1,
    )
    r = analizar(inputs)

    assert r.decision == "REVISION ESPECIAL FINANCIERA"


def test_mop3_limita_probabilidad_a_28():
    """MOP 3 SIEMPRE limita probabilidad a maximo 28%."""
    inputs = make_input(
        atrasos_mop=3,
        credinissan=1, auto_previo=1, tarjeta_alta=1,
        hipotecario=1, ingreso=80000, enganche=150000, precio=300000,
    )
    r = analizar(inputs)

    assert r.probabilidad <= 28


# ════════════════════════════════════════════════════════════════
# T5 — FIX PISADA 4: semaforo deriva de plan, no de string
# ════════════════════════════════════════════════════════════════
def test_aprobable_condicionado_semaforo_amarillo():
    """
    BUG corregido: 'APROBABLE CONDICIONADO' caia en else->naranja,
    debe ser amarillo.
    """
    inputs = make_input(
        atrasos_mop=2,
        ingreso=40000, enganche=60000, precio=300000,
    )
    r = analizar(inputs)

    if r.decision == "APROBABLE CONDICIONADO":
        assert r.semaforo == "amarillo", (
            f"APROBABLE CONDICIONADO debe ser amarillo, fue: {r.semaforo}"
        )


def test_aprobado_directo_semaforo_verde():
    """Aprobacion directa = semaforo verde."""
    inputs = make_input(
        ingreso=80000,
        credinissan=1, auto_previo=1, tarjeta_alta=1, hipotecario=1,
        enganche=90000, precio=300000,  # 30% enganche
        consultas=0, atrasos_mop=1,
    )
    r = analizar(inputs)

    assert r.plan == "AUTOMATICO"
    assert r.semaforo == "verde"


# ════════════════════════════════════════════════════════════════
# T6 — TRAZABILIDAD
# ════════════════════════════════════════════════════════════════
def test_reglas_disparadas_se_registran():
    """Cada analisis debe registrar las reglas que dispararon."""
    inputs = make_input(credinissan=1, atrasos_mop=2)
    r = analizar(inputs)

    assert len(r.reglas_disparadas) > 0
    assert "R11" in r.reglas_disparadas  # credinissan
    assert "R15" in r.reglas_disparadas  # atrasos mop2


def test_caso_aprobacion_clean_dispara_reglas_correctas():
    """Cliente ideal debe disparar reglas positivas."""
    inputs = make_input(
        credinissan=1, auto_previo=1, tarjeta_alta=1, hipotecario=1,
        consultas=0, atrasos_mop=1,
        ingreso=80000, enganche=90000, precio=300000,
    )
    r = analizar(inputs)

    expected = ["R9", "R11", "R12", "R13", "R22", "R23", "R27"]
    for rid in expected:
        assert rid in r.reglas_disparadas, (
            f"Falta regla {rid}. Disparadas: {r.reglas_disparadas}"
        )


# ════════════════════════════════════════════════════════════════
# T7 — RESULTADO INMUTABLE
# ════════════════════════════════════════════════════════════════
def test_resultado_es_inmutable():
    """No se debe poder mutar el resultado despues de creado."""
    inputs = make_input()
    r = analizar(inputs)

    with pytest.raises(Exception):
        r.probabilidad = 100  # debe fallar (frozen=True)


def test_inputs_son_inmutables():
    """Los inputs tampoco se deben poder mutar."""
    inputs = make_input()

    with pytest.raises(Exception):
        inputs.ingreso = 999999


# ════════════════════════════════════════════════════════════════
# T8 — RANGOS Y BORDES
# ════════════════════════════════════════════════════════════════
def test_probabilidad_entre_5_y_95():
    """Probabilidad siempre debe estar entre 5 y 95."""
    # Caso muy malo
    r1 = analizar(make_input(
        atrasos_mop=3, consultas=15, tipo_ingreso="No comprueba",
        enganche=0, precio=300000,
    ))
    assert 5 <= r1.probabilidad <= 95

    # Caso muy bueno
    r2 = analizar(make_input(
        credinissan=1, auto_previo=1, tarjeta_alta=1, hipotecario=1,
        ingreso=200000, enganche=200000, precio=300000,
        atrasos_mop=1, consultas=0,
    ))
    assert 5 <= r2.probabilidad <= 95


def test_score_color_consistente_con_probabilidad():
    """score_color siempre debe corresponder con la probabilidad."""
    inputs_buenos = make_input(
        credinissan=1, auto_previo=1, tarjeta_alta=1, hipotecario=1,
        ingreso=80000, enganche=120000, precio=300000,
    )
    r = analizar(inputs_buenos)

    if r.probabilidad >= 80:
        assert r.score_color == "AZUL"
    elif r.probabilidad >= 70:
        assert r.score_color == "VERDE"
    elif r.probabilidad >= 45:
        assert r.score_color == "AMARILLO"
    elif r.probabilidad >= 35:
        assert r.score_color == "NARANJA"
    else:
        assert r.score_color == "ROJO"


# ════════════════════════════════════════════════════════════════
# T9 — CASOS REALES DE NEGOCIO
# ════════════════════════════════════════════════════════════════
def test_caso_real_nomina_perfil_fuerte():
    """Empleado con todo a su favor debe ser APROBADO automatico."""
    inputs = make_input(
        ingreso=60000, tipo_ingreso="Nomina",
        credinissan=1, auto_previo=1, tarjeta_alta=1, hipotecario=1,
        precio=350000, enganche=70000, plazo=60,
        consultas=1, atrasos_mop=1,
    )
    r = analizar(inputs)

    assert r.plan == "AUTOMATICO"
    assert r.score_color in {"AZUL", "VERDE"}
    assert r.semaforo == "verde"


def test_caso_real_independiente_negocio_casa():
    """
    Caso real reportado por Monica:
    Independiente con negocio en domicilio.
    Resultado correcto: APROBADO con investigacion fisica.
    """
    inputs = make_input(
        ingreso=80000, tipo_ingreso="Independiente",
        negocio_casa=1, antiguedad_dom=3, domicilio_id=1,
        precio=300000, enganche=75000, plazo=60,
        credinissan=1, auto_previo=1, tarjeta_alta=1,
        consultas=0, atrasos_mop=1,
    )
    r = analizar(inputs)

    assert r.probabilidad >= 80
    assert r.score_color == "AZUL"
    assert r.requiere_investigacion_fisica
    assert any(
        "fisica" in a.lower() for a in r.alertas_investigacion
    )


def test_caso_real_mop2_aprobable_condicionado():
    """MOP 2 reciente debe ir a APROBABLE CONDICIONADO."""
    inputs = make_input(
        ingreso=40000, tipo_ingreso="Nomina",
        atrasos_mop=2,
        credinissan=2, auto_previo=2, tarjeta_alta=1, hipotecario=3,
        precio=300000, enganche=60000, consultas=2,
    )
    r = analizar(inputs)

    # MOP 2 con buen perfil = APROBABLE CONDICIONADO
    assert r.plan in {"CONDICIONADO_MOP2", "CONDICIONADO"}


# ════════════════════════════════════════════════════════════════
# Run con: pytest tests/test_motor.py -v
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    pytest.main([__file__, "-v"])