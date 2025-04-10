/**
 * Progress tracking utilities for the Markdown Forge application.
 * Provides functions for tracking and displaying progress for file uploads and conversions.
 */

/**
 * Progress tracker class for managing progress tracking
 */
class ProgressTracker {
    /**
     * Creates a new progress tracker
     * @param {Object} options - Configuration options
     * @param {string} [options.containerId='progressContainer'] - ID of the progress container element
     * @param {string} [options.barClass='.progress-bar'] - Class of the progress bar element
     * @param {string} [options.statusId='progressStatus'] - ID of the status text element
     * @param {boolean} [options.showPercentage=true] - Whether to show percentage in status
     */
    constructor(options = {}) {
        this.containerId = options.containerId || 'progressContainer';
        this.barClass = options.barClass || '.progress-bar';
        this.statusId = options.statusId || 'progressStatus';
        this.showPercentage = options.showPercentage !== false;
        
        this.container = document.getElementById(this.containerId);
        this.bar = this.container ? this.container.querySelector(this.barClass) : null;
        this.status = document.getElementById(this.statusId);
        
        this.currentProgress = 0;
        this.totalSteps = 0;
        this.currentStep = 0;
        this.stepDescriptions = [];
    }
    
    /**
     * Initializes the progress tracker
     * @param {number} totalSteps - Total number of steps
     * @param {string[]} stepDescriptions - Descriptions for each step
     */
    init(totalSteps, stepDescriptions = []) {
        this.totalSteps = totalSteps;
        this.currentStep = 0;
        this.currentProgress = 0;
        this.stepDescriptions = stepDescriptions;
        
        this.show();
        this.update(0, 'Initializing...');
    }
    
    /**
     * Shows the progress container
     */
    show() {
        if (this.container) {
            this.container.classList.remove('d-none');
        }
    }
    
    /**
     * Hides the progress container
     */
    hide() {
        if (this.container) {
            this.container.classList.add('d-none');
        }
    }
    
    /**
     * Updates the progress
     * @param {number} progress - Progress percentage (0-100)
     * @param {string} [status] - Status message
     */
    update(progress, status = null) {
        this.currentProgress = Math.min(100, Math.max(0, progress));
        
        if (this.bar) {
            this.bar.style.width = `${this.currentProgress}%`;
        }
        
        if (this.status) {
            let statusText = status || '';
            
            if (this.showPercentage) {
                statusText = `${statusText} (${Math.round(this.currentProgress)}%)`;
            }
            
            this.status.textContent = statusText;
        }
    }
    
    /**
     * Advances to the next step
     * @param {string} [status] - Status message for the new step
     */
    nextStep(status = null) {
        this.currentStep++;
        
        if (this.currentStep > this.totalSteps) {
            this.currentStep = this.totalSteps;
        }
        
        const stepProgress = (this.currentStep / this.totalSteps) * 100;
        const stepStatus = status || 
            (this.stepDescriptions[this.currentStep - 1] || `Step ${this.currentStep} of ${this.totalSteps}`);
        
        this.update(stepProgress, stepStatus);
    }
    
    /**
     * Completes the progress
     * @param {string} [status='Complete!'] - Final status message
     */
    complete(status = 'Complete!') {
        this.update(100, status);
        
        // Hide after a delay
        setTimeout(() => {
            this.hide();
        }, 1500);
    }
    
    /**
     * Resets the progress tracker
     */
    reset() {
        this.currentStep = 0;
        this.currentProgress = 0;
        this.update(0, '');
    }
}

/**
 * Creates a new progress tracker instance
 * @param {Object} options - Configuration options
 * @returns {ProgressTracker} - Progress tracker instance
 */
function createProgressTracker(options = {}) {
    return new ProgressTracker(options);
}

/**
 * Tracks upload progress for a fetch request
 * @param {string} url - URL to send the request to
 * @param {Object} options - Fetch options
 * @param {ProgressTracker} progressTracker - Progress tracker instance
 * @returns {Promise} - Fetch promise
 */
function trackUploadProgress(url, options, progressTracker) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.open(options.method || 'GET', url, true);
        
        // Set headers
        if (options.headers) {
            Object.keys(options.headers).forEach(key => {
                xhr.setRequestHeader(key, options.headers[key]);
            });
        }
        
        // Track progress
        xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
                const percentComplete = (event.loaded / event.total) * 100;
                progressTracker.update(percentComplete, 'Uploading...');
            }
        });
        
        // Handle completion
        xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } catch (e) {
                    resolve(xhr.responseText);
                }
            } else {
                reject(new Error(`Request failed with status ${xhr.status}`));
            }
        });
        
        // Handle errors
        xhr.addEventListener('error', () => {
            reject(new Error('Network error occurred'));
        });
        
        // Send the request
        if (options.body) {
            xhr.send(options.body);
        } else {
            xhr.send();
        }
    });
}

// Export functions for use in other modules
window.createProgressTracker = createProgressTracker;
window.trackUploadProgress = trackUploadProgress; 