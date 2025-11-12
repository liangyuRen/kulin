# Flask Crawler Service Dockerfile
# Optimized for slow networks and dependency caching
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables early
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    TZ=Asia/Shanghai \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies in multiple steps for better resilience
# Step 1: Install basic packages
RUN pip install --timeout=120 -i https://mirrors.aliyun.com/pypi/simple/ --prefer-binary \
    Flask==3.0.0 Flask-CORS==4.0.0 requests==2.31.0 python-dotenv==1.0.0 \
    pymysql==1.1.0 beautifulsoup4==4.12.2 tqdm==4.66.1 gunicorn==21.2.0

# Step 2: Install data science packages (these are larger)
RUN pip install --timeout=120 -i https://mirrors.aliyun.com/pypi/simple/ --prefer-binary \
    numpy==1.26.2 pandas==2.1.4

# Step 3: Install ML and text processing packages
RUN pip install --timeout=120 -i https://mirrors.aliyun.com/pypi/simple/ --prefer-binary \
    scikit-learn==1.3.2 nltk==3.8.1

# Step 4: Install lxml (uses pre-compiled wheel, no system deps needed)
RUN pip install --timeout=120 -i https://mirrors.aliyun.com/pypi/simple/ --prefer-binary \
    lxml==5.1.0

# Step 5: Install remaining packages
RUN pip install --timeout=120 -i https://mirrors.aliyun.com/pypi/simple/ --prefer-binary \
    dashscope==1.19.0 openai==1.30.0 python-Levenshtein==0.23.0

# Step 6: Install missing YAML support
RUN pip install --timeout=120 -i https://mirrors.aliyun.com/pypi/simple/ --prefer-binary \
    PyYAML==6.0.1 httpx

# Copy application code
COPY . .

# Create NLTK data directory (download will happen at runtime if needed)
RUN mkdir -p /app/nltk_data

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh 2>/dev/null || true

# Create a non-root user for security
RUN useradd -m -u 1000 -s /bin/bash flaskuser && \
    chown -R flaskuser:flaskuser /app

# Switch to non-root user
USER flaskuser

# Set NLTK data path
ENV NLTK_DATA=/app/nltk_data

# Expose Flask port
EXPOSE 5000

# Health check (using python urllib instead of curl to avoid extra dependencies)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/vulnerabilities/test', timeout=3).read()" || exit 1

# Run Flask application with Gunicorn (production-ready WSGI server)
# Use entrypoint script to download NLTK data first
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
