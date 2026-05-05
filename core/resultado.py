"""
Resultado del motor de decision.
Dataclass INMUTABLE — nadie modifica el resultado despues de calculado.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ResultadoMotor:
    """
    Resultado completo del analisis crediticio.
    Inmutable — garantia de que ninguna funcion lo va a mutar.
    """

    # ─── Decision principal ──────────────────────────────────────
    decision: str            # texto principal mostrado al asesor
    plan: str                # codigo del plan (AUTOMATICO/COTITULAR/etc)

    # ─── Metricas crediticias ────────────────────────────────────
    score_color: str         # AZUL/VERDE/AMARILLO/NARANJA/ROJO
    score_puntos: int        # score numerico (puede ser negativo)
    perfil_interno: str      # DELGADO/MEDIO/FUERTE
    probabilidad: int        # 5-95 (porcentaje)

    # ─── Indicadores comerciales ─────────────────────────────────
    semaforo: str            # verde/amarillo/naranja/rojo
    temperatura: str         # CALIENTE/TIBIO/FRIO
    financiera_sugerida: str # Automatico/Condicionado/Especial

    # ─── Capacidad financiera ────────────────────────────────────
    capacidad_pago: float    # mensualidad maxima recomendada
    mensualidad_estimada: float
    enganche_pct: float      # porcentaje del precio
    excede_capacidad: bool   # mensualidad > capacidad_pago

    # ─── Listas (nunca se sobrescriben) ──────────────────────────
    condicionamientos: List[str] = field(default_factory=list)
    documentos_requeridos: List[str] = field(default_factory=list)
    alertas_investigacion: List[str] = field(default_factory=list)

    # ─── Mensajes ────────────────────────────────────────────────
    mensaje_cliente: str = ""
    mensaje_asesor: str = ""

    # ─── Banderas explicitas (no string-matching) ────────────────
    requiere_cotitular: bool = False
    requiere_validacion_ingresos: bool = False
    requiere_investigacion_fisica: bool = False

    # ─── Auditoria ───────────────────────────────────────────────
    reglas_disparadas: List[str] = field(default_factory=list)
    version_motor: str = "v2.0.0"
    timestamp: str = ""

    def to_dict(self) -> dict:
        """Convierte a dict para persistencia (Sheets, JSON)."""
        return {
            "decision": self.decision,
            "plan": self.plan,
            "score_color": self.score_color,
            "score_puntos": self.score_puntos,
            "perfil_interno": self.perfil_interno,
            "probabilidad": self.probabilidad,
            "semaforo": self.semaforo,
            "temperatura": self.temperatura,
            "financiera_sugerida": self.financiera_sugerida,
            "capacidad_pago": self.capacidad_pago,
            "mensualidad_estimada": self.mensualidad_estimada,
            "enganche_pct": self.enganche_pct,
            "excede_capacidad": self.excede_capacidad,
            "condicionamientos": self.condicionamientos,
            "documentos_requeridos": self.documentos_requeridos,
            "alertas_investigacion": self.alertas_investigacion,
            "mensaje_cliente": self.mensaje_cliente,
            "mensaje_asesor": self.mensaje_asesor,
            "requiere_cotitular": self.requiere_cotitular,
            "requiere_validacion_ingresos": self.requiere_validacion_ingresos,
            "requiere_investigacion_fisica": self.requiere_investigacion_fisica,
            "reglas_disparadas": self.reglas_disparadas,
            "version_motor": self.version_motor,
            "timestamp": self.timestamp,
        }

    # ─── Compatibilidad con UI actual (alias legibles) ──────────
    @property
    def sc(self) -> str:
        """Alias legacy para score_color."""
        return self.score_color

    @property
    def prob(self) -> int:
        """Alias legacy para probabilidad."""
        return self.probabilidad

    @property
    def sem(self) -> str:
        """Alias legacy para semaforo."""
        return self.semaforo

    @property
    def temp(self) -> str:
        """Alias legacy para temperatura."""
        return self.temperatura

    @property
    def inv(self) -> str:
        """Alias legacy: alertas como texto unico (compatibilidad UI)."""
        if not self.alertas_investigacion:
            return "Sin alerta relevante"
        if len(self.alertas_investigacion) == 1:
            return self.alertas_investigacion[0]
        return " · ".join(self.alertas_investigacion)