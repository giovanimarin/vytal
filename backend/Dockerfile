FROM python:3.12-slim

WORKDIR /app

# Dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Código da aplicação
COPY app/ ./app/
COPY config.yaml .

# Usuário não-root
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Diretório para o SQLite em modo local (montado como volume em dev)
RUN mkdir -p /app/data

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
