# syntax=docker/dockerfile:1
# Production image: the React build is served by Django (WhiteNoise) from the
# same origin as the API, behind gunicorn on port 8000. Multi-arch bases
# (linux/amd64 and linux/arm64). Used by compose.demo.yml.

# --- Stage 1: build the frontend ---------------------------------------------
FROM node:22-alpine AS frontend
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
# No VITE_API_URL: the app calls /api on its own origin.
RUN npm run build

# --- Stage 2: Django + gunicorn ----------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FRONTEND_DIST=/app/frontend_dist

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-compile -r requirements.txt \
 && python -m compileall -q /usr/local/lib/python3.12/site-packages

COPY backend/ ./
COPY --from=frontend /src/dist /app/frontend_dist

# Static files are collected at build time (the root filesystem is read-only
# at run time). The key below exists only for this build step.
RUN SECRET_KEY=collectstatic-build-step-only python manage.py collectstatic --noinput -v0 \
 && python -m compileall -q /app \
 && chmod 0555 /app/docker-entrypoint.sh

USER app:app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health/', timeout=4).status == 200 else 1)"]

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", "--threads", "4", "--worker-class", "gthread", \
     "--worker-tmp-dir", "/dev/shm", \
     "--timeout", "30", "--graceful-timeout", "20", \
     "--max-requests", "1000", "--max-requests-jitter", "100", \
     "--access-logfile", "-", "--error-logfile", "-"]
