# Markdown Forge Utilities

This directory contains utility modules for the Markdown Forge frontend application.

## Logger (`logger.py`)

The logger utility provides structured logging with context tracking and performance metrics.

### Features

- **Context Tracking**: Automatically tracks request context including request ID, user ID, page, etc.
- **Performance Metrics**: Timing utilities for tracking code execution time
- **Structured JSON Logging**: Outputs logs in structured JSON format for easy parsing and analysis
- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Batch Operation Logging**: Specialized logging for batch operations
- **Request Logging**: HTTP request logging with timing

### Usage

```python
from utils.logger import get_logger

# Create a logger instance
logger = get_logger(__name__)

# Set context information (usually at the beginning of a request handler)
logger.set_context(page="home", user_id="user123")

# Log messages at different levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# Log exceptions with traceback
try:
    # Some code that might raise an exception
    raise ValueError("Example error")
except Exception as e:
    logger.exception("An error occurred")

# Performance tracking
logger.start_timer("operation")
# Code to measure
result = process_data()
elapsed = logger.stop_timer("operation")  # Returns elapsed time in ms

# Log metrics
logger.log_metric("data_processing_time", elapsed, "ms")
logger.log_metric("items_processed", 100)

# Log batch operations
logger.log_batch_operation("file_conversion", total=10, success=8, failed=2)

# Always clear context at the end of the request
logger.clear_context()
```

## Route Helpers (`route_helpers.py`)

The route helpers module provides decorators and utilities for consistent route handling in Flask applications.

### Features

- **Performance Tracking**: Automatically tracks and logs execution time for routes
- **Error Handling**: Consistent error handling and logging across routes
- **Context Management**: Automatically sets and clears context for each request
- **API Request Helper**: Simplifies making API requests with error handling and logging

### Usage

```python
from flask import Flask, render_template
from utils.route_helpers import track_performance, api_request

app = Flask(__name__)

@app.route('/')
@track_performance(page_name="home")
def index():
    """Home page route"""
    return render_template('index.html')

@app.route('/files')
@track_performance(page_name="files")
def files():
    """Files page route"""
    
    # Make API request with automatic logging
    response = api_request(
        url="https://api.example.com/files",
        method="GET"
    )
    
    if response and response.status_code == 200:
        return render_template('files.html', files=response.json())
    else:
        return render_template('error.html', message="Failed to load files"), 500
```

## Configuration (`config.py`) 

The configuration utility provides a structured way to manage application settings.

### Features

- **Environment-based Configuration**: Load different configurations based on environment
- **Type Safety**: Uses dataclasses to provide type checking for configuration values
- **Hierarchy**: Organized hierarchy of configuration settings (API, Logging, Files, etc.)
- **Directory Creation**: Automatically creates required directories

### Usage

```python
from utils.config import Config

# Load configuration
config = Config()

# Access configuration values
api_url = config.api.base_url
log_level = config.logging.level

# Create a custom configuration
custom_config = Config(
    debug=True,
    api=ApiConfig(base_url="http://custom-api.example.com")
)
```

## Testing

All utilities have corresponding test files in the `tests` directory. Run tests using:

```bash
pytest app/tests/test_logger.py
pytest app/tests/test_route_helpers.py
pytest app/tests/test_config.py
``` 