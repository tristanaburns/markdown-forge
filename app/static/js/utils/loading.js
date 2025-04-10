/**
 * Loading utility functions for the Markdown Forge application.
 * Provides functions for showing and hiding loading indicators.
 */

/**
 * Show a loading overlay with a custom message.
 * @param {string} message - The message to display in the loading overlay.
 * @param {string} id - The ID of the loading overlay element.
 */
function showLoading(message = 'Loading...', id = 'loading-overlay') {
    const loadingOverlay = document.getElementById(id);
    if (!loadingOverlay) {
        console.error(`Loading overlay with ID "${id}" not found.`);
        return;
    }
    
    // Update message if provided
    const messageElement = loadingOverlay.querySelector('.loading-message');
    if (messageElement && message) {
        messageElement.textContent = message;
    }
    
    // Show the overlay
    loadingOverlay.classList.remove('d-none');
}

/**
 * Hide a loading overlay.
 * @param {string} id - The ID of the loading overlay element.
 */
function hideLoading(id = 'loading-overlay') {
    const loadingOverlay = document.getElementById(id);
    if (!loadingOverlay) {
        console.error(`Loading overlay with ID "${id}" not found.`);
        return;
    }
    
    // Hide the overlay
    loadingOverlay.classList.add('d-none');
}

/**
 * Show a loading overlay for a specific duration.
 * @param {string} message - The message to display in the loading overlay.
 * @param {number} duration - The duration in milliseconds to show the loading overlay.
 * @param {string} id - The ID of the loading overlay element.
 */
function showLoadingForDuration(message = 'Loading...', duration = 1000, id = 'loading-overlay') {
    showLoading(message, id);
    
    setTimeout(() => {
        hideLoading(id);
    }, duration);
}

// Export functions for use in other modules
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showLoadingForDuration = showLoadingForDuration; 