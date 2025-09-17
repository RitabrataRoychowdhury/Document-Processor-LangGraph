# Production-Ready QME System - Multi-stage Docker Build
# Optimized for production deployment with security and performance

# Build stage - Compile dependencies and prepare assets
FROM python:3.11-slim as builder

LABEL maintainer="QME System Team"
LABEL version="1.0.0"
LABEL description="Production-ready QME System with comprehensive monitoring"

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    git \
    curl \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Compile Python bytecode for faster startup
RUN python -m compileall /root/.local/lib/python3.11/site-packages/

# Production stage - Minimal runtime image
FROM python:3.11-slim as production

# Security: Create non-root user
RUN groupadd -r qme && useradd -r -g qme -s /bin/bash qme

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set up application directory
WORKDIR /app
RUN chown -R qme:qme /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/qme/.local

# Copy application code with proper ownership
COPY --chown=qme:qme . .

# Create directory structure with proper permissions
RUN mkdir -p \
    logs/audit \
    data/database \
    data/documents \
    data/qme_references \
    results/generated_documents \
    results/validation_reports \
    results/performance_reports \
    config/secrets \
    && chown -R qme:qme logs data results config \
    && chmod 755 logs data results \
    && chmod 700 config/secrets \
    && chmod +x scripts/*.sh

# Production environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV PATH=/home/qme/.local/bin:$PATH
ENV QME_ENVIRONMENT=production
ENV QME_LOG_LEVEL=INFO
ENV QME_ENABLE_MONITORING=true
ENV QME_ENABLE_HEALTH_CHECKS=true
ENV QME_ENABLE_AUDIT_LOGGING=true
ENV QME_MAX_FILE_SIZE_MB=50
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Security: Run as non-root user
USER qme

# Expose ports
EXPOSE 8501 8502

# Comprehensive health check with multiple validation points
HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=3 \
    CMD python -c "
import sys
import requests
import time
import json
from pathlib import Path

def check_health():
    try:
        # Check main application health
        main_response = requests.get('http://localhost:8501/_stcore/health', timeout=10)
        if main_response.status_code != 200:
            print('Main application health check failed')
            return False
        
        # Check comprehensive health endpoint if available
        try:
            health_response = requests.get('http://localhost:8502/health', timeout=5)
            if health_response.status_code == 200:
                health_data = health_response.json()
                if not health_data.get('healthy', False):
                    print('System health check failed')
                    return False
        except:
            pass  # Health endpoint might not be available
        
        # Check critical directories
        critical_dirs = ['logs', 'data/database', 'results']
        for dir_path in critical_dirs:
            if not Path(dir_path).exists():
                print(f'Critical directory missing: {dir_path}')
                return False
        
        print('All health checks passed')
        return True
        
    except Exception as e:
        print(f'Health check error: {e}')
        return False

sys.exit(0 if check_health() else 1)
"

# Production startup script
COPY --chown=qme:qme scripts/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set entrypoint and default command
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["production"]

# Metadata labels for production tracking
LABEL org.opencontainers.image.title="QME System"
LABEL org.opencontainers.image.description="Production-ready Qualified Medical Evaluator system"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.created="2024-01-01T00:00:00Z"
LABEL org.opencontainers.image.source="https://github.com/qme-system/qme"
LABEL org.opencontainers.image.licenses="MIT"