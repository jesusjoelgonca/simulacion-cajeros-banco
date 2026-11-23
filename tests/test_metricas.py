"""Pruebas de las funciones estadísticas."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cajero_banco.metricas import (  # noqa: E402
    desviacion_simple,
    media_simple,
    resumen_columna,
    resumen_configuraciones,
)


def test_resumen_columna() -> None:
    resumen = resumen_columna(pd.Series([1.0, 2.0, 3.0, 4.0]))
    assert resumen["media"] == 2.5
    assert resumen["limite_inferior"] < resumen["media"] < resumen["limite_superior"]


def test_resumen_ignora_nulos() -> None:
    resumen = resumen_columna(pd.Series([1.0, None, 3.0]))
    assert resumen["media"] == 2.0


def test_resumen_configuraciones() -> None:
    trama = pd.DataFrame(
        {
            "configuracion": ["a", "a", "b", "b"],
            "espera": [1.0, 3.0, 2.0, 4.0],
        }
    )
    resumen = resumen_configuraciones(trama, ("espera",))
    assert list(resumen["configuracion"]) == ["a", "b"]
    assert resumen.loc[0, "espera_media"] == 2.0
    assert resumen.loc[1, "espera_media"] == 3.0


def test_helpers_de_listas() -> None:
    assert media_simple([]) == 0.0
    assert desviacion_simple([5.0]) == 0.0
    assert media_simple([2.0, 4.0]) == 3.0
