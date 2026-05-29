FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .
COPY backend ./backend
COPY init_db.py ./
COPY entrypoint.sh ./
COPY data/seed ./data/seed
COPY --from=frontend /app/frontend/dist ./frontend/dist
RUN chmod +x /app/entrypoint.sh && mkdir -p /app/runtime

ENV DATABASE_URL=sqlite:////app/runtime/job_title_archaeology.db \
    PORT=8080
EXPOSE 8080
CMD ["/app/entrypoint.sh"]
