# Usamos a imagem oficial do Python em versão slim (muito mais leve)
FROM python:3.10-slim

# Instala Chromium, ChromeDriver e dependências necessárias para rodar em headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Cria um usuário não-root para rodar a aplicação de forma segura
RUN groupadd -r scraper && useradd -r -g scraper -G audio,video scraper \
    && mkdir -p /home/scraper/Downloads \
    && chown -R scraper:scraper /home/scraper

WORKDIR /app

# Copia as dependências primeiro para aproveitar o cache de camadas do Docker
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --break-system-packages -r requirements.txt

# Copia o restante do código com as permissões corretas
COPY --chown=scraper:scraper . .

# Altera para o usuário não-root
USER scraper

# Garante que o Chrome rode sempre em headless dentro do container
ENV HEADLESS=true

# Comando para iniciar o worker consumidor
CMD ["python", "worker.py"]
