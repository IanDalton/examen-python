# syntax=docker/dockerfile:1

##########
# Frontend build stage
##########
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

##########
# Backend runtime image
##########
FROM python:3.11-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend ./backend
COPY tests ./tests
COPY bookbyte.py ./bookbyte.py
COPY AUTOGRADER.md ./AUTOGRADER.md
COPY README ./README
COPY --from=frontend-builder /app/frontend/out ./static-frontend
RUN mkdir -p /app/submissions && groupadd -r app && useradd -r -g app app && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

##########
# Frontend runtime image
##########
FROM nginx:alpine AS frontend
COPY --from=frontend-builder /app/frontend/out /usr/share/nginx/html
