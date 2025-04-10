/**
 * @file preview.js
 * @description Handles file preview functionality for the Markdown Forge application
 * @module preview
 */

// DOM Elements
const fileTitle = document.getElementById('fileTitle');
const previewContent = document.getElementById('previewContent');
const usePandocToggle = document.getElementById('usePandocToggle');
const downloadHtmlBtn = document.getElementById('downloadHtml');
const downloadPdfBtn = document.getElementById('downloadPdf');
const downloadDocxBtn = document.getElementById('downloadDocx');
const downloadPngBtn = document.getElementById('downloadPng');

// State
let currentFileId = null;
let currentFileName = null;
let usePandoc = false;

/**
 * Initializes the preview page
 * @function init
 */
function init() {
    // Get file ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    currentFileId = urlParams.get('id');
    currentFileName = urlParams.get('name');
    
    if (!currentFileId) {
        showError('No file ID provided');
        return;
    }
    
    // Set file title
    if (currentFileName) {
        fileTitle.textContent = decodeURIComponent(currentFileName);
    }
    
    // Check if Pandoc should be used
    usePandoc = urlParams.get('pandoc') === 'true';
    usePandocToggle.checked = usePandoc;
    
    // Load file content
    loadFileContent();
    
    // Set up event listeners
    setupEventListeners();
}

/**
 * Sets up event listeners for the preview page
 * @function setupEventListeners
 */
function setupEventListeners() {
    // Toggle Pandoc conversion
    usePandocToggle.addEventListener('change', function() {
        usePandoc = this.checked;
        loadFileContent();
    });
    
    // Download buttons
    downloadHtmlBtn.addEventListener('click', () => downloadFile('html'));
    downloadPdfBtn.addEventListener('click', () => downloadFile('pdf'));
    downloadDocxBtn.addEventListener('click', () => downloadFile('docx'));
    downloadPngBtn.addEventListener('click', () => downloadFile('png'));
}

/**
 * Loads the file content for preview
 * @async
 * @function loadFileContent
 */
async function loadFileContent() {
    try {
        showLoading();
        
        const response = await fetch(`/api/files/${currentFileId}/preview?pandoc=${usePandoc}`);
        if (!response.ok) {
            throw new Error('Failed to fetch file preview');
        }
        
        const data = await response.json();
        previewContent.innerHTML = data.content;
        
        // Apply syntax highlighting to code blocks
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        
        hideLoading();
    } catch (error) {
        console.error('Error loading file content:', error);
        showError('Failed to load file content. Please try again later.');
        hideLoading();
    }
}

/**
 * Downloads a file in the specified format
 * @async
 * @function downloadFile
 * @param {string} format - The format to download (html, pdf, docx, png)
 */
async function downloadFile(format) {
    try {
        showLoading();
        
        const response = await fetch(`/api/files/${currentFileId}/download?format=${format}&pandoc=${usePandoc}`);
        if (!response.ok) {
            throw new Error(`Failed to download ${format.toUpperCase()} file`);
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = response.headers.get('Content-Disposition')?.split('filename=')[1] || `file.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        hideLoading();
    } catch (error) {
        console.error(`Error downloading ${format.toUpperCase()} file:`, error);
        showError(`Failed to download ${format.toUpperCase()} file. Please try again later.`);
        hideLoading();
    }
}

/**
 * Shows a loading indicator
 * @function showLoading
 */
function showLoading() {
    previewContent.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="height: 200px;">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
}

/**
 * Hides the loading indicator
 * @function hideLoading
 */
function hideLoading() {
    // Loading is hidden when content is loaded
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

/**
 * Escapes HTML special characters in a string
 * @function escapeHtml
 * @param {string} unsafe - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', init);

const MarkdownForge = {
    /**
     * Shows a loading overlay with a custom message
     * @param {string} message - The message to display while loading
     */
    showLoading: function(message = 'Loading...') {
        const overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">${message}</p>
            </div>
        `;
        
        // Add styles
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
        
        document.body.appendChild(overlay);
    },

    /**
     * Hides the loading overlay
     */
    hideLoading: function() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.remove();
        }
    },

    /**
     * Shows a Bootstrap alert message
     * @param {string} message - The message to display
     * @param {string} type - The type of alert (success, danger, warning, info)
     * @param {number} duration - How long to show the alert in milliseconds
     */
    showAlert: function(message, type = 'info', duration = 3000) {
        const alertContainer = document.getElementById('alertContainer') || (() => {
            const container = document.createElement('div');
            container.id = 'alertContainer';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
            return container;
        })();

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        alertContainer.appendChild(alert);

        // Initialize Bootstrap alert
        const bsAlert = new bootstrap.Alert(alert);

        // Auto-dismiss after duration
        setTimeout(() => {
            bsAlert.close();
        }, duration);

        // Remove from DOM after animation
        alert.addEventListener('closed.bs.alert', () => {
            alert.remove();
            if (alertContainer.children.length === 0) {
                alertContainer.remove();
            }
        });
    },

    /**
     * Initializes syntax highlighting for code blocks
     */
    initSyntaxHighlighting: function() {
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightBlock(block);
        });
    },

    /**
     * Initializes MathJax for rendering mathematical expressions
     */
    initMathJax: function() {
        if (window.MathJax) {
            MathJax.typesetPromise();
        }
    },

    /**
     * Initializes Mermaid for rendering diagrams
     */
    initMermaid: function() {
        if (window.mermaid) {
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));
        }
    },

    /**
     * Initializes all preview features
     */
    initPreview: function() {
        this.initSyntaxHighlighting();
        this.initMathJax();
        this.initMermaid();
    },

    /**
     * Preview state management
     */
    state: {
        currentMode: 'single', // 'single' or 'comparison'
        conversionMethod: 'native', // 'native' or 'pandoc'
        fileId: null,
        fileName: null
    },

    /**
     * Initializes the preview page
     */
    init: async function() {
        // Get file ID and name from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        this.state.fileId = urlParams.get('id');
        this.state.fileName = urlParams.get('name');

        if (!this.state.fileId) {
            this.showAlert('No file ID provided', 'danger');
            return;
        }

        // Set up event listeners
        this.setupEventListeners();

        // Load initial preview
        await this.loadPreview();

        // Initialize preview features
        this.initPreview();
    },

    /**
     * Sets up event listeners for the preview page
     */
    setupEventListeners: function() {
        // View mode toggle
        document.getElementById('viewModeToggle').addEventListener('change', async (e) => {
            this.state.currentMode = e.target.checked ? 'comparison' : 'single';
            await this.loadPreview();
        });

        // Conversion method toggle
        document.getElementById('conversionMethodToggle').addEventListener('change', async (e) => {
            this.state.conversionMethod = e.target.checked ? 'pandoc' : 'native';
            await this.loadPreview();
        });

        // Download buttons
        const formats = ['html', 'pdf', 'docx', 'png', 'md'];
        formats.forEach(format => {
            const btn = document.getElementById(`download${format.toUpperCase()}`);
            if (btn) {
                btn.addEventListener('click', () => this.downloadFile(format));
            }
        });
    },

    /**
     * Loads the preview content based on current state
     */
    loadPreview: async function() {
        try {
            this.showLoading('Loading preview...');

            const response = await fetch(`/api/v1/preview/${this.state.fileId}?method=${this.state.conversionMethod}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load preview: ${response.statusText}`);
            }

            const data = await response.json();

            // Update preview containers based on view mode
            if (this.state.currentMode === 'single') {
                document.getElementById('previewContainer').innerHTML = data.html;
                document.getElementById('comparisonContainer').style.display = 'none';
                document.getElementById('previewContainer').style.display = 'block';
            } else {
                document.getElementById('markdownContent').textContent = data.markdown;
                document.getElementById('htmlPreview').innerHTML = data.html;
                document.getElementById('comparisonContainer').style.display = 'flex';
                document.getElementById('previewContainer').style.display = 'none';
            }

            // Re-initialize preview features
            this.initPreview();

        } catch (error) {
            console.error('Preview loading error:', error);
            this.showAlert(error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    },

    /**
     * Downloads the file in the specified format
     * @param {string} format - The format to download (html, pdf, docx, png, md)
     */
    downloadFile: async function(format) {
        try {
            this.showLoading(`Preparing ${format.toUpperCase()} download...`);

            const response = await fetch(`/api/v1/convert/${this.state.fileId}?format=${format}&method=${this.state.conversionMethod}`, {
                method: 'GET'
            });

            if (!response.ok) {
                throw new Error(`Download failed: ${response.statusText}`);
            }

            // Create a download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${this.state.fileName}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

            this.showAlert(`File downloaded successfully as ${format.toUpperCase()}`, 'success');

        } catch (error) {
            console.error('Download error:', error);
            this.showAlert(error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    MarkdownForge.init();
}); 