# Markdown Forge

A modern web application for converting Markdown files to various formats, built with Flask (frontend) and FastAPI (backend).

## Project Structure

```
markdown-forge/
├── app/                    # Frontend Flask application
│   ├── static/            # Static assets (CSS, JS, images)
│   │   ├── css/           # CSS stylesheets
│   │   │   ├── components/ # Reusable component styles
│   │   │   └── style.css  # Main stylesheet
│   │   └── js/            # JavaScript files
│   │       ├── components/ # Reusable component scripts
│   │       └── utils/     # Utility scripts
│   │       └── main.js    # Main JavaScript file
│   ├── templates/         # Jinja2 templates
│   │   ├── components/    # Reusable template components
│   │   ├── errors/       # Error page templates
│   │   └── base.html     # Base template
│   ├── views/             # Standalone HTML views
│   ├── services/          # Frontend services
│   ├── utils/             # Frontend utilities
│   └── main.py            # Flask application entry point
│
├── backend/               # Backend FastAPI application
│   ├── api/              # API endpoints
│   ├── core/             # Core functionality
│   ├── models/           # Database models
│   ├── services/         # Backend services
│   ├── utils/            # Backend utilities
│   └── main.py           # FastAPI application entry point
│
├── requirements/          # Project requirements and documentation
├── tests/                # Test files
├── docker/               # Docker configuration
└── scripts/              # Utility scripts
```

## Features

- Modern web interface with responsive design
- RESTful API for file operations and conversions
- Markdown to multiple format conversion:
  - HTML
  - PDF
  - DOCX
  - PNG
  - CSV
  - XLSX
- Reverse conversion from multiple formats to Markdown:
  - HTML to Markdown
  - PDF to Markdown
  - DOCX to Markdown
  - CSV to Markdown
  - XLSX to Markdown
- File management (upload, list, rename, delete)
- Conversion status tracking
- Comprehensive error handling
- Advanced error recovery system with multiple strategies
- Conversion queue with concurrent processing
- Conversion templates for customizable output
- Rate limiting for API endpoints
- Docker containerization
- Comprehensive test suite
- Loading indicators for asynchronous operations
- Responsive design for all devices

## UI Components

### Loading Indicator

The application includes a reusable loading indicator component that can be used to show loading states during asynchronous operations.

#### Usage in Templates

```html
{% from 'components/loading.html' import loading_overlay %}
{{ loading_overlay() }}
```

#### JavaScript API

```javascript
// Show default loading overlay
showLoading('Processing your request...');

// Hide loading overlay
hideLoading();

// Show custom loading overlay
showCustomLoading('Converting file...');

// Hide custom loading overlay
hideCustomLoading();
```

#### CSS Customization

The loading indicator styles can be customized by modifying the `app/static/css/components/loading.css` file.

### Error Handling

The application includes a comprehensive error handling system for both server-side and client-side errors.

#### Server-Side Error Handling

The application uses custom exception classes and error handlers to provide consistent error responses:

```python
# Custom exception classes
class ValidationError(AppError):
    """Exception raised for validation errors."""
    
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=400, payload=payload)

class NotFoundError(AppError):
    """Exception raised when a resource is not found."""
    
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=404, payload=payload)

# Usage
raise ValidationError('Invalid file format')
```

#### Client-Side Error Handling

The application includes a client-side error handling utility for handling API errors:

```javascript
// Handle API response
try {
    const response = await fetch('/api/files');
    const data = await handleApiResponse(response);
    // Process data
} catch (error) {
    if (error instanceof ApiError) {
        showError(error.message);
    } else {
        showError('An unexpected error occurred');
    }
}

// Show error message
showError('File upload failed', 'danger', 5000);
```

#### Error Pages

The application includes custom error pages for common HTTP errors:

- 404 Not Found
- 500 Internal Server Error

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

#### Usage

The error recovery system is automatically integrated with the conversion queue:

```python
# The conversion queue automatically applies recovery strategies
await conversion_queue.add_task(file_id, formats, template_id)
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Pandoc 3.1.3+

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/markdown-forge.git
cd markdown-forge
```

2. Set up the frontend (Flask):
```bash
cd app
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the backend (FastAPI):
```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp backend/.env.example backend/.env
# Edit .env with your configuration
```

## Development

1. Start the frontend development server:
```bash
cd app
flask run --debug
```

2. Start the backend development server:
```bash
cd backend
uvicorn main:app --reload
```

3. Access the applications:
- Frontend: http://localhost:5000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

2. Access the applications:
- Frontend: http://localhost:5000
- Backend API: http://localhost:8000

## Testing

1. Run frontend tests:
```bash
cd app
pytest
```

2. Run backend tests:
```bash
cd backend
pytest
```

## API Documentation

The API provides the following endpoints:

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 