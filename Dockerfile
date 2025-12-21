# Use Python 3.11 slim image  
FROM python:3.11-slim

# Set working directory to backend where server.py is located
WORKDIR /app/backend

# Copy requirements file
COPY backend/requirements.txt ./

# Install Python dependencies (including emergentintegrations from Emergent's private index)
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Copy the entire project
COPY . /app/

# Debug: Show what's in /app/backend where server.py should be
RUN echo "=== Working directory ===" && pwd && echo "=== Files in /app/backend ===" && ls -la /app/backend/ && echo "=== End debug ==="

# Expose the port
EXPOSE 8001

# Start the server directly - no script needed
CMD ["python", "/app/backend/server.py"]
