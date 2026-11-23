"""Simulador de eventos discretos para el caso del banco.

Cada caja se comporta como un sistema M/M/1 independiente. Las llegadas se
generan fuera del simulador con semillas fijas y se reutilizan en todas las
configuraciones, de modo que la comparación usa números aleatorios comunes.
"""

from __future__ import annotations

import heapq
import itertools
import random
from dataclasses import dataclass

from .parametros import (
    ACCIONES,
    MINUTOS_POR_JORNADA,
    PROB_RETIRO,
    Configuracion,
    TipoUsuario,
    tipos_por_accion,
)


@dataclass
class Cliente:
    """Un usuario que llega al banco."""

    id: int
    llegada: float
    accion: str
    tipo: TipoUsuario
    servicio: float
    inicio_servicio: float | None = None
    fin_servicio: float | None = None
    caja_id: int | None = None


@dataclass
class Caja:
    """Estado de una caja durante una réplica."""

    id: int
    accion: str | None
    ocupada: bool = False
    cliente: Cliente | None = None
    ultimo_cambio: float = 0.0
    area_ocupada: float = 0.0
    tiempo_servicio: float = 0.0
    atendidos: int = 0

    def actualizar_area(self, instante: float) -> None:
        """Acumula el tiempo ocupado solo dentro de la jornada de 8 horas."""
        instante_efectivo = min(instante, MINUTOS_POR_JORNADA)
        if instante_efectivo > self.ultimo_cambio:
            self.area_ocupada += (instante_efectivo - self.ultimo_cambio) * (
                1.0 if self.ocupada else 0.0
            )
            self.ultimo_cambio = instante_efectivo


def generar_llegadas(semilla: int) -> list[Cliente]:
    """Genera la lista de usuarios de una réplica.

    Primero se decide la acción con las probabilidades 70 % y 30 %. Después se
    elige el tipo dentro de esa acción y se toman dos exponenciales: una para
    el tiempo de servicio y otra para el intervalo hasta la siguiente llegada.
    """
    rng = random.Random(semilla)
    clientes: list[Cliente] = []
    instantes = 0.0
    contador = 0

    while instantes < MINUTOS_POR_JORNADA:
        accion = "retiro" if rng.random() < PROB_RETIRO else "pago"
        tipos = tipos_por_accion(accion)
        valor = rng.random()
        acumulado = 0.0
        tipo = tipos[-1]
        for candidato in tipos:
            acumulado += candidato.probabilidad
            if valor <= acumulado:
                tipo = candidato
                break

        servicio = rng.expovariate(1.0 / tipo.media_servicio)
        clientes.append(Cliente(contador, instantes, accion, tipo, servicio))
        contador += 1
        instantes += rng.expovariate(1.0 / tipo.media_llegada)

    return clientes


def _media(valores: list[float]) -> float:
    return sum(valores) / len(valores) if valores else 0.0


def _percentil(valores: list[float], fraccion: float) -> float:
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    indice = min(len(ordenados) - 1, int(fraccion * (len(ordenados) - 1)))
    return ordenados[indice]


class Simulador:
    """Ejecuta una réplica completa de una configuración de cajas."""

    def __init__(self, configuracion: Configuracion, clientes: list[Cliente]) -> None:
        self.configuracion = configuracion
        self.clientes = clientes
        self.secuencia = itertools.count()
        self.eventos: list[tuple[float, int, int, str, object]] = []

        self.cajas = self._crear_cajas(configuracion)
        self.cola_compartida: list[Cliente] = []
        self.colas: dict[str, list[Cliente]] = {accion: [] for accion in ACCIONES}

        self.ultimo_tiempo = 0.0
        self.en_sistema = 0
        self.area_sistema = 0.0
        self.en_sistema_por_accion: dict[str, int] = {accion: 0 for accion in ACCIONES}
        self.area_sistema_por_accion: dict[str, float] = {accion: 0.0 for accion in ACCIONES}

        for cliente in clientes:
            heapq.heappush(
                self.eventos,
                (cliente.llegada, 1, next(self.secuencia), "llegada", cliente),
            )

    @staticmethod
    def _crear_cajas(configuracion: Configuracion) -> list[Caja]:
        cajas: list[Caja] = []
        if configuracion.compartida:
            for indice in range(configuracion.total_cajas):
                cajas.append(Caja(indice + 1, None))
            return cajas

        identificador = 1
        for accion in ACCIONES:
            cantidad = configuracion.retiros if accion == "retiro" else configuracion.pagos
            for _ in range(cantidad):
                cajas.append(Caja(identificador, accion))
                identificador += 1
        return cajas

    def _avanzar(self, instante: float) -> None:
        instante_efectivo = min(instante, MINUTOS_POR_JORNADA)
        if instante_efectivo > self.ultimo_tiempo:
            delta = instante_efectivo - self.ultimo_tiempo
            self.area_sistema += delta * self.en_sistema
            for accion in ACCIONES:
                self.area_sistema_por_accion[accion] += delta * self.en_sistema_por_accion[accion]
            self.ultimo_tiempo = instante_efectivo
        for caja in self.cajas:
            caja.actualizar_area(instante)

    def _caja_libre(self, accion: str) -> Caja | None:
        for caja in self.cajas:
            if caja.ocupada:
                continue
            if self.configuracion.compartida or caja.accion == accion:
                return caja
        return None

    def _iniciar_servicio(self, caja: Caja, cliente: Cliente, instante: float) -> None:
        caja.actualizar_area(instante)
        caja.ocupada = True
        caja.cliente = cliente
        caja.ultimo_cambio = instante
        caja.tiempo_servicio += cliente.servicio
        caja.atendidos += 1
        cliente.inicio_servicio = instante
        cliente.fin_servicio = instante + cliente.servicio
        cliente.caja_id = caja.id
        heapq.heappush(
            self.eventos,
            (cliente.fin_servicio, 0, next(self.secuencia), "salida", caja),
        )

    def _procesar_llegada(self, cliente: Cliente, instante: float) -> None:
        self.en_sistema += 1
        self.en_sistema_por_accion[cliente.accion] += 1
        caja = self._caja_libre(cliente.accion)
        if caja is not None:
            self._iniciar_servicio(caja, cliente, instante)
        elif self.configuracion.compartida:
            self.cola_compartida.append(cliente)
        else:
            self.colas[cliente.accion].append(cliente)

    def _procesar_salida(self, caja: Caja, instante: float) -> None:
        cliente = caja.cliente
        caja.actualizar_area(instante)
        caja.ocupada = False
        caja.cliente = None
        self.en_sistema -= 1
        if cliente is not None:
            self.en_sistema_por_accion[cliente.accion] -= 1

        cola = (
            self.cola_compartida
            if self.configuracion.compartida
            else self.colas[cliente.accion if cliente else "retiro"]
        )
        if cola:
            self._iniciar_servicio(caja, cola.pop(0), instante)

    def ejecutar(self) -> dict[str, float | str]:
        """Corre la réplica y devuelve las métricas agregadas."""
        while self.eventos:
            instante, _prioridad, _orden, tipo_evento, payload = heapq.heappop(self.eventos)
            self._avanzar(instante)
            if tipo_evento == "llegada":
                self._procesar_llegada(payload, instante)
            else:
                self._procesar_salida(payload, instante)

        self._avanzar(MINUTOS_POR_JORNADA)
        for caja in self.cajas:
            caja.actualizar_area(MINUTOS_POR_JORNADA)

        esperas = [
            cliente.inicio_servicio - cliente.llegada
            for cliente in self.clientes
            if cliente.inicio_servicio is not None
        ]
        esperas_retiro = [
            espera
            for cliente, espera in zip(
                [c for c in self.clientes if c.inicio_servicio is not None], esperas
            )
            if cliente.accion == "retiro"
        ]
        esperas_pago = [
            espera
            for cliente, espera in zip(
                [c for c in self.clientes if c.inicio_servicio is not None], esperas
            )
            if cliente.accion == "pago"
        ]
        tiempos_sistema = [
            cliente.fin_servicio - cliente.llegada
            for cliente in self.clientes
            if cliente.fin_servicio is not None
        ]
        atendidas = [
            cliente
            for cliente in self.clientes
            if cliente.fin_servicio is not None
            and cliente.fin_servicio <= MINUTOS_POR_JORNADA
        ]
        pendientes = [cliente for cliente in self.clientes if cliente not in atendidas]
        utilizaciones = [caja.area_ocupada / MINUTOS_POR_JORNADA for caja in self.cajas]
        servicios_por_caja = [
            caja.tiempo_servicio / caja.atendidos for caja in self.cajas if caja.atendidos
        ]

        return {
            "configuracion": self.configuracion.clave,
            "llegadas": len(self.clientes),
            "atendidas_8h": len(atendidas),
            "pendientes_8h": len(pendientes),
            "espera_cola_media": _media(esperas),
            "espera_cola_p95": _percentil(esperas, 0.95),
            "espera_retiro_media": _media(esperas_retiro),
            "espera_pago_media": _media(esperas_pago),
            "tiempo_sistema_media": _media(tiempos_sistema),
            "usuarios_promedio_sistema": self.area_sistema / MINUTOS_POR_JORNADA,
            "usuarios_promedio_retiro": self.area_sistema_por_accion["retiro"] / MINUTOS_POR_JORNADA,
            "usuarios_promedio_pago": self.area_sistema_por_accion["pago"] / MINUTOS_POR_JORNADA,
            "utilizacion_media": _media(utilizaciones),
            "utilizacion_max": max(utilizaciones) if utilizaciones else 0.0,
            "servicio_medio_caja": _media(servicios_por_caja),
        }
