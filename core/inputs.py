"""
Inputs del motor de decision v3.
Dataclass INMUTABLE — nadie puede modificar los inputs despues de creados.

v3.0: Agrega 4 variables nuevas para detectar presion financiera y estabilidad.
Todas opcionales con defaults conservadores — no rompen flujos existentes.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class InputsAnalisis:
    """
    Datos de entrada del motor de decision crediticio.

    Convencion de codigos:
      - tipo_ingreso:    "Nomina" | "Independiente" | "No comprueba"
      - negocio_casa:    0=NoAplica, 1=Si, 2=No
      - antiguedad_dom:  1=<1ano, 2=1-3anos, 3=+3anos
      - domicilio_id:    1=Si, 2=No   (si la direccion en buro coincide con ID)
      - hipotecario:     1=Bancario, 2=Infonavit, 3=No tiene
      - tarjeta_alta:    1=Si, 2=No   (tiene tarjeta con limite >100K)
      - tarjeta_baja:    1=Si, 2=No   (tiene tarjeta con limite <100K)
      - atrasos_mop:     1=1-30dias, 2=31-60dias, 3=+61dias
      - auto_previo:     1=Si, 2=No   (tiene credito automotriz previo)
      - credinissan:     1=Si, 2=No   (tiene credito CrediNissan previo)
      - enganche_disp:   1=Si, 2=No   (cliente tiene enganche disponible)
      - compra_mes:      1=Si, 2=No   (cliente compra este mes)
      - unidad_disp:     1=Si, 2=No   (hay unidad disponible)
    """

    # ─── Cliente ──────────────────────────────────────────────────
    nombre: str
    telefono: str
    correo: str
    edad: int

    # ─── Perfil financiero ───────────────────────────────────────
    ingreso: float
    tipo_ingreso: str
    negocio_casa: int
    antiguedad_dom: int
    domicilio_id: int

    # ─── Vehiculo ────────────────────────────────────────────────
    precio: float
    enganche: float
    plazo: int

    # ─── Buro ────────────────────────────────────────────────────
    consultas: int
    auto_previo: int
    credinissan: int
    hipotecario: int
    tarjeta_alta: int
    tarjeta_baja: int
    atrasos_mop: int

    # ─── Compra ──────────────────────────────────────────────────
    enganche_disp: int
    compra_mes: int
    unidad_disp: int

    # ─── Estabilidad laboral e historial (NUEVOS v3.1) ──────────
    # antiguedad_empleo: tiempo en el trabajo actual
    #   0 = no aplica / jubilado
    #   1 = menos de 6 meses
    #   2 = 6 meses a 2 años
    #   3 = 2 a 5 años
    #   4 = más de 5 años
    antiguedad_empleo: int = 3    # default conservador: 2-5 años

    # antiguedad_historial: desde cuándo tiene créditos o tarjetas
    #   0 = sin créditos previos
    #   1 = menos de 1 año
    #   2 = 1 a 3 años
    #   3 = 3 a 7 años
    #   4 = más de 7 años
    antiguedad_historial: int = 2  # default conservador: 1-3 años

    # ─── Presion financiera (NUEVOS v3.0 — todos con defaults) ───
    # utilizacion_revolvente: % promedio de uso de tarjetas (0-100)
    #   0 = sin tarjetas o dato no disponible
    utilizacion_revolvente: int = 0
    # productos_activos: cuantos creditos abiertos tiene HOY
    #   tarjetas + hipoteca + autos + personales
    productos_activos: int = 0
    # consultas_recientes: consultas en los ultimos 6 meses
    #   0 = no disponible (motor usa campo `consultas` como proxy)
    consultas_recientes: int = 0
    # nivel_deuda_actual: evaluacion global de carga de deuda
    #   0=ninguna, 1=baja, 2=media, 3=alta
    nivel_deuda_actual: int = 0

    # ─── Asesor (opcional, para auditoria) ───────────────────────
    asesor_nombre: str = ""
    asesor_rfc: str = ""
    asesor_telefono: str = ""
    asesor_correo: str = ""

    def to_dict(self) -> dict:
        """Convierte a dict para persistencia."""
        return {
            "nombre": self.nombre,
            "telefono": self.telefono,
            "correo": self.correo,
            "edad": self.edad,
            "ingreso": self.ingreso,
            "tipo_ingreso": self.tipo_ingreso,
            "negocio_casa": self.negocio_casa,
            "antiguedad_dom": self.antiguedad_dom,
            "domicilio_id": self.domicilio_id,
            "precio": self.precio,
            "enganche": self.enganche,
            "plazo": self.plazo,
            "consultas": self.consultas,
            "auto_previo": self.auto_previo,
            "credinissan": self.credinissan,
            "hipotecario": self.hipotecario,
            "tarjeta_alta": self.tarjeta_alta,
            "tarjeta_baja": self.tarjeta_baja,
            "atrasos_mop": self.atrasos_mop,
            "enganche_disp": self.enganche_disp,
            "compra_mes": self.compra_mes,
            "unidad_disp": self.unidad_disp,
            "antiguedad_empleo": self.antiguedad_empleo,
            "antiguedad_historial": self.antiguedad_historial,
            "utilizacion_revolvente": self.utilizacion_revolvente,
            "productos_activos": self.productos_activos,
            "consultas_recientes": self.consultas_recientes,
            "nivel_deuda_actual": self.nivel_deuda_actual,
            "asesor_nombre": self.asesor_nombre,
            "asesor_rfc": self.asesor_rfc,
            "asesor_telefono": self.asesor_telefono,
            "asesor_correo": self.asesor_correo,
        }