# Autor: Jeshua Romero Guadarrama
# Tarea 2: CI/CD para un ETL de Ventas con Python
# Curso: CI/CD para Workflows de Datos con Python

"""
Configuracion de pytest a nivel raiz del repositorio.

Con solo existir, este 'conftest.py' hace que pytest agregue la raiz del
proyecto al 'sys.path'. Asi las pruebas pueden importar el paquete con
'from src.transform import ...' sin importar desde que carpeta se invoque
'pytest' (local, Docker o el agente de Jenkins).
"""
