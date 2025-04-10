"""
Main FastAPI application for Markdown Forge.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from pathlib import Path
import os
import logging
from fastapi.responses import JSONResponse

from .routers import files, web, conversion, auth, projects, templates
from .utils.error_handler import register_error_handlers
from .utils.api_docs import custom_openapi, generate_api_docs
from .core.config import settings
from .core.logging import setup_logging
from .services.conversion_queue import ConversionQueue
from .database import engine, Base

# Configure logging
logger = logging.getLogger(__name__)
setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="Markdown Forge",
    description="""
    # Markdown Forge API
    
    A comprehensive API for converting Markdown files to various formats.
    
    ## Features
    
    - File management (upload, list, delete, rename)
    - File conversion (HTML, PDF, DOCX, PNG)
    - Conversion status tracking
    - Project management
    
    ## Authentication
    
    All endpoints require authentication using JWT tokens.
    Include the token in the Authorization header:
    
    ```
    Authorization: Bearer <token>
    ```
    
    ## Rate Limiting
    
    API endpoints are rate-limited to prevent abuse:
    
    - File operations: 10 requests per minute
    - Conversion operations: 5 requests per minute
    - Other operations: 30 requests per minute
    
    ## Error Handling
    
    All errors follow a standard format:
    
    ```json
    {
      "code": "ERROR_CODE",
      "message": "Human readable message",
      "details": "Additional error details (optional)"
    }
    ```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize conversion queue
conversion_queue = ConversionQueue()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Start the conversion queue on application startup."""
    logger.info("Starting conversion queue")
    await conversion_queue.start()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Stop the conversion queue on application shutdown."""
    logger.info("Stopping conversion queue")
    await conversion_queue.stop()

# Include routers
app.include_router(web.router)
app.include_router(files.router, prefix="/api/v1")
app.include_router(conversion.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")

# Register error handlers
register_error_handlers(app)

# Generate custom OpenAPI schema
custom_openapi(
    app=app,
    title="Markdown Forge API",
    version="1.0.0",
    description="A comprehensive API for converting Markdown files to various formats."
)

# Custom documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI documentation."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Markdown Forge API - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_favicon_url="/static/favicon.ico",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """ReDoc documentation."""
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Markdown Forge API - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.ico",
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_json():
    """Get OpenAPI schema as JSON."""
    return app.openapi_schema

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# Generate API documentation files
@app.on_event("startup")
async def generate_docs():
    """Generate API documentation files on startup."""
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
    generate_api_docs(app, docs_dir)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "Markdown Forge API for converting markdown files to various formats",
        "docs": "/docs",
        "redoc": "/redoc",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 