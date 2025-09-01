# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application files
COPY backend/server.py ./
COPY backend/.env ./

# Debug: List files and show current directory
RUN pwd && ls -la

# Expose the port
EXPOSE 8001

# Start the application
CMD ["python", "server.py"]