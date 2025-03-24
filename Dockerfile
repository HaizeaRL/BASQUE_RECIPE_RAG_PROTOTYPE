# Usa la imagen oficial de Python 3.8
FROM python:3.8

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /usr/local/app

# Instala dependencias del sistema (curl,supervisor, etc.)
RUN apt-get update && apt-get install -y curl supervisor

# Instala Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Agrega Ollama al PATH
ENV PATH="/root/.ollama/bin:${PATH}"

# Copia los archivos de la app al contenedor
COPY . /usr/local/app

# Asegura que el script tenga permisos de ejecución
RUN chmod +x /usr/local/app/run_ollama.sh

# Instala las dependencias de Python
RUN pip install --no-cache-dir jupyter
RUN pip install --no-cache-dir -r requirements.txt

# Copia el archivo de configuración de supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expone el puerto de Ollama (11434) y el de Jupyter (8888)
EXPOSE 11434
EXPOSE 8888

# Set the default command to start a bash shell
#CMD ["/bin/bash"]

# Ejecuta supervisord para manejar ambos procesos
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
