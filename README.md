# Markdown Forge

A modern, high-performance document conversion platform with component-based architecture that transforms Markdown files into multiple formats with advanced features for enterprise and personal use.

## Purpose & Vision

Markdown Forge is designed to solve the challenges of document conversion at scale. It provides a reliable, efficient, and feature-rich platform for converting Markdown documents into various formats while maintaining document integrity and styling. The project aims to:

- Enable seamless conversion between Markdown and multiple document formats
- Process conversions efficiently at scale with performance optimization
- Provide a modern, responsive interface for document management
- Offer powerful API access for integration with other systems
- Maintain high reliability with comprehensive error handling and recovery
- Support enterprise requirements with monitoring, metrics, and security features

## Architecture Philosophy

Markdown Forge follows a component-based architecture with strict separation of concerns:

- **Frontend and Backend Autonomy**: The UI (Flask application) and API (FastAPI application) function as independent systems
- **API-Only Communication**: Frontend interacts with backend exclusively through well-defined REST endpoints
- **Independent Development Lifecycle**: Components can be developed, tested, and deployed separately
- **Clear Interface Boundaries**: All component communication follows defined API contracts

## Key Features

### Conversion Capabilities
- **Multiple Format Support**: Convert to HTML, PDF, DOCX, PNG, CSV, XLSX
- **Bidirectional Conversion**: Both Markdown-to-format and format-to-Markdown conversions 
- **Template System**: Customize output with configurable templates
- **Batch Processing**: Process multiple files concurrently with configurable batch size
- **Custom Formatting**: Control conversion options and styling

### Performance & Scalability
- **Concurrent Processing**: Process multiple conversion tasks simultaneously
- **Queue Management**: Intelligent queue system for handling conversion tasks
- **Memory Optimization**: Efficient resource usage for large documents
- **Load Balancing**: Support for horizontal scaling across multiple nodes
- **Resource Monitoring**: Track system resource usage during conversions

### User Experience
- **Modern Interface**: Clean, responsive UI built with modern web standards
- **Real-time Updates**: Live progress tracking for conversion tasks
- **Drag-and-Drop**: Easy file uploading with drag-and-drop support
- **Dark Mode**: Full support for light and dark themes
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### Monitoring & Management
- **Conversion History**: Comprehensive dashboard for tracking all conversion tasks
- **System Metrics**: Real-time monitoring of system performance
- **Error Analytics**: Detailed tracking and reporting of conversion issues
- **Advanced Logging**: Structured logging with context tracking
- **Performance Metrics**: Track conversion times and resource usage

### Advanced Error Handling
- **Recovery Strategies**: Multiple strategies for handling different error types
- **Graceful Degradation**: Continue operation despite partial failures
- **Detailed Reporting**: Comprehensive error information for troubleshooting
- **Automatic Retries**: Intelligent retry system with exponential backoff
- **Alternative Processing**: Fallback to alternative conversion methods when needed

## Project Structure

```
markdown-forge/
├── app/                    # Frontend Flask application
│   ├── static/             # Static assets
│   ├── templates/          # HTML templates
│   ├── utils/              # Utility modules
│   │   ├── logger.py       # Logging utility
│   │   ├── config.py       # Configuration utility
│   │   └── route_helpers.py # Route helper utilities
│   ├── tests/              # Frontend tests
│   └── main.py             # Flask application entry point
├── backend/                # Backend FastAPI application
│   ├── api/                # API endpoints
│   ├── models/             # Data models
│   ├── services/           # Business logic
│   ├── utils/              # Utility functions
│   ├── tests/              # Backend tests
│   └── main.py             # FastAPI application entry point
├── requirements/           # Project requirements and documentation
├── tests/                  # Integration and e2e tests
├── docker/                 # Docker configuration
├── scripts/                # Utility scripts
├── requirements.txt        # Python dependencies
├── run.py                  # Run script for development
└── README.md               # This file
```

## Prerequisites

- Python 3.8+
- Node.js 18+ (for frontend development)
- Docker and Docker Compose (for containerized deployment)
- Pandoc 2.11+ (for document conversion)
- PostgreSQL 15+

## Quick Start

The project includes a convenient run script that simplifies development, testing, and setup:

```bash
# Set up the development environment
python run.py setup

# Run both frontend and backend
python run.py run

# Run just the frontend or backend
python run.py run frontend
python run.py run backend

# Run tests
python run.py test
python run.py test frontend
python run.py test backend
python run.py test unit
python run.py test integration
```

## Manual Installation

### Frontend (Flask)

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Flask application
cd app
flask run
```

### Backend (FastAPI)

```bash
# Create a virtual environment (if not already created)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI application
cd backend
uvicorn main:app --reload
```

### Database Setup

```bash
# Create the database
createdb markdown_forge

# Run migrations
alembic upgrade head
```

## Development

### Frontend

```bash
# Start the Flask development server
cd app
flask run --debug
```

### Backend

```bash
# Start the FastAPI development server
cd backend
uvicorn main:app --reload
```

## Docker Deployment

```bash
# Build and start the containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the containers
docker-compose down
```

## Testing

```bash
# Run all tests
pytest

# Run frontend tests
pytest app/tests

# Run backend tests
pytest backend/tests

# Run with coverage
pytest --cov=app --cov=backend

# Run performance tests
pytest tests/performance

# Run security tests
pytest tests/security
```

## API Documentation

The API documentation is available at `/docs` when the backend is running:

- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/files` | GET | List all files |
| `/api/files` | POST | Upload a file |
| `/api/files/{file_id}` | GET | Get file details |
| `/api/files/{file_id}` | PUT | Update file |
| `/api/files/{file_id}` | DELETE | Delete file |
| `/api/convert` | POST | Convert a file |
| `/api/batch` | POST | Batch convert files |
| `/api/templates` | GET | List templates |
| `/api/templates` | POST | Create template |
| `/api/templates/{template_id}` | GET | Get template |
| `/api/health` | GET | System health check |
| `/api/queue/status` | GET | Get queue status |
| `/api/queue/stats` | GET | Get queue statistics |
| `/api/conversions/active` | GET | Get active conversions |
| `/api/system/metrics` | GET | Get system metrics |

## Logging and Performance Tracking

The application features a comprehensive logging system with:

- Structured JSON logging
- Context tracking across requests
- Performance metrics collection
- Request/response logging
- Batch operation tracking

Use the route helper utilities to automatically add performance tracking and consistent error handling to your routes:

```python
from utils.route_helpers import track_performance, api_request

@app.route('/my-route')
@track_performance(page_name="my_page")
def my_route():
    # This route is automatically instrumented with:
    # - Performance timing
    # - Context tracking
    # - Error handling
    # - Metrics logging
    
    # Use the API request helper for consistent logging
    response = api_request(url="http://api.example.com/endpoint")
    
    return render_template('my-template.html')
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 