# Pin to specific Python version for reproducible builds
FROM python:3.11.7-slim

WORKDIR /app

# Install curl for healthcheck and create non-root user
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --gid 1001 --no-create-home appuser

# Install dependencies first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application modules
COPY config.py .
COPY utils.py .
COPY storage.py .
COPY sheets.py .
COPY momence.py .
COPY failed_queue.py .
COPY notifications.py .
COPY error_types.py .
COPY monitor.py .
COPY web/ ./web/

# Create directory for data persistence with proper ownership
# Note: For Cloud Run, use Cloud Storage or a mounted volume
# For local Docker/cloud deployment, mount secrets and data volumes
RUN mkdir -p /data /data/logs /secrets \
    && chown -R appuser:appgroup /data /secrets /app

# Build-time argument for version (set by docker build --build-arg)
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

# Set default environment variables for Cloud Run
# Cloud Run sets PORT automatically; we use it via HEALTH_PORT
ENV DATABASE_FILE=/data/lead_monitor.db
ENV SENT_TRACKER_FILE=/data/sent_entries.json
ENV FAILED_QUEUE_FILE=/data/failed_queue.json
ENV LOG_DIR=/data/logs
ENV CONFIG_FILE=/app/config.json

# Encryption key should be provided via secrets mount or environment
# Default location for mounted secrets
ENV ENCRYPTION_KEY_FILE=/secrets/.encryption_key

# Default to JSON logging for Cloud Run structured logging
ENV LOG_LEVEL=INFO

# Cloud Run requires the container to listen on $PORT
# The health server will use this port
ENV HEALTH_PORT=8080

# Security: Dashboard authentication (override these in deployment)
# DASHBOARD_API_KEY or DASHBOARD_USERNAME/DASHBOARD_PASSWORD should be set
# via secrets manager or environment variables

# Trusted proxy IPs for X-Forwarded-For header handling
# Default includes private IP ranges for typical cloud load balancers
ENV TRUSTED_PROXY_IPS="127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

# Expose the health/dashboard port (Cloud Run uses 8080 by default)
EXPOSE 8080

# Switch to non-root user
USER appuser

# Health check for local testing
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${HEALTH_PORT}/health || exit 1

# Run the monitor in daemon mode
# Cloud Run will send SIGTERM for graceful shutdown
CMD ["python", "monitor.py", "--daemon"]
