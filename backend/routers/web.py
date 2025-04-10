"""
Web routes for Markdown Forge.
This module handles rendering of HTML templates.
"""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

# Initialize router
router = APIRouter(tags=["web"])

# Initialize templates
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the index page."""
    return templates.TemplateResponse("base.html", {"request": request})

@router.get("/upload", response_class=HTMLResponse)
async def upload(request: Request):
    """Render the upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})

@router.get("/files", response_class=HTMLResponse)
async def files(request: Request):
    """Render the files page."""
    return templates.TemplateResponse("files.html", {"request": request})

@router.get("/preview/{file_id}", response_class=HTMLResponse)
async def preview(request: Request, file_id: int):
    """Render the preview page for a specific file."""
    return templates.TemplateResponse(
        "preview.html",
        {"request": request, "file_id": file_id}
    ) 