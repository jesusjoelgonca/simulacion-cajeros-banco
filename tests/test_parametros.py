"""Pruebas de los parámetros del caso."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cajero_banco.parametros import (  # noqa: E402
    ACCIONES,
    PROB_PAGO,
    PROB_RETIRO,
    TIPOS,
    probabilidad_global,
    tipos_por_accion,
)


def test_probabilidades_de_accion_suman_uno() -> None:
    assert abs(PROB_RETIRO + PROB_PAGO - 1.0) < 1e-12


def test_probabilidades_por_accion_suman_uno() -> None:
    for accion in ACCIONES:
        total = sum(tipo.probabilidad for tipo in tipos_por_accion(accion))
        assert abs(total - 1.0) < 1e-12


def test_hay_cuatro_tipos_por_accion() -> None:
    assert len(TIPOS) == 8
    for accion in ACCIONES:
        assert len(tipos_por_accion(accion)) == 4


def test_probabilidad_global_sumada_da_uno() -> None:
    assert abs(sum(probabilidad_global(tipo) for tipo in TIPOS) - 1.0) < 1e-12


def test_todos_los_tiempos_son_positivos() -> None:
    for tipo in TIPOS:
        assert tipo.media_llegada > 0
        assert tipo.media_servicio > 0
