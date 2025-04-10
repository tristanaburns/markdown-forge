/**
 * Loading indicator component for Markdown Forge
 * Provides functions to show and hide loading overlays with customizable messages
 */

// Default loading overlay
const defaultOverlay = document.getElementById('loading-overlay');
const defaultMessage = defaultOverlay.querySelector('.loading-message');

// Custom loading overlay
const customOverlay = document.getElementById('loading-overlay-custom');
const customMessage = customOverlay.querySelector('.loading-message');

/**
 * Shows the default loading overlay
 * @param {string} [message='Loading...'] - Optional message to display
 */
function showLoading(message = 'Loading...') {
    defaultMessage.textContent = message;
    defaultOverlay.style.display = 'flex';
}

/**
 * Hides the default loading overlay
 */
function hideLoading() {
    defaultOverlay.style.display = 'none';
}

/**
 * Shows the custom loading overlay with a specified message
 * @param {string} message - Message to display
 */
function showCustomLoading(message) {
    customMessage.textContent = message;
    customOverlay.style.display = 'flex';
}

/**
 * Hides the custom loading overlay
 */
function hideCustomLoading() {
    customOverlay.style.display = 'none';
}

// Export functions for use in other modules
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showCustomLoading = showCustomLoading;
window.hideCustomLoading = hideCustomLoading; 