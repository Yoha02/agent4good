FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY bigquery_worker.py .

# Start worker (run as root is fine for Cloud Run)
CMD ["python", "-u", "bigquery_worker.py"]
