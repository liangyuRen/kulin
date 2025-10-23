#!/bin/bash
# Flask-crawler entrypoint script

echo "Starting Flask Crawler Service..."
echo "Note: NLTK data download skipped - using pretrained model API instead"

echo "Starting Gunicorn..."
exec gunicorn --workers=2 --threads=2 --bind=0.0.0.0:5000 --timeout=120 --access-logfile=- --error-logfile=- app:app
