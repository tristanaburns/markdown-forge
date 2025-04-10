"""
Format validator utility for Markdown Forge.
This module provides functions for validating file formats.
"""

import logging
import mimetypes
import os
from typing import List, Dict, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Supported input formats
SUPPORTED_INPUT_FORMATS = {
    "text/markdown": [".md", ".markdown"],
    "text/html": [".html", ".htm"],
    "application/pdf": [".pdf"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "text/csv": [".csv"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
}

# Supported output formats
SUPPORTED_OUTPUT_FORMATS = {
    "html": ["text/html", ".html"],
    "pdf": ["application/pdf", ".pdf"],
    "docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"],
    "png": ["image/png", ".png"],
    "csv": ["text/csv", ".csv"],
    "xlsx": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"],
    "md": ["text/markdown", ".md"],
}

# Format conversion matrix
# Key: input format, Value: list of supported output formats
FORMAT_CONVERSION_MATRIX = {
    "text/markdown": ["html", "pdf", "docx", "png", "csv", "xlsx"],
    "text/html": ["md", "pdf", "docx", "png"],
    "application/pdf": ["md", "html", "docx", "png"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ["md", "html", "pdf", "png"],
    "text/csv": ["md", "html", "xlsx"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ["md", "html", "csv"],
}

class FormatValidationError(Exception):
    """Exception raised for format validation errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def get_mime_type(file_path: str) -> str:
    """
    Get the MIME type of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: MIME type of the file
    """
    # Get file extension
    _, ext = os.path.splitext(file_path)
    
    # Try to guess MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    
    # If MIME type is not found, try to determine from extension
    if not mime_type:
        for mime, extensions in SUPPORTED_INPUT_FORMATS.items():
            if ext.lower() in extensions:
                mime_type = mime
                break
    
    # If still not found, use application/octet-stream
    if not mime_type:
        mime_type = "application/octet-stream"
        
    return mime_type

def is_supported_input_format(mime_type: str) -> bool:
    """
    Check if a MIME type is a supported input format.
    
    Args:
        mime_type: MIME type to check
        
    Returns:
        bool: True if the format is supported, False otherwise
    """
    return mime_type in SUPPORTED_INPUT_FORMATS

def is_supported_output_format(format: str) -> bool:
    """
    Check if a format is a supported output format.
    
    Args:
        format: Format to check
        
    Returns:
        bool: True if the format is supported, False otherwise
    """
    return format in SUPPORTED_OUTPUT_FORMATS

def get_supported_output_formats(mime_type: str) -> List[str]:
    """
    Get the list of supported output formats for a given input MIME type.
    
    Args:
        mime_type: Input MIME type
        
    Returns:
        List[str]: List of supported output formats
    """
    if mime_type not in FORMAT_CONVERSION_MATRIX:
        return []
    
    return FORMAT_CONVERSION_MATRIX[mime_type]

def validate_input_format(file_path: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate the input format of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple[bool, str, Optional[str]]: (is_valid, mime_type, error_message)
    """
    try:
        # Get MIME type
        mime_type = get_mime_type(file_path)
        
        # Check if format is supported
        if not is_supported_input_format(mime_type):
            return False, mime_type, f"Unsupported input format: {mime_type}"
            
        return True, mime_type, None
        
    except Exception as e:
        logger.error(f"Error validating input format: {str(e)}")
        return False, "application/octet-stream", f"Error validating input format: {str(e)}"

def validate_output_formats(mime_type: str, formats: List[str]) -> Tuple[bool, List[str], Optional[str]]:
    """
    Validate the output formats for a given input MIME type.
    
    Args:
        mime_type: Input MIME type
        formats: List of output formats to validate
        
    Returns:
        Tuple[bool, List[str], Optional[str]]: (is_valid, valid_formats, error_message)
    """
    try:
        # Get supported output formats
        supported_formats = get_supported_output_formats(mime_type)
        
        # Check if all requested formats are supported
        valid_formats = []
        invalid_formats = []
        
        for format in formats:
            if format in supported_formats:
                valid_formats.append(format)
            else:
                invalid_formats.append(format)
                
        # If any format is invalid, return error
        if invalid_formats:
            return False, valid_formats, f"Unsupported output formats: {', '.join(invalid_formats)}"
            
        return True, valid_formats, None
        
    except Exception as e:
        logger.error(f"Error validating output formats: {str(e)}")
        return False, [], f"Error validating output formats: {str(e)}"

def get_file_extension(format: str) -> str:
    """
    Get the file extension for a format.
    
    Args:
        format: Format to get extension for
        
    Returns:
        str: File extension
    """
    if format not in SUPPORTED_OUTPUT_FORMATS:
        return ""
        
    return SUPPORTED_OUTPUT_FORMATS[format][1]

def get_format_from_extension(extension: str) -> Optional[str]:
    """
    Get the format from a file extension.
    
    Args:
        extension: File extension
        
    Returns:
        Optional[str]: Format if found, None otherwise
    """
    for format, (_, ext) in SUPPORTED_OUTPUT_FORMATS.items():
        if extension.lower() == ext.lower():
            return format
            
    return None 