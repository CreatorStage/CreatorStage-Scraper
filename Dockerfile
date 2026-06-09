# Usamos a imagem oficial do Python em versão slim (muito mais leve)
FROM python:3.10-slim

# Instala Chromium, ChromeDriver e dependências necessárias para rodar em headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia as dependências primeiro para aproveitar o cache de camadas do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copia os arquivos do projeto (exclui o .deb e outros pesados com .dockerignore)
COPY . .

# Expõe a porta que o FastAPI vai rodar
EXPOSE 8000

# Garante que o Chrome rode sempre em headless dentro do container
ENV HEADLESS=true

# Comando para iniciar o servidor
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
