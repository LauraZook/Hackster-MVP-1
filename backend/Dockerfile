# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy everything from backend directory
COPY backend/ ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Debug: List all files to see what's actually copied
RUN echo "=== Current directory ===" && pwd && echo "=== Files in /app ===" && ls -la && echo "=== End debug ==="

# Expose the port
EXPOSE 8001

# Start the application
CMD ["python", "server.py"]