# Markdown Forge Docker Configuration

This directory contains Docker configuration files for containerizing the Markdown Forge application.

## Overview

Markdown Forge uses Docker for containerized deployment, providing:

- Consistent environment across development and production
- Isolation of services
- Easy scaling and management
- Simplified deployment

## Files

- **Dockerfile**: Multi-stage build configuration for the application image
- **docker-compose.yml**: (In parent directory) Orchestration configuration for running all services

## Docker Image

The Dockerfile creates a multi-stage build that:

1. **First Stage (Builder)**:
   - Installs build dependencies
   - Compiles Python packages with C extensions
   - Creates wheel packages for all dependencies

2. **Second Stage (Runtime)**:
   - Installs runtime dependencies including:
     - PostgreSQL client
     - Pandoc for document conversion
     - wkhtmltopdf for HTML-to-PDF conversion
     - LaTeX for PDF generation
     - Cairo for SVG support
     - Font libraries
   - Copies wheels from the builder stage
   - Sets up the application code
   - Creates necessary directories
   - Configures a non-root user for security

## Services

The docker-compose.yml file in the parent directory defines three services:

1. **PostgreSQL Database**:
   - Uses postgres:15 image
   - Persists data in a named volume
   - Includes health checks

2. **Backend (FastAPI)**:
   - Built from the Dockerfile
   - Runs the FastAPI application
   - Connects to the PostgreSQL database
   - Exposes port 8000

3. **Frontend (Flask)**:
   - Built from the same Dockerfile
   - Runs the Flask application
   - Communicates with the backend
   - Exposes port 5000

## Usage

From the parent directory:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Stop all services
docker-compose down

# Rebuild images (after code changes)
docker-compose build

# Stop services and remove volumes
docker-compose down -v
```

## Development with Docker

For development, you can use Docker Compose with volume mounts to enable live code reloading:

```bash
# Start services with development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Production Deployment

For production deployment:

1. Build the Docker image:
```bash
docker build -t markdown-forge:latest -f docker/Dockerfile .
```

2. Configure environment variables for production in `.env.production`

3. Deploy using Docker Compose:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Customization

To customize the Docker configuration:

1. Edit the Dockerfile to add additional dependencies or change build steps
2. Create custom docker-compose override files for different environments
3. Modify environment variables in the docker-compose.yml file or .env files 