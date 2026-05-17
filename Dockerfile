FROM python:3.9-slim

# Instalar dependencias del sistema necesarias para geoespacial y compilación
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    proj-bin \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Variables de entorno para GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Crear directorio de trabajo
WORKDIR /app

# Copiar e instalar requisitos de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando de ejecución
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
