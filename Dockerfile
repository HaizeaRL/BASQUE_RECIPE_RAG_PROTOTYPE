# Usa la imagen oficial de Python 3.7
FROM python:3.7

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /usr/local/app

# Copia los archivos necesarios
COPY requirements.txt .
COPY config.yaml .
COPY src/ /usr/local/app/src/
COPY modules/ /usr/local/app/modules/
COPY data/ /usr/local/app/data/

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Ejecutar el script desde src
RUN python /usr/local/app/src/download_spacy_model.py

# Comando por defecto
CMD ["/bin/bash"]
