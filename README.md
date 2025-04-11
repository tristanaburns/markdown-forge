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
│   │   ├── css/            # CSS stylesheets
│   │   ├── js/             # JavaScript files
│   │   ├── uploads/        # Upload storage
│   │   └── converted/      # Converted file storage
│   ├── templates/          # HTML templates
│   │   ├── components/     # Reusable components
│   │   └── errors/         # Error pages
│   ├── utils/              # Utility modules
│   │   ├── logger.py       # Logging utility
│   │   ├── config.py       # Configuration utility
│   │   ├── api_client.py   # API client
│   │   ├── error_handler.py # Error handling
│   │   └── route_helpers.py # Route helper utilities
│   ├── routes/             # Route definitions
│   ├── services/           # Frontend services
│   ├── models/             # Frontend data models
│   ├── views/              # Standalone views
│   ├── controllers/        # Request handlers
│   ├── middleware/         # Request/response middleware
│   ├── config/             # Configuration files
│   ├── public/             # Public assets
│   ├── logs/               # Log files
│   ├── tests/              # Frontend tests
│   ├── data/               # Data storage
│   └── main.py             # Flask application entry point
├── backend/                # Backend FastAPI application
│   ├── api/                # API endpoints
│   │   └── routes/         # API routes
│   ├── routers/            # FastAPI router definitions
│   ├── models/             # Database models
│   ├── services/           # Business logic
│   ├── utils/              # Utility functions
│   │   ├── logger.py       # Logging configuration
│   │   ├── error_handler.py # Error handling
│   │   ├── cache.py        # Caching utilities
│   │   └── api_docs.py     # API documentation
│   ├── data/               # Data storage
│   ├── logs/               # Log files
│   ├── tests/              # Backend tests
│   ├── conversion_queue.py # Conversion queue implementation
│   ├── models.py           # Data models
│   ├── config.py           # Configuration
│   ├── database.py         # Database connection
│   ├── auth.py             # Authentication
│   └── main.py             # FastAPI application entry point
├── requirements/           # Project requirements and documentation
│   ├── project-plan.md     # Project planning
│   ├── project-requirements.md # Project requirements
│   └── ad-hoc-prompts.md   # Development instructions
├── docs/                   # Documentation
│   └── api/                # API documentation
├── docker/                 # Docker configuration
│   ├── Dockerfile          # Multi-stage Dockerfile
│   └── README.md           # Docker setup instructions
├── .vscode/                # VS Code configuration
│   └── launch.json         # Launch configurations
├── docker-compose.yml      # Docker Compose configuration
├── .env.development        # Development environment variables
├── run.py                  # Run script for development
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore file
├── .dockerignore           # Docker ignore file
├── Dockerfile              # Root Dockerfile
├── tsconfig.json           # TypeScript configuration
├── .eslintrc.json          # ESLint configuration
├── .prettierrc             # Prettier configuration
├── package.json            # Node.js dependencies
└── README.md               # This file
```

## Prerequisites

- Python 3.10+
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

# Run with debug mode enabled
python run.py run --debug

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

# Set environment variables
cp app/.env.example app/.env

# Run the Flask application
cd app
flask run --debug
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

# Set environment variables
cp backend/.env.example backend/.env

# Run the FastAPI application
cd backend
uvicorn main:app --reload --host=0.0.0.0 --port=8000
```

### Database Setup

```bash
# Create the database
createdb markdown_forge

# Run migrations
cd backend
alembic upgrade head
```

## Development

### Using VS Code

The project includes VS Code launch configurations for easy development:

1. Open the project in VS Code
2. Go to the Run and Debug panel
3. Select one of the launch configurations:
   - "Frontend: Flask" - Run just the frontend
   - "Backend: FastAPI" - Run just the backend
   - "Full Stack: Frontend + Backend" - Run both services

### Debug Mode

Enable debug logging for detailed information:

```bash
# Run with debug mode enabled
python run.py run --debug

# Or set the environment variables manually
export LOG_LEVEL=DEBUG
export FLASK_DEBUG=1
export MARKDOWN_FORGE_ENV=development
```

## Docker Deployment

The project includes a Docker setup for containerized deployment with separate services for the frontend, backend, and PostgreSQL database.

```bash
# Build and start the containers
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for a specific service
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f postgres

# Stop the containers
docker-compose down

# Stop the containers and remove volumes
docker-compose down -v
```

### Docker Configuration

The `docker-compose.yml` file defines three services:

1. **postgres**: PostgreSQL database service
2. **backend**: FastAPI backend service
3. **frontend**: Flask frontend service

Each service is configured with appropriate environment variables, volumes, and network settings to ensure proper communication between components.

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