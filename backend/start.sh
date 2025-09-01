#!/bin/bash
echo "Starting Hackster.ai Backend..."
uvicorn server:app --host 0.0.0.0 --port ${PORT:-8001} --log-level info