# Build a multi-stage Docker image for Markdown Forge
# First stage: Build dependencies
FROM python:3.10-slim AS builder

WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Install production-specific dependencies
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels psycopg2==2.9.7

# Second stage: Runtime image
FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MARKDOWN_FORGE_ENV=production

# Install system dependencies for runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client for database access
    postgresql-client \
    # Pandoc for document conversion
    pandoc \
    # PDF conversion tools
    wkhtmltopdf \
    # LaTeX for PDF generation
    texlive-xetex \
    texlive-fonts-recommended \
    # Cairo for SVG support
    libcairo2-dev \
    # Font libraries
    fonts-liberation \
    # Headless browser support
    xvfb \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder stage
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p \
    app/static/uploads \
    app/static/converted \
    app/logs \
    backend/logs \
    backend/data

# Expose ports
EXPOSE 5000 8000

# Create a non-root user to run the application
RUN useradd -m markdown-user
RUN chown -R markdown-user:markdown-user /app
USER markdown-user

# Command to run the application
CMD ["python", "run.py", "run", "all"] 