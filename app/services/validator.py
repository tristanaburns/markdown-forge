"""
Validation service for Markdown Forge.
Handles input validation and sanitization.
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Validator:
    """Handles input validation and sanitization."""
    
    def __init__(
        self,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        allowed_extensions: List[str] = None,
        max_filename_length: int = 255,
        sanitize_filename: bool = True
    ):
        """
        Initialize the validator.
        
        Args:
            max_file_size (int): Maximum file size in bytes
            allowed_extensions (List[str]): List of allowed file extensions
            max_filename_length (int): Maximum filename length
            sanitize_filename (bool): Whether to sanitize filenames
        """
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions or ['.md', '.markdown']
        self.max_filename_length = max_filename_length
        self.sanitize_filename = sanitize_filename
        
        # Compile regex patterns
        self.filename_pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')
        self.markdown_pattern = re.compile(r'^[\x00-\x7F\u0080-\uFFFF\s]*$')
    
    def validate_file(
        self,
        file_path: str,
        file_size: int,
        content: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate a file.
        
        Args:
            file_path (str): Path to the file
            file_size (int): Size of the file in bytes
            content (Optional[str]): File content for validation
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Check file size
            if file_size > self.max_file_size:
                return False, f"File size exceeds maximum of {self.max_file_size} bytes"
            
            # Validate filename
            filename = Path(file_path).name
            if not self._validate_filename(filename):
                return False, "Invalid filename"
            
            # Check extension
            if not self._validate_extension(filename):
                return False, f"File extension not allowed. Allowed extensions: {', '.join(self.allowed_extensions)}"
            
            # Validate content if provided
            if content is not None:
                if not self._validate_content(content):
                    return False, "Invalid file content"
            
            return True, ""
        
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def _validate_filename(self, filename: str) -> bool:
        """
        Validate a filename.
        
        Args:
            filename (str): Filename to validate
        
        Returns:
            bool: Whether the filename is valid
        """
        try:
            # Check length
            if len(filename) > self.max_filename_length:
                return False
            
            # Check pattern
            if not self.filename_pattern.match(filename):
                return False
            
            # Check for path traversal
            if '..' in filename or '/' in filename or '\\' in filename:
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Filename validation error: {str(e)}")
            return False
    
    def _validate_extension(self, filename: str) -> bool:
        """
        Validate a file extension.
        
        Args:
            filename (str): Filename to validate
        
        Returns:
            bool: Whether the extension is valid
        """
        try:
            ext = Path(filename).suffix.lower()
            return ext in self.allowed_extensions
        
        except Exception as e:
            logger.error(f"Extension validation error: {str(e)}")
            return False
    
    def _validate_content(self, content: str) -> bool:
        """
        Validate file content.
        
        Args:
            content (str): Content to validate
        
        Returns:
            bool: Whether the content is valid
        """
        try:
            # Check for valid characters
            if not self.markdown_pattern.match(content):
                return False
            
            # Check for maximum content length
            if len(content) > self.max_file_size:
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Content validation error: {str(e)}")
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename.
        
        Args:
            filename (str): Filename to sanitize
        
        Returns:
            str: Sanitized filename
        """
        try:
            # Remove path components
            filename = Path(filename).name
            
            # Replace invalid characters
            filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
            
            # Ensure filename starts with alphanumeric
            if not filename[0].isalnum():
                filename = 'f_' + filename
            
            # Truncate if too long
            if len(filename) > self.max_filename_length:
                name, ext = os.path.splitext(filename)
                filename = name[:self.max_filename_length - len(ext)] + ext
            
            return filename
        
        except Exception as e:
            logger.error(f"Filename sanitization error: {str(e)}")
            return f"file_{hash(filename)}.md"
    
    def sanitize_content(self, content: str) -> str:
        """
        Sanitize file content.
        
        Args:
            content (str): Content to sanitize
        
        Returns:
            str: Sanitized content
        """
        try:
            # Remove null bytes
            content = content.replace('\0', '')
            
            # Remove invalid characters
            content = ''.join(char for char in content if ord(char) < 0x10000)
            
            # Normalize line endings
            content = content.replace('\r\n', '\n').replace('\r', '\n')
            
            return content
        
        except Exception as e:
            logger.error(f"Content sanitization error: {str(e)}")
            return "" 