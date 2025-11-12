#!/bin/bash
# Flask-crawler entrypoint script
set -e

echo "==========================================="
echo "Starting Flask Crawler Service (Production)"
echo "==========================================="
echo ""

# Check if required environment variables are set
echo "Checking configuration..."
if [ -z "$ALI_API_KEY" ]; then
    echo "⚠️  Warning: ALI_API_KEY is not set. LLM features will be disabled."
else
    echo "✓ ALI_API_KEY is configured"
fi

echo ""
echo "Verifying Python environment..."
python --version
python -c "import yaml; print('✓ PyYAML available')" || echo "✗ PyYAML not found"
python -c "import flask; print('✓ Flask available')" || echo "✗ Flask not found"

echo ""
echo "Starting Gunicorn (Production WSGI Server)..."
echo "Workers: 2 | Threads per worker: 2 | Port: 5000 | Timeout: 120s"
echo ""

# Run Flask with Gunicorn in production mode
exec gunicorn \
    --workers=2 \
    --threads=2 \
    --worker-class=gthread \
    --bind=0.0.0.0:5000 \
    --timeout=120 \
    --graceful-timeout=30 \
    --keep-alive=5 \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=info \
    app:app
