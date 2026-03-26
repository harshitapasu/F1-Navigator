# Multi-stage build: Frontend + Backend on Railway

# ============================================================================
# Stage 1: Build Frontend (Next.js)
# ============================================================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install dependencies
RUN npm install -g pnpm && pnpm install

# Copy rest of frontend source
COPY frontend/ .

# Build Next.js
RUN pnpm build

# ============================================================================
# Stage 2: Runtime - Backend + Frontend Assets
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/.next ./static/.next
COPY --from=frontend-builder /app/frontend/public ./static/public

# Expose port
EXPOSE 8000

# Start backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
