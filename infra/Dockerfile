FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements if exists
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port (if your app runs on a specific port, e.g., 8000)
EXPOSE 8000

# Set environment variables if needed
ENV PYTHONUNBUFFERED=1

# Default command to run the app
CMD ["python", "main.py"]
