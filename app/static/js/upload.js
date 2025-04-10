/**
 * @file upload.js
 * @description Handles batch file upload functionality for the Markdown Forge application
 * @module upload
 */

// DOM Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const filesList = document.getElementById('filesList');
const filesTableBody = document.getElementById('filesTableBody');
const uploadForm = document.getElementById('uploadForm');
const submitBtn = document.getElementById('submitBtn');
const clearAllBtn = document.getElementById('clearAllBtn');
const batchProgress = document.getElementById('batchProgress');
const batchProgressBar = document.getElementById('batchProgressBar');
const batchProgressPercent = document.getElementById('batchProgressPercent');
const batchSizeSelect = document.getElementById('batchSize');

// Format checkboxes
const formatHTML = document.getElementById('formatHTML');
const formatPDF = document.getElementById('formatPDF');
const formatDOCX = document.getElementById('formatDOCX');
const formatPNG = document.getElementById('formatPNG');

// State
let files = [];
let uploadedFiles = 0;
let totalFiles = 0;
let activeBatch = false;

/**
 * Initializes the upload page
 * @function init
 */
function init() {
    setupEventListeners();
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
    
    // Clear all files
    clearAllBtn.addEventListener('click', clearAllFiles);
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
    
    // Reset file input
    fileInput.value = '';
}

/**
 * Processes files for upload
 * @function processFiles
 * @param {File[]} newFiles - Array of files to process
 */
async function processFiles(newFiles) {
    if (activeBatch) {
        showError('Please wait for the current batch to complete before adding more files', 'warning');
        return;
    }
    
    // Filter markdown files
    const markdownFiles = newFiles.filter(file => {
        const extension = file.name.split('.').pop().toLowerCase();
        return ['md', 'markdown', 'mdown'].includes(extension);
    });
    
    // Check for non-markdown files
    if (markdownFiles.length < newFiles.length) {
        showError('Some files were skipped. Only Markdown files (.md, .markdown, .mdown) are allowed', 'warning');
    }
    
    if (markdownFiles.length === 0) {
        return;
    }
    
    // Add files with status
    const newFilesWithStatus = markdownFiles.map(file => ({
        file,
        id: generateFileId(file),
        status: 'ready', // ready, uploading, success, error
        message: '',
        formats: []
    }));
    
    // Add to files array
    files = [...files, ...newFilesWithStatus];
    
    // Update UI
    updateFilesList();
    updateSubmitButton();
}

/**
 * Generates a unique file ID
 * @function generateFileId
 * @param {File} file - The file to generate an ID for
 * @returns {string} - A unique file ID
 */
function generateFileId(file) {
    return `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Updates the files list display
 * @function updateFilesList
 */
function updateFilesList() {
    filesTableBody.innerHTML = '';
    
    if (files.length === 0) {
        filesList.classList.add('d-none');
        return;
    }
    
    filesList.classList.remove('d-none');
    
    files.forEach((fileData, index) => {
        const tr = document.createElement('tr');
        
        // File name
        const nameTd = document.createElement('td');
        nameTd.textContent = fileData.file.name;
        
        // File size
        const sizeTd = document.createElement('td');
        sizeTd.textContent = formatFileSize(fileData.file.size);
        
        // Status
        const statusTd = document.createElement('td');
        const statusBadge = document.createElement('span');
        statusBadge.className = `badge ${getStatusBadgeClass(fileData.status)}`;
        statusBadge.textContent = getStatusText(fileData.status);
        statusTd.appendChild(statusBadge);
        
        if (fileData.message) {
            const statusMessage = document.createElement('small');
            statusMessage.className = 'd-block text-muted mt-1';
            statusMessage.textContent = fileData.message;
            statusTd.appendChild(statusMessage);
        }
        
        // Actions
        const actionsTd = document.createElement('td');
        
        if (fileData.status !== 'uploading') {
            const removeButton = document.createElement('button');
            removeButton.className = 'btn btn-sm btn-outline-danger';
            removeButton.innerHTML = '<i class="fas fa-times"></i>';
            removeButton.addEventListener('click', () => removeFile(index));
            actionsTd.appendChild(removeButton);
        }
        
        if (fileData.status === 'success' && fileData.formats.length > 0) {
            const viewButton = document.createElement('a');
            viewButton.className = 'btn btn-sm btn-outline-primary ms-1';
            viewButton.href = `/preview/${fileData.id}`;
            viewButton.innerHTML = '<i class="fas fa-eye"></i>';
            actionsTd.appendChild(viewButton);
        }
        
        tr.appendChild(nameTd);
        tr.appendChild(sizeTd);
        tr.appendChild(statusTd);
        tr.appendChild(actionsTd);
        
        filesTableBody.appendChild(tr);
    });
}

/**
 * Gets the appropriate status badge class
 * @function getStatusBadgeClass
 * @param {string} status - The file status
 * @returns {string} - The badge class
 */
function getStatusBadgeClass(status) {
    switch (status) {
        case 'ready':
            return 'bg-secondary';
        case 'uploading':
            return 'bg-primary';
        case 'success':
            return 'bg-success';
        case 'error':
            return 'bg-danger';
        default:
            return 'bg-secondary';
    }
}

/**
 * Gets the status text
 * @function getStatusText
 * @param {string} status - The file status
 * @returns {string} - The status text
 */
function getStatusText(status) {
    switch (status) {
        case 'ready':
            return 'Ready';
        case 'uploading':
            return 'Uploading';
        case 'success':
            return 'Success';
        case 'error':
            return 'Error';
        default:
            return 'Unknown';
    }
}

/**
 * Removes a file from the list
 * @function removeFile
 * @param {number} index - Index of the file to remove
 */
function removeFile(index) {
    if (activeBatch) {
        showError('Cannot remove files during active upload', 'warning');
        return;
    }
    
    files.splice(index, 1);
    updateFilesList();
    updateSubmitButton();
}

/**
 * Clears all files from the list
 * @function clearAllFiles
 */
function clearAllFiles() {
    if (activeBatch) {
        showError('Cannot clear files during active upload', 'warning');
        return;
    }
    
    files = [];
    updateFilesList();
    updateSubmitButton();
}

/**
 * Updates the submit button state
 * @function updateSubmitButton
 */
function updateSubmitButton() {
    submitBtn.disabled = files.length === 0 || activeBatch || !isAnyFormatSelected();
}

/**
 * Checks if any output format is selected
 * @function isAnyFormatSelected
 * @returns {boolean} - True if at least one format is selected
 */
function isAnyFormatSelected() {
    return formatHTML.checked || formatPDF.checked || formatDOCX.checked || formatPNG.checked;
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
    
    if (!isAnyFormatSelected()) {
        showError('Please select at least one output format');
        return;
    }
    
    // Get selected formats
    const selectedFormats = [];
    if (formatHTML.checked) selectedFormats.push('html');
    if (formatPDF.checked) selectedFormats.push('pdf');
    if (formatDOCX.checked) selectedFormats.push('docx');
    if (formatPNG.checked) selectedFormats.push('png');
    
    // Get batch size
    let batchSize = parseInt(batchSizeSelect.value, 10);
    if (isNaN(batchSize) || batchSizeSelect.value === 'all') {
        batchSize = files.length;
    }
    
    // Check if Pandoc should be used
    const usePandoc = document.getElementById('usePandoc').checked;
    
    // Set active batch
    activeBatch = true;
    uploadedFiles = 0;
    totalFiles = files.length;
    
    // Update UI
    updateSubmitButton();
    
    // Show batch progress
    batchProgress.classList.remove('d-none');
    batchProgressBar.style.width = '0%';
    batchProgressPercent.textContent = '0%';
    
    // Get ready files
    const filesToUpload = files.filter(f => f.status === 'ready' || f.status === 'error');
    
    // Process files in batches
    try {
        // Create batches
        const batches = [];
        for (let i = 0; i < filesToUpload.length; i += batchSize) {
            batches.push(filesToUpload.slice(i, i + batchSize));
        }
        
        // Process each batch sequentially
        for (let i = 0; i < batches.length; i++) {
            const batch = batches[i];
            await processFileBatch(batch, selectedFormats, usePandoc);
        }
        
        // Upload completed
        showError('All uploads completed successfully!', 'success');
        
    } catch (error) {
        console.error('Upload error:', error);
        showError(error.message || 'An error occurred during upload');
    } finally {
        // Set active batch to false
        activeBatch = false;
        updateSubmitButton();
    }
}

/**
 * Processes a batch of files
 * @function processFileBatch
 * @param {Array} batch - The batch of files to process
 * @param {Array} formats - The selected formats
 * @param {boolean} usePandoc - Whether to use Pandoc
 */
async function processFileBatch(batch, formats, usePandoc) {
    // Process files in parallel within the batch
    const promises = batch.map(fileData => processFile(fileData, formats, usePandoc));
    
    // Wait for all files in the batch to complete
    await Promise.all(promises);
    
    // Return batch completion
    return true;
}

/**
 * Processes a single file
 * @function processFile
 * @param {Object} fileData - The file data object
 * @param {Array} formats - The selected formats
 * @param {boolean} usePandoc - Whether to use Pandoc
 */
async function processFile(fileData, formats, usePandoc) {
    // Update file status
    updateFileStatus(fileData.id, 'uploading');
    
    try {
        // Create FormData
        const formData = new FormData();
        formData.append('file', fileData.file);
        
        // Add formats
        formats.forEach(format => {
            formData.append('formats', format);
        });
        
        // Add Pandoc flag
        formData.append('usePandoc', usePandoc);
        
        // Send request
        const response = await fetch('/api/convert', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Upload failed');
        }
        
        const result = await response.json();
        
        // Update file status
        updateFileStatus(fileData.id, 'success', 'Conversion successful', formats);
        
        // Increment uploaded files
        uploadedFiles++;
        updateBatchProgress();
        
        return result;
        
    } catch (error) {
        console.error(`Error processing file ${fileData.file.name}:`, error);
        updateFileStatus(fileData.id, 'error', error.message || 'Upload failed');
        
        // Increment uploaded files (even if error)
        uploadedFiles++;
        updateBatchProgress();
        
        throw error;
    }
}

/**
 * Updates a file's status
 * @function updateFileStatus
 * @param {string} fileId - The file ID
 * @param {string} status - The new status
 * @param {string} message - Optional status message
 * @param {Array} formats - Optional formats array
 */
function updateFileStatus(fileId, status, message = '', formats = []) {
    const fileIndex = files.findIndex(f => f.id === fileId);
    if (fileIndex !== -1) {
        files[fileIndex].status = status;
        files[fileIndex].message = message;
        if (formats.length > 0) {
            files[fileIndex].formats = formats;
        }
        updateFilesList();
    }
}

/**
 * Updates the batch progress
 * @function updateBatchProgress
 */
function updateBatchProgress() {
    const progress = (uploadedFiles / totalFiles) * 100;
    batchProgressBar.style.width = `${progress}%`;
    batchProgressPercent.textContent = `${Math.round(progress)}%`;
}

/**
 * Shows an error message
 * @function showError
 * @param {string} message - The error message to display
 * @param {string} type - The message type (danger, warning, success)
 */
function showError(message, type = 'danger') {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto dismiss after 5 seconds for non-error alerts
    if (type !== 'danger') {
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

/**
 * Creates an alert container
 * @function createAlertContainer
 * @returns {HTMLElement} - The alert container
 */
function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1050';
    document.body.appendChild(container);
    return container;
}

/**
 * Formats file size in a human-readable format
 * @function formatFileSize
 * @param {number} bytes - The file size in bytes
 * @returns {string} - The formatted file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init); 