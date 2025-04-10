/**
 * @file files.js
 * @description Handles file management functionality for the Markdown Forge application
 * @module files
 */

// DOM Elements
const filesTable = document.querySelector('.table-responsive table tbody');
const emptyState = document.querySelector('.card-body.text-center');
const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
const deleteFileName = document.getElementById('deleteFileName');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const previewModal = new bootstrap.Modal(document.getElementById('previewModal'));
const previewContent = document.getElementById('previewContent');

// State
let currentFileId = null;
let files = [];

/**
 * Initialize the files page
 */
function init() {
    fetchFiles();
    setupEventListeners();
}

/**
 * Set up event listeners for file management actions
 */
function setupEventListeners() {
    // Delete confirmation modal
    confirmDeleteBtn.addEventListener('click', handleDelete);
    
    // Close modal when clicking cancel or outside
    document.querySelectorAll('[data-bs-dismiss="modal"]').forEach(button => {
        button.addEventListener('click', () => {
            currentFileId = null;
        });
    });
}

/**
 * Fetch and display the list of files
 */
async function fetchFiles() {
    try {
        showLoading('Loading files...');
        const response = await fetch('/api/v1/files');
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to fetch files');
        }
        
        files = await response.json();
        displayFiles(files);
    } catch (error) {
        console.error('Error fetching files:', error);
        showError('Failed to load files. Please try again.');
    } finally {
        hideLoading();
    }
}

/**
 * Display the list of files in the table
 * @param {Array} files - List of file objects
 */
function displayFiles(files) {
    if (!files || files.length === 0) {
        document.querySelector('.card').style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    document.querySelector('.card').style.display = 'block';
    emptyState.style.display = 'none';

    filesTable.innerHTML = files.map(file => `
        <tr>
            <td>${escapeHtml(file.original_filename)}</td>
            <td>${escapeHtml(file.file_type)}</td>
            <td>
                ${file.converted_formats ? file.converted_formats.map(format => 
                    `<span class="badge bg-success">${escapeHtml(format)}</span>`
                ).join('') : ''}
            </td>
            <td>${formatDate(file.created_at)}</td>
            <td>
                <div class="btn-group">
                    <a href="/preview/${file.id}" 
                       class="btn btn-sm btn-outline-primary"
                       title="Preview">
                        <i class="fas fa-eye"></i>
                    </a>
                    <button type="button"
                            class="btn btn-sm btn-outline-secondary"
                            onclick="convertFile('${file.id}')"
                            title="Convert">
                        <i class="fas fa-exchange-alt"></i>
                    </button>
                    <button type="button"
                            class="btn btn-sm btn-outline-danger"
                            onclick="confirmDelete('${file.id}', '${escapeHtml(file.original_filename)}')"
                            title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

/**
 * Show the delete confirmation modal
 * @param {string} fileId - ID of the file to delete
 * @param {string} fileName - Name of the file to delete
 */
function confirmDelete(fileId, fileName) {
    currentFileId = fileId;
    deleteFileName.textContent = fileName;
    deleteModal.show();
}

/**
 * Handle file deletion
 */
async function handleDelete() {
    if (!currentFileId) return;

    try {
        showLoading('Deleting file...');
        const response = await fetch(`/api/v1/files/${currentFileId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to delete file');
        }

        showAlert('File deleted successfully', 'success');
        fetchFiles();
    } catch (error) {
        console.error('Error deleting file:', error);
        showError('Failed to delete file. Please try again.');
    } finally {
        hideLoading();
        deleteModal.hide();
        currentFileId = null;
    }
}

/**
 * Convert a file to different formats
 * @param {string} fileId - ID of the file to convert
 */
async function convertFile(fileId) {
    try {
        showLoading('Converting file...');
        
        // Get selected formats from checkboxes
        const formatCheckboxes = document.querySelectorAll('input[name="formats"]:checked');
        const formats = Array.from(formatCheckboxes).map(cb => cb.value);
        
        if (formats.length === 0) {
            showError('Please select at least one output format');
            return;
        }
        
        const response = await fetch(`/api/v1/files/${fileId}/convert`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ formats })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to convert file');
        }

        const result = await response.json();
        showAlert('File converted successfully', 'success');
        
        // Update the file list to show new converted formats
        fetchFiles();
        
        // Show conversion status
        showConversionStatus(fileId);
    } catch (error) {
        console.error('Error converting file:', error);
        showError('Failed to convert file. Please try again.');
    } finally {
        hideLoading();
    }
}

/**
 * Show conversion status for a file
 * @param {string} fileId - ID of the file to check status
 */
async function showConversionStatus(fileId) {
    try {
        const response = await fetch(`/api/v1/convert/${fileId}/status`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to get conversion status');
        }
        
        const status = await response.json();
        
        // Create a status modal if it doesn't exist
        let statusModal = document.getElementById('statusModal');
        if (!statusModal) {
            const modalHtml = `
                <div class="modal fade" id="statusModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Conversion Status</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div id="statusContent"></div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            statusModal = document.getElementById('statusModal');
        }
        
        // Update status content
        const statusContent = document.getElementById('statusContent');
        statusContent.innerHTML = `
            <div class="list-group">
                ${Object.entries(status).map(([format, info]) => `
                    <div class="list-group-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <h6 class="mb-0">${format.toUpperCase()}</h6>
                            <span class="badge bg-${info.status === 'completed' ? 'success' : info.status === 'processing' ? 'warning' : 'danger'}">
                                ${info.status}
                            </span>
                        </div>
                        ${info.message ? `<small class="text-muted">${info.message}</small>` : ''}
                    </div>
                `).join('')}
            </div>
        `;
        
        // Show the modal
        const modal = new bootstrap.Modal(statusModal);
        modal.show();
        
        // If any conversions are still processing, check again in 2 seconds
        if (Object.values(status).some(info => info.status === 'processing')) {
            setTimeout(() => showConversionStatus(fileId), 2000);
        }
    } catch (error) {
        console.error('Error getting conversion status:', error);
        showError('Failed to get conversion status. Please try again.');
    }
}

/**
 * Format a date string for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    return new Date(dateString).toLocaleString();
}

/**
 * Escape HTML special characters
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Show a loading overlay
 * @param {string} message - Loading message to display
 */
function showLoading(message) {
    // Implementation depends on your loading overlay component
    console.log('Loading:', message);
}

/**
 * Hide the loading overlay
 */
function hideLoading() {
    // Implementation depends on your loading overlay component
    console.log('Loading complete');
}

/**
 * Show a Bootstrap alert message
 * @param {string} message - Message to display
 * @param {string} type - Alert type (success, danger, etc.)
 * @param {number} duration - Duration in milliseconds
 */
function showAlert(message, type, duration = 3000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, duration);
}

/**
 * Previews a file in the modal
 * @async
 * @function previewFile
 * @param {string} fileId - ID of the file to preview
 */
async function previewFile(fileId) {
    try {
        const response = await fetch(`/api/files/${fileId}/preview`);
        if (!response.ok) {
            throw new Error('Failed to fetch file preview');
        }
        
        const data = await response.json();
        previewContent.innerHTML = data.content;
        previewModal.show();
    } catch (error) {
        console.error('Error previewing file:', error);
        showError('Failed to load file preview. Please try again later.');
    }
}

/**
 * Downloads a file
 * @async
 * @function downloadFile
 * @param {string} fileId - ID of the file to download
 */
async function downloadFile(fileId) {
    try {
        const response = await fetch(`/api/files/${fileId}/download`);
        if (!response.ok) {
            throw new Error('Failed to download file');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = response.headers.get('Content-Disposition')?.split('filename=')[1] || 'download';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Error downloading file:', error);
        showError('Failed to download file. Please try again later.');
    }
}

/**
 * Shows an error message using Bootstrap toast
 * @function showError
 * @param {string} message - Error message to display
 */
function showError(message) {
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-danger border-0';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${escapeHtml(message)}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', init); 