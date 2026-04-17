# AI Use Impact Tracker — ETL container
# Runs on Railway (Phase 1) and AWS ECS/Fargate (Phase 2).
#
# Invocation: the container runs main.py as CLI. Configure via env vars
# or arguments. For scheduled execution wire to EventBridge (AWS) or
# Railway's cron service.

FROM python:3.11-slim

WORKDIR /app

# System deps for pyarrow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command — override at runtime with real paths
CMD ["python", "main.py", \
     "--source", "csv", \
     "--path", "/data/gmp_latest.csv", \
     "--out",  "/data/output"]
