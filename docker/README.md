# Markdown Forge - Docker Configuration

This directory contains the Docker configuration for the Markdown Forge project, including a multi-stage Dockerfile for building optimized container images.

## Docker Architecture

The Markdown Forge project uses a multi-container architecture with three main services:

1. **Frontend (Flask)**: Web interface for user interaction
2. **Backend (FastAPI)**: API service for file operations and conversions
3. **PostgreSQL**: Database for storing file metadata and conversion history

## Dockerfile

The `Dockerfile` in this directory is a multi-stage build that:

1. **Builds the application code** in a builder stage
2. **Creates a minimal runtime image** with only the necessary dependencies
3. **Sets up a non-root user** for security
4. **Configures the application** with appropriate environment variables

### Key Features

- **Multi-stage build** to minimize image size
- **Layer optimization** for efficient caching
- **Security hardening** with non-root user
- **Environment configuration** via build arguments
- **Health checks** for container monitoring
- **Volume configuration** for persistent data

## Docker Compose

The project uses Docker Compose for orchestrating the multi-container application. The `docker-compose.yml` file in the root directory defines:

- Service dependencies and startup order
- Environment variables for each service
- Volume mappings for persistent data
- Network configuration
- Health checks
- Resource constraints

## Usage

### Building the Images

```bash
# Build all services
docker-compose build

# Build a specific service
docker-compose build frontend
docker-compose build backend
```

### Running the Application

```bash
# Start all services
docker-compose up -d

# Start a specific service
docker-compose up -d frontend
docker-compose up -d backend
```

### Viewing Logs

```bash
# View logs for all services
docker-compose logs -f

# View logs for a specific service
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f postgres
```

### Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Configuration

### Environment Variables

The Docker setup uses environment variables for configuration. These can be set in:

- `.env` files
- Docker Compose environment section
- Command line arguments

Key environment variables:

#### Frontend
- `FLASK_APP`: Path to the Flask application
- `FLASK_ENV`: Environment (development, production)
- `FLASK_DEBUG`: Debug mode (0, 1)
- `API_BASE_URL`: URL of the backend API
- `SECRET_KEY`: Secret key for Flask session

#### Backend
- `PROJECT_NAME`: Name of the project
- `VERSION`: Version of the application
- `API_V1_STR`: API version prefix
- `POSTGRES_SERVER`: PostgreSQL server host
- `POSTGRES_USER`: PostgreSQL user
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: PostgreSQL database name
- `SECRET_KEY`: Secret key for JWT token generation

#### Database
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_DB`: Database name

### Volumes

The Docker setup uses volumes for persistent data:

- `frontend_data`: Stores uploaded files for the frontend
- `backend_data`: Stores converted files for the backend
- `postgres_data`: Stores the PostgreSQL database

### Networks

The Docker setup uses a custom network for service communication:

- `markdown_forge_network`: Network for inter-service communication

## Development

### Development Mode

For development, you can use the development configuration:

```bash
# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

This configuration includes:
- Volume mounts for live code reloading
- Debug mode enabled
- Additional development tools

### Debugging

To debug the application:

```bash
# Attach to a container
docker-compose exec frontend bash
docker-compose exec backend bash

# View logs
docker-compose logs -f
```

## Production Deployment

For production deployment, use the production configuration:

```bash
# Start in production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

This configuration includes:
- Optimized for performance
- Security hardening
- Production-ready settings

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check if the PostgreSQL container is running
   - Verify database credentials
   - Check network connectivity

2. **File Permission Issues**
   - Check volume permissions
   - Verify user permissions in containers

3. **Service Startup Issues**
   - Check logs for error messages
   - Verify environment variables
   - Check service dependencies

### Health Checks

The Docker setup includes health checks for all services:

```bash
# Check health status
docker-compose ps
```

## Security Considerations

- All services run as non-root users
- Sensitive data is stored in environment variables
- Network access is restricted to necessary ports
- Regular security updates are applied
- Secrets are managed securely 