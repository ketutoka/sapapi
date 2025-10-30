# SAP API Docker Container
# Multi-stage build for production deployment

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Set labels
LABEL maintainer="SAP API Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="sap-api" \
      org.label-schema.description="SAP Sales Data API with PostgreSQL" \
      org.label-schema.version=$VERSION \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/ketutoka/sapapi" \
      org.label-schema.schema-version="1.0"

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create application user
RUN groupadd -r sapapi && useradd -r -g sapapi sapapi

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    HOST=0.0.0.0 \
    PORT=8000

# Create application directory
WORKDIR /app

# Copy application code
COPY --chown=sapapi:sapapi . .

# Create logs directory
RUN mkdir -p /var/log/sapapi && \
    chown -R sapapi:sapapi /var/log/sapapi

# Switch to non-root user
USER sapapi

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["gunicorn", "--config", "deployment/gunicorn.conf.py", "app:app"]