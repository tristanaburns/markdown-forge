/**
 * @file upload.js
 * @description Handles file upload functionality for the Markdown Forge application
 * @module upload
 */

// DOM Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const uploadForm = document.getElementById('uploadForm');
const uploadButton = document.getElementById('uploadButton');

// State
let files = [];
let progressTracker;

/**
 * Initializes the upload page
 * @function init
 */
function init() {
    setupEventListeners();
    progressTracker = createProgressTracker();
}

/**
 * Sets up event listeners for the upload page
 * @function setupEventListeners
 */
function setupEventListeners() {
    // Drag and drop events
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Form submission
    uploadForm.addEventListener('submit', handleFormSubmit);
}

/**
 * Handles drag over event
 * @function handleDragOver
 * @param {DragEvent} e - The drag event
 */
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add('border-primary');
}

/**
 * Handles drag leave event
 * @function handleDragLeave
 * @param {DragEvent} e - The drag event
 */
function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('border-primary');
}

/**
 * Handles drop event
 * @function handleDrop
 * @param {DragEvent} e - The drag event
 */
function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('border-primary');
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    processFiles(droppedFiles);
}

/**
 * Handles file input change event
 * @function handleFileSelect
 * @param {Event} e - The change event
 */
function handleFileSelect(e) {
    const selectedFiles = Array.from(e.target.files);
    processFiles(selectedFiles);
}

/**
 * Processes files for upload
 * @function processFiles
 * @param {File[]} newFiles - Array of files to process
 */
async function processFiles(newFiles) {
    // Validate files
    const { validFiles, invalidFiles } = await validateFiles(newFiles);
    
    // Show errors for invalid files
    if (invalidFiles.length > 0) {
        invalidFiles.forEach(({ file, error }) => {
            showError(`Invalid file: ${file.name} - ${error}`, 'warning');
        });
    }
    
    if (validFiles.length === 0) {
        return;
    }
    
    // Add to files array
    files = [...files, ...validFiles];
    
    // Update UI
    updateFileList();
    updateUploadButton();
}

/**
 * Updates the file list display
 * @function updateFileList
 */
function updateFileList() {
    fileList.innerHTML = '';
    
    if (files.length === 0) {
        return;
    }
    
    const ul = document.createElement('ul');
    ul.className = 'list-group';
    
    files.forEach((file, index) => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        
        const fileInfo = document.createElement('div');
        fileInfo.innerHTML = `
            <span class="fw-bold">${escapeHtml(file.name)}</span>
            <span class="badge bg-secondary rounded-pill ms-2">${formatFileSize(file.size)}</span>
        `;
        
        const removeButton = document.createElement('button');
        removeButton.className = 'btn btn-sm btn-outline-danger';
        removeButton.innerHTML = '<i class="bi bi-x"></i>';
        removeButton.addEventListener('click', () => removeFile(index));
        
        li.appendChild(fileInfo);
        li.appendChild(removeButton);
        ul.appendChild(li);
    });
    
    fileList.appendChild(ul);
}

/**
 * Removes a file from the list
 * @function removeFile
 * @param {number} index - Index of the file to remove
 */
function removeFile(index) {
    files.splice(index, 1);
    updateFileList();
    updateUploadButton();
}

/**
 * Updates the upload button state
 * @function updateUploadButton
 */
function updateUploadButton() {
    uploadButton.disabled = files.length === 0;
}

/**
 * Handles form submission
 * @function handleFormSubmit
 * @param {Event} e - The submit event
 */
async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (files.length === 0) {
        showError('Please select at least one Markdown file to upload');
        return;
    }
    
    // Get selected formats
    const formatCheckboxes = document.querySelectorAll('input[name="formats"]:checked');
    const formats = Array.from(formatCheckboxes).map(cb => cb.value);
    
    if (formats.length === 0) {
        showError('Please select at least one output format');
        return;
    }
    
    // Check if Pandoc should be used
    const usePandoc = document.getElementById('usePandocToggle')?.checked || false;
    
    // Initialize progress tracker
    progressTracker.init(files.length, files.map(file => `Uploading ${file.name}`));
    
    try {
        // Create FormData
        const formData = new FormData();
        
        // Add files
        files.forEach(file => {
            formData.append('files', file);
        });
        
        // Add formats
        formats.forEach(format => {
            formData.append('formats', format);
        });
        
        // Add Pandoc flag
        formData.append('usePandoc', usePandoc);
        
        // Send request with progress tracking
        const result = await trackUploadProgress('/api/upload', {
            method: 'POST',
            body: formData
        }, progressTracker);
        
        // Show success message
        progressTracker.complete('Upload successful! Redirecting...');
        showError('Upload successful! Redirecting...', 'success');
        
        // Redirect to files page
        setTimeout(() => {
            window.location.href = '/files';
        }, 1500);
        
    } catch (error) {
        console.error('Upload error:', error);
        showError(error.message || 'An error occurred during upload');
        progressTracker.hide();
    }
}

/**
 * Shows an error message
 * @function showError
 * @param {string} message - The error message to display
 */
function showError(message, type = 'danger') {
    // Use the global showError function from error.js
    window.showError(message, type);
}

/**
 * Formats file size in bytes to a human-readable string
 * @function formatFileSize
 * @param {number} bytes - File size in bytes
 * @returns {string} - Formatted file size
 */
function formatFileSize(bytes) {
    // Use the global formatFileSize function from file-validation.js
    return window.formatFileSize(bytes);
}

/**
 * Escapes HTML special characters
 * @function escapeHtml
 * @param {string} unsafe - The string to escape
 * @returns {string} - Escaped string
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Initialize the upload page
document.addEventListener('DOMContentLoaded', init); 