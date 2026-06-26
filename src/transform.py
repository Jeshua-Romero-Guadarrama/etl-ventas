# Autor: Jeshua Romero Guadarrama
# Tarea 2: CI/CD para un ETL de Ventas con Python
# Curso: CI/CD para Workflows de Datos con Python

"""
Logica de transformacion del ETL de ventas.

Este modulo concentra las dos etapas centrales del pipeline:

    1. Limpieza   -> 'limpiar_ventas': normaliza nombres de columnas y fechas,
                     elimina nulos y duplicados, y descarta los montos invalidos.
    2. Agregacion -> 'total_por_producto': resume las ventas totales por producto.

Separo la limpieza de la agregacion a proposito: asi cada funcion hace una sola
cosa, se puede probar por separado con pytest y el orquestador
('run_pipeline.py') solo tiene que encadenarlas. Tambien dejo una pequena ayuda
('normalizar_fecha') por si el origen manda las fechas con formatos mezclados.
"""

import pandas as pd

# Columnas que el pipeline necesita para funcionar (ya normalizadas a minusculas).
# Las dejo como constante para validar la entrada en un solo lugar.
COLUMNAS_REQUERIDAS = ["producto", "monto"]


def normalizar_fecha(cadena_fecha):
    """
    Normaliza una cadena de fecha al estandar ISO (YYYY-MM-DD).

    Recorto los espacios sobrantes y cambio los separadores alternativos
    (diagonales y puntos) por guiones. Los sistemas transaccionales suelen
    mandar las fechas con formatos mezclados, asi que conviene dejarlas todas
    iguales antes de cargarlas.

    Parametros:
        cadena_fecha: el texto con la fecha original a normalizar.

    Retorna:
        La cadena de fecha ya limpia, o None si la entrada esta vacia o es nula.
    """
    # Si la cadena llega vacia o como None (NaN de pandas), no hay nada que hacer
    if cadena_fecha is None or pd.isna(cadena_fecha):
        return None

    # Eliminamos los espacios corruptos del inicio y del final
    cadena_limpia = str(cadena_fecha).strip()

    # Una cadena que solo tenia espacios queda vacia: la tratamos como nula
    if not cadena_limpia:
        return None

    # Unificamos los separadores: las diagonales y los puntos pasan a guiones ISO
    cadena_limpia = cadena_limpia.replace("/", "-").replace(".", "-")

    return cadena_limpia


def limpiar_ventas(df):
    """
    Normaliza columnas, elimina nulos, duplicados y montos invalidos.

    Pasos que aplico, en orden:
        - Dejo los nombres de columna en minusculas y sin espacios, que es por
          donde mas suele colarse la suciedad del origen.
        - Reviso que esten las columnas que el pipeline necesita.
        - Si viene una columna de fecha, la paso a formato ISO.
        - Recorto los espacios sobrantes del nombre del producto.
        - Tiro las filas sin producto o sin monto.
        - Quito los registros duplicados exactos.
        - Convierto el monto a numero y me quedo solo con los positivos, porque
          una venta de cero o negativa no tiene sentido de negocio.

    Parametros:
        df: DataFrame de pandas con las ventas crudas leidas del CSV.

    Retorna:
        Un DataFrame nuevo, ya limpio y con el indice reiniciado.

    Lanza:
        ValueError si falta alguna de las columnas requeridas.
    """
    # Trabajamos sobre una copia para no tocar el DataFrame que nos pasaron
    df = df.copy()

    # Dejamos los nombres de columna sin espacios y en minusculas
    df.columns = [c.strip().lower() for c in df.columns]

    # Si falta una columna clave, preferimos fallar aqui mismo en lugar de
    # arrastrar el error mas adelante.
    columnas_faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas requeridas en el dataset: "
            + ", ".join(columnas_faltantes)
        )

    # Si el origen trae una columna de fecha, la dejamos en formato ISO
    if "fecha" in df.columns:
        df["fecha"] = df["fecha"].apply(normalizar_fecha)

    # Quitamos los espacios sobrantes del nombre del producto
    df["producto"] = df["producto"].astype("string").str.strip()

    # Fuera las filas que no sirven: sin producto o sin monto
    df = df.dropna(subset=["producto", "monto"])

    # Quitamos las ventas duplicadas (las que llegaron cargadas dos veces)
    df = df.drop_duplicates()

    # Pasamos el monto a numero; lo que no se pueda convertir queda como nulo
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce")
    df = df.dropna(subset=["monto"])
    df["monto"] = df["monto"].astype(float)

    # Nos quedamos solo con los montos positivos y reiniciamos el indice
    df = df[df["monto"] > 0].reset_index(drop=True)

    return df


def total_por_producto(df):
    """
    Resume las ventas totales por producto.

    Agrupa por 'producto' y suma el 'monto' de todas sus lineas. Devuelvo el
    resultado ordenado de mayor a menor total, que es como normalmente uno
    quiere leer un reporte de ventas.

    Parametros:
        df: DataFrame de ventas YA limpio (salida de 'limpiar_ventas').

    Retorna:
        Un DataFrame con dos columnas, 'producto' y 'total', ordenado de mayor a
        menor total.
    """
    resumen = (
        df.groupby("producto", as_index=False)["monto"]
        .sum()
        .rename(columns={"monto": "total"})
        .sort_values("total", ascending=False)
        .reset_index(drop=True)
    )

    return resumen
