# Autor: Jeshua Romero Guadarrama
# Tarea 2: CI/CD para un ETL de Ventas con Python
# Curso: CI/CD para Workflows de Datos con Python

# Imagen base ligera y reproducible: misma version de Python en local y en CI.
FROM python:3.12-slim

# Buenas practicas para Python dentro de contenedores:
#   - no generar archivos .pyc en disco
#   - no almacenar en buffer la salida estandar (logs en tiempo real)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos primero las dependencias para aprovechar la cache de capas:
# si el codigo cambia pero las dependencias no, Docker no reinstala todo.
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copiamos el resto del proyecto (codigo, datos y pruebas)
COPY . .

# Por defecto, al levantar el contenedor se ejecuta el ETL completo.
# Para correr las pruebas basta con sobreescribir el comando:
#   docker run --rm etl-ventas pytest -v
CMD ["python", "run_pipeline.py"]
