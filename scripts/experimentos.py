"""Genera todas las réplicas y escribe la evidencia en resultados/.

Uso:
    python scripts/experimentos.py
"""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy import stats

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from cajero_banco.metricas import resumen_configuraciones  # noqa: E402
from cajero_banco.parametros import (  # noqa: E402
    CONFIGURACIONES,
    MINUTOS_POR_JORNADA,
    REPLICAS,
    SEMILLA_BASE,
    TIPOS,
    servicio_medio_global,
    tasa_llegada_global,
)
from cajero_banco.simulacion import Simulador, generar_llegadas  # noqa: E402

RESULTADOS = RAIZ / "resultados"
RESULTADOS.mkdir(parents=True, exist_ok=True)

COLUMNAS = (
    "espera_cola_media",
    "tiempo_sistema_media",
    "usuarios_promedio_sistema",
    "usuarios_promedio_retiro",
    "usuarios_promedio_pago",
    "utilizacion_media",
    "utilizacion_max",
    "atendidas_8h",
    "pendientes_8h",
)


def main() -> None:
    filas_replica: list[dict[str, object]] = []
    filas_tipo: list[dict[str, object]] = []
    filas_caja: list[dict[str, object]] = []

    for replica in range(1, REPLICAS + 1):
        semilla = SEMILLA_BASE + replica
        llegadas = generar_llegadas(semilla)

        for configuracion in CONFIGURACIONES:
            simulador = Simulador(configuracion, llegadas)
            metricas = simulador.ejecutar()
            fila: dict[str, object] = {"replica": replica, "semilla": semilla}
            fila.update(metricas)
            filas_replica.append(fila)

            for tipo in TIPOS:
                del_clientes = [cliente for cliente in simulador.clientes if cliente.tipo.codigo == tipo.codigo]
                atendidos = [
                    cliente
                    for cliente in del_clientes
                    if cliente.fin_servicio is not None
                    and cliente.fin_servicio <= MINUTOS_POR_JORNADA
                ]
                filas_tipo.append(
                    {
                        "configuracion": configuracion.clave,
                        "replica": replica,
                        "tipo": tipo.codigo,
                        "accion": tipo.accion,
                        "etiqueta": tipo.etiqueta,
                        "llegadas": len(del_clientes),
                        "atendidas_8h": len(atendidos),
                        "pendientes_8h": len(del_clientes) - len(atendidos),
                    }
                )

            for caja in simulador.cajas:
                filas_caja.append(
                    {
                        "configuracion": configuracion.clave,
                        "replica": replica,
                        "caja": caja.id,
                        "accion": caja.accion or "compartida",
                        "atendidos": caja.atendidos,
                        "tiempo_servicio_medio": (
                            caja.tiempo_servicio / caja.atendidos if caja.atendidos else 0.0
                        ),
                        "utilizacion": caja.area_ocupada / MINUTOS_POR_JORNADA,
                    }
                )

    por_replica = pd.DataFrame(filas_replica)
    por_tipo = pd.DataFrame(filas_tipo)
    por_caja = pd.DataFrame(filas_caja)

    por_replica.to_csv(RESULTADOS / "resumen_por_replica.csv", index=False, float_format="%.6f")
    por_tipo.to_csv(RESULTADOS / "usuarios_por_tipo_replica.csv", index=False, float_format="%.6f")
    por_caja.to_csv(RESULTADOS / "cajeros_por_replica.csv", index=False, float_format="%.6f")

    resumen = resumen_configuraciones(por_replica, COLUMNAS)
    resumen.insert(1, "etiqueta", resumen["configuracion"].map(
        {config.clave: config.etiqueta for config in CONFIGURACIONES}
    ))
    resumen.to_csv(RESULTADOS / "resumen_configuraciones.csv", index=False, float_format="%.6f")

    pendientes_por_config = (
        por_tipo.groupby("configuracion")["pendientes_8h"].sum().sort_values()
    )
    sistema_por_config = por_replica.groupby("configuracion")["usuarios_promedio_sistema"].mean().sort_values()

    resumen_json = {
        "replicas": REPLICAS,
        "semilla_base": SEMILLA_BASE,
        "minutos_por_replica": MINUTOS_POR_JORNADA,
        "tasa_llegada_global_por_minuto": tasa_llegada_global(),
        "servicio_medio_global_minutos": servicio_medio_global(),
        "carga_ofrecida_erlang": tasa_llegada_global() * servicio_medio_global(),
        "configuracion_menos_pendientes": pendientes_por_config.index[0],
        "configuracion_menos_usuarios_en_sistema": sistema_por_config.index[0],
        "criterio_aceptacion_usado": (
            "Se considera aceptable una espera media en cola menor o igual a 5 minutos, "
            "un tiempo medio en sistema menor o igual a 8 minutos y una utilización máxima "
            "menor o igual a 85 %."
        ),
    }
    (RESULTADOS / "resumen.json").write_text(
        json.dumps(resumen_json, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    entorno = "\n".join(
        [
            f"python={platform.python_version()}",
            f"numpy={np.__version__}",
            f"pandas={pd.__version__}",
            f"scipy={scipy.__version__}",
            f"t_critico_95_df{REPLICAS - 1}={stats.t.ppf(0.975, REPLICAS - 1):.6f}",
            f"replicas={REPLICAS}",
            f"semilla_base={SEMILLA_BASE}",
        ]
    )
    (RESULTADOS / "entorno.txt").write_text(entorno + "\n", encoding="utf-8")

    print(resumen.to_string(index=False))
    print(f"\nCSV y resumen escritos en {RESULTADOS}")


if __name__ == "__main__":
    main()
