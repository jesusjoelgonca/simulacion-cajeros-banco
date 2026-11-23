# Simulación de cajas bancarias M/M/1

Trabajo de la actividad didáctica 2 del módulo 3 de Simulación. El caso es el Banco de Colombia: hay tres cajas y dos tipos de trámite, retiros y pagos. Con los datos del enunciado corrí 30 réplicas de una jornada de ocho horas y comparé cuatro formas de repartir las cajas, incluida la opción de abrir una cuarta.

La conclusión fue quedarse con dos cajas para retiros y una para pagos. Esa distribución deja la espera media en cola en 2,45 minutos y la caja más ocupada en 60,8 %. La cuarta caja baja la espera a 0,39 minutos, pero deja la utilización media en 32 % y no se justifica.

## Cómo ejecutarlo

Necesita Python 3.11 o superior. Desde esta carpeta:

```bash
python -m pip install -e ".[figuras,pruebas]"
python -m pytest -q
python scripts/experimentos.py
python scripts/figuras.py
```

`scripts/experimentos.py` usa las semillas fijas de `src/cajero_banco/parametros.py` y deja los resultados en `resultados/`. Las figuras se generan después con `scripts/figuras.py`. Si solo quiere ver el resumen, está en `resultados/resumen.json`.

## Qué hay en el repositorio

- `src/cajero_banco/`: parámetros, generación de llegadas, simulador de eventos discretos y cálculo de estadísticas.
- `scripts/`: ejecución de los experimentos y dibujo de las figuras.
- `tests/`: 15 pruebas de parámetros, simulación y métricas.
- `resultados/`: CSV de las 30 réplicas, resumen por configuración y las cuatro figuras.
- `docs/Gonzalez_Jesus_Cajeros.pdf`: informe final en formato APA.

El material de construcción del documento y de la presentación quedó fuera del repositorio porque es trabajo local.

## Evidencias

- Informe: `docs/Gonzalez_Jesus_Cajeros.pdf`
- Video de sustentación: https://drive.google.com/file/d/1-l0enhrBz-lpPKI1A-9E2przMrPV1vd4/view?usp=sharing
