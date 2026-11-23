"""Interfaz de línea de comandos para una demostración rápida."""

from __future__ import annotations

import argparse

from .parametros import CONFIGURACIONES, SEMILLA_BASE
from .simulacion import Simulador, generar_llegadas


def main() -> None:
    ap = argparse.ArgumentParser(description="Simulación de cajas bancarias M/M/1")
    ap.add_argument(
        "--configuracion",
        choices=[config.clave for config in CONFIGURACIONES],
        default="dedicada_2r_1p",
    )
    ap.add_argument("--replica", type=int, default=1)
    ap.add_argument("--semilla", type=int, default=None)
    args = ap.parse_args()

    configuracion = next(
        config for config in CONFIGURACIONES if config.clave == args.configuracion
    )
    semilla = args.semilla if args.semilla is not None else SEMILLA_BASE + args.replica
    simulador = Simulador(configuracion, generar_llegadas(semilla))
    resultados = simulador.ejecutar()

    print(f"Configuración: {configuracion.etiqueta}")
    for clave, valor in resultados.items():
        print(f"  {clave:28} {valor}")


if __name__ == "__main__":
    main()
