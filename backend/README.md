# Markdown Forge - Backend API

This directory contains the autonomous backend service for Markdown Forge, built with FastAPI and PostgreSQL.

## Backend Autonomy Principles

The backend API follows these key principles:

- **Independent Operation**: The API functions as a standalone application that operates independently from any frontend implementation.
- **API-First Design**: All functionality is exposed through well-defined API endpoints that follow REST principles.
- **No Frontend Dependencies**: The backend has no dependencies on frontend code, libraries, or implementation details.
- **Self-Contained Business Logic**: All business logic is contained within the backend, never leaking to the frontend.
- **Independent Testing**: The backend can be tested in isolation using API requests, without requiring any frontend components.
- **Separate Deployment**: The backend can be deployed independently from the frontend.
- **Frontend Agnostic**: The API is designed to work with any frontend implementation that adheres to the API contract.

## Overview

The backend API provides:
- RESTful endpoints for file operations
- File conversion services
- Database integration for file metadata
- Authentication and authorization
- Comprehensive API documentation
- Conversion templates management
- Advanced error recovery system
- Performance optimization
- Batch processing
- Concurrent conversions
- Template caching
- Load balancing support
- Conversion history tracking
- Queue monitoring and management

## Directory Structure

```
backend/
├── api/                 # API endpoints
│   └── routes/         # API route definitions
├── routers/             # FastAPI router definitions
├── models/              # Database models
│   ├── file.py         # File model
│   ├── conversion.py   # Conversion model
│   ├── template.py     # Template model
├── services/            # Business logic services
│   ├── converter.py    # Conversion service
│   ├── template_manager.py # Template management service
│   ├── file_service.py # File management service
├── utils/               # Utility functions
│   ├── error_handler.py # Error handling utilities
│   ├── conversion_error_handler.py # Conversion error handling
│   ├── logger.py       # Logging configuration
│   ├── cache.py        # Caching utilities
│   ├── api_docs.py     # API documentation utilities
│   ├── format_validator.py # Format validation utilities
│   └── rate_limiter.py # Rate limiting utilities
├── data/                # Data storage directory
├── logs/                # Log files
├── conversion_queue.py  # Queue implementation for batch processing
├── models.py            # Database model definitions
├── config.py            # Configuration management
├── database.py          # Database connection handling
├── auth.py              # Authentication utilities
├── main.py              # FastAPI application entry point
├── .env                 # Environment variables for development
└── .env.example         # Example environment variables
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```
Edit the `.env` file with your specific configuration values.

4. Set up the database:
```bash
# Create PostgreSQL database
createdb markdown_forge

# Run migrations
alembic upgrade head
```

## Configuration

The application uses Pydantic for configuration management. Key configuration files:

- `config.py`: Contains the `Settings` class that manages all application settings
- `.env`: Contains environment-specific configuration values
- `.env.example`: Template for required environment variables

### Required Environment Variables

#### Application
- `PROJECT_NAME`: Name of the project
- `VERSION`: Version of the application
- `API_V1_STR`: API version prefix
- `MARKDOWN_FORGE_ENV`: Environment (development, production)

#### Security
- `SECRET_KEY`: Secret key for JWT token generation
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT token expiration time in minutes

#### Database
- `POSTGRES_SERVER`: PostgreSQL server host
- `POSTGRES_USER`: PostgreSQL user
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: PostgreSQL database name

#### File Storage
- `UPLOAD_DIR`: Directory for uploaded files
- `OUTPUT_DIR`: Directory for converted files
- `MAX_UPLOAD_SIZE`: Maximum file size in bytes

#### Performance
- `BATCH_SIZE`: Number of files to process in a batch
- `MAX_CONCURRENT_TASKS`: Maximum number of concurrent conversion tasks
- `CACHE_TTL`: Template cache time-to-live in seconds
- `CLEANUP_INTERVAL`: Interval for cleanup operations in seconds

#### Logging
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Running the Application

### Using run.py Script

```bash
# Run just the backend
python run.py run backend

# Run with debug mode enabled
python run.py run backend --debug
```

### Using Uvicorn Directly

```bash
# Start the development server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Using VS Code Launch Configuration

Use the VS Code "Run and Debug" panel and select "Backend: FastAPI" configuration.

### Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Contract

The backend exposes a well-defined API contract that any frontend can implement:

### File Operations
- `POST /api/v1/files/upload` - Upload files
- `GET /api/v1/files` - List files
- `GET /api/v1/files/{id}` - Get file details
- `DELETE /api/v1/files/{id}` - Delete file
- `PUT /api/v1/files/{id}/rename` - Rename file

### Conversion
- `POST /api/v1/convert` - Convert file
- `POST /api/v1/convert/batch` - Batch convert multiple files
- `GET /api/v1/convert/{id}/status` - Get conversion status
- `GET /api/v1/convert/{id}/download` - Download converted file
- `GET /api/v1/convert/queue/status` - Get conversion queue status
- `GET /api/v1/convert/history` - Get conversion history with pagination
- `DELETE /api/v1/convert/history/{id}` - Delete specific history record
- `POST /api/v1/convert/history/clear` - Clear all conversion history
- `POST /api/v1/convert/{id}/retry` - Retry failed conversion
- `POST /api/v1/convert/{id}/cancel` - Cancel active conversion

### Templates
- `POST /api/v1/templates` - Create a new template
- `GET /api/v1/templates` - List all templates
- `GET /api/v1/templates/{id}` - Get template details
- `PUT /api/v1/templates/{id}` - Update a template
- `DELETE /api/v1/templates/{id}` - Delete a template
- `GET /api/v1/templates/{id}/options/{format}` - Get template options for a format

### System
- `GET /api/v1/health` - Health check
- `GET /api/v1/status` - System status
- `GET /api/v1/config` - Configuration
- `GET /api/v1/metrics` - System metrics

## Development

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Document functions and classes with docstrings
- Run linting before committing:
```bash
flake8 .
black .
isort .
```

### Testing

Run tests with:
```bash
pytest
```

### Performance Testing

Run performance tests with:
```bash
pytest performance/
```

### Security Testing

Run security tests with:
```bash
pytest security/
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

## API Documentation

The API documentation is automatically generated and available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Security

- All endpoints are protected with JWT authentication
- Passwords are hashed using bcrypt
- CORS is configured for allowed frontend domains
- Rate limiting is implemented for API endpoints
- Input validation and sanitization
- File type verification
- Size limitations

## Error Handling

The application uses a standardized error response format:
```json
{
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": "Additional error details (optional)"
}
```

### Error Recovery System

The application includes an advanced error recovery system for file conversions:

#### Recovery Strategies

The system supports multiple recovery strategies for different types of errors:

- **Timeout Increase**: Automatically increases timeout for operations that time out
- **Simplified Options**: Retries with simplified conversion options
- **Memory Optimization**: Reduces memory usage for memory-intensive operations
- **Network Retry**: Implements exponential backoff for network-related errors
- **Backoff Strategy**: Implements exponential backoff for general errors
- **Alternative Converter**: Falls back to alternative conversion methods

#### Implementation

The error recovery system is implemented in the following components:

- `utils/error_handler.py`: Defines error types and recovery strategies
- `utils/conversion_error_handler.py`: Specialized error handling for conversions
- `conversion_queue.py`: Integrates error recovery with the conversion queue
- `services/converter.py`: Implements recovery strategies for conversion errors

## Performance Optimization

The application includes several performance optimizations:

### Batch Processing
- Concurrent processing of multiple files
- Configurable batch size
- Efficient resource utilization
- Progress tracking

### Memory Management
- Memory-efficient task management
- Resource cleanup after completion
- Concurrent processing with controlled limits
- Status monitoring and reporting

### Caching
- Template caching with expiry
- In-memory caching for frequently accessed data
- Cache invalidation on updates
- Cache size limits

### Load Balancing
- Horizontal scaling support
- Load distribution
- Health checks
- Failover handling

## Logging

Logging is configured in `utils/logger.py`. The application supports both synchronous and asynchronous logging:

### Log Levels
- DEBUG: Detailed information for debugging
- INFO: General operational information
- WARNING: Warning messages for potentially problematic situations
- ERROR: Error messages for serious problems
- CRITICAL: Critical messages for fatal errors

### Key Features
- **Structured Logging**: Logs include structured context information
- **Asynchronous Support**: Asynchronous logging for FastAPI endpoints
- **File Rotation**: Logs are automatically rotated to prevent file growth
- **Environment Detection**: Debug logging in development environment

## Monitoring

The application includes comprehensive monitoring:

### Performance Metrics
- Batch processing statistics
- Concurrent task tracking
- Memory usage monitoring
- Resource cleanup status
- Queue performance metrics
- API response times
- Conversion history metrics
- CPU and memory usage per conversion
- Conversion success/failure rates
- Average conversion durations

### Conversion History Tracking
The backend implements a robust conversion history tracking system that:
- Records detailed metrics for each conversion job
- Captures CPU and memory usage during conversion
- Tracks conversion duration and outcome
- Maintains error information for failed conversions
- Supports pagination for efficient retrieval
- Provides statistical aggregations (success rates, averages)
- Enables filtering and searching capabilities
- Supports CSV export for reporting

### Health Checks
- Database connectivity
- File system access
- External service availability
- Resource utilization
- Error rates
- Response times 