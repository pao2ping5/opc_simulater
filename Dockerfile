# ── Stage 1: build React SPA ─────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /build
# Copy lockfile + package.json first for layer caching
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy sources and build
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python runtime ──────────────────────────────────────────
FROM python:3.12-slim

# Run as non-root for defense-in-depth
RUN useradd --create-home --uid 1000 opc
WORKDIR /app

# Install Python deps first for layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY --chown=opc:opc . /app/

# Copy built frontend from stage 1
COPY --chown=opc:opc --from=frontend-builder /build/dist /app/frontend/dist

# Default point table is committed at opc_list_test.xlsx; allow override
ENV OPC_POINT_TABLE=/app/opc_list_test.xlsx \
    OPC_WEB_HOST=0.0.0.0 \
    OPC_WEB_PORT=18480 \
    PYTHONUNBUFFERED=1

USER opc

EXPOSE 18480

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:18480/api/health', timeout=3).status==200 else sys.exit(1)"

CMD ["python", "web_server.py"]
