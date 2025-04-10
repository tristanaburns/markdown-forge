/**
 * Main JavaScript file for Markdown Forge
 * Contains common utility functions and initialization code
 */

// Global utility object
const MarkdownForge = {
    /**
     * Initialize the application
     */
    init() {
        this.initializeTooltips();
        this.initializePopovers();
        this.setupThemeToggle();
        this.setupAlertDismissal();
    },

    /**
     * Initialize Bootstrap tooltips
     */
    initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    },

    /**
     * Initialize Bootstrap popovers
     */
    initializePopovers() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    },

    /**
     * Setup theme toggle functionality
     */
    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    },

    /**
     * Toggle between light and dark theme
     */
    toggleTheme() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        this.updateThemeIcon(newTheme);
    },

    /**
     * Update theme icon based on current theme
     * @param {string} theme - The current theme ('light' or 'dark')
     */
    updateThemeIcon(theme) {
        const icon = document.querySelector('#themeToggle i');
        if (icon) {
            icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    },

    /**
     * Setup automatic alert dismissal
     */
    setupAlertDismissal() {
        document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    },

    /**
     * Show a loading spinner
     * @param {string} message - Optional loading message
     */
    showLoading(message = 'Loading...') {
        const spinner = document.createElement('div');
        spinner.className = 'spinner-overlay';
        spinner.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="mt-2">${message}</div>
            </div>
        `;
        document.body.appendChild(spinner);
    },

    /**
     * Hide the loading spinner
     */
    hideLoading() {
        const spinner = document.querySelector('.spinner-overlay');
        if (spinner) {
            spinner.remove();
        }
    },

    /**
     * Show an alert message
     * @param {string} message - The message to display
     * @param {string} type - The alert type (success, danger, warning, info)
     * @param {boolean} autoDismiss - Whether to automatically dismiss the alert
     */
    showAlert(message, type = 'info', autoDismiss = true) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        if (autoDismiss) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alertDiv);
                bsAlert.close();
            }, 5000);
        }
    },

    /**
     * Format a file size in bytes to a human-readable string
     * @param {number} bytes - The file size in bytes
     * @returns {string} The formatted file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Format a date string to a human-readable format
     * @param {string} dateString - The date string to format
     * @returns {string} The formatted date string
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * Copy text to clipboard
     * @param {string} text - The text to copy
     * @returns {Promise<void>}
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showAlert('Copied to clipboard!', 'success');
        } catch (err) {
            this.showAlert('Failed to copy text.', 'danger');
            console.error('Failed to copy text:', err);
        }
    },

    /**
     * Validate a file based on type and size
     * @param {File} file - The file to validate
     * @param {string[]} allowedTypes - Array of allowed file extensions
     * @param {number} maxSize - Maximum file size in bytes
     * @returns {boolean} Whether the file is valid
     */
    validateFile(file, allowedTypes, maxSize) {
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        const isValidType = allowedTypes.includes(fileExtension);
        const isValidSize = file.size <= maxSize;
        
        if (!isValidType) {
            this.showAlert(`Invalid file type. Allowed types: ${allowedTypes.join(', ')}`, 'danger');
        }
        if (!isValidSize) {
            this.showAlert(`File too large. Maximum size: ${this.formatFileSize(maxSize)}`, 'danger');
        }
        
        return isValidType && isValidSize;
    }
};

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    MarkdownForge.init();
}); 