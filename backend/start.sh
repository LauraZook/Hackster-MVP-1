#!/bin/bash
echo "=== Debugging container startup ==="
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la
echo "Files in /app:"
ls -la /app/ 2>/dev/null || echo "/app directory not found"
echo "Looking for server.py:"
find . -name "server.py" -type f
echo "=== Starting Python server ==="
exec python server.py