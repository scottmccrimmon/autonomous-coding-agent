
FROM python:3.10-slim

# Set working directory for the app
WORKDIR /app

# Install essential system dependencies for Torch, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 \
        && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code and configs into the container
COPY .. .

# Expose no ports, as this is a headless job container

# Default command: run the training script
CMD ["python", "src/train.py"]