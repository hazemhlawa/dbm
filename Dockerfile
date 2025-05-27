FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies required for matplotlib and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    make \
    pkg-config \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install dependencies as root
RUN python3 -m pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -v -r requirements.txt

COPY . .

# Create non-root user and fix permissions
RUN useradd -m dbmuser && \
    chown -R dbmuser:dbmuser /app /usr/local/lib/python3.12 /usr/local/bin
USER dbmuser

EXPOSE 5000

CMD ["python3", "app.py"]