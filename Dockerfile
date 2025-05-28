FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    make \
    pkg-config \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install dependencies
RUN python3 -m pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir --verbose -r requirements.txt || { echo "pip install failed"; exit 1; }

COPY . .

# Create non-root user and fix permissions
RUN useradd -m dbmuser && \
    chown -R dbmuser:dbmuser /app /usr/local/lib/python3.12 /usr/local/bin
USER dbmuser

EXPOSE 5000

CMD ["gunicorn", "--worker-class=eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "app:app"]