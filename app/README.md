# Markdown Forge - Frontend Application

This directory contains the autonomous frontend application for Markdown Forge, built with Flask and Bootstrap.

## Frontend Autonomy Principles

The frontend application follows these key principles:

- **Independent Operation**: The UI functions as a standalone application that operates independently from the backend.
- **API-Only Communication**: All interaction with the backend occurs exclusively through well-defined API endpoints.
- **No Direct Backend Dependencies**: The frontend code has no direct dependencies on backend code or implementation details.
- **Self-Contained State Management**: UI state is managed entirely within the frontend application.
- **Independent Testing**: The frontend can be tested in isolation using mock API responses.
- **Separate Deployment**: The frontend can be deployed independently from the backend.

## Overview

The frontend application provides a modern, responsive web interface for:
- Uploading Markdown files
- Converting files to various formats (HTML, PDF, DOCX, PNG, CSV, XLSX)
- Managing converted files
- Previewing converted content
- Monitoring conversion history and system metrics

## Directory Structure

```
app/
├── static/            # Static assets
│   ├── css/          # CSS stylesheets
│   │   ├── components/ # Component-specific styles
│   │   └── conversion_history.css # Styles for conversion history page
│   ├── js/           # JavaScript files
│   │   ├── components/ # Component-specific scripts
│   │   ├── utils/     # Utility scripts
│   │   └── conversion_history.js # Scripts for conversion history page
│   ├── converted/    # Storage for converted files
│   └── uploads/      # Storage for uploaded files
├── templates/         # Jinja2 templates
│   ├── base.html     # Base template with common elements
│   ├── upload.html   # File upload page
│   ├── files.html    # File management page
│   ├── preview.html  # File preview page
│   ├── conversion_history.html # Conversion history dashboard
│   ├── components/   # Reusable template components
│   └── errors/       # Error page templates
├── views/             # Standalone HTML views
├── services/          # Frontend services
├── utils/             # Frontend utilities
│   ├── config.py     # Configuration management
│   ├── logger.py     # Logging and context tracking
│   ├── api.py        # API utilities
│   ├── api_client.py # API client for backend communication
│   ├── error_handler.py # Error handling utilities
│   └── route_helpers.py # Route helper utilities
├── routes/            # Route definitions
├── middleware/        # Request/response middleware
├── data/              # Data storage
├── models/            # Frontend data models
├── controllers/       # Request handlers
├── config/            # Configuration files
├── logs/              # Log files
└── main.py            # Flask application entry point
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

The application uses environment variables for configuration. Key configuration files:

- `.env`: Contains environment-specific configuration values
- `.env.example`: Template for required environment variables
- `utils/config.py`: Configuration management with dataclasses

### Required Environment Variables

- `FLASK_APP`: Path to the Flask application
- `FLASK_ENV`: Environment (development, production)
- `FLASK_DEBUG`: Debug mode (0, 1)
- `API_BASE_URL`: URL of the backend API (the only connection to the backend)
- `SECRET_KEY`: Secret key for Flask session
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Running the Application

### Using run.py Script

```bash
# Run just the frontend
python run.py run frontend

# Run with debug mode enabled
python run.py run frontend --debug
```

### Using Flask Directly

```bash
# Start the development server
flask run --debug

# Access the application
# Web Interface: http://localhost:5000
```

### Using VS Code Launch Configuration

Use the VS Code "Run and Debug" panel and select "Frontend: Flask" configuration.

## Features

### File Upload
- Drag-and-drop interface
- Multiple file selection
- File type validation
- Progress tracking
- Batch upload support
  - Configurable batch size (5, 10, 20, or all files)
  - Multiple output format selection
  - Batch progress monitoring
  - Per-file status tracking
- Concurrent processing

### File Management
- List all uploaded files
- Preview converted files
- Download converted files
- Delete files
- Batch operations
- Real-time status updates

### File Preview
- Syntax highlighting for code blocks
- MathJax for mathematical expressions
- Mermaid for diagrams
- Responsive layout
- Dark mode support
- Custom template support

### Conversion History
- Comprehensive dashboard displaying conversion activities
- Queue statistics showing pending, active, completed, and failed conversions
- Active conversions monitoring with real-time progress indicators
- System metrics visualization (CPU, memory, disk usage, uptime)
- Detailed conversion history log with timestamps and durations
- Search and filter capabilities by filename, format, or status
- Export history to CSV for reporting and analysis
- Actions for each history item (download, retry, view details, remove)
- Pagination for efficient browsing of large history datasets
- Responsive design that works on all device sizes

### Performance
- Batch processing
- Concurrent conversions
- Memory optimization
- Resource cleanup
- Status monitoring
- Progress tracking

### Batch Processing
The application includes robust batch processing capabilities:

- **Multiple File Selection**: Upload multiple files simultaneously through drag-and-drop or file browser.
- **Batch Configuration**: Set batch size to control processing load (5, 10, 20, or all files at once).
- **Multiple Output Formats**: Select multiple output formats for each file in the batch (HTML, PDF, DOCX, PNG).
- **Status Tracking**: Monitor both overall batch progress and individual file status.
- **Concurrent Processing**: Files within a batch are processed in parallel for optimal performance.
- **Error Handling**: Robust error handling for individual files, allowing the batch to continue even if some files fail.

#### Usage

1. Navigate to the upload page
2. Drag and drop multiple Markdown files or use the file browser
3. Configure batch processing options:
   - Set batch size
   - Select output formats
   - Choose conversion options
4. Click "Upload and Convert"
5. Monitor progress in real-time
6. View and download results when processing completes

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

## Integration with Backend

The frontend communicates with the backend via REST API endpoints **only**. No direct code dependencies exist between the frontend and backend implementations.

### API Contract

- File upload: `POST /api/v1/files/upload`
- File listing: `GET /api/v1/files`
- File conversion: `POST /api/v1/convert`
- File download: `GET /api/v1/convert/{id}/download`
- File deletion: `DELETE /api/v1/files/{id}`
- Template management: `GET/POST/PUT/DELETE /api/v1/templates`
- Queue status: `GET /api/v1/convert/queue/status`
- Conversion history: `GET /api/v1/convert/history`
- Clear history: `POST /api/v1/convert/history/clear`
- Remove history item: `DELETE /api/v1/convert/history/{id}`
- Retry conversion: `POST /api/v1/convert/{id}/retry`
- Cancel conversion: `POST /api/v1/convert/{id}/cancel`

### Error Handling for API Communication

The frontend implements comprehensive error handling for API communication:
- Network error detection and recovery
- API response validation
- Graceful degradation when the API is unavailable
- Retry mechanisms with exponential backoff
- User-friendly error messages

## Error Handling

The application uses a standardized error handling approach:
- User-friendly error messages
- Logging of errors
- Graceful degradation
- Retry mechanisms for API calls
- Error recovery strategies
- Real-time error notifications

## Logging

Logging is configured in `utils/logger.py`. The application uses a structured logging system with context tracking and performance metrics:

- **Context Tracking**: Track request context across function calls
- **Performance Metrics**: Track timing and resource usage
- **Structured JSON Logging**: Log events in structured JSON format
- **Log Levels**:
  - DEBUG: Detailed information for debugging
  - INFO: General operational information
  - WARNING: Warning messages for potentially problematic situations
  - ERROR: Error messages for serious problems
  - CRITICAL: Critical messages for fatal errors

## Performance Monitoring

The application includes comprehensive performance monitoring:
- Batch processing metrics
- Concurrent task tracking
- Memory usage monitoring
- Resource cleanup status
- Queue performance metrics
- API response times
- Conversion history statistics
- System resource utilization (CPU, memory, disk)
- Request/response timing
- Route performance tracking 