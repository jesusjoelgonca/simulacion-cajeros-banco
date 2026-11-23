"""Parámetros del caso del Banco de Colombia.

Los tiempos vienen en minutos. La jornada es de ocho horas, así que el
horizonte de simulación son 480 minutos por réplica.
"""

from __future__ import annotations

from dataclasses import dataclass

MINUTOS_POR_JORNADA = 480.0
REPLICAS = 30
SEMILLA_BASE = 20261122

PROB_RETIRO = 0.70
PROB_PAGO = 0.30


@dataclass(frozen=True)
class TipoUsuario:
    """Un tipo de usuario dentro de una acción bancaria."""

    accion: str
    codigo: str
    etiqueta: str
    media_llegada: float
    media_servicio: float
    probabilidad: float


TIPOS: tuple[TipoUsuario, ...] = (
    TipoUsuario("retiro", "R1", "Retiro rápido", 1.0, 1.0, 0.23),
    TipoUsuario("retiro", "R2", "Retiro normal", 2.0, 2.0, 0.40),
    TipoUsuario("retiro", "R3", "Retiro lento", 3.0, 3.0, 0.17),
    TipoUsuario("retiro", "R4", "Retiro muy lento", 3.0, 4.0, 0.20),
    TipoUsuario("pago", "P1", "Pago rápido", 1.0, 3.0, 0.10),
    TipoUsuario("pago", "P2", "Pago normal", 2.0, 3.0, 0.20),
    TipoUsuario("pago", "P3", "Pago lento", 3.0, 5.0, 0.30),
    TipoUsuario("pago", "P4", "Pago muy lento", 4.0, 7.0, 0.40),
)

ACCIONES = ("retiro", "pago")


def tipos_por_accion(accion: str) -> tuple[TipoUsuario, ...]:
    """Devuelve los cuatro tipos que pertenecen a una acción."""
    return tuple(tipo for tipo in TIPOS if tipo.accion == accion)


def probabilidad_global(tipo: TipoUsuario) -> float:
    """Probabilidad del tipo en la mezcla total de usuarios del banco."""
    prob_de_accion = PROB_RETIRO if tipo.accion == "retiro" else PROB_PAGO
    return prob_de_accion * tipo.probabilidad


def tasa_llegada_global() -> float:
    """Tasa de llegadas por minuto según la mezcla de tipos."""
    return sum(probabilidad_global(tipo) / tipo.media_llegada for tipo in TIPOS)


def servicio_medio_global() -> float:
    """Tiempo medio de servicio esperado en la mezcla de tipos."""
    return sum(probabilidad_global(tipo) * tipo.media_servicio for tipo in TIPOS)


@dataclass(frozen=True)
class Configuracion:
    """Distribución de cajas que se evalúa en una corrida."""

    clave: str
    etiqueta: str
    retiros: int
    pagos: int
    compartida: bool = False

    @property
    def total_cajas(self) -> int:
        return self.retiros + self.pagos


CONFIGURACIONES: tuple[Configuracion, ...] = (
    Configuracion("compartida_3", "Tres cajas compartidas", 3, 0, compartida=True),
    Configuracion("dedicada_1r_2p", "Una caja de retiros y dos de pagos", 1, 2),
    Configuracion("dedicada_2r_1p", "Dos cajas de retiros y una de pagos", 2, 1),
    Configuracion("nueva_2r_2p", "Cuatro cajas: dos de retiros y dos de pagos", 2, 2),
)
