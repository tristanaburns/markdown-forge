# Markdown Forge - Backend API

This directory contains the backend service for Markdown Forge, built with FastAPI and PostgreSQL.

## Overview

The backend API provides:
- RESTful endpoints for file operations
- File conversion services
- Database integration for file metadata
- Authentication and authorization
- Comprehensive API documentation
- Conversion templates management
- Advanced error recovery system

## Directory Structure

```
backend/
├── api/               # API endpoints
│   ├── v1/           # API version 1
│   │   ├── files.py  # File operations endpoints
│   │   ├── convert.py # Conversion endpoints
│   │   ├── templates.py # Template management endpoints
│   │   └── auth.py   # Authentication endpoints
│   └── deps.py       # Dependency injection
├── core/              # Core functionality
│   ├── config.py     # Configuration management
│   ├── security.py   # Security utilities
│   └── logging.py    # Logging configuration
├── models/            # Database models
│   ├── file.py       # File model
│   ├── template.py   # Template model
│   └── conversion.py # Conversion model
├── services/          # Business logic
│   ├── converter.py  # File conversion service
│   ├── template_manager.py # Template management service
│   ├── conversion_queue.py # Conversion queue service
│   └── file.py       # File management service
├── utils/             # Utility functions
│   ├── format_validator.py # Format validation utilities
│   └── conversion_error_handler.py # Error handling utilities
├── alembic/           # Database migrations
├── tests/             # Test files
├── .env               # Environment variables
├── .env.example       # Example environment variables
├── config.py          # Configuration management
├── main.py            # FastAPI application entry point
└── requirements.txt   # Python dependencies
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

## Database Setup

1. Create a PostgreSQL database:
```sql
CREATE DATABASE markdown_forge;
```

2. Run migrations:
```bash
alembic upgrade head
```

## Running the Application

1. Start the development server:
```bash
uvicorn main:app --reload
```

2. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### File Operations
- `POST /api/v1/files/upload` - Upload files
- `GET /api/v1/files` - List files
- `GET /api/v1/files/{id}` - Get file details
- `DELETE /api/v1/files/{id}` - Delete file
- `PUT /api/v1/files/{id}/rename` - Rename file

### Conversion
- `POST /api/v1/convert` - Convert file
- `GET /api/v1/convert/{id}/status` - Get conversion status
- `GET /api/v1/convert/{id}/download` - Download converted file
- `GET /api/v1/convert/queue/status` - Get conversion queue status

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
- CORS is configured for the frontend domain
- Rate limiting is implemented for API endpoints

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

- `utils/conversion_error_handler.py`: Defines error types and recovery strategies
- `services/conversion_queue.py`: Integrates error recovery with the conversion queue
- `services/markdown_converter.py`: Implements recovery strategies for conversion errors

#### Usage

The error recovery system is automatically integrated with the conversion queue:

```python
# The conversion queue automatically applies recovery strategies
await conversion_queue.add_task(file_id, formats, template_id)
```

## Logging

Logging is configured in `core/logging.py`. Log levels:
- DEBUG: Detailed information for debugging
- INFO: General operational information
- WARNING: Warning messages for potentially problematic situations
- ERROR: Error messages for serious problems
- CRITICAL: Critical messages for fatal errors 