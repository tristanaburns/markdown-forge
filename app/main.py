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

# Import error handler
from utils.error_handler import register_error_handlers, ValidationError, NotFoundError, ConversionError

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
@track_performance(page_name="home")
def index():
    """
    Main landing page route
    """
    try:
        # Add request context to logger
        logger.set_context(page="index", user_id=session.get('user_id', 'anonymous'))
        
        # Start performance timer
        logger.start_timer("render_index")
        
        # Log page access
        logger.info("Accessing index page")
        
        # Get the files from the API
        response = requests.get(f"{config.api.base_url}/files")
        
        if response.status_code == 200:
            files = response.json()
            logger.info(f"Retrieved {len(files)} files from API")
        else:
            files = []
            logger.error(f"Failed to retrieve files from API, status code: {response.status_code}")
        
        # Render the template
        result = render_template('index.html', files=files)
        
        # Stop timer and log performance
        elapsed = logger.stop_timer("render_index")
        logger.log_metric("page_render_time", elapsed, "ms")
        
        # Clear context before returning
        logger.clear_context()
        
        return result
    except Exception as e:
        logger.exception("Error rendering index page")
        logger.clear_context()
        return render_template('error.html', message="Failed to load files"), 500

@app.route('/upload')
@track_performance(page_name="upload")
def upload():
    """
    File upload page route
    """
    try:
        # Add request context to logger
        logger.set_context(page="upload", user_id=session.get('user_id', 'anonymous'), 
                         method=request.method)
        
        # Start performance timer
        logger.start_timer("upload_process")
        
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
                    elapsed = logger.stop_timer("upload_process")
                    logger.log_metric("upload_time", elapsed, "ms")
                    logger.log_metric("file_size", file.tell(), "bytes")
                    logger.clear_context()
                    
                    return redirect(url_for('preview', file_id=file_id))
                else:
                    logger.error(f"API upload failed with status: {response.status_code}, {response.text}")
                    
                    # Stop timer and log performance
                    elapsed = logger.stop_timer("upload_process")
                    logger.log_metric("failed_upload_time", elapsed, "ms")
                    logger.clear_context()
                    
                    flash('Error uploading file')
                    return redirect(request.url)
            else:
                logger.warning(f"Invalid file type: {file.filename}")
                flash('File type not allowed')
                return redirect(request.url)
                
        # For GET requests, just render the template
        result = render_template('upload.html')
        
        # Stop timer and log performance
        elapsed = logger.stop_timer("upload_process")
        logger.log_metric("page_render_time", elapsed, "ms")
        logger.clear_context()
        
        return result
    except Exception as e:
        logger.exception("Error in upload process")
        logger.clear_context()
        return render_template('error.html', message="Error processing upload"), 500

@app.route('/files')
def files():
    """Render files list page."""
    return render_template('files.html')

@app.route('/preview/<file_id>')
@track_performance(page_name="preview")
def preview(file_id):
    """
    File preview page route
    """
    # Add file_id to context
    logger.add_context(file_id=file_id)
    
    # Get file data from API
    response = api_request(
        url=f"{config.api.base_url}/files/{file_id}",
        method="GET"
    )
    
    if response and response.status_code == 200:
        file_data = response.json()
        logger.debug("File retrieved successfully for preview", extra={
            "file_size": len(file_data.get('content', '')),
            "file_name": file_data.get('filename', '')
        })
        return render_template('preview.html', file_id=file_id)
    else:
        status_code = response.status_code if response else "N/A"
        logger.warning(f"Failed to retrieve file for preview", extra={"status_code": status_code})
        return render_template('error.html', message="File not found"), 404

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

@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file by ID."""
    try:
        # Delete all formats of the file
        deleted = False
        for ext in ['.html', '.pdf', '.docx', '.png']:
            file_path = os.path.join(app.config['CONVERTED_FOLDER'], f"{file_id}{ext}")
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted = True
        
        if not deleted:
            raise NotFoundError(f"File with ID {file_id} not found")
            
        return jsonify({'message': 'File deleted successfully'})
    except NotFoundError:
        # Re-raise NotFoundError to be handled by the error handler
        raise
    except Exception as e:
        # Use the error handler
        raise ConversionError(f"Error deleting file: {str(e)}")

@app.route('/api/convert', methods=['POST'])
def convert_file():
    """Convert uploaded Markdown file with support for multiple output formats."""
    try:
        if 'file' not in request.files:
            raise ValidationError('No file provided')
        
        file = request.files['file']
        if file.filename == '':
            raise ValidationError('No file selected')
        
        if not allowed_file(file.filename):
            raise ValidationError('Invalid file type. Only Markdown files (.md, .markdown, .mdown) are allowed')
        
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
        
        return jsonify({
            'message': 'File converted successfully',
            'file_id': file_id,
            'original_name': filename,
            'converted_files': converted_files
        })
    except ValidationError:
        # Re-raise ValidationError to be handled by the error handler
        raise
    except Exception as e:
        # Use the error handler
        raise ConversionError(f"Error converting file: {str(e)}")

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