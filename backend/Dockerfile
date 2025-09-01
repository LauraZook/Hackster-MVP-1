# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server.py file explicitly
COPY server.py ./

# Copy other necessary files
COPY .env ./
COPY *.py ./

# Debug: List files and show current directory
RUN pwd && ls -la

# Expose the port
EXPOSE 8001

# Health check removed for now to simplify

# Start the application
CMD ["python", "server.py"]