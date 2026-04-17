FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Persistent volume for uploaded data & baked dashboards
ENV DATA_DIR=/app/data
RUN mkdir -p /app/data

# Railway sets PORT env var automatically
ENV PORT=8080
EXPOSE 8080

# Railway injects $PORT at runtime — must use shell form so it expands
CMD gunicorn app:app --bind "0.0.0.0:$PORT" --timeout 300 --workers 2 --threads 4
