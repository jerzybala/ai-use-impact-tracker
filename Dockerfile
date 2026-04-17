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

# Railway injects PORT at runtime; default to 8080 for local dev
ENV PORT=8080

# Use ENTRYPOINT with shell form so $PORT expands at runtime
ENTRYPOINT ["sh", "-c", "exec gunicorn app:app --bind 0.0.0.0:${PORT} --timeout 300 --workers 1 --threads 2 --log-level info"]
