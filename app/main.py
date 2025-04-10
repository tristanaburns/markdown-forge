"""
Main Flask application module for Markdown Forge.
Handles routing and application configuration.
"""

import os
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pathlib import Path

# Import error handler
from utils.error_handler import register_error_handlers, ValidationError, NotFoundError, ConversionError

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config.update(
    UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'uploads'),
    CONVERTED_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'converted'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
    ALLOWED_EXTENSIONS={'md', 'markdown', 'mdown'}
)

# Ensure upload and converted directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
Path(app.config['CONVERTED_FOLDER']).mkdir(parents=True, exist_ok=True)

# Register error handlers
register_error_handlers(app)

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Redirect to upload page."""
    return render_template('upload.html')

@app.route('/upload')
def upload():
    """Render upload page."""
    return render_template('upload.html')

@app.route('/files')
def files():
    """Render files list page."""
    return render_template('files.html')

@app.route('/preview/<file_id>')
def preview(file_id):
    """Render preview page for a specific file."""
    return render_template('preview.html', file_id=file_id)

@app.route('/api/files', methods=['GET'])
def list_files():
    """List all converted files."""
    try:
        files = []
        for file in os.listdir(app.config['CONVERTED_FOLDER']):
            if file.endswith('.html'):  # Only list HTML files as they're our primary format
                file_path = os.path.join(app.config['CONVERTED_FOLDER'], file)
                files.append({
                    'id': os.path.splitext(file)[0],
                    'name': file,
                    'size': os.path.getsize(file_path),
                    'created_at': os.path.getctime(file_path)
                })
        return jsonify({'files': files})
    except Exception as e:
        # Use the error handler
        raise ConversionError(f"Error listing files: {str(e)}")

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
    """Convert uploaded Markdown file."""
    try:
        if 'file' not in request.files:
            raise ValidationError('No file provided')
        
        file = request.files['file']
        if file.filename == '':
            raise ValidationError('No file selected')
        
        if not allowed_file(file.filename):
            raise ValidationError('Invalid file type. Only Markdown files (.md, .markdown, .mdown) are allowed')
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # TODO: Implement file conversion logic
        # This will be implemented in the next step
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_id': os.path.splitext(filename)[0]
        })
    except ValidationError:
        # Re-raise ValidationError to be handled by the error handler
        raise
    except Exception as e:
        # Use the error handler
        raise ConversionError(f"Error converting file: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True) 