"""Pruebas del motor de simulación."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cajero_banco.parametros import CONFIGURACIONES, MINUTOS_POR_JORNADA  # noqa: E402
from cajero_banco.simulacion import Simulador, generar_llegadas  # noqa: E402


def configuracion(clave: str):
    return next(config for config in CONFIGURACIONES if config.clave == clave)


def test_generar_llegadas_es_reproducible() -> None:
    primera = generar_llegadas(123)
    segunda = generar_llegadas(123)
    assert [cliente.llegada for cliente in primera] == [cliente.llegada for cliente in segunda]
    assert [cliente.tipo.codigo for cliente in primera] == [
        cliente.tipo.codigo for cliente in segunda
    ]


def test_llegadas_dentro_de_la_jornada() -> None:
    clientes = generar_llegadas(321)
    assert clientes
    assert clientes[0].llegada == 0.0
    assert clientes[-1].llegada < MINUTOS_POR_JORNADA


def test_todos_los_usuarios_son_atendidos_al_final() -> None:
    clientes = generar_llegadas(77)
    simulador = Simulador(configuracion("compartida_3"), clientes)
    simulador.ejecutar()
    assert all(cliente.fin_servicio is not None for cliente in clientes)
    assert all(cliente.inicio_servicio is not None for cliente in clientes)


def test_esperas_no_son_negativas() -> None:
    clientes = generar_llegadas(88)
    simulador = Simulador(configuracion("dedicada_2r_1p"), clientes)
    simulador.ejecutar()
    esperas = [
        cliente.inicio_servicio - cliente.llegada
        for cliente in clientes
        if cliente.inicio_servicio is not None
    ]
    assert all(espera >= -1e-9 for espera in esperas)


def test_contabilidad_de_usuarios() -> None:
    clientes = generar_llegadas(99)
    simulador = Simulador(configuracion("dedicada_1r_2p"), clientes)
    resultado = simulador.ejecutar()
    assert resultado["atendidas_8h"] + resultado["pendientes_8h"] == len(clientes)


def test_cajas_dedicadas_reciben_solo_su_accion() -> None:
    clientes = generar_llegadas(101)
    simulador = Simulador(configuracion("dedicada_2r_1p"), clientes)
    simulador.ejecutar()
    por_caja = {caja.id: caja for caja in simulador.cajas}
    for cliente in clientes:
        caja = por_caja[cliente.caja_id]
        assert caja.accion == cliente.accion
