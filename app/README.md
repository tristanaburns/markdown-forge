# Markdown Forge - Frontend Application

This directory contains the frontend application for Markdown Forge, built with Flask and Bootstrap.

## Overview

The frontend application provides a modern, responsive web interface for:
- Uploading Markdown files
- Converting files to various formats (HTML, PDF, DOCX, PNG)
- Managing converted files
- Previewing converted content

## Directory Structure

```
app/
├── static/            # Static assets
│   ├── css/          # CSS stylesheets
│   ├── js/           # JavaScript files
│   └── img/          # Images and icons
├── templates/         # Jinja2 templates
│   ├── base.html     # Base template with common elements
│   ├── upload.html   # File upload page
│   ├── files.html    # File management page
│   ├── preview.html  # File preview page
│   └── components/   # Reusable template components
├── views/             # Standalone HTML views
├── services/          # Frontend services
├── utils/             # Frontend utilities
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

### Required Environment Variables

- `FLASK_APP`: Path to the Flask application
- `FLASK_ENV`: Environment (development, production)
- `FLASK_DEBUG`: Debug mode (0, 1)
- `API_BASE_URL`: URL of the backend API
- `SECRET_KEY`: Secret key for Flask session

## Running the Application

1. Start the development server:
```bash
flask run --debug
```

2. Access the application:
- Web Interface: http://localhost:5000

## Features

### File Upload
- Drag-and-drop interface
- Multiple file selection
- File type validation
- Progress tracking

### File Management
- List all uploaded files
- Preview converted files
- Download converted files
- Delete files

### File Preview
- Syntax highlighting for code blocks
- MathJax for mathematical expressions
- Mermaid for diagrams
- Responsive layout

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

## Integration with Backend

The frontend communicates with the backend via REST API:

- File upload: `POST /api/v1/files/upload`
- File listing: `GET /api/v1/files`
- File conversion: `POST /api/v1/convert`
- File download: `GET /api/v1/convert/{id}/download`
- File deletion: `DELETE /api/v1/files/{id}`

## Error Handling

The application uses a standardized error handling approach:
- User-friendly error messages
- Logging of errors
- Graceful degradation
- Retry mechanisms for API calls

## Logging

Logging is configured in `utils/logger.py`. Log levels:
- DEBUG: Detailed information for debugging
- INFO: General operational information
- WARNING: Warning messages for potentially problematic situations
- ERROR: Error messages for serious problems
- CRITICAL: Critical messages for fatal errors 