/**
 * Error handling utilities for the Markdown Forge application.
 * Provides functions for handling API errors and displaying user-friendly error messages.
 */

/**
 * Handle API error responses
 * @param {Response} response - The fetch API response object
 * @returns {Promise} - Resolves with the response data or rejects with an error
 */
async function handleApiResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({
            message: 'An unexpected error occurred',
            status_code: response.status
        }));
        
        throw new ApiError(
            errorData.message || 'An unexpected error occurred',
            errorData.status_code || response.status,
            errorData
        );
    }
    
    return response.json();
}

/**
 * Display an error message to the user
 * @param {string} message - The error message to display
 * @param {string} [type='danger'] - The Bootstrap alert type (danger, warning, info)
 * @param {number} [duration=5000] - How long to show the message in milliseconds
 */
function showError(message, type = 'danger', duration = 5000) {
    const alertContainer = document.getElementById('alert-container') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    if (duration > 0) {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, duration);
    }
}

/**
 * Create the alert container if it doesn't exist
 * @returns {HTMLElement} - The alert container element
 */
function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1050';
    document.body.appendChild(container);
    return container;
}

/**
 * Custom error class for API errors
 */
class ApiError extends Error {
    constructor(message, statusCode, data = null) {
        super(message);
        this.name = 'ApiError';
        this.statusCode = statusCode;
        this.data = data;
    }
}

// Export functions for use in other modules
window.handleApiResponse = handleApiResponse;
window.showError = showError;
window.ApiError = ApiError; 