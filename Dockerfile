FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies (Playwright will pull the rest via --with-deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright + Chromium + OS deps needed by Chromium
RUN playwright install --with-deps chromium

COPY . .

# Helps platforms/router auto-detect the container's listening port.
# Railway will still set $PORT; we default to 8080 when not provided.
EXPOSE 8080

# Railway provides $PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
