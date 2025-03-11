# Usa la imagen oficial de Python 3.7
FROM python:3.7

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /usr/local/app

# Copia los archivos necesarios
COPY . .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Comando por defecto
CMD ["/bin/bash"]
