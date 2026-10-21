# ReconKit backend (also bundles the built frontend so one container serves all).

# --- Stage 1: build the React frontend ---
FROM node:20-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# --- Stage 2: python runtime ---
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# System deps for whois + optional metadata/PDF libs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    whois ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY reconkit/ ./reconkit/
COPY server/ ./server/
RUN pip install --no-cache-dir .

# Bring in the compiled frontend.
COPY --from=web /web/dist ./web/dist

RUN mkdir -p /app/data
EXPOSE 8000
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
