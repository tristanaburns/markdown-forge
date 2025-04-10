/**
 * File validation utilities for the Markdown Forge application.
 * Provides functions for validating file types, sizes, and content.
 */

/**
 * Validates a file based on type, size, and content
 * @param {File} file - The file to validate
 * @param {Object} options - Validation options
 * @param {string[]} [options.allowedTypes=['md', 'markdown', 'mdown', 'mkdn']] - Allowed file extensions
 * @param {number} [options.maxSize=10485760] - Maximum file size in bytes (default: 10MB)
 * @param {boolean} [options.validateContent=true] - Whether to validate file content
 * @returns {Object} - Validation result with isValid and error properties
 */
function validateFile(file, options = {}) {
    const {
        allowedTypes = ['md', 'markdown', 'mdown', 'mkdn'],
        maxSize = 10485760, // 10MB
        validateContent = true
    } = options;

    // Check file type
    const extension = file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(extension)) {
        return {
            isValid: false,
            error: `File type not allowed. Allowed types: ${allowedTypes.join(', ')}`
        };
    }

    // Check file size
    if (file.size > maxSize) {
        return {
            isValid: false,
            error: `File size exceeds the maximum allowed size of ${formatFileSize(maxSize)}`
        };
    }

    // Validate content if requested
    if (validateContent) {
        return validateMarkdownContent(file);
    }

    return { isValid: true };
}

/**
 * Validates the content of a Markdown file
 * @param {File} file - The file to validate
 * @returns {Promise<Object>} - Validation result with isValid and error properties
 */
function validateMarkdownContent(file) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        
        reader.onload = (event) => {
            const content = event.target.result;
            
            // Basic validation: check if the file is empty
            if (!content || content.trim() === '') {
                resolve({
                    isValid: false,
                    error: 'File is empty'
                });
                return;
            }
            
            // Check for common Markdown syntax
            const hasMarkdownSyntax = /^#|^\s*[-*+]\s|^\s*\d+\.\s|^\s*>\s|^\s*`|^\s*\*\*|^\s*__|^\s*\[|^\s*!\[/.test(content);
            
            if (!hasMarkdownSyntax) {
                resolve({
                    isValid: false,
                    error: 'File does not appear to contain valid Markdown content'
                });
                return;
            }
            
            resolve({ isValid: true });
        };
        
        reader.onerror = () => {
            resolve({
                isValid: false,
                error: 'Error reading file content'
            });
        };
        
        reader.readAsText(file);
    });
}

/**
 * Validates multiple files
 * @param {File[]} files - Array of files to validate
 * @param {Object} options - Validation options
 * @returns {Promise<Object>} - Validation result with validFiles and invalidFiles properties
 */
async function validateFiles(files, options = {}) {
    const validFiles = [];
    const invalidFiles = [];
    
    for (const file of files) {
        const result = await validateFile(file, options);
        
        if (result.isValid) {
            validFiles.push(file);
        } else {
            invalidFiles.push({
                file,
                error: result.error
            });
        }
    }
    
    return {
        validFiles,
        invalidFiles
    };
}

/**
 * Formats file size in bytes to a human-readable string
 * @param {number} bytes - File size in bytes
 * @returns {string} - Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Export functions for use in other modules
window.validateFile = validateFile;
window.validateFiles = validateFiles;
window.formatFileSize = formatFileSize; 