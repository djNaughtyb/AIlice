# Production-ready Dockerfile for AIlice on Google Cloud Run
# Optimized for Ubuntu base with all required dependencies

FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    cmake \
    ninja-build \
    build-essential \
    wget \
    curl \
    ca-certificates \
    gnupg \
    libpq-dev \
    # Chrome dependencies for selenium/browser automation
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libnss3 \
    libgbm1 \
    libasound2 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libdrm2 \
    libxshmfence1 \
    # Additional libraries
    libsndfile1 \
    ffmpeg \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Note: FFmpeg is installed for media processing (transcoding, streaming, etc.)

# Install Google Chrome for browser automation
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
# Note: Heavy ML dependencies (torch, transformers) have been removed from requirements.txt
# This significantly reduces image size. Use API-based LLM integrations instead.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the band_of_misfits folder explicitly
COPY band_of_misfits /app/band_of_misfits

# Copy the entire AIlice codebase
COPY . .

# Copy user's config.json to a default location
# Users can override this with volume mounts or environment variables
RUN mkdir -p /root/.config/ailice/Steven\ Lu
COPY config.json /root/.config/ailice/Steven\ Lu/config.json

# Install AIlice in development mode
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/chat_history /app/static /app/templates

# Copy capabilities configuration
COPY capabilities_config.json /app/capabilities_config.json

# Set environment variables for Cloud Run
ENV PORT=8080
ENV AILICE_HOST=0.0.0.0
ENV AILICE_EXPOSE=true
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV ENVIRONMENT=production
ENV CAPABILITIES_CONFIG=/app/capabilities_config.json

# Expose the port (Cloud Run uses PORT env var)
EXPOSE 8080

# Health check for FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Make apps executable
RUN chmod +x /app/cloud_run_app.py /app/fastapi_app.py

# Use the FastAPI app as entrypoint (or cloud_run_app.py for Flask)
# To use FastAPI (recommended for new features):
ENTRYPOINT ["python3", "/app/unified_app.py"]
# This runs BOTH Flask (AIlice UI) and FastAPI together!
# To use original Flask app:
# ENTRYPOINT ["python3", "/app/cloud_run_app.py"]

# Labels for metadata
LABEL maintainer="viralspark-ailice"
LABEL description="AIlice - Fully Autonomous AI Agent for Google Cloud Run"
LABEL version="1.0.0"
