FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (build-essential for some pip packages)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt
# Install uvicorn and celery explicitly if not in requirements (it should be)
RUN pip install uvicorn celery redis

COPY . ./ml

# Set python path
ENV PYTHONPATH=/app

# Default command (overridden in docker-compose)
CMD ["uvicorn", "ml.main:app", "--host", "0.0.0.0", "--port", "8000"]
