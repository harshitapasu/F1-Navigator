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

# Install Node.js for serving frontend (optional, or use Python)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/.next ./static/.next
COPY --from=frontend-builder /app/frontend/public ./static/public

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start backend (which will serve frontend via static files or reverse proxy)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
