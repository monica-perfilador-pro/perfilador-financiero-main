"""
Motor de decision — punto de entrada unico.

Pipeline lineal, deterministico, sin mutaciones retroactivas.
Mismo input -> mismo output, siempre.

v3.0: Incorpora presion financiera y estabilidad estructural.
Las 5 dimensiones del motor:
  [1] Score historico       score_engine.py
  [2] Madurez crediticia    madurez.py
  [3] PTI operacion         pti.py
  [4] Presion financiera    presion.py   ← NUEVO v3
  [5] Estabilidad perfil    estabilidad.py ← NUEVO v3
"""
import datetime
from .inputs import InputsAnalisis
from .resultado import ResultadoMotor
from .trace import Trace
from .perfil_engine import detectar_riesgos
from .score_engine import calcular_score, determinar_perfil
from .prob_engine import calcular_probabilidad, determinar_color
from .decision_engine import decidir, mapear_semaforo
from .investigacion import generar_alertas_investigacion
from .financieras import determinar_financiera, determinar_documentos
from .madurez import evaluar_madurez
from .pti import validar_pti
from .presion import evaluar_presion
from .estabilidad import evaluar_estabilidad


# ════════════════════════════════════════════════════════════════
# CALCULOS BASICOS (no requieren reglas)
# ════════════════════════════════════════════════════════════════
def _calcular_enganche_pct(inputs: InputsAnalisis) -> float:
    if inputs.precio <= 0:
        return 0.0
    return round((inputs.enganche / inputs.precio) * 100, 2)


def _calcular_mensualidad(inputs: InputsAnalisis) -> float:
    """Calcula mensualidad con tasa fija mensual de 1.5%."""
    monto = max(inputs.precio - inputs.enganche, 0)
    if inputs.plazo <= 0 or monto <= 0:
        return 0.0
    tasa_m = 0.015
    factor = (tasa_m * (1 + tasa_m) ** inputs.plazo) / (
        (1 + tasa_m) ** inputs.plazo - 1
    )
    return round(monto * factor, 2)


def _calcular_capacidad(inputs: InputsAnalisis) -> float:
    """Capacidad de pago segun tipo de ingreso."""
    if inputs.tipo_ingreso == "Nomina":
        return round(inputs.ingreso / 2, 2)
    return round(inputs.ingreso / 3.33, 2)


def _calcular_temperatura(inputs: InputsAnalisis) -> str:
    """Termometro comercial del cliente."""
    if inputs.compra_mes == 2:
        return "FRIO"
    if (
        inputs.compra_mes == 1
        and inputs.enganche_disp == 1
        and inputs.unidad_disp == 1
    ):
        return "CALIENTE"
    return "TIBIO"


# ════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ════════════════════════════════════════════════════════════════
def analizar(inputs: InputsAnalisis) -> ResultadoMotor:
    """
    Punto de entrada unico del motor. Deterministico.

    Pipeline v3.0 — 5 dimensiones:
      FASE 1:  Calculos basicos
      FASE 2:  Deteccion de riesgos
      FASE 3:  Score numerico y perfil
      FASE 4:  Probabilidad final
      FASE 5:  Score color
      FASE 6:  Madurez crediticia
      FASE 7:  Validacion PTI
      FASE 8:  Presion financiera        ← NUEVO v3
      FASE 9:  Estabilidad estructural   ← NUEVO v3
      FASE 10: Decisionado base
      FASE 11: Post-decision limitantes
      FASE 12: Alertas investigacion
      FASE 13: Documentos y financiera
      FASE 14: Indicadores comerciales
    """
    trace = Trace()

    # ─── FASE 1: Calculos basicos ────────────────────────────────
    enganche_pct = _calcular_enganche_pct(inputs)
    mensualidad = _calcular_mensualidad(inputs)
    capacidad_pago = _calcular_capacidad(inputs)
    excede = mensualidad > capacidad_pago

    # ─── FASE 2: Deteccion de riesgos ───────────────────────────
    riesgos = detectar_riesgos(inputs, enganche_pct, trace)

    # ─── FASE 3: Score numerico y perfil ─────────────────────────
    score = calcular_score(inputs, trace)
    perfil = determinar_perfil(score, trace)

    # ─── FASE 4: Probabilidad final ──────────────────────────────
    probabilidad = calcular_probabilidad(inputs, perfil, enganche_pct, trace)

    # ─── FASE 5: Score color ─────────────────────────────────────
    score_color = determinar_color(probabilidad, trace)

    # ─── FASE 6: Madurez crediticia ──────────────────────────────
    madurez = evaluar_madurez(inputs, trace)

    # ─── FASE 7: Validacion PTI ──────────────────────────────────
    pti = validar_pti(
        mensualidad=mensualidad,
        capacidad_pago=capacidad_pago,
        ingreso=inputs.ingreso,
        enganche_pct=enganche_pct,
        trace=trace,
    )

    # ─── FASE 8: Presion financiera ──────────────────────────────
    # Evalua tension de deuda actual: tarjetas al tope,
    # muchos creditos abiertos, busqueda activa de credito.
    presion = evaluar_presion(inputs, trace)

    # ─── FASE 9: Estabilidad estructural ─────────────────────────
    # Evalua factores de largo plazo: edad+plazo, ingreso estable,
    # domicilio estable.
    estabilidad = evaluar_estabilidad(inputs, trace)

    # ─── FASE 10: Decisionado base ────────────────────────────────
    decision_data = decidir(
        inputs=inputs,
        riesgos=riesgos,
        perfil=perfil,
        score_color=score_color,
        prob=probabilidad,
        excede=excede,
        trace=trace,
    )

    # ─── FASE 11: Post-decision — aplicar limitantes ──────────────
    # Orden de prioridad al aplicar limitantes:
    #   1. PTI       (problema inmediato de capacidad)
    #   2. Presion   (riesgo oculto actual)
    #   3. Estabilidad (riesgo estructural largo plazo)
    #   4. Madurez   (historial poco profundo)
    decision_final = decision_data.decision
    plan_final = decision_data.plan
    condicionamientos_finales = list(decision_data.condicionamientos)
    mensaje_cliente_final = decision_data.mensaje_cliente
    mensaje_asesor_final = decision_data.mensaje_asesor
    requiere_cotitular_final = decision_data.requiere_cotitular

    if plan_final in ("AUTOMATICO", "DIRECTO"):

        # Limitante 1: PTI bloquea
        if pti.bloquea_automatico:
            plan_final = "SE_VA_A_ANALISIS"
            decision_final = "APROBADO EN ANALISIS DE FINANCIERA"
            condicionamientos_finales = list(pti.condicionamientos_pti)
            mensaje_cliente_final = (
                "Tu historial crediticio es positivo, pero la estructura "
                "financiera actual requiere un ajuste antes de avanzar."
            )
            mensaje_asesor_final = (
                f"Buen score pero estructura inviable. {pti.mensaje_asesor} "
                "Ajustar enganche o plazo antes de enviar a financiera."
            )
            trace.disparar("POST_PTI")

        # Limitante 2: Presion financiera alta/critica
        elif presion.bloquea_automatico:
            plan_final = "SE_VA_A_ANALISIS"
            decision_final = "APROBADO EN ANALISIS DE FINANCIERA"
            condicionamientos_finales = list(presion.condicionamientos)
            condicionamientos_finales.append("REVISAR CARGA DE DEUDA ACTUAL")
            mensaje_cliente_final = (
                "Tu historial de pagos es positivo, pero necesitamos "
                "revisar tu situacion financiera actual antes de avanzar."
            )
            mensaje_asesor_final = (
                f"Historial limpio pero cliente tensionado financieramente. "
                f"{presion.razon}. "
                "No proceder automatico. Revisar buro completo con asesor."
            )
            trace.disparar("POST_PRESION")

        # Limitante 3: Estabilidad estructural baja
        elif estabilidad.bloquea_automatico:
            plan_final = "SE_VA_A_ANALISIS"
            decision_final = "APROBADO EN ANALISIS DE FINANCIERA"
            condicionamientos_finales = list(estabilidad.condicionamientos)
            mensaje_cliente_final = (
                "Tu perfil es aprobable, pero el plazo o la estructura "
                "del credito necesitan un ajuste."
            )
            mensaje_asesor_final = (
                f"Factores estructurales de largo plazo. "
                f"{estabilidad.razon}. "
                f"Plazo recomendado: {estabilidad.plazo_maximo_rec} meses."
            )
            trace.disparar("POST_ESTABILIDAD")

        # Limitante 4: Madurez insuficiente
        elif madurez.limitante_automatico:
            plan_final = "SE_VA_A_ANALISIS"
            decision_final = "APROBADO EN ANALISIS DE FINANCIERA"
            condicionamientos_finales = [
                "VALIDACION DE MADUREZ CREDITICIA",
                "INVESTIGACION ADICIONAL REQUERIDA",
            ]
            mensaje_cliente_final = (
                "Tu perfil es aprobable, pero requiere validacion "
                "adicional por parte de la financiera."
            )
            mensaje_asesor_final = (
                f"Historial limpio pero poco profundo. "
                f"{madurez.razon_limitante}. "
                "Enviar a revision manual."
            )
            trace.disparar("POST_MADUREZ")

    # Para cualquier plan: si hay presion MEDIA, enriquecer mensaje
    elif presion.requiere_validacion and presion.nivel == "MEDIA":
        # No cambia el plan pero agrega contexto al asesor
        if "presion" not in mensaje_asesor_final.lower():
            mensaje_asesor_final = (
                f"{mensaje_asesor_final} | "
                f"Atencion: {presion.razon}"
            )
        trace.disparar("POST_PRESION_MEDIA")

    # Para cualquier plan: si estabilidad es ATENCION, agregar condicionamiento
    if estabilidad.riesgo_edad_plazo == "ATENCION":
        cond_plazo = (
            f"VERIFICAR PLAZO — cliente termina credito a los "
            f"{estabilidad.edad_al_terminar} anos"
        )
        if cond_plazo not in condicionamientos_finales:
            condicionamientos_finales.append(cond_plazo)

    # Agregar condicionamientos PTI si no generaron cambio de plan
    if pti.condicionamientos_pti and plan_final not in ("AUTOMATICO", "DIRECTO"):
        for cond in pti.condicionamientos_pti:
            if cond not in condicionamientos_finales:
                condicionamientos_finales.append(cond)

    # ─── FASE 12: Alertas investigacion ──────────────────────────
    alertas = generar_alertas_investigacion(inputs, probabilidad, trace)

    # Agregar alerta de presion si es relevante
    if presion.nivel in ("ALTA", "CRITICA"):
        alertas = list(alertas)
        if "Sin alerta relevante" in alertas:
            alertas.remove("Sin alerta relevante")
        alertas.append(f"Presion financiera {presion.nivel.lower()}: {presion.razon}")

    # ─── FASE 13: Documentos y financiera ────────────────────────
    documentos = determinar_documentos(plan_final, inputs)
    financiera = determinar_financiera(plan_final)

    # ─── FASE 14: Indicadores comerciales ────────────────────────
    temperatura = _calcular_temperatura(inputs)
    semaforo = mapear_semaforo(plan_final)

    # ─── Banderas explicitas ─────────────────────────────────────
    requiere_validacion_ingresos = (
        "INGRESO" in " ".join(condicionamientos_finales).upper()
        or "INGRESOS" in " ".join(condicionamientos_finales).upper()
    )
    requiere_investigacion_fisica = (
        inputs.tipo_ingreso == "Independiente"
        and inputs.negocio_casa == 1
    )

    # ─── CONSTRUCCION RESULTADO INMUTABLE ────────────────────────
    return ResultadoMotor(
        decision=decision_final,
        plan=plan_final,
        score_color=score_color,
        score_puntos=score,
        perfil_interno=perfil,
        probabilidad=probabilidad,
        semaforo=semaforo,
        temperatura=temperatura,
        financiera_sugerida=financiera,
        capacidad_pago=capacidad_pago,
        mensualidad_estimada=mensualidad,
        enganche_pct=enganche_pct,
        excede_capacidad=excede,
        condicionamientos=condicionamientos_finales,
        documentos_requeridos=list(documentos),
        alertas_investigacion=list(alertas),
        mensaje_cliente=mensaje_cliente_final,
        mensaje_asesor=mensaje_asesor_final,
        requiere_cotitular=requiere_cotitular_final,
        requiere_validacion_ingresos=requiere_validacion_ingresos,
        requiere_investigacion_fisica=requiere_investigacion_fisica,
        reglas_disparadas=trace.to_list(),
        version_motor="3.0.0",
        timestamp=datetime.datetime.now().isoformat(),
    )
    trace = Trace()

    # ─── FASE 1: Calculos basicos ────────────────────────────────
    enganche_pct = _calcular_enganche_pct(inputs)
    mensualidad = _calcular_mensualidad(inputs)
    capacidad_pago = _calcular_capacidad(inputs)
    excede = mensualidad > capacidad_pago

    # ─── FASE 2: Deteccion de riesgos ───────────────────────────
    riesgos = detectar_riesgos(inputs, enganche_pct, trace)

    # ─── FASE 3: Score numerico y perfil interno ─────────────────
    score = calcular_score(inputs, trace)
    perfil = determinar_perfil(score, trace)

    # ─── FASE 4: Probabilidad final ──────────────────────────────
    probabilidad = calcular_probabilidad(inputs, perfil, enganche_pct, trace)

    # ─── FASE 5: Score color ─────────────────────────────────────
    score_color = determinar_color(probabilidad, trace)

    # ─── FASE 6: Madurez crediticia ──────────────────────────────
    # Evalua profundidad historica y estabilidad del perfil.
    # Puede marcar que el perfil NO califica para AUTOMATICO
    # aunque la probabilidad matematica sea alta.
    madurez = evaluar_madurez(inputs, trace)

    # ─── FASE 7: Validacion PTI ──────────────────────────────────
    # Evalua si la estructura financiera de la operacion es viable.
    # Genera condicionamientos contextuales (no sugiere lo que ya tiene).
    pti = validar_pti(
        mensualidad=mensualidad,
        capacidad_pago=capacidad_pago,
        ingreso=inputs.ingreso,
        enganche_pct=enganche_pct,
        trace=trace,
    )

    # ─── FASE 8: Decisionado base ────────────────────────────────
    decision_data = decidir(
        inputs=inputs,
        riesgos=riesgos,
        perfil=perfil,
        score_color=score_color,
        prob=probabilidad,
        excede=excede,
        trace=trace,
    )

    # ─── FASE 9: Post-decision — aplicar limitantes ───────────────
    # Si la decision base fue AUTOMATICO, verificamos que sea viable.
    # El score puede ser bueno pero la madurez o el PTI pueden impedirlo.
    decision_final = decision_data.decision
    plan_final = decision_data.plan
    condicionamientos_finales = list(decision_data.condicionamientos)
    mensaje_cliente_final = decision_data.mensaje_cliente
    mensaje_asesor_final = decision_data.mensaje_asesor
    requiere_cotitular_final = decision_data.requiere_cotitular

    if plan_final == "AUTOMATICO":

        # Limitante por PTI: mensualidad excede capacidad
        if pti.bloquea_automatico:
            plan_final = "SE_VA_A_ANALISIS"
            decision_final = "APROBADO EN ANALISIS DE FINANCIERA"
            condicionamientos_finales = list(pti.condicionamientos_pti)
            mensaje_cliente_final = (
                "Tu historial crediticio es positivo, pero la estructura "
                "financiera actual requiere un ajuste antes de avanzar."
            )
            mensaje_asesor_final = (
                f"Buen score, estructura inviable. {pti.mensaje_asesor} "
                "Ajustar enganche o plazo antes de enviar a financiera."
            )
            trace.disparar("POST_PTI")

        # Limitante por madurez: historial poco profundo
        elif madurez.limitante_automatico:
            plan_final = "SE_VA_A_ANALISIS"
            decision_final = "APROBADO EN ANALISIS DE FINANCIERA"
            condicionamientos_finales = [
                "VALIDACION DE MADUREZ CREDITICIA",
                "INVESTIGACION ADICIONAL REQUERIDA",
            ]
            mensaje_cliente_final = (
                "Tu perfil es aprobable, pero requiere una validacion "
                "adicional por parte de la financiera."
            )
            mensaje_asesor_final = (
                f"Historial limpio pero poco profundo. "
                f"{madurez.razon_limitante}. "
                "Enviar a revision manual, no proceder en automatico."
            )
            trace.disparar("POST_MADUREZ")

    # Si la decision es DIRECTO, verificar PTI
    elif plan_final == "DIRECTO" and pti.bloquea_automatico:
        plan_final = "CONDICIONADO"
        decision_final = "APROBABLE CON AJUSTES"
        condicionamientos_finales = list(pti.condicionamientos_pti)
        mensaje_asesor_final = (
            f"Perfil estable pero estructura financiera ajustable. "
            f"{pti.mensaje_asesor}"
        )
        trace.disparar("POST_PTI_DIRECTO")

    # Si cualquier otro plan tiene PTI excedido, enriquecer el mensaje
    elif pti.bloquea_automatico and "estructura" not in mensaje_asesor_final.lower():
        mensaje_asesor_final = (
            f"{mensaje_asesor_final} | Estructura financiera: {pti.mensaje_asesor}"
        )
        # Agregar condicionamientos PTI sin duplicar
        for cond in pti.condicionamientos_pti:
            if cond not in condicionamientos_finales:
                condicionamientos_finales.append(cond)
        trace.disparar("POST_PTI_ENRICH")

    # ─── FASE 10: Alertas de investigacion ───────────────────────
    alertas = generar_alertas_investigacion(inputs, probabilidad, trace)

    # ─── FASE 11: Documentos y financiera ────────────────────────
    documentos = determinar_documentos(plan_final, inputs)
    financiera = determinar_financiera(plan_final)

    # ─── FASE 12: Indicadores comerciales ────────────────────────
    temperatura = _calcular_temperatura(inputs)
    semaforo = mapear_semaforo(plan_final)

    # ─── Condicionamientos PTI contextuales (si aplica) ──────────
    # Solo se agregan si no generaron ya un cambio de plan
    if pti.condicionamientos_pti and plan_final not in ("AUTOMATICO", "DIRECTO"):
        for cond in pti.condicionamientos_pti:
            if cond not in condicionamientos_finales:
                condicionamientos_finales.append(cond)

    # ─── Banderas explicitas ─────────────────────────────────────
    requiere_validacion_ingresos = (
        "INGRESO" in " ".join(condicionamientos_finales).upper()
        or "INGRESOS" in " ".join(condicionamientos_finales).upper()
    )
    requiere_investigacion_fisica = (
        inputs.tipo_ingreso == "Independiente"
        and inputs.negocio_casa == 1
    )

    # ─── CONSTRUCCION DEL RESULTADO INMUTABLE ────────────────────
    return ResultadoMotor(
        decision=decision_final,
        plan=plan_final,
        score_color=score_color,
        score_puntos=score,
        perfil_interno=perfil,
        probabilidad=probabilidad,
        semaforo=semaforo,
        temperatura=temperatura,
        financiera_sugerida=financiera,
        capacidad_pago=capacidad_pago,
        mensualidad_estimada=mensualidad,
        enganche_pct=enganche_pct,
        excede_capacidad=excede,
        condicionamientos=condicionamientos_finales,
        documentos_requeridos=list(documentos),
        alertas_investigacion=list(alertas),
        mensaje_cliente=mensaje_cliente_final,
        mensaje_asesor=mensaje_asesor_final,
        requiere_cotitular=requiere_cotitular_final,
        requiere_validacion_ingresos=requiere_validacion_ingresos,
        requiere_investigacion_fisica=requiere_investigacion_fisica,
        reglas_disparadas=trace.to_list(),
        version_motor="2.1.0",
        timestamp=datetime.datetime.now().isoformat(),
    )