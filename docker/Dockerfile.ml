# ML Training Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ML code and data
COPY ml/ ./ml/
COPY data/ ./data/

# Set the default command (can be overridden in docker-compose)
CMD ["python", "ml/data_pipeline.py"]