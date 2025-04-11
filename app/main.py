"""
Main Flask application module for Markdown Forge.
Handles routing and application configuration.
"""

import os
import uuid
import time
import psutil
import requests
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime, timedelta
import math
import random
import markdown

# Import error handler
from utils.error_handler import register_error_handlers, ValidationError, NotFoundError, ConversionError

# Import configuration and route helpers
from utils.config import Config
from utils.route_helpers import track_performance, api_request

# Configure logger
import logging
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key')

# Configuration
app.config.update(
    UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'uploads'),
    CONVERTED_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'converted'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
    ALLOWED_EXTENSIONS={'md', 'markdown', 'mdown'},
    BATCH_SIZE=5  # Default batch size for processing
)

# Ensure upload and converted directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
Path(app.config['CONVERTED_FOLDER']).mkdir(parents=True, exist_ok=True)

# Register error handlers
register_error_handlers(app)

# Load configuration
config = Config()

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
@track_performance(page_name="index")
def index():
    """
    Display the home page with a list of markdown files
    """
    try:
        # Add request context to logger
        try:
            logger.set_context(page="index", user_id=session.get('user_id', 'anonymous'))
        except AttributeError:
            logger.info("Logger context setting not available")
        
        # Start performance timer
        try:
            logger.start_timer("index_process")
        except AttributeError:
            pass
        
        logger.info("Accessing index page")
        
        try:
            # Start timer for API call
            try:
                logger.start_timer("api_get_files")
            except AttributeError:
                pass
            
            # Get list of files from API
            response = requests.get(f"{config.api.base_url}/files")
            
            # Log performance for API call
            try:
                api_time = logger.stop_timer("api_get_files")
                logger.log_metric("api_get_files_time", api_time, "ms")
            except AttributeError:
                pass
            
            if response.status_code == 200:
                files = response.json()
                logger.info(f"Successfully retrieved {len(files)} files")
                
                # Stop timer and log performance
                try:
                    elapsed = logger.stop_timer("index_process")
                    logger.log_metric("index_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                return render_template('index.html', files=files)
            else:
                logger.error(f"Failed to retrieve files, status: {response.status_code}")
                
                # Stop timer and log performance
                try:
                    elapsed = logger.stop_timer("index_process")
                    logger.log_metric("index_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                return render_template('error.html', message="Failed to retrieve files from the API"), response.status_code
        
        except Exception as e:
            logger.exception(f"Error fetching files: {str(e)}")
            
            # Stop timer and log performance
            try:
                elapsed = logger.stop_timer("index_process")
                logger.log_metric("index_total_time", elapsed, "ms")
            except AttributeError:
                pass
            
            try:
                logger.clear_context()
            except AttributeError:
                pass
            
            return render_template('error.html', message="Error fetching files"), 500
    
    except Exception as e:
        logger.exception(f"Error in index process: {str(e)}")
        
        try:
            logger.clear_context()
        except AttributeError:
            pass
        
        return render_template('error.html', message="Error processing index page"), 500

@app.route('/upload')
@track_performance(page_name="upload")
def upload():
    """
    File upload page route
    """
    try:
        # Add request context to logger
        try:
            logger.set_context(page="upload", user_id=session.get('user_id', 'anonymous'), 
                            method=request.method)
        except AttributeError:
            logger.info("Logger context setting not available")
        
        # Start performance timer
        try:
            logger.start_timer("upload_process")
        except AttributeError:
            pass
        
        # Log page access
        logger.info(f"Accessing upload page via {request.method}")
        
        if request.method == 'POST':
            # Check if the post request has the file part
            if 'file' not in request.files:
                logger.warning("No file part in the request")
                flash('No file part')
                return redirect(request.url)
            
            file = request.files['file']
            
            # If user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                logger.warning("No file selected")
                flash('No selected file')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                logger.info(f"Processing file upload: {file.filename}")
                
                # Call the API to handle the file upload
                files = {'file': (file.filename, file.stream, file.content_type)}
                response = requests.post(f"{config.api.base_url}/files/upload", files=files)
                
                if response.status_code == 200:
                    file_data = response.json()
                    file_id = file_data.get('id')
                    logger.info(f"File uploaded successfully with ID: {file_id}")
                    
                    # Stop timer and log performance
                    try:
                        elapsed = logger.stop_timer("upload_process")
                        logger.log_metric("upload_time", elapsed, "ms")
                        logger.log_metric("file_size", file.tell(), "bytes")
                    except AttributeError:
                        pass
                    
                    try:
                        logger.clear_context()
                    except AttributeError:
                        pass
                    
                    return redirect(url_for('preview', file_id=file_id))
                else:
                    logger.error(f"API upload failed with status: {response.status_code}, {response.text}")
                    
                    # Stop timer and log performance
                    try:
                        elapsed = logger.stop_timer("upload_process")
                        logger.log_metric("failed_upload_time", elapsed, "ms")
                    except AttributeError:
                        pass
                    
                    try:
                        logger.clear_context()
                    except AttributeError:
                        pass
                    
                    flash('Error uploading file')
                    return redirect(request.url)
            else:
                logger.warning(f"Invalid file type: {file.filename}")
                flash('File type not allowed')
                return redirect(request.url)
                
        # For GET requests, just render the template
        result = render_template('upload.html')
        
        # Stop timer and log performance
        try:
            elapsed = logger.stop_timer("upload_process")
            logger.log_metric("page_render_time", elapsed, "ms")
        except AttributeError:
            pass
        
        try:
            logger.clear_context()
        except AttributeError:
            pass
        
        return result
    except Exception as e:
        logger.exception("Error in upload process")
        try:
            logger.clear_context()
        except AttributeError:
            pass
        return render_template('error.html', message="Error processing upload"), 500

@app.route('/files')
def files():
    """Render files list page."""
    return render_template('files.html')

@app.route('/preview/<file_id>')
@track_performance(page_name="preview")
def preview(file_id):
    """
    Preview page for a specific file
    """
    try:
        # Add request context to logger
        try:
            logger.set_context(page="preview", file_id=file_id, user_id=session.get('user_id', 'anonymous'))
        except AttributeError:
            logger.info("Logger context setting not available")
        
        # Start performance timer
        try:
            logger.start_timer("preview_process")
        except AttributeError:
            pass
        
        logger.info(f"Accessing preview page for file: {file_id}")
        
        # Fetch file details from the API
        response = requests.get(f"{config.api.base_url}/files/{file_id}")
        
        if response.status_code == 200:
            file_data = response.json()
            
            # Get the file content for preview
            content_response = requests.get(f"{config.api.base_url}/files/{file_id}/content")
            
            if content_response.status_code == 200:
                file_content = content_response.json().get('content', '')
                
                # Stop timer and log performance
                try:
                    elapsed = logger.stop_timer("preview_process")
                    logger.log_metric("preview_load_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                return render_template('preview.html', 
                                    file=file_data, 
                                    content=file_content,
                                    file_id=file_id)
            else:
                logger.error(f"Failed to get file content, status: {content_response.status_code}")
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                return render_template('error.html', message="Failed to load file content"), 404
        else:
            logger.error(f"Failed to get file data, status: {response.status_code}")
            
            try:
                logger.clear_context()
            except AttributeError:
                pass
            
            return render_template('error.html', message="File not found"), 404
    
    except Exception as e:
        logger.exception(f"Error in preview process: {str(e)}")
        
        try:
            logger.clear_context()
        except AttributeError:
            pass
        
        return render_template('error.html', message="Error processing preview"), 500

@app.route('/conversion-history')
@track_performance(page_name="conversion_history")
def conversion_history():
    """
    Route for displaying conversion history and statistics.
    """
    try:
        # Add request context to logger
        logger.set_context(page="conversion_history", user_id=session.get('user_id', 'anonymous'))
        
        # Start performance timer
        logger.start_timer("conversion_history_render")
        
        # Log page access
        logger.info("Accessing conversion history page")
        
        # Call APIs to get conversion statistics data
        try:
            queue_stats_response = requests.get(f"{config.api.base_url}/queue/stats")
            active_conversions_response = requests.get(f"{config.api.base_url}/conversions/active")
            system_metrics_response = requests.get(f"{config.api.base_url}/system/metrics")
            
            # Log API responses
            logger.debug("API responses received", extra={
                "queue_stats_status": queue_stats_response.status_code,
                "active_conversions_status": active_conversions_response.status_code,
                "system_metrics_status": system_metrics_response.status_code
            })
            
            # Check if all APIs returned successfully
            apis_success = all([
                queue_stats_response.status_code == 200,
                active_conversions_response.status_code == 200,
                system_metrics_response.status_code == 200
            ])
            
            if not apis_success:
                logger.warning("Some API requests failed for conversion history")
        except Exception as api_error:
            logger.error(f"Error fetching data from APIs: {str(api_error)}")
        
        # Render the template
        result = render_template('conversion_history.html')
        
        # Stop timer and log performance
        elapsed = logger.stop_timer("conversion_history_render")
        logger.log_metric("conversion_history_render_time", elapsed, "ms")
        logger.clear_context()
        
        return result
    except Exception as e:
        logger.exception("Error rendering conversion history page")
        logger.clear_context()
        return render_template('error.html', message="Error loading conversion history"), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    """
    API endpoint to list files
    """
    try:
        response = api_request(
            url=f"{config.api.base_url}/files",
            method="GET"
        )
        
        if response and response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to retrieve files"}), 500
    except Exception as e:
        logger.exception("Error in list_files endpoint")
        return jsonify({"error": str(e)}), 500

@app.route('/api/files/<file_id>', methods=['GET'])
def get_file(file_id):
    """Get file content by ID."""
    try:
        file_path = os.path.join(app.config['CONVERTED_FOLDER'], f"{file_id}.html")
        if not os.path.exists(file_path):
            raise NotFoundError(f"File with ID {file_id} not found")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    except NotFoundError:
        # Re-raise NotFoundError to be handled by the error handler
        raise
    except Exception as e:
        # Use the error handler
        raise ConversionError(f"Error retrieving file: {str(e)}")

@app.route('/delete/<file_id>', methods=['GET', 'POST'])
@track_performance(page_name="delete_file")
def delete_file(file_id):
    """
    Delete a markdown file by ID
    """
    try:
        # Add request context to logger
        try:
            logger.set_context(page="delete_file", file_id=file_id, user_id=session.get('user_id', 'anonymous'))
        except AttributeError:
            logger.info("Logger context setting not available")
        
        # Start performance timer
        try:
            logger.start_timer("delete_file_process")
        except AttributeError:
            pass
        
        logger.info(f"Processing delete request for file with ID: {file_id}")
        
        if request.method == 'GET':
            logger.info(f"Displaying delete confirmation for file {file_id}")
            
            try:
                # Start timer for API call
                try:
                    logger.start_timer("api_get_file")
                except AttributeError:
                    pass
                
                # Get file metadata to confirm deletion
                response = requests.get(f"{config.api.base_url}/files/{file_id}")
                
                # Log performance for API call
                try:
                    api_time = logger.stop_timer("api_get_file")
                    logger.log_metric("api_get_file_time", api_time, "ms")
                except AttributeError:
                    pass
                
                if response.status_code != 200:
                    logger.error(f"Failed to retrieve file {file_id} for deletion confirmation, API returned: {response.status_code}")
                    
                    # Stop timer and log performance
                    try:
                        elapsed = logger.stop_timer("delete_file_process")
                        logger.log_metric("delete_file_total_time", elapsed, "ms")
                    except AttributeError:
                        pass
                    
                    try:
                        logger.clear_context()
                    except AttributeError:
                        pass
                    
                    flash(f"File not found: {response.reason}", "error")
                    return redirect(url_for('dashboard'))
                
                file_data = response.json()
                logger.info(f"Retrieved file {file_id} for deletion confirmation")
                
                # Start timer for rendering template
                try:
                    logger.start_timer("render_delete_confirmation")
                except AttributeError:
                    pass
                
                # Render the delete confirmation template
                rendered = render_template('delete.html', file=file_data)
                
                # Log performance for rendering
                try:
                    render_time = logger.stop_timer("render_delete_confirmation")
                    logger.log_metric("render_delete_confirmation_time", render_time, "ms")
                except AttributeError:
                    pass
                
                # Stop main timer and log performance
                try:
                    elapsed = logger.stop_timer("delete_file_process")
                    logger.log_metric("delete_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                return rendered
            
            except requests.RequestException as e:
                logger.exception(f"Network error retrieving file {file_id} for deletion: {str(e)}")
                
                # Stop timer and log performance
                try:
                    elapsed = logger.stop_timer("delete_file_process")
                    logger.log_metric("delete_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                flash(f"Network error: {str(e)}", "error")
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                logger.exception(f"Error retrieving file {file_id} for deletion: {str(e)}")
                
                # Stop timer and log performance
                try:
                    elapsed = logger.stop_timer("delete_file_process")
                    logger.log_metric("delete_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                flash(f"Error: {str(e)}", "error")
                return redirect(url_for('dashboard'))
        
        elif request.method == 'POST':
            logger.info(f"Executing deletion of file {file_id}")
            
            try:
                # Start timer for API call
                try:
                    logger.start_timer("api_delete_file")
                except AttributeError:
                    pass
                
                # Delete the file
                response = requests.delete(f"{config.api.base_url}/files/{file_id}")
                
                # Log performance for API call
                try:
                    api_time = logger.stop_timer("api_delete_file")
                    logger.log_metric("api_delete_file_time", api_time, "ms")
                except AttributeError:
                    pass
                
                # Stop main timer and log performance
                try:
                    elapsed = logger.stop_timer("delete_file_process")
                    logger.log_metric("delete_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                if response.status_code == 200:
                    logger.info(f"Successfully deleted file {file_id}")
                    flash("File deleted successfully", "success")
                else:
                    logger.error(f"Failed to delete file {file_id}, API returned: {response.status_code}")
                    flash(f"Failed to delete file: {response.reason}", "error")
                
                return redirect(url_for('dashboard'))
            
            except requests.RequestException as e:
                logger.exception(f"Network error deleting file {file_id}: {str(e)}")
                
                # Stop timer and log performance
                try:
                    elapsed = logger.stop_timer("delete_file_process")
                    logger.log_metric("delete_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                flash(f"Network error: {str(e)}", "error")
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                logger.exception(f"Error deleting file {file_id}: {str(e)}")
                
                # Stop timer and log performance
                try:
                    elapsed = logger.stop_timer("delete_file_process")
                    logger.log_metric("delete_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                flash(f"Error: {str(e)}", "error")
                return redirect(url_for('dashboard'))
    
    except Exception as e:
        logger.exception(f"Unexpected error in delete file process: {str(e)}")
        
        try:
            elapsed = logger.stop_timer("delete_file_process")
            logger.log_metric("delete_file_total_time", elapsed, "ms")
        except AttributeError:
            pass
        
        try:
            logger.clear_context()
        except AttributeError:
            pass
        
        flash("An unexpected error occurred", "error")
        return redirect(url_for('dashboard'))

@app.route('/api/convert', methods=['POST'])
@track_performance(page_name="api_convert")
def convert_file():
    """Convert uploaded Markdown file with support for multiple output formats."""
    try:
        # Add request context to logger
        try:
            logger.set_context(
                page="api_convert", 
                user_id=session.get('user_id', 'anonymous'),
                file_name=request.files.get('file').filename if 'file' in request.files else None
            )
        except AttributeError:
            logger.info("Logger context setting not available")
        
        # Start performance timer
        try:
            logger.start_timer("convert_file_process")
        except AttributeError:
            pass
        
        logger.info("Processing file conversion request")
        
        try:
            # Validate input
            if 'file' not in request.files:
                logger.warning("No file provided in conversion request")
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                raise ValidationError('No file provided')
            
            file = request.files['file']
            if file.filename == '':
                logger.warning("Empty file name in conversion request")
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                raise ValidationError('No file selected')
            
            if not allowed_file(file.filename):
                logger.warning(f"Invalid file type: {file.filename}")
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                raise ValidationError('Invalid file type. Only Markdown files (.md, .markdown, .mdown) are allowed')
            
            # Get requested formats (default to HTML if none specified)
            formats = request.form.getlist('formats')
            if not formats:
                formats = ['html']
                logger.info("No formats specified, defaulting to HTML")
            else:
                logger.info(f"Requested formats: {', '.join(formats)}")
            
            # Validate formats
            valid_formats = ['html', 'pdf', 'docx', 'png']
            for fmt in formats:
                if fmt not in valid_formats:
                    logger.warning(f"Invalid format requested: {fmt}")
                    
                    try:
                        logger.clear_context()
                    except AttributeError:
                        pass
                    
                    raise ValidationError(f"Invalid format: {fmt}. Supported formats are: {', '.join(valid_formats)}")
            
            # Check if Pandoc should be used
            use_pandoc = request.form.get('usePandoc', 'false').lower() == 'true'
            logger.info(f"Using Pandoc for conversion: {use_pandoc}")
            
            # Generate a unique file ID
            file_id = str(uuid.uuid4())
            logger.add_context(file_id=file_id)
            
            # Start timer for saving file
            try:
                logger.start_timer("file_save")
            except AttributeError:
                pass
            
            # Save the uploaded file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            
            # Log performance for file save
            try:
                save_time = logger.stop_timer("file_save")
                logger.log_metric("file_save_time", save_time, "ms")
                logger.log_metric("file_size", file_size, "bytes")
            except AttributeError:
                pass
            
            logger.info(f"Saved file {filename} ({file_size} bytes) with ID: {file_id}")
            
            # Start timer for conversion
            try:
                logger.start_timer("file_conversion")
            except AttributeError:
                pass
            
            # Conversion logic for each format
            converted_files = []
            for fmt in formats:
                # Start timer for individual format conversion
                try:
                    logger.start_timer(f"convert_to_{fmt}")
                except AttributeError:
                    pass
                
                # TODO: Implement actual file conversion logic for each format
                # This is a placeholder for the conversion logic
                output_path = os.path.join(app.config['CONVERTED_FOLDER'], f"{file_id}.{fmt}")
                
                with open(output_path, 'w') as f:
                    f.write(f"Placeholder for {fmt.upper()} conversion of {filename}")
                
                converted_size = os.path.getsize(output_path)
                
                # Log performance for individual format conversion
                try:
                    fmt_time = logger.stop_timer(f"convert_to_{fmt}")
                    logger.log_metric(f"convert_to_{fmt}_time", fmt_time, "ms")
                    logger.log_metric(f"converted_{fmt}_size", converted_size, "bytes")
                except AttributeError:
                    pass
                
                logger.info(f"Converted file to {fmt} format: {output_path} ({converted_size} bytes)")
                
                converted_files.append({
                    'format': fmt,
                    'path': output_path,
                    'size': converted_size
                })
            
            # Log performance for overall conversion
            try:
                conversion_time = logger.stop_timer("file_conversion")
                logger.log_metric("file_conversion_time", conversion_time, "ms")
            except AttributeError:
                pass
            
            # Prepare response
            response_data = {
                'message': 'File converted successfully',
                'file_id': file_id,
                'original_name': filename,
                'converted_files': converted_files
            }
            
            # Stop main timer and log performance
            try:
                elapsed = logger.stop_timer("convert_file_process")
                logger.log_metric("convert_file_total_time", elapsed, "ms")
            except AttributeError:
                pass
            
            logger.info(f"Successfully converted file {filename} to {len(formats)} formats")
            
            try:
                logger.clear_context()
            except AttributeError:
                pass
            
            return jsonify(response_data)
            
        except ValidationError as ve:
            # Stop main timer and log performance
            try:
                elapsed = logger.stop_timer("convert_file_process")
                logger.log_metric("convert_file_validation_error_time", elapsed, "ms")
            except AttributeError:
                pass
            
            try:
                logger.clear_context()
            except AttributeError:
                pass
            
            # Re-raise ValidationError to be handled by the error handler
            raise
            
        except Exception as e:
            logger.exception(f"Error in file conversion process: {str(e)}")
            
            # Stop main timer and log performance
            try:
                elapsed = logger.stop_timer("convert_file_process")
                logger.log_metric("convert_file_error_time", elapsed, "ms")
            except AttributeError:
                pass
            
            try:
                logger.clear_context()
            except AttributeError:
                pass
            
            # Use the error handler
            raise ConversionError(f"Error converting file: {str(e)}")
    
    except Exception as e:
        logger.exception(f"Unexpected error in convert file process: {str(e)}")
        
        try:
            elapsed = logger.stop_timer("convert_file_process")
            logger.log_metric("convert_file_total_time", elapsed, "ms")
        except AttributeError:
            pass
        
        try:
            logger.clear_context()
        except AttributeError:
            pass
        
        raise ConversionError(f"Unexpected error in file conversion: {str(e)}")

@app.route('/api/convert/batch', methods=['POST'])
def convert_batch():
    """
    Convert multiple Markdown files in a batch.
    
    Accepts:
    - files: List of files to convert
    - formats: List of output formats
    - usePandoc: Whether to use Pandoc for conversion
    - batchSize: Number of files to process in a batch (optional)
    
    Returns a list of conversion results.
    """
    try:
        if 'files[]' not in request.files:
            raise ValidationError('No files provided')
        
        # Get files
        files = request.files.getlist('files[]')
        if not files:
            raise ValidationError('No files selected')
        
        # Get requested formats (default to HTML if none specified)
        formats = request.form.getlist('formats')
        if not formats:
            formats = ['html']
        
        # Validate formats
        valid_formats = ['html', 'pdf', 'docx', 'png']
        for fmt in formats:
            if fmt not in valid_formats:
                raise ValidationError(f"Invalid format: {fmt}. Supported formats are: {', '.join(valid_formats)}")
        
        # Check if Pandoc should be used
        use_pandoc = request.form.get('usePandoc', 'false').lower() == 'true'
        
        # Get batch size (default to app config)
        try:
            batch_size = int(request.form.get('batchSize', app.config['BATCH_SIZE']))
        except ValueError:
            batch_size = app.config['BATCH_SIZE']
        
        # Process files
        results = []
        for file in files:
            if file.filename == '':
                continue
            
            if not allowed_file(file.filename):
                results.append({
                    'name': file.filename,
                    'success': False,
                    'error': 'Invalid file type. Only Markdown files (.md, .markdown, .mdown) are allowed'
                })
                continue
            
            try:
                # Generate a unique file ID
                file_id = str(uuid.uuid4())
                
                # Save the uploaded file
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
                file.save(file_path)
                
                # TODO: Implement actual file conversion logic for each format
                # This is a placeholder for the conversion logic
                converted_files = []
                for fmt in formats:
                    output_path = os.path.join(app.config['CONVERTED_FOLDER'], f"{file_id}.{fmt}")
                    with open(output_path, 'w') as f:
                        f.write(f"Placeholder for {fmt.upper()} conversion of {filename}")
                    converted_files.append({
                        'format': fmt,
                        'path': output_path,
                        'size': os.path.getsize(output_path)
                    })
                
                results.append({
                    'name': filename,
                    'file_id': file_id,
                    'success': True,
                    'converted_files': converted_files
                })
            except Exception as e:
                results.append({
                    'name': file.filename,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'message': 'Batch processing completed',
            'total': len(files),
            'successful': sum(1 for r in results if r.get('success', False)),
            'failed': sum(1 for r in results if not r.get('success', False)),
            'results': results
        })
    except ValidationError:
        # Re-raise ValidationError to be handled by the error handler
        raise
    except Exception as e:
        # Use the error handler
        raise ConversionError(f"Error processing batch: {str(e)}")

@app.route('/api/convert/status', methods=['GET'])
def conversion_status():
    """Get the status of the conversion queue."""
    try:
        # This is a placeholder for real queue status
        # In a real implementation, this would query the conversion queue service
        return jsonify({
            'active': False,
            'queue_length': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0
        })
    except Exception as e:
        # Use the error handler
        raise ConversionError(f"Error retrieving queue status: {str(e)}")

@app.route('/api/conversion/queue/status', methods=['GET'])
def queue_status():
    """
    Get the full status of the conversion queue including active conversions,
    system metrics, and history for the conversion history page.
    """
    try:
        # In a real implementation, we would fetch this data from the backend API
        # For demonstration purposes, we'll fetch from our backend API
        
        # Create base URL for backend API
        backend_url = os.environ.get('BACKEND_API_URL', 'http://localhost:8000')
        
        try:
            # Get queue status
            queue_response = requests.get(f"{backend_url}/api/v1/convert/queue/status")
            queue_data = queue_response.json() if queue_response.status_code == 200 else {
                "queue_length": 0,
                "active_conversions": 0
            }
            
            # Get conversion history
            history_response = requests.get(f"{backend_url}/api/v1/convert/history?limit=20")
            history_data = history_response.json() if history_response.status_code == 200 else {
                "history": [],
                "total_count": 0,
                "success_count": 0,
                "failed_count": 0
            }
            
            # Get system metrics (in a production system, this would come from a monitoring service)
            # For now, we'll use psutil to get system metrics from the current process
            process = psutil.Process()
            
            system_metrics = {
                "cpuUsage": psutil.cpu_percent(),
                "memoryUsage": process.memory_percent(),
                "diskUsage": psutil.disk_usage('/').percent,
                "uptime": int(time.time() - psutil.boot_time())
            }
            
            # Format for the frontend
            stats = {
                'size': queue_data.get("queue_length", 0),
                'completed': history_data.get("success_count", 0),
                'failed': history_data.get("failed_count", 0),
                'processing': queue_data.get("active_conversions", 0)
            }
            
            # Format history data
            history = []
            for item in history_data.get("history", []):
                history.append({
                    'id': str(item.get("id")),
                    'file_name': item.get("file_name", "Unknown"),
                    'output_format': item.get("target_format", ""),
                    'timestamp': item.get("started_at"),
                    'duration': item.get("duration", 0) * 1000,  # Convert to milliseconds
                    'status': "Completed" if item.get("success") else "Failed",
                    'error': item.get("error_message")
                })
            
            # In a real implementation, we would also fetch active conversions
            # For now, use mock data
            active_conversions = [
                {
                    'id': 'task-001',
                    'file_name': 'document1.md',
                    'output_format': 'pdf',
                    'status': 'Processing',
                    'progress': 0.75
                },
                {
                    'id': 'task-002',
                    'file_name': 'report.md',
                    'output_format': 'html',
                    'status': 'Processing',
                    'progress': 0.3
                }
            ]
            
            return jsonify({
                'stats': stats,
                'active_conversions': active_conversions,
                'system_metrics': system_metrics,
                'history': history
            })
            
        except requests.RequestException as e:
            # If backend is not available, use mock data
            logger.warning(f"Backend API not available: {str(e)}")
            
            # Get current timestamp
            now = datetime.now()
            
            # Mock queue stats
            stats = {
                'size': 3,
                'completed': 25,
                'failed': 2,
                'processing': 2
            }
            
            # Mock active conversions
            active_conversions = [
                {
                    'id': 'task-001',
                    'file_name': 'document1.md',
                    'output_format': 'pdf',
                    'status': 'Processing',
                    'progress': 0.75
                },
                {
                    'id': 'task-002',
                    'file_name': 'report.md',
                    'output_format': 'html',
                    'status': 'Processing',
                    'progress': 0.3
                }
            ]
            
            # Mock system metrics
            system_metrics = {
                'cpuUsage': 45,
                'memoryUsage': 38,
                'diskUsage': 62,
                'uptime': 3600 * 24 * 2 + 3600 * 5 + 60 * 23 + 15  # 2 days, 5 hours, 23 minutes, 15 seconds
            }
            
            # Mock conversion history
            history = [
                {
                    'id': 'hist-001',
                    'file_name': 'article.md',
                    'output_format': 'pdf',
                    'timestamp': (now - timedelta(minutes=15)).isoformat(),
                    'duration': 12500,  # 12.5 seconds
                    'status': 'Completed'
                },
                {
                    'id': 'hist-002',
                    'file_name': 'notes.md',
                    'output_format': 'docx',
                    'timestamp': (now - timedelta(minutes=30)).isoformat(),
                    'duration': 8200,  # 8.2 seconds
                    'status': 'Completed'
                },
                {
                    'id': 'hist-003',
                    'file_name': 'complex_doc.md',
                    'output_format': 'epub',
                    'timestamp': (now - timedelta(hours=2)).isoformat(),
                    'duration': 25000,  # 25 seconds
                    'status': 'Failed',
                    'error': 'Conversion error: Invalid content format'
                },
                {
                    'id': 'hist-004',
                    'file_name': 'presentation.md',
                    'output_format': 'html',
                    'timestamp': (now - timedelta(hours=3)).isoformat(),
                    'duration': 5300,  # 5.3 seconds
                    'status': 'Completed'
                },
                {
                    'id': 'hist-005',
                    'file_name': 'readme.md',
                    'output_format': 'html',
                    'timestamp': (now - timedelta(days=1)).isoformat(),
                    'duration': 3200,  # 3.2 seconds
                    'status': 'Completed'
                }
            ]
            
            return jsonify({
                'stats': stats,
                'active_conversions': active_conversions,
                'system_metrics': system_metrics,
                'history': history
            })
            
    except Exception as e:
        # Use the error handler
        raise ConversionError(f"Error retrieving queue status: {str(e)}")

@app.route('/api/conversion/history/clear', methods=['POST'])
def clear_conversion_history():
    """Clear the conversion history."""
    try:
        # In a real implementation, we would clear the history from a database
        # For now, we'll just return success
        return jsonify({
            'success': True,
            'message': 'Conversion history cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error clearing history: {str(e)}"
        })

@app.route('/api/conversion/history/<conversion_id>', methods=['DELETE'])
def remove_history_item(conversion_id):
    """Remove a specific item from the conversion history."""
    try:
        # In a real implementation, we would remove the item from a database
        # For now, we'll just return success
        return jsonify({
            'success': True,
            'message': f'History item {conversion_id} removed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error removing history item: {str(e)}"
        })

@app.route('/api/conversion/<conversion_id>/cancel', methods=['POST'])
def cancel_conversion(conversion_id):
    """Cancel an active conversion."""
    try:
        # In a real implementation, we would cancel the conversion in the backend
        # For now, we'll just return success
        return jsonify({
            'success': True,
            'message': f'Conversion {conversion_id} cancelled successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error cancelling conversion: {str(e)}"
        })

@app.route('/api/conversion/<conversion_id>/retry', methods=['POST'])
def retry_conversion(conversion_id):
    """Retry a failed conversion."""
    try:
        # In a real implementation, we would retry the conversion in the backend
        # For now, we'll just return success
        return jsonify({
            'success': True,
            'message': f'Conversion {conversion_id} retry initiated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrying conversion: {str(e)}"
        })

@app.route('/api/conversion/history', methods=['GET'])
def get_conversion_history():
    """
    Get the conversion history with support for pagination and filtering.
    
    Query parameters:
    - page: Page number (default: 1)
    - limit: Number of items per page (default: 10)
    - status: Filter by status (completed, failed, all)
    - search: Search term for file name or format
    - sort: Sort field (timestamp, file_name, status)
    - order: Sort order (asc, desc)
    """
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        status = request.args.get('status', 'all')
        search = request.args.get('search', '')
        sort = request.args.get('sort', 'timestamp')
        order = request.args.get('order', 'desc')
        
        # Validate parameters
        page = max(1, page)  # Ensure page is at least 1
        limit = min(max(1, limit), 50)  # Ensure limit is between 1 and 50
        
        # In a real implementation, we would fetch this from the backend API
        backend_url = os.environ.get('BACKEND_API_URL', 'http://localhost:8000')
        
        try:
            # Get conversion history from backend
            params = {
                'page': page,
                'limit': limit,
                'status': status,
                'search': search,
                'sort': sort,
                'order': order
            }
            
            history_response = requests.get(
                f"{backend_url}/api/v1/convert/history", 
                params=params
            )
            
            if history_response.status_code == 200:
                return jsonify(history_response.json())
            else:
                # If backend request fails, use mock data
                logger.warning(f"Backend API returned error: {history_response.status_code}")
                raise requests.RequestException("Backend API error")
                
        except requests.RequestException as e:
            # If backend is not available, use mock data
            logger.warning(f"Backend API not available: {str(e)}")
            
            # Get current timestamp
            now = datetime.now()
            
            # Mock conversion history data
            mock_history = [
                {
                    'id': f'hist-{i:03d}',
                    'file_name': f'document{i}.md',
                    'output_format': random.choice(['pdf', 'html', 'docx', 'epub']),
                    'timestamp': (now - timedelta(minutes=i*15)).isoformat(),
                    'duration': random.randint(1000, 30000),  # 1-30 seconds
                    'status': random.choice(['Completed', 'Completed', 'Completed', 'Failed']),
                    'error': 'Conversion error: Invalid content format' if random.random() < 0.25 else None,
                    'options': {
                        'toc': random.choice([True, False]),
                        'numbered_headings': random.choice([True, False]),
                        'include_metadata': random.choice([True, False])
                    }
                }
                for i in range(1, 26)  # Generate 25 items
            ]
            
            # Apply status filter
            if status.lower() != 'all':
                mock_history = [
                    item for item in mock_history 
                    if item['status'].lower() == status.lower()
                ]
            
            # Apply search filter
            if search:
                search = search.lower()
                mock_history = [
                    item for item in mock_history
                    if search in item['file_name'].lower() or search in item['output_format'].lower()
                ]
            
            # Apply sorting
            reverse = order.lower() == 'desc'
            if sort == 'timestamp':
                mock_history.sort(key=lambda x: x['timestamp'], reverse=reverse)
            elif sort == 'file_name':
                mock_history.sort(key=lambda x: x['file_name'].lower(), reverse=reverse)
            elif sort == 'status':
                mock_history.sort(key=lambda x: x['status'], reverse=reverse)
            
            # Apply pagination
            total_items = len(mock_history)
            total_pages = math.ceil(total_items / limit)
            start_index = (page - 1) * limit
            end_index = start_index + limit
            paginated_history = mock_history[start_index:end_index]
            
            # Return response
            return jsonify({
                'history': paginated_history,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total_items': total_items,
                    'total_pages': total_pages
                }
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving conversion history: {str(e)}",
            'history': [],
            'pagination': {
                'page': 1,
                'limit': 10,
                'total_items': 0,
                'total_pages': 0
            }
        })

@app.route('/edit/<file_id>', methods=['GET', 'POST'])
@track_performance(page_name="edit_file")
def edit_file(file_id):
    """Edit a markdown file"""
    try:
        # Add request context to logger
        try:
            logger.set_context(page="edit_file", file_id=file_id, user_id=session.get('user_id', 'anonymous'))
        except AttributeError:
            logger.info("Logger context setting not available")
        
        # Start performance timer
        try:
            logger.start_timer("edit_file_process")
        except AttributeError:
            pass
        
        logger.info(f"Editing file with ID: {file_id}")
        
        if request.method == 'POST':
            # For POST requests, update the file content
            try:
                # Get form data
                title = request.form.get('title', '').strip()
                content = request.form.get('content', '').strip()
                
                if not title:
                    logger.warning("Empty title submitted in edit form")
                    flash("Title cannot be empty", "error")
                    
                    # Start timer for API call
                    try:
                        logger.start_timer("api_get_file")
                    except AttributeError:
                        pass
                    
                    # Get file details from API
                    file_response = requests.get(f"{config.api.base_url}/files/{file_id}")
                    
                    # Log performance for API call
                    try:
                        api_time = logger.stop_timer("api_get_file")
                        logger.log_metric("api_get_file_time", api_time, "ms")
                    except AttributeError:
                        pass
                    
                    if file_response.status_code == 200:
                        file_data = file_response.json()
                        
                        # Start timer for rendering template
                        try:
                            logger.start_timer("render_edit_form")
                        except AttributeError:
                            pass
                        
                        # Render the form again with existing data
                        rendered = render_template(
                            'edit_file.html',
                            file=file_data
                        )
                        
                        # Log performance for rendering
                        try:
                            render_time = logger.stop_timer("render_edit_form")
                            logger.log_metric("render_edit_form_time", render_time, "ms")
                        except AttributeError:
                            pass
                        
                        # Stop main timer and log performance
                        try:
                            elapsed = logger.stop_timer("edit_file_process")
                            logger.log_metric("edit_file_total_time", elapsed, "ms")
                        except AttributeError:
                            pass
                        
                        try:
                            logger.clear_context()
                        except AttributeError:
                            pass
                        
                        return rendered
                    else:
                        logger.error(f"Failed to retrieve file {file_id}, API returned: {file_response.status_code}")
                        
                        # Stop timer and log performance
                        try:
                            elapsed = logger.stop_timer("edit_file_process")
                            logger.log_metric("edit_file_total_time", elapsed, "ms")
                        except AttributeError:
                            pass
                        
                        try:
                            logger.clear_context()
                        except AttributeError:
                            pass
                        
                        flash(f"Failed to retrieve file: {file_response.reason}", "error")
                        return redirect(url_for('dashboard'))
                
                # Prepare request data
                update_data = {
                    'title': title,
                    'content': content
                }
                
                logger.info(f"Updating file {file_id} with new content")
                
                # Start timer for API call
                try:
                    logger.start_timer("api_update_file")
                except AttributeError:
                    pass
                
                # Send update request to API
                response = requests.put(
                    f"{config.api.base_url}/files/{file_id}",
                    json=update_data
                )
                
                # Log performance for API call
                try:
                    api_time = logger.stop_timer("api_update_file")
                    logger.log_metric("api_update_file_time", api_time, "ms")
                except AttributeError:
                    pass
                
                if response.status_code == 200:
                    logger.info(f"Successfully updated file {file_id}")
                    
                    # Stop timer and log performance
                    try:
                        elapsed = logger.stop_timer("edit_file_process")
                        logger.log_metric("edit_file_total_time", elapsed, "ms")
                    except AttributeError:
                        pass
                    
                    try:
                        logger.clear_context()
                    except AttributeError:
                        pass
                    
                    flash('File updated successfully', 'success')
                    return redirect(url_for('view_file', file_id=file_id))
                else:
                    logger.error(f"Failed to update file {file_id}, API returned: {response.status_code}")
                    
                    # Stop timer and log performance
                    try:
                        elapsed = logger.stop_timer("edit_file_process")
                        logger.log_metric("edit_file_total_time", elapsed, "ms")
                    except AttributeError:
                        pass
                    
                    try:
                        logger.clear_context()
                    except AttributeError:
                        pass
                    
                    flash(f"Failed to update file: {response.reason}", "error")
                    return redirect(url_for('edit_file', file_id=file_id))
                    
            except requests.RequestException as e:
                logger.exception(f"Network error updating file {file_id}: {str(e)}")
                
                # Stop timer and log performance
                try:
                    elapsed = logger.stop_timer("edit_file_process")
                    logger.log_metric("edit_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                flash(f"Network error: {str(e)}", "error")
                return redirect(url_for('edit_file', file_id=file_id))
        
        else:
            # For GET requests, load the file and show the edit form
            try:
                # Start timer for API call
                try:
                    logger.start_timer("api_get_file")
                except AttributeError:
                    pass
                
                # Get file details from API
                response = requests.get(f"{config.api.base_url}/files/{file_id}")
                
                # Log performance for API call
                try:
                    api_time = logger.stop_timer("api_get_file")
                    logger.log_metric("api_get_file_time", api_time, "ms")
                except AttributeError:
                    pass
                
                if response.status_code != 200:
                    logger.error(f"Failed to retrieve file {file_id}, API returned: {response.status_code}")
                    
                    # Stop timer and log performance
                    try:
                        elapsed = logger.stop_timer("edit_file_process")
                        logger.log_metric("edit_file_total_time", elapsed, "ms")
                    except AttributeError:
                        pass
                    
                    try:
                        logger.clear_context()
                    except AttributeError:
                        pass
                    
                    flash(f"Failed to retrieve file: {response.reason}", "error")
                    return redirect(url_for('dashboard'))
                
                file_data = response.json()
                
                # Start timer for rendering template
                try:
                    logger.start_timer("render_edit_form")
                except AttributeError:
                    pass
                
                # Render the edit form with file data
                rendered = render_template(
                    'edit_file.html',
                    file=file_data
                )
                
                # Log performance for rendering
                try:
                    render_time = logger.stop_timer("render_edit_form")
                    logger.log_metric("render_edit_form_time", render_time, "ms")
                except AttributeError:
                    pass
                
                # Stop main timer and log performance
                try:
                    elapsed = logger.stop_timer("edit_file_process")
                    logger.log_metric("edit_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                return rendered
                
            except requests.RequestException as e:
                logger.exception(f"Network error retrieving file {file_id}: {str(e)}")
                
                # Stop timer and log performance
                try:
                    elapsed = logger.stop_timer("edit_file_process")
                    logger.log_metric("edit_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                flash(f"Network error: {str(e)}", "error")
                return redirect(url_for('dashboard'))
        
    except Exception as e:
        logger.exception(f"Unexpected error in edit file process: {str(e)}")
        
        try:
            elapsed = logger.stop_timer("edit_file_process")
            logger.log_metric("edit_file_total_time", elapsed, "ms")
        except AttributeError:
            pass
        
        try:
            logger.clear_context()
        except AttributeError:
            pass
        
        flash("An unexpected error occurred", "error")
        return redirect(url_for('dashboard'))

@app.route('/new', methods=['GET', 'POST'])
@track_performance(page_name="new_file")
def new_file():
    """
    Create a new markdown file
    """
    try:
        # Add request context to logger
        try:
            logger.set_context(page="new_file", user_id=session.get('user_id', 'anonymous'))
        except AttributeError:
            logger.info("Logger context setting not available")
        
        # Start performance timer
        try:
            logger.start_timer("new_file_process")
        except AttributeError:
            pass
        
        logger.info("Loading new file page")
        
        if request.method == 'POST':
            title = request.form.get('title', '')
            content = request.form.get('content', '')
            
            if not title:
                logger.warning("Attempted to create file with empty title")
                flash("Title is required", "error")
                
                try:
                    elapsed = logger.stop_timer("new_file_process")
                    logger.log_metric("new_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                return render_template('new_file.html', title=title, content=content)
            
            logger.info(f"Creating new file with title: {title}")
            
            try:
                # Start timer for API call
                try:
                    logger.start_timer("api_create_file")
                except AttributeError:
                    pass
                
                # Create file via API
                response = requests.post(
                    f"{config.api.base_url}/files",
                    json={'title': title, 'content': content}
                )
                
                # Log performance for API call
                try:
                    api_time = logger.stop_timer("api_create_file")
                    logger.log_metric("api_create_file_time", api_time, "ms")
                except AttributeError:
                    pass
                
                if response.status_code != 201:
                    logger.error(f"Failed to create file, API returned: {response.status_code}")
                    flash("Failed to create file", "error")
                    
                    # Stop timer and log performance
                    try:
                        elapsed = logger.stop_timer("new_file_process")
                        logger.log_metric("new_file_total_time", elapsed, "ms")
                    except AttributeError:
                        pass
                    
                    try:
                        logger.clear_context()
                    except AttributeError:
                        pass
                    
                    return render_template('new_file.html', title=title, content=content)
                
                file_data = response.json()
                file_id = file_data.get('id')
                
                if not file_id:
                    logger.error("API response missing file ID")
                    flash("Error creating file: missing file ID", "error")
                    
                    # Stop timer and log performance
                    try:
                        elapsed = logger.stop_timer("new_file_process")
                        logger.log_metric("new_file_total_time", elapsed, "ms")
                    except AttributeError:
                        pass
                    
                    try:
                        logger.clear_context()
                    except AttributeError:
                        pass
                    
                    return render_template('new_file.html', title=title, content=content)
                
                logger.info(f"File created successfully with ID: {file_id}")
                flash("File created successfully", "success")
                
                # Stop timer and log performance
                try:
                    elapsed = logger.stop_timer("new_file_process")
                    logger.log_metric("new_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                return redirect(url_for('view_file', file_id=file_id))
                
            except requests.RequestException as e:
                logger.exception(f"Network error creating file: {str(e)}")
                flash(f"Network error: {str(e)}", "error")
                
                # Stop timer and log performance
                try:
                    elapsed = logger.stop_timer("new_file_process")
                    logger.log_metric("new_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                return render_template('new_file.html', title=title, content=content)
        
        # Start timer for rendering template
        try:
            logger.start_timer("render_new_file")
        except AttributeError:
            pass
        
        # Render the new file template
        rendered = render_template('new_file.html', title='', content='')
        
        # Log performance for rendering
        try:
            render_time = logger.stop_timer("render_new_file")
            logger.log_metric("render_new_file_time", render_time, "ms")
        except AttributeError:
            pass
        
        # Stop main timer and log performance
        try:
            elapsed = logger.stop_timer("new_file_process")
            logger.log_metric("new_file_total_time", elapsed, "ms")
        except AttributeError:
            pass
        
        try:
            logger.clear_context()
        except AttributeError:
            pass
        
        return rendered
        
    except Exception as e:
        logger.exception(f"Unexpected error in new file process: {str(e)}")
        
        try:
            elapsed = logger.stop_timer("new_file_process")
            logger.log_metric("new_file_total_time", elapsed, "ms")
        except AttributeError:
            pass
        
        try:
            logger.clear_context()
        except AttributeError:
            pass
        
        flash("An unexpected error occurred", "error")
        return render_template('new_file.html', title='', content='')

@app.route('/view/<file_id>')
@track_performance(page_name="view_file")
def view_file(file_id):
    """
    View a markdown file
    """
    try:
        # Add request context to logger
        try:
            logger.set_context(page="view_file", file_id=file_id, user_id=session.get('user_id', 'anonymous'))
        except AttributeError:
            logger.info("Logger context setting not available")
        
        # Start performance timer
        try:
            logger.start_timer("view_file_process")
        except AttributeError:
            pass
        
        logger.info(f"Viewing file with ID: {file_id}")
        
        try:
            # Start timer for API call
            try:
                logger.start_timer("api_get_file")
            except AttributeError:
                pass
            
            # Get file details from API
            response = requests.get(f"{config.api.base_url}/files/{file_id}")
            
            # Log performance for API call
            try:
                api_time = logger.stop_timer("api_get_file")
                logger.log_metric("api_get_file_time", api_time, "ms")
            except AttributeError:
                pass
            
            if response.status_code != 200:
                logger.error(f"Failed to retrieve file {file_id}, API returned: {response.status_code}")
                
                # Stop timer and log performance
                try:
                    elapsed = logger.stop_timer("view_file_process")
                    logger.log_metric("view_file_total_time", elapsed, "ms")
                except AttributeError:
                    pass
                
                try:
                    logger.clear_context()
                except AttributeError:
                    pass
                
                flash(f"Failed to retrieve file: {response.reason}", "error")
                return redirect(url_for('dashboard'))
            
            file_data = response.json()
            
            # Convert markdown to HTML
            try:
                logger.start_timer("markdown_conversion")
                content_html = markdown.markdown(
                    file_data.get('content', ''),
                    extensions=['extra', 'codehilite', 'tables', 'toc']
                )
                try:
                    markdown_time = logger.stop_timer("markdown_conversion")
                    logger.log_metric("markdown_conversion_time", markdown_time, "ms")
                except AttributeError:
                    pass
            except Exception as e:
                logger.exception(f"Error converting markdown to HTML: {str(e)}")
                content_html = f"<p>Error rendering markdown: {str(e)}</p>"
            
            # Start timer for rendering template
            try:
                logger.start_timer("render_view_file")
            except AttributeError:
                pass
            
            # Render the template
            rendered = render_template(
                'view_file.html',
                file=file_data,
                content_html=content_html
            )
            
            # Log performance for rendering
            try:
                render_time = logger.stop_timer("render_view_file")
                logger.log_metric("render_view_file_time", render_time, "ms")
            except AttributeError:
                pass
            
            # Stop main timer and log performance
            try:
                elapsed = logger.stop_timer("view_file_process")
                logger.log_metric("view_file_total_time", elapsed, "ms")
            except AttributeError:
                pass
            
            try:
                logger.clear_context()
            except AttributeError:
                pass
            
            return rendered
            
        except requests.RequestException as e:
            logger.exception(f"Network error retrieving file {file_id}: {str(e)}")
            
            # Stop timer and log performance
            try:
                elapsed = logger.stop_timer("view_file_process")
                logger.log_metric("view_file_total_time", elapsed, "ms")
            except AttributeError:
                pass
            
            try:
                logger.clear_context()
            except AttributeError:
                pass
            
            flash(f"Network error: {str(e)}", "error")
            return redirect(url_for('dashboard'))
        
    except Exception as e:
        logger.exception(f"Unexpected error in view file process: {str(e)}")
        
        try:
            elapsed = logger.stop_timer("view_file_process")
            logger.log_metric("view_file_total_time", elapsed, "ms")
        except AttributeError:
            pass
        
        try:
            logger.clear_context()
        except AttributeError:
            pass
        
        flash("An unexpected error occurred", "error")
        return render_template('dashboard.html', files=[], stats={
            'total_files': 0,
            'total_conversions': 0,
            'storage_used': '0 KB',
            'conversion_success_rate': '0%'
        })

@app.route('/dashboard')
@track_performance(page_name="dashboard")
def dashboard():
    """
    Display the user's dashboard with file listings and statistics
    """
    try:
        # Add request context to logger
        try:
            logger.set_context(page="dashboard", user_id=session.get('user_id', 'anonymous'))
        except AttributeError:
            logger.info("Logger context setting not available")
        
        # Start performance timer
        try:
            logger.start_timer("dashboard_process")
        except AttributeError:
            pass
        
        logger.info("Loading dashboard page")
        
        try:
            # Start timer for API call
            try:
                logger.start_timer("api_get_files")
            except AttributeError:
                pass
            
            # Get files from API
            response = requests.get(f"{config.api.base_url}/files")
            
            # Log performance for API call
            try:
                api_time = logger.stop_timer("api_get_files")
                logger.log_metric("api_get_files_time", api_time, "ms")
            except AttributeError:
                pass
            
            if response.status_code != 200:
                logger.error(f"Failed to retrieve files for dashboard, status: {response.status_code}")
                files_data = []
            else:
                files_data = response.json()
                logger.info(f"Retrieved {len(files_data)} files for dashboard")
            
            # Start timer for stats API call
            try:
                logger.start_timer("api_get_stats")
            except AttributeError:
                pass
            
            # Get usage statistics from API
            stats_response = requests.get(f"{config.api.base_url}/statistics")
            
            # Log performance for stats API call
            try:
                stats_api_time = logger.stop_timer("api_get_stats")
                logger.log_metric("api_get_stats_time", stats_api_time, "ms")
            except AttributeError:
                pass
            
            if stats_response.status_code != 200:
                logger.error(f"Failed to retrieve statistics, status: {stats_response.status_code}")
                stats = {
                    'total_files': 0,
                    'total_conversions': 0,
                    'storage_used': '0 KB',
                    'conversion_success_rate': '0%'
                }
            else:
                stats = stats_response.json()
                logger.info("Retrieved statistics for dashboard")
            
            # Start timer for rendering template
            try:
                logger.start_timer("render_dashboard")
            except AttributeError:
                pass
            
            # Render the dashboard template
            rendered = render_template('dashboard.html', files=files_data, stats=stats)
            
            # Log performance for rendering
            try:
                render_time = logger.stop_timer("render_dashboard")
                logger.log_metric("render_dashboard_time", render_time, "ms")
            except AttributeError:
                pass
            
            # Stop main timer and log performance
            try:
                elapsed = logger.stop_timer("dashboard_process")
                logger.log_metric("dashboard_total_time", elapsed, "ms")
            except AttributeError:
                pass
            
            try:
                logger.clear_context()
            except AttributeError:
                pass
            
            return rendered
        
        except requests.RequestException as e:
            logger.exception(f"Network error retrieving data for dashboard: {str(e)}")
            
            # Stop timer and log performance
            try:
                elapsed = logger.stop_timer("dashboard_process")
                logger.log_metric("dashboard_total_time", elapsed, "ms")
            except AttributeError:
                pass
            
            try:
                logger.clear_context()
            except AttributeError:
                pass
            
            flash(f"Network error: {str(e)}", "error")
            return render_template('dashboard.html', files=[], stats={
                'total_files': 0,
                'total_conversions': 0,
                'storage_used': '0 KB',
                'conversion_success_rate': '0%'
            })
            
        except Exception as e:
            logger.exception(f"Error retrieving data for dashboard: {str(e)}")
            
            # Stop timer and log performance
            try:
                elapsed = logger.stop_timer("dashboard_process")
                logger.log_metric("dashboard_total_time", elapsed, "ms")
            except AttributeError:
                pass
            
            try:
                logger.clear_context()
            except AttributeError:
                pass
            
            flash(f"Error: {str(e)}", "error")
            return render_template('dashboard.html', files=[], stats={
                'total_files': 0,
                'total_conversions': 0,
                'storage_used': '0 KB',
                'conversion_success_rate': '0%'
            })
    
    except Exception as e:
        logger.exception(f"Unexpected error in dashboard process: {str(e)}")
        
        try:
            logger.clear_context()
        except AttributeError:
            pass
        
        flash("An unexpected error occurred", "error")
        return render_template('dashboard.html', files=[], stats={
            'total_files': 0,
            'total_conversions': 0,
            'storage_used': '0 KB',
            'conversion_success_rate': '0%'
        })

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"404 error: {request.path}", extra={"remote_addr": request.remote_addr})
    return render_template('error.html', message="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error: {str(e)}", extra={"remote_addr": request.remote_addr})
    return render_template('error.html', message="Server error"), 500

if __name__ == '__main__':
    app.run(debug=config.debug, host='0.0.0.0', port=5000) 