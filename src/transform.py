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
cosa, es facil de probar de forma aislada con pytest y el orquestador
('run_pipeline.py') simplemente las encadena. La normalizacion de fechas la
reutilizo de la Tarea 1, pero ahora trabajando sobre un DataFrame de pandas en
lugar de una sola cadena.
"""

import pandas as pd

# Columnas que el pipeline necesita para funcionar (ya normalizadas a minusculas).
# Las dejo como constante para validar la entrada en un solo lugar.
COLUMNAS_REQUERIDAS = ["producto", "monto"]


def normalizar_fecha(cadena_fecha):
    """
    Normaliza una cadena de fecha al estandar ISO (YYYY-MM-DD).

    Reutilizo el criterio de la Tarea 1: recorto los espacios en blanco
    corruptos y unifico los separadores alternativos (diagonales y puntos)
    convirtiendolos en guiones. Los sistemas transaccionales mandan las fechas
    con formatos mezclados y conviene homogeneizarlas antes de cargarlas.

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
        - Homogeneizo los nombres de columna: sin espacios y en minusculas, que
          es de donde mas suciedad llega desde el origen.
        - Verifico que esten las columnas que el pipeline necesita.
        - Normalizo la fecha al formato ISO con 'normalizar_fecha' (si viene).
        - Recorto los espacios sobrantes en el texto de 'producto'.
        - Descarto las filas sin 'producto' o sin 'monto'.
        - Elimino los registros duplicados exactos.
        - Convierto 'monto' a numero y me quedo solo con los montos positivos
          (una venta de cero o negativa no tiene sentido de negocio).

    Parametros:
        df: DataFrame de pandas con las ventas crudas leidas del CSV.

    Retorna:
        Un DataFrame nuevo, ya limpio y con el indice reiniciado.

    Lanza:
        ValueError si falta alguna de las columnas requeridas.
    """
    # Trabajamos sobre una copia para no mutar el DataFrame original del autor
    df = df.copy()

    # Normalizamos los nombres de columna: recorte de espacios y a minusculas
    df.columns = [c.strip().lower() for c in df.columns]

    # Validamos la estructura: si falta una columna clave, fallamos de inmediato
    # en lugar de arrastrar el error rio abajo.
    columnas_faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas requeridas en el dataset: "
            + ", ".join(columnas_faltantes)
        )

    # Si el origen trae fecha, la normalizamos al formato ISO de la Tarea 1
    if "fecha" in df.columns:
        df["fecha"] = df["fecha"].apply(normalizar_fecha)

    # Recortamos los espacios corruptos del texto del producto
    df["producto"] = df["producto"].astype("string").str.strip()

    # Quitamos las filas que no sirven: sin producto o sin monto
    df = df.dropna(subset=["producto", "monto"])

    # Eliminamos registros duplicados exactos (mismas ventas cargadas dos veces)
    df = df.drop_duplicates()

    # Forzamos el monto a numero; lo que no se pueda convertir queda como nulo
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce")
    df = df.dropna(subset=["monto"])
    df["monto"] = df["monto"].astype(float)

    # Nos quedamos solo con los montos positivos y reiniciamos el indice
    df = df[df["monto"] > 0].reset_index(drop=True)

    return df


def total_por_producto(df):
    """
    Resume las ventas totales por producto.

    Agrupa por 'producto' y suma el 'monto' de todas sus lineas. El resultado
    queda ordenado de mayor a menor total, que es como normalmente se quiere
    leer un reporte de ventas.

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
