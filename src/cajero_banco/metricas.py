"""Estadísticas descriptivas de las réplicas."""

from __future__ import annotations

from statistics import mean, stdev

import pandas as pd
from scipy import stats


def resumen_columna(valores: pd.Series) -> dict[str, float]:
    """Media, desviación e intervalo de confianza 95 % de una columna."""
    serie = pd.Series(valores).dropna().astype(float)
    media_valor = float(serie.mean())
    desviacion = float(serie.std(ddof=1)) if len(serie) > 1 else 0.0
    error_estandar = desviacion / (len(serie) ** 0.5) if len(serie) else 0.0
    if len(serie) > 1:
        critico = float(stats.t.ppf(0.975, len(serie) - 1))
    else:
        critico = 0.0
    return {
        "media": media_valor,
        "desviacion": desviacion,
        "limite_inferior": media_valor - critico * error_estandar,
        "limite_superior": media_valor + critico * error_estandar,
    }


def resumen_configuraciones(
    trama: pd.DataFrame, columnas: tuple[str, ...]
) -> pd.DataFrame:
    """Tabla con media e IC 95 % por configuración para varias métricas."""
    filas = []
    for clave, grupo in trama.groupby("configuracion", sort=False):
        fila: dict[str, object] = {"configuracion": clave, "replicas": len(grupo)}
        for columna in columnas:
            resumen = resumen_columna(grupo[columna])
            fila[f"{columna}_media"] = resumen["media"]
            fila[f"{columna}_li"] = resumen["limite_inferior"]
            fila[f"{columna}_ls"] = resumen["limite_superior"]
        filas.append(fila)
    return pd.DataFrame(filas)


def media_simple(valores: list[float]) -> float:
    """Media de una lista, con cero para listas vacías."""
    return float(mean(valores)) if valores else 0.0


def desviacion_simple(valores: list[float]) -> float:
    """Desviación muestral de una lista."""
    return float(stdev(valores)) if len(valores) > 1 else 0.0
