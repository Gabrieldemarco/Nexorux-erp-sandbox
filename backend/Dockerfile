FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    gosu \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/scripts/entrypoint.sh \
    && adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/storage \
    && chown -R appuser:appuser /app

# Entrypoint starts as root to fix volume perms, then drops to appuser via gosu
USER root

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV DEBUG=false

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD []
