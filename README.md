# ETL de Ventas

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Micro-proyecto de la **Tarea 2** del curso **CI/CD para Workflows de Datos con Python**.

**Autor:** Jeshua Romero Guadarrama

## Descripcion

Pipeline ETL que toma un archivo crudo de ventas (`data/ventas.csv`), lo limpia
y genera un resumen del total vendido por producto. Es la continuacion natural
de la Tarea 1: ahi normalizaba fechas sueltas y aqui aplico la misma idea de
limpieza, pero ya sobre un dataset completo con pandas y dentro de un flujo de
CI/CD (pruebas, Docker y Jenkins).

El ETL sigue las tres etapas clasicas:

- **Extract**: lee el CSV crudo de `data/ventas.csv`.
- **Transform**: limpia los datos y los agrega (`src/transform.py`).
- **Load**: escribe en `output/` el dataset limpio (`ventas_limpias.csv`) y el
  resumen por producto (`resumen_ventas_limpias.csv`).

## Estructura del proyecto

```
etl-ventas/
    Jenkinsfile             # pipeline as code (raiz del repo)
    Dockerfile              # entorno reproducible para CI y ejecucion
    requirements.txt        # pandas (runtime)
    requirements-dev.txt    # + pytest (solo CI/desarrollo)
    .gitignore              # .venv/, output/, __pycache__/
    data/
        ventas.csv          # dataset crudo de entrada
    src/
        __init__.py
        transform.py        # logica de limpieza y agregacion
    tests/
        test_transform.py   # pruebas unitarias
    run_pipeline.py         # orquestador del ETL (CLI)
```

## Logica de transformacion

En `src/transform.py`:

- `limpiar_ventas(df)`: normaliza los nombres de columna, normaliza la fecha al
  formato ISO, elimina nulos y duplicados, y descarta los montos invalidos
  (cero o negativos).
- `total_por_producto(df)`: agrupa por producto y suma el monto, devolviendo el
  total ordenado de mayor a menor.

## Como ejecutar las pruebas (local)

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v
```

## Como ejecutar el ETL (local)

```bash
pip install -r requirements.txt
python run_pipeline.py
# o apuntando a otros archivos:
python run_pipeline.py --input data/ventas.csv --output output/ventas_limpias.csv
```

Se generan dos archivos en `output/`: el dataset limpio (`ventas_limpias.csv`) y
el resumen por producto (`resumen_ventas_limpias.csv`), que ademas se imprime en
consola.

## Como ejecutar con Docker

```bash
# Construir la imagen
docker build -t etl-ventas .

# Ejecutar el ETL completo
docker run --rm etl-ventas

# Correr unicamente las pruebas
docker run --rm etl-ventas pytest -v
```

## Integracion continua (Jenkins)

El `Jenkinsfile` describe el pipeline as code. Construye la imagen a partir del
`Dockerfile` y, dentro de ese contenedor, ejecuta las etapas de verificacion de
entorno, pruebas, ejecucion del ETL y archivado del resumen como artefacto.
