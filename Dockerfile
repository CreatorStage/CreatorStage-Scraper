# Usamos a imagem oficial do Selenium com Chrome já instalado e configurado
FROM selenium/standalone-chrome:latest

# Troca para root para instalar Python e dependências
USER root

# Instala Python, pip e dependências de sistema
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto (exclui o .deb pesado com .dockerignore)
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

# Expõe a porta que o FastAPI vai rodar
EXPOSE 8000

# Garante que o Chrome rode sempre em headless dentro do container
ENV HEADLESS=true

# Comando para iniciar o servidor
CMD ["python3", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
