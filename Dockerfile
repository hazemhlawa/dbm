# Use a multi-arch compatible Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for mysql-connector-python, matplotlib, and psutil
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    python3-dev \
    pkg-config \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*


# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]