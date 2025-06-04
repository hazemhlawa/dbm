# Use Python 3.11 slim base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmariadb-dev-compat \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Initialize SQLite database
RUN python -c "from db_utils import init_db; init_db()"

# Expose Flask port
EXPOSE 5000

# Command to run the app
CMD ["python", "app.py"]