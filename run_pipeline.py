# Autor: Jeshua Romero Guadarrama
# Tarea 2: CI/CD para un ETL de Ventas con Python
# Curso: CI/CD para Workflows de Datos con Python

"""
Orquestador del ETL de ventas (interfaz de linea de comandos).

Encadena las tres etapas clasicas de un ETL:

    Extract  -> leemos el CSV crudo de 'data/ventas.csv'.
    Transform-> limpiamos y agregamos usando 'src.transform'.
    Load     -> escribimos dos archivos en 'output/':
                  - el dataset YA limpio (ruta de '--output')
                  - el resumen por producto (mismo nombre con prefijo 'resumen_')

Lo dejo como CLI para poder correrlo igual a mano, dentro de Docker o desde un
agente de Jenkins, siempre con el mismo comando. La logica de negocio NO vive
aqui: este archivo solo coordina las etapas e imprime un pequeno reporte.

Dejo '--input' y '--output' como opcionales, con valores por defecto: asi el
contenedor puede correr 'python run_pipeline.py' sin argumentos, pero tambien
puedo apuntar a otros archivos cuando haga falta.

Ejemplos de uso:

    python run_pipeline.py
    python run_pipeline.py --input data/ventas.csv --output output/ventas_limpias.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from src.transform import limpiar_ventas, total_por_producto

# Rutas por defecto, relativas a la raiz del repositorio
ENTRADA_POR_DEFECTO = "data/ventas.csv"
SALIDA_POR_DEFECTO = "output/ventas_limpias.csv"


def construir_parser():
    """
    Arma el parser de argumentos de la CLI.

    Dejo las rutas como parametros opcionales para poder reutilizar el mismo
    pipeline con otros archivos sin tocar el codigo (util en CI o en Docker).
    """
    parser = argparse.ArgumentParser(description="ETL de ventas")
    parser.add_argument(
        "--input",
        default=ENTRADA_POR_DEFECTO,
        help=f"Ruta del CSV crudo de entrada (por defecto: {ENTRADA_POR_DEFECTO}).",
    )
    parser.add_argument(
        "--output",
        default=SALIDA_POR_DEFECTO,
        help=(
            "Ruta del CSV con los datos limpios (por defecto: "
            f"{SALIDA_POR_DEFECTO}). El resumen por producto se guarda junto a "
            "este archivo con el prefijo 'resumen_'."
        ),
    )
    return parser


def ejecutar_pipeline(ruta_entrada, ruta_salida):
    """
    Ejecuta el ETL completo de principio a fin.

    Parametros:
        ruta_entrada: ruta al CSV crudo de ventas.
        ruta_salida : ruta donde se escribira el CSV con los datos ya limpios.

    Retorna:
        Una tupla '(df_limpio, resumen)' con el DataFrame limpio y el resumen
        por producto que se escribieron en disco.

    Lanza:
        FileNotFoundError si el archivo de entrada no existe.
    """
    ruta_entrada = Path(ruta_entrada)
    ruta_salida = Path(ruta_salida)

    # Extract: validamos que exista el archivo antes de intentar leerlo
    if not ruta_entrada.exists():
        raise FileNotFoundError(
            f"No se encontro el archivo de entrada: {ruta_entrada}"
        )

    print(f"[ETL] Leyendo datos crudos desde: {ruta_entrada}")
    df_crudo = pd.read_csv(ruta_entrada)
    print(f"[ETL] Registros crudos leidos: {len(df_crudo)}")

    # Transform: limpieza y luego agregacion
    df_limpio = limpiar_ventas(df_crudo)
    resumen = total_por_producto(df_limpio)

    # Load: nos aseguramos de que exista la carpeta de salida
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    # Guardamos el dataset limpio y, junto a el, el resumen con prefijo 'resumen_'
    ruta_resumen = ruta_salida.with_name("resumen_" + ruta_salida.name)
    df_limpio.to_csv(ruta_salida, index=False)
    resumen.to_csv(ruta_resumen, index=False)

    print(f"[ETL] Datos limpios escritos en:   {ruta_salida}")
    print(f"[ETL] Resumen por producto en:     {ruta_resumen}")
    print(f"[ETL] Filas validas: {len(df_limpio)} | Productos: {len(resumen)}")

    # Reporte rapido en consola para verificar el resultado de un vistazo
    print("\n[ETL] Resumen de ventas por producto:")
    print(resumen.to_string(index=False))

    return df_limpio, resumen


def main(argv=None):
    """
    Punto de entrada de la CLI.

    Separo 'main' de 'ejecutar_pipeline' para poder probar la logica sin pasar
    por el manejo de argumentos ni por los codigos de salida del proceso.
    """
    parser = construir_parser()
    args = parser.parse_args(argv)

    try:
        ejecutar_pipeline(args.input, args.output)
    except FileNotFoundError as error:
        # Error esperado y claro: devolvemos codigo 1 para que CI lo detecte
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    print("\n[ETL] Pipeline finalizado correctamente.")
    return 0


if __name__ == "__main__":
    # El codigo de salida permite que Jenkins o Docker sepan si el ETL fallo
    sys.exit(main())
