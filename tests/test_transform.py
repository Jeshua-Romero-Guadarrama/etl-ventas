# Autor: Jeshua Romero Guadarrama
# Tarea 2: CI/CD para un ETL de Ventas con Python
# Curso: CI/CD para Workflows de Datos con Python

"""
Pruebas unitarias de la logica de transformacion del ETL.

Cubro las tres piezas del modulo 'src.transform':

    - 'limpiar_ventas'     : eliminacion de nulos, duplicados y montos invalidos.
    - 'total_por_producto' : resumen del total de ventas por producto.
    - 'normalizar_fecha'   : separadores, espacios y entradas nulas.

La idea es tener pruebas pequenas, con un solo motivo de fallo cada una, para
que cuando alguna se rompa quede claro de inmediato por que.
"""

import pandas as pd
import pytest

from src.transform import (
    limpiar_ventas,
    normalizar_fecha,
    total_por_producto,
)


# ---------------------------------------------------------------------------
# Apoyo: un DataFrame de demostracion con los defectos tipicos del origen
# ---------------------------------------------------------------------------

def _df_demo():
    """
    DataFrame minimo para ejercitar la limpieza:
        - dos filas iguales (A, 10.0) -> una es duplicada
        - una fila sin producto (None) -> nula
        - una fila con monto negativo (B, -3.0) -> invalida
    Tras limpiar, solo debe sobrevivir la fila (A, 10.0).
    """
    return pd.DataFrame(
        {
            "Producto": ["A", "A", None, "B"],
            "Monto": [10.0, 10.0, 5.0, -3.0],
        }
    )


# ---------------------------------------------------------------------------
# Pruebas de limpiar_ventas
# ---------------------------------------------------------------------------

def test_elimina_nulos_duplicados_y_negativos():
    out = limpiar_ventas(_df_demo())
    assert out["producto"].notna().all()
    assert (out["monto"] > 0).all()
    assert len(out) == 1  # solo sobrevive (A, 10.0)


def test_limpiar_ventas_normaliza_nombres_de_columna():
    # Los encabezados con mayusculas y espacios deben quedar en minusculas
    df = pd.DataFrame({" Producto ": ["A"], "MONTO": [10.0]})
    out = limpiar_ventas(df)
    assert list(out.columns) == ["producto", "monto"]


def test_limpiar_ventas_falla_si_faltan_columnas():
    # Si el dataset no trae las columnas esperadas, debe fallar de inmediato
    df_incompleto = pd.DataFrame({"producto": ["A"]})
    with pytest.raises(ValueError):
        limpiar_ventas(df_incompleto)


# ---------------------------------------------------------------------------
# Pruebas de total_por_producto
# ---------------------------------------------------------------------------

def test_total_por_producto():
    tot = total_por_producto(limpiar_ventas(_df_demo()))
    # Tras limpiar solo queda el producto A, con un total de 10.0
    assert list(tot.columns) == ["producto", "total"]
    assert len(tot) == 1
    assert tot.loc[0, "producto"] == "A"
    assert tot.loc[0, "total"] == 10.0


def test_total_por_producto_suma_varias_lineas():
    # Dos lineas de A (10 + 20 = 30) y una de B (100): B debe ir primero
    df = pd.DataFrame(
        {
            "producto": ["A", "A", "B"],
            "monto": [10.0, 20.0, 100.0],
        }
    )
    tot = total_por_producto(df)
    assert tot.loc[0, "producto"] == "B"
    assert tot.loc[0, "total"] == 100.0
    total_a = tot.loc[tot["producto"] == "A", "total"].iloc[0]
    assert total_a == 30.0


# ---------------------------------------------------------------------------
# Pruebas de normalizar_fecha
# ---------------------------------------------------------------------------

def test_normalizar_fecha_cambia_diagonales_por_guiones():
    assert normalizar_fecha("2024/01/05") == "2024-01-05"


def test_normalizar_fecha_cambia_puntos_por_guiones():
    assert normalizar_fecha("2024.01.05") == "2024-01-05"


def test_normalizar_fecha_recorta_espacios():
    assert normalizar_fecha("  2024-01-05  ") == "2024-01-05"


def test_normalizar_fecha_entrada_nula_o_vacia_regresa_none():
    assert normalizar_fecha(None) is None
    assert normalizar_fecha("") is None
    assert normalizar_fecha("   ") is None
