"""
Conversion service for Markdown Forge.
Handles file format conversions using Pandoc.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Converter:
    """Handles file format conversions using Pandoc."""
    
    def __init__(self, pandoc_path: str = "pandoc"):
        """
        Initialize the converter.
        
        Args:
            pandoc_path (str): Path to Pandoc executable
        """
        self.pandoc_path = pandoc_path
        self._validate_pandoc()
    
    def _validate_pandoc(self) -> None:
        """Validate Pandoc installation."""
        try:
            subprocess.run(
                [self.pandoc_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Pandoc validation successful")
        except subprocess.CalledProcessError as e:
            logger.error(f"Pandoc validation failed: {str(e)}")
            raise
        except FileNotFoundError:
            logger.error(f"Pandoc not found at {self.pandoc_path}")
            raise
    
    def convert(
        self,
        input_file: str,
        output_format: str,
        output_dir: str,
        use_pandoc: bool = True,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert a Markdown file to the specified format.
        
        Args:
            input_file (str): Path to input Markdown file
            output_format (str): Desired output format
            output_dir (str): Directory for output files
            use_pandoc (bool): Whether to use Pandoc for conversion
            options (Optional[Dict[str, Any]]): Additional conversion options
        
        Returns:
            str: Path to converted file
        """
        try:
            # Validate input file
            input_path = Path(input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_file}")
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate output filename
            output_file = output_path / f"{input_path.stem}.{output_format}"
            
            if use_pandoc:
                return self._convert_with_pandoc(
                    input_file,
                    output_file,
                    output_format,
                    options
                )
            else:
                return self._convert_without_pandoc(
                    input_file,
                    output_file,
                    output_format,
                    options
                )
        
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            raise
    
    def _convert_with_pandoc(
        self,
        input_file: str,
        output_file: Path,
        output_format: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert file using Pandoc.
        
        Args:
            input_file (str): Path to input file
            output_file (Path): Path to output file
            output_format (str): Output format
            options (Optional[Dict[str, Any]]): Pandoc options
        
        Returns:
            str: Path to converted file
        """
        try:
            # Build Pandoc command
            cmd = [self.pandoc_path, input_file, "-o", str(output_file)]
            
            # Add format-specific options
            if options:
                if output_format == "pdf":
                    cmd.extend(["--pdf-engine=xelatex"])
                elif output_format == "docx":
                    cmd.extend(["--reference-doc", options.get("template", "")])
                elif output_format == "html":
                    cmd.extend(["--standalone", "--self-contained"])
            
            # Execute conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Pandoc conversion successful: {output_file}")
            return str(output_file)
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Pandoc conversion failed: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Pandoc conversion: {str(e)}")
            raise
    
    def _convert_without_pandoc(
        self,
        input_file: str,
        output_file: Path,
        output_format: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert file without using Pandoc.
        
        Args:
            input_file (str): Path to input file
            output_file (Path): Path to output file
            output_format (str): Output format
            options (Optional[Dict[str, Any]]): Conversion options
        
        Returns:
            str: Path to converted file
        """
        try:
            # Read input file
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert based on format
            if output_format == "html":
                converted = self._to_html(content)
            elif output_format == "pdf":
                converted = self._to_pdf(content)
            elif output_format == "docx":
                converted = self._to_docx(content)
            elif output_format == "png":
                converted = self._to_png(content)
            else:
                raise ValueError(f"Unsupported format: {output_format}")
            
            # Write output file
            with open(output_file, 'wb') as f:
                f.write(converted)
            
            logger.info(f"Conversion successful: {output_file}")
            return str(output_file)
        
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            raise
    
    def _to_html(self, content: str) -> bytes:
        """Convert Markdown to HTML."""
        # TODO: Implement HTML conversion
        raise NotImplementedError("HTML conversion not implemented")
    
    def _to_pdf(self, content: str) -> bytes:
        """Convert Markdown to PDF."""
        # TODO: Implement PDF conversion
        raise NotImplementedError("PDF conversion not implemented")
    
    def _to_docx(self, content: str) -> bytes:
        """Convert Markdown to DOCX."""
        # TODO: Implement DOCX conversion
        raise NotImplementedError("DOCX conversion not implemented")
    
    def _to_png(self, content: str) -> bytes:
        """Convert Markdown to PNG."""
        # TODO: Implement PNG conversion
        raise NotImplementedError("PNG conversion not implemented") 