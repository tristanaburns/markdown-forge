"""
Markdown converter service for Markdown Forge.
This module provides functionality for converting markdown files to various formats.
"""

import logging
import os
import tempfile
import time
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

from ..utils.format_validator import (
    validate_input_format,
    validate_output_formats,
    get_mime_type,
    FormatValidationError
)
from ..utils.conversion_error_handler import (
    ConversionError,
    ConversionErrorType,
    RecoveryStrategy,
    handle_conversion_error,
    is_recoverable_error,
    get_error_recovery_strategy,
    apply_recovery_strategy
)

# Configure logging
logger = logging.getLogger(__name__)

class MarkdownConverter:
    """Service for converting markdown files to various formats."""
    
    def __init__(self, output_dir: str, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the markdown converter service.
        
        Args:
            output_dir: Directory to store converted files
            max_retries: Maximum number of retry attempts for recoverable errors
            retry_delay: Delay between retry attempts in seconds
        """
        self.output_dir = output_dir
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        os.makedirs(output_dir, exist_ok=True)
        
    def convert(self, file_path: str, formats: List[str], template_id: Optional[int] = None) -> Dict[str, str]:
        """
        Convert a markdown file to the specified formats.
        
        Args:
            file_path: Path to the markdown file
            formats: List of output formats
            template_id: Optional template ID to use for conversion
            
        Returns:
            Dict[str, str]: Dictionary mapping formats to output file paths
            
        Raises:
            ConversionError: If the conversion fails
        """
        try:
            # Validate input format
            is_valid, mime_type, error = validate_input_format(file_path)
            if not is_valid:
                raise ConversionError(
                    message=error or "Invalid input format",
                    error_type=ConversionErrorType.INPUT_VALIDATION,
                    details={"file_path": file_path, "mime_type": mime_type},
                    status_code=400
                )
                
            # Validate output formats
            is_valid, valid_formats, error = validate_output_formats(mime_type, formats)
            if not is_valid:
                raise ConversionError(
                    message=error or "Invalid output formats",
                    error_type=ConversionErrorType.FORMAT_VALIDATION,
                    details={"mime_type": mime_type, "requested_formats": formats},
                    status_code=400
                )
                
            # Create temporary directory for conversion
            with tempfile.TemporaryDirectory() as temp_dir:
                # Convert to each format
                output_files = {}
                for format in valid_formats:
                    output_path = self._convert_to_format_with_retry(file_path, format, temp_dir, template_id)
                    if output_path:
                        output_files[format] = output_path
                        
                return output_files
                
        except Exception as e:
            # Handle the error and re-raise as ConversionError if needed
            error_response = handle_conversion_error(e)
            raise ConversionError(
                message=error_response["message"],
                error_type=ConversionErrorType(error_response["code"]),
                details=error_response["details"],
                status_code=error_response["status_code"]
            )
            
    def _convert_to_format_with_retry(
        self, 
        file_path: str, 
        format: str, 
        temp_dir: str, 
        template_id: Optional[int] = None,
        retry_count: int = 0
    ) -> Optional[str]:
        """
        Convert a file to a specific format with retry logic for recoverable errors.
        
        Args:
            file_path: Path to the input file
            format: Target format
            temp_dir: Temporary directory for conversion
            template_id: Optional template ID to use for conversion
            retry_count: Current retry attempt count
            
        Returns:
            Optional[str]: Path to the converted file if successful, None otherwise
            
        Raises:
            ConversionError: If the conversion fails after all retry attempts
        """
        try:
            # Get output file path
            output_path = os.path.join(self.output_dir, f"{Path(file_path).stem}.{format}")
            
            # Get conversion options
            options = self._get_conversion_options(format, template_id)
            
            # Perform conversion based on format
            if format in ["html", "pdf", "docx"]:
                # Use Pandoc for these formats
                self._convert_with_pandoc(file_path, output_path, format, options)
            elif format == "png":
                # Use Pandoc to convert to HTML first, then use a HTML-to-image converter
                html_path = os.path.join(temp_dir, "temp.html")
                self._convert_with_pandoc(file_path, html_path, "html", options)
                self._convert_html_to_image(html_path, output_path)
            elif format in ["csv", "xlsx"]:
                # Use pandas for these formats
                self._convert_with_pandas(file_path, output_path, format)
            else:
                logger.error(f"Unsupported format: {format}")
                return None
                
            return output_path
            
        except Exception as e:
            # Check if the error is recoverable and we haven't exceeded max retries
            if is_recoverable_error(e) and retry_count < self.max_retries:
                # Get recovery strategy
                strategy = get_error_recovery_strategy(e)
                if strategy:
                    logger.info(f"Retrying conversion with strategy: {strategy.value} (attempt {retry_count + 1}/{self.max_retries})")
                    
                    # Apply recovery strategy
                    result, error = apply_recovery_strategy(
                        strategy,
                        self._convert_to_format_with_retry,
                        file_path,
                        format,
                        temp_dir,
                        template_id,
                        retry_count + 1
                    )
                    
                    if error:
                        # If we got a new error, check if it's recoverable
                        if is_recoverable_error(error) and retry_count + 1 < self.max_retries:
                            # Try a different strategy
                            alternative_strategy = self._get_alternative_strategy(strategy)
                            if alternative_strategy:
                                logger.info(f"Trying alternative strategy: {alternative_strategy.value}")
                                return self._convert_to_format_with_retry(
                                    file_path, 
                                    format, 
                                    temp_dir, 
                                    template_id, 
                                    retry_count + 1
                                )
                        
                        # If we can't recover, raise the error
                        raise error
                    
                    return result
                    
            # If we've exhausted retries or the error is not recoverable, handle it
            error_response = handle_conversion_error(e)
            raise ConversionError(
                message=error_response["message"],
                error_type=ConversionErrorType(error_response["code"]),
                details=error_response["details"],
                status_code=error_response["status_code"],
                recovery_attempts=retry_count,
                recovery_strategy=get_error_recovery_strategy(e)
            )
            
    def _get_alternative_strategy(self, current_strategy: RecoveryStrategy) -> Optional[RecoveryStrategy]:
        """
        Get an alternative recovery strategy if the current one fails.
        
        Args:
            current_strategy: The current recovery strategy
            
        Returns:
            Optional[RecoveryStrategy]: An alternative strategy, or None if none available
        """
        # Map of strategies to alternatives
        alternatives = {
            RecoveryStrategy.RETRY_WITH_TIMEOUT_INCREASE: RecoveryStrategy.RETRY_WITH_SIMPLIFIED_OPTIONS,
            RecoveryStrategy.RETRY_WITH_SIMPLIFIED_OPTIONS: RecoveryStrategy.RETRY_WITH_MEMORY_OPTIMIZATION,
            RecoveryStrategy.RETRY_WITH_MEMORY_OPTIMIZATION: RecoveryStrategy.RETRY_WITH_BACKOFF,
            RecoveryStrategy.RETRY_WITH_NETWORK_RETRY: RecoveryStrategy.RETRY_WITH_BACKOFF,
            RecoveryStrategy.RETRY_WITH_BACKOFF: RecoveryStrategy.FALLBACK_TO_ALTERNATIVE_CONVERTER
        }
        
        return alternatives.get(current_strategy)
            
    def _get_conversion_options(self, format: str, template_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get conversion options for a format.
        
        Args:
            format: Target format
            template_id: Optional template ID to use for conversion
            
        Returns:
            Dict[str, Any]: Dictionary of conversion options
        """
        # Base options for each format
        options = {
            "html": ["--standalone", "--self-contained"],
            "pdf": ["--pdf-engine=weasyprint"],
            "docx": ["--reference-doc=template.docx"],
        }
        
        # Add template-specific options if template_id is provided
        if template_id:
            # TODO: Get template options from template manager
            pass
            
        return options.get(format, {})
        
    def _get_simplified_options(self, format: str) -> Dict[str, Any]:
        """
        Get simplified conversion options for retry attempts.
        
        Args:
            format: Target format
            
        Returns:
            Dict[str, Any]: Dictionary of simplified conversion options
        """
        # Simplified options with fewer features for retry attempts
        simplified_options = {
            "html": ["--standalone"],
            "pdf": ["--pdf-engine=weasyprint", "--no-toc"],
            "docx": [],
        }
        
        return simplified_options.get(format, {})
        
    def _convert_with_pandoc(self, input_path: str, output_path: str, format: str, options: Dict[str, Any]) -> None:
        """
        Convert a file using Pandoc.
        
        Args:
            input_path: Path to the input file
            output_path: Path to the output file
            format: Target format
            options: Dictionary of Pandoc options
            
        Raises:
            ConversionError: If the Pandoc conversion fails
        """
        try:
            # TODO: Implement Pandoc conversion
            # This is a placeholder for the actual implementation
            logger.info(f"Converting {input_path} to {format} using Pandoc")
            logger.debug(f"Pandoc options: {options}")
            
            # Simulate conversion for now
            with open(output_path, 'w') as f:
                f.write(f"Converted {input_path} to {format}")
                
        except Exception as e:
            raise ConversionError(
                message=f"Pandoc conversion failed: {str(e)}",
                error_type=ConversionErrorType.PANDOC_ERROR,
                details={"input_path": input_path, "output_path": output_path, "format": format},
                status_code=500
            )
        
    def _convert_html_to_image(self, html_path: str, output_path: str) -> None:
        """
        Convert HTML to an image.
        
        Args:
            html_path: Path to the HTML file
            output_path: Path to the output image file
            
        Raises:
            ConversionError: If the HTML to image conversion fails
        """
        try:
            # TODO: Implement HTML to image conversion
            # This is a placeholder for the actual implementation
            logger.info(f"Converting {html_path} to image")
            
            # Simulate conversion for now
            with open(output_path, 'w') as f:
                f.write(f"Converted {html_path} to image")
                
        except Exception as e:
            raise ConversionError(
                message=f"HTML to image conversion failed: {str(e)}",
                error_type=ConversionErrorType.UNKNOWN_ERROR,
                details={"html_path": html_path, "output_path": output_path},
                status_code=500
            )
        
    def _convert_with_pandas(self, input_path: str, output_path: str, format: str) -> None:
        """
        Convert a file using pandas.
        
        Args:
            input_path: Path to the input file
            output_path: Path to the output file
            format: Target format
            
        Raises:
            ConversionError: If the pandas conversion fails
        """
        try:
            # TODO: Implement pandas conversion
            # This is a placeholder for the actual implementation
            logger.info(f"Converting {input_path} to {format} using pandas")
            
            # Simulate conversion for now
            with open(output_path, 'w') as f:
                f.write(f"Converted {input_path} to {format} using pandas")
                
        except Exception as e:
            raise ConversionError(
                message=f"Pandas conversion failed: {str(e)}",
                error_type=ConversionErrorType.UNKNOWN_ERROR,
                details={"input_path": input_path, "output_path": output_path, "format": format},
                status_code=500
            ) 