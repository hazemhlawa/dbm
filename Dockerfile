# Start from a clean slim image
FROM python:3.12-slim

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --upgrade pip

# Copy requirements and install them
COPY requirements.txt .

# Force pip to fail if dependency conflict exists
RUN pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt

# Copy application
COPY . .

# Create user
RUN useradd -m dbmuser && chown -R dbmuser:dbmuser /app
USER dbmuser

EXPOSE 5000

CMD ["python", "app.py"]
