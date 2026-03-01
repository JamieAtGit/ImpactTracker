#!/bin/bash
# Start script for Railway deployment

echo "Starting DSP Eco Tracker backend..."
echo "PORT: ${PORT:-5000}"
echo "Current directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "PATH: $PATH"

# Set default port if not provided
export PORT=${PORT:-5000}

# Add current directory to Python path
export PYTHONPATH=/app:$PYTHONPATH

# Check if gunicorn is available
echo "Checking for gunicorn..."
which gunicorn || echo "gunicorn not found in PATH"
python -m pip show gunicorn || echo "gunicorn not installed via pip"

# Try different ways to start the server
if command -v gunicorn &> /dev/null; then
    echo "Starting with gunicorn..."
    exec gunicorn main:app --bind 0.0.0.0:$PORT --workers 1 --timeout 300 --log-level info
elif python -c "import gunicorn" 2>/dev/null; then
    echo "Starting with python -m gunicorn..."
    exec python -m gunicorn main:app --bind 0.0.0.0:$PORT --workers 1 --timeout 300 --log-level info
else
    echo "Gunicorn not available, starting with Flask development server..."
    exec python main.py
fi