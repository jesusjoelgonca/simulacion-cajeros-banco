"""Genera las figuras del informe a partir de los CSV de resultados."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
RESULTADOS = RAIZ / "resultados"
FIGURAS = RESULTADOS / "figuras"
FIGURAS.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(RAIZ / "src"))

from cajero_banco.parametros import CONFIGURACIONES  # noqa: E402

ETIQUETAS = {config.clave: config.etiqueta for config in CONFIGURACIONES}
AZUL = "#2F5597"
NARANJA = "#C55A11"
GRIS = "#7F7F7F"


def barras_con_ic(resumen: pd.DataFrame, columna: str, archivo: str, titulo: str, eje_y: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    valores = resumen[f"{columna}_media"].to_numpy()
    li = resumen[f"{columna}_li"].to_numpy()
    ls = resumen[f"{columna}_ls"].to_numpy()
    error_inferior = valores - li
    error_superior = ls - valores
    etiquetas = [ETIQUETAS.get(clave, clave) for clave in resumen["configuracion"]]
    posiciones = range(len(etiquetas))

    ax.bar(posiciones, valores, color=AZUL, width=0.62)
    ax.errorbar(
        posiciones,
        valores,
        yerr=[error_inferior, error_superior],
        fmt="none",
        ecolor=GRIS,
        capsize=5,
        linewidth=1.2,
    )
    ax.set_xticks(list(posiciones))
    ax.set_xticklabels(etiquetas, rotation=12, ha="right")
    ax.set_ylabel(eje_y)
    ax.set_title(titulo)
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / archivo, dpi=300)
    plt.close(fig)


def main() -> None:
    resumen = pd.read_csv(RESULTADOS / "resumen_configuraciones.csv")

    barras_con_ic(
        resumen,
        "espera_cola_media",
        "fig1_espera_cola.png",
        "Espera media en cola por configuración",
        "Minutos",
    )
    barras_con_ic(
        resumen,
        "tiempo_sistema_media",
        "fig2_tiempo_sistema.png",
        "Tiempo medio en el sistema por configuración",
        "Minutos",
    )
    barras_con_ic(
        resumen,
        "pendientes_8h",
        "fig3_pendientes.png",
        "Usuarios pendientes al cierre de la jornada",
        "Usuarios por réplica",
    )

    fig, ax = plt.subplots(figsize=(9, 5.2))
    posiciones = range(len(resumen))
    media = resumen["utilizacion_media_media"].to_numpy() * 100
    maxima = resumen["utilizacion_max_media"].to_numpy() * 100
    ancho = 0.36
    ax.bar([p - ancho / 2 for p in posiciones], media, ancho, label="Media", color=AZUL)
    ax.bar([p + ancho / 2 for p in posiciones], maxima, ancho, label="Máxima", color=NARANJA)
    ax.axhline(85, color=GRIS, linestyle="--", linewidth=1, label="Umbral 85 %")
    ax.set_xticks(list(posiciones))
    ax.set_xticklabels(
        [ETIQUETAS.get(clave, clave) for clave in resumen["configuracion"]],
        rotation=12,
        ha="right",
    )
    ax.set_ylabel("Utilización (%)")
    ax.set_title("Utilización de las cajas por configuración")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig4_utilizacion.png", dpi=300)
    plt.close(fig)

    print(f"Figuras escritas en {FIGURAS}")


if __name__ == "__main__":
    main()
