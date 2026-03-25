FROM python:3.11-slim

WORKDIR /app

# Copy only requirements first (for better caching)
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of backend
COPY backend/ .

# Expose port
EXPOSE 8000

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
