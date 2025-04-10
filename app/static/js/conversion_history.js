/**
 * Conversion History JavaScript
 * Handles fetching and displaying conversion queue status, active conversions, and history
 */

document.addEventListener('DOMContentLoaded', function() {
    // Constants
    const REFRESH_INTERVAL = 10000; // 10 seconds
    const MAX_HISTORY_ITEMS = 100; // Maximum number of history items to keep
    const ITEMS_PER_PAGE = 10;
    
    // DOM Elements
    const searchInput = document.getElementById('historySearch');
    const searchBtn = document.getElementById('searchBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const exportBtn = document.getElementById('exportBtn');
    const clearBtn = document.getElementById('clearBtn');
    const queueSizeEl = document.getElementById('queue-size');
    const completedEl = document.getElementById('completed-count');
    const failedEl = document.getElementById('failed-count');
    const processingEl = document.getElementById('processing-count');
    const historyTableBody = document.getElementById('historyTableBody');
    const activeConversionsTableBody = document.getElementById('active-conversions-body');
    const alertContainer = document.getElementById('alert-container');
    const paginationContainer = document.getElementById('historyPagination');
    const statusFilter = document.getElementById('statusFilter');
    
    // State variables
    let refreshInterval = null;
    let conversionHistory = [];
    let activeConversions = [];
    let queueStats = {
        size: 0,
        completed: 0,
        failed: 0,
        processing: 0
    };
    let systemMetrics = {
        cpuUsage: 0,
        memoryUsage: 0,
        diskUsage: 0,
        uptime: 0
    };
    let currentPage = 1;
    let itemsPerPage = ITEMS_PER_PAGE;
    let filteredHistory = [];
    let totalPages = 1;
    let totalItems = 0;
    
    // Initialize the page
    init();
    
    function init() {
        // Fetch initial data
        fetchData();
        
        // Start automatic refresh
        startRefreshInterval();
        
        // Setup event listeners
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                fetchData();
            });
        }
        
        if (exportBtn) {
            exportBtn.addEventListener('click', function() {
                exportHistory();
            });
        }
        
        if (clearBtn) {
            clearBtn.addEventListener('click', function() {
                clearHistory();
            });
        }
        
        if (searchBtn) {
            searchBtn.addEventListener('click', function() {
                currentPage = 1; // Reset to first page
                fetchData();
            });
        }
        
        // Handle visibility change (pause updates when tab is not visible)
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                // Page is hidden, pause updates to save resources
                stopRefreshInterval();
            } else {
                // Page is visible again, resume updates
                startRefreshInterval();
            }
        });
        
        // Add event listener for status filter
        if (statusFilter) {
            statusFilter.addEventListener('change', function() {
                currentPage = 1; // Reset to first page
                fetchData();
            });
        }
        
        // Update search input event listener
        if (searchInput) {
            // Remove any existing listeners
            searchInput.removeEventListener('input', filterAndRenderHistory);
            
            // Add debounced search event
            let debounceTimeout;
            searchInput.addEventListener('input', function() {
                clearTimeout(debounceTimeout);
                debounceTimeout = setTimeout(function() {
                    currentPage = 1; // Reset to first page
                    fetchData();
                }, 300);
            });
        }
    }
    
    function startRefreshInterval() {
        if (!refreshInterval) {
            refreshInterval = setInterval(fetchData, REFRESH_INTERVAL);
        }
    }
    
    function stopRefreshInterval() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    }
    
    function fetchData() {
        // Show loading state
        refreshBtn.classList.add('refreshing');
        
        // Fetch queue status
        fetch('/api/conversion/queue/status')
            .then(response => response.json())
            .then(data => {
                // Update queue stats
                updateQueueStats(data.stats);
                
                // Update active conversions
                updateActiveConversions(data.active_conversions);
                
                // Update system metrics
                updateSystemMetrics(data.system_metrics);
                
                // Update conversion history with data from queue status
                // This ensures we have the most recent conversions if they're not yet in our history call
                updateConversionHistoryFromQueue(data.history);
            })
            .catch(error => {
                console.error('Error fetching queue status:', error);
                showNotification('Failed to fetch data. Please try again.', 'danger');
            })
            .finally(() => {
                // Remove loading state
                refreshBtn.classList.remove('refreshing');
            });
        
        // Fetch conversion history with pagination and filtering
        const status = statusFilter ? statusFilter.value : 'all';
        const search = searchInput ? searchInput.value : '';
        
        // Build URL with query parameters
        const url = new URL('/api/conversion/history', window.location.origin);
        url.searchParams.append('page', currentPage);
        url.searchParams.append('limit', itemsPerPage);
        url.searchParams.append('status', status);
        url.searchParams.append('search', search);
        url.searchParams.append('sort', 'timestamp');
        url.searchParams.append('order', 'desc');
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.history) {
                    // Use the history items and pagination
                    conversionHistory = data.history;
                    totalPages = data.pagination.total_pages;
                    totalItems = data.pagination.total_items;
                    
                    // Update the UI
                    filterAndRenderHistory();
                }
            })
            .catch(error => {
                console.error('Error fetching conversion history:', error);
                showNotification('Failed to fetch history. Please try again.', 'danger');
            });
    }
    
    function updateQueueStats(stats) {
        if (!stats) return;
        
        queueStats = stats;
        queueSizeEl.textContent = stats.size;
        completedEl.textContent = stats.completed;
        failedEl.textContent = stats.failed;
        processingEl.textContent = stats.processing;
        
        // Update progress bars
        document.getElementById('queue-progress').style.width = `${calculateQueueProgress()}%`;
        document.getElementById('queue-progress').setAttribute('aria-valuenow', calculateQueueProgress());
        document.getElementById('queue-progress-label').textContent = `${calculateQueueProgress()}%`;
    }
    
    function calculateQueueProgress() {
        const total = queueStats.completed + queueStats.failed + queueStats.processing + queueStats.size;
        if (total === 0) return 0;
        return Math.round((queueStats.completed + queueStats.failed) / total * 100);
    }
    
    function updateActiveConversions(conversions) {
        if (!conversions) return;
        
        activeConversions = conversions;
        activeConversionsTableBody.innerHTML = '';
        
        if (conversions.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = `
                <td colspan="5" class="text-center">
                    <div class="empty-state">
                        <i class="fas fa-tasks"></i>
                        <h5>No Active Conversions</h5>
                        <p>There are currently no files being processed</p>
                    </div>
                </td>
            `;
            activeConversionsTableBody.appendChild(emptyRow);
            return;
        }
        
        conversions.forEach(conversion => {
            const row = document.createElement('tr');
            row.className = `status-${conversion.status.toLowerCase()}`;
            
            // Calculate progress percentage
            const progress = conversion.progress * 100;
            
            row.innerHTML = `
                <td>
                    <i class="fas ${getFileIcon(conversion.file_name)}" aria-hidden="true"></i>
                    ${conversion.file_name}
                </td>
                <td>${conversion.output_format}</td>
                <td>
                    <div class="progress-container">
                        <div class="progress">
                            <div class="progress-bar ${getProgressBarClass(conversion.status)}" 
                                role="progressbar" 
                                style="width: ${progress}%" 
                                aria-valuenow="${progress}" 
                                aria-valuemin="0" 
                                aria-valuemax="100">
                            </div>
                        </div>
                        <span class="progress-label">${Math.round(progress)}%</span>
                    </div>
                </td>
                <td>
                    <span class="badge ${getStatusBadgeClass(conversion.status)}">${conversion.status}</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-danger action-btn" 
                            onclick="cancelConversion('${conversion.id}')" 
                            ${conversion.status === 'Completed' ? 'disabled' : ''}>
                        <i class="fas fa-times"></i> Cancel
                    </button>
                </td>
            `;
            
            activeConversionsTableBody.appendChild(row);
        });
    }
    
    function updateSystemMetrics(metrics) {
        if (!metrics) return;
        
        systemMetrics = metrics;
        
        // Update CPU usage
        document.getElementById('cpu-usage').style.width = `${metrics.cpuUsage}%`;
        document.getElementById('cpu-usage').setAttribute('aria-valuenow', metrics.cpuUsage);
        document.getElementById('cpu-usage-label').textContent = `${metrics.cpuUsage}%`;
        
        // Update memory usage
        document.getElementById('memory-usage').style.width = `${metrics.memoryUsage}%`;
        document.getElementById('memory-usage').setAttribute('aria-valuenow', metrics.memoryUsage);
        document.getElementById('memory-usage-label').textContent = `${metrics.memoryUsage}%`;
        
        // Update disk usage
        document.getElementById('disk-usage').style.width = `${metrics.diskUsage}%`;
        document.getElementById('disk-usage').setAttribute('aria-valuenow', metrics.diskUsage);
        document.getElementById('disk-usage-label').textContent = `${metrics.diskUsage}%`;
        
        // Update uptime
        document.getElementById('uptime-value').textContent = formatUptime(metrics.uptime);
    }
    
    function updateConversionHistoryFromQueue(queueHistory) {
        if (!Array.isArray(queueHistory) || queueHistory.length === 0) return;
        
        // Only add items that aren't in the current page
        // This ensures we have the most up-to-date data for active conversions
        const currentIds = conversionHistory.map(item => item.id);
        
        queueHistory.forEach(item => {
            if (!currentIds.includes(item.id)) {
                // This is a new item that our paginated history doesn't contain
                // Add it temporarily to the displayed history
                conversionHistory.unshift(item);
            } else {
                // Update existing items with latest status
                const existingItem = conversionHistory.find(h => h.id === item.id);
                if (existingItem) {
                    Object.assign(existingItem, item);
                }
            }
        });
        
        // Refresh the display
        filterAndRenderHistory();
    }
    
    function filterAndRenderHistory() {
        // Already have filtered data from the API
        filteredHistory = conversionHistory;
        
        // Render pagination
        renderPagination();
        
        // Render history items for current page
        renderHistoryPage();
    }
    
    function renderHistoryPage() {
        historyTableBody.innerHTML = '';
        
        if (filteredHistory.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = `
                <td colspan="6" class="text-center">
                    <div class="empty-state">
                        <i class="fas fa-history"></i>
                        <h5>No Conversion History</h5>
                        <p>Your conversion history will appear here</p>
                    </div>
                </td>
            `;
            historyTableBody.appendChild(emptyRow);
            return;
        }
        
        // Calculate page items
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, filteredHistory.length);
        const pageItems = filteredHistory.slice(startIndex, endIndex);
        
        // Render each history item
        pageItems.forEach(item => {
            const row = document.createElement('tr');
            row.className = `status-${item.status.toLowerCase()}`;
            
            row.innerHTML = `
                <td>
                    <i class="fas ${getFileIcon(item.file_name)}" aria-hidden="true"></i>
                    ${item.file_name}
                </td>
                <td>${item.output_format}</td>
                <td><span class="timestamp">${formatTimestamp(item.timestamp)}</span></td>
                <td class="duration-cell">${formatDuration(item.duration)}</td>
                <td>
                    <span class="badge ${getStatusBadgeClass(item.status)}">${item.status}</span>
                </td>
                <td>
                    <div class="btn-group">
                        ${item.status === 'Completed' ? `
                            <button class="btn btn-sm btn-outline-primary action-btn" onclick="downloadFile('${item.id}')">
                                <i class="fas fa-download"></i> Download
                            </button>
                        ` : ''}
                        ${item.status === 'Failed' ? `
                            <button class="btn btn-sm btn-outline-warning action-btn" onclick="retryConversion('${item.id}')">
                                <i class="fas fa-redo"></i> Retry
                            </button>
                        ` : ''}
                        <button class="btn btn-sm btn-outline-info action-btn" onclick="viewDetails('${item.id}')">
                            <i class="fas fa-info-circle"></i> Details
                        </button>
                        <button class="btn btn-sm btn-outline-danger action-btn" onclick="removeHistoryItem('${item.id}')">
                            <i class="fas fa-trash"></i> Remove
                        </button>
                    </div>
                </td>
            `;
            
            historyTableBody.appendChild(row);
        });
    }
    
    function renderPagination() {
        if (!paginationContainer) return;
        
        paginationContainer.innerHTML = '';
        
        if (totalPages <= 1) return;
        
        const ul = document.createElement('ul');
        ul.className = 'pagination justify-content-center';
        
        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `
            <a class="page-link" href="#" aria-label="Previous" ${currentPage === 1 ? 'tabindex="-1"' : ''}>
                <span aria-hidden="true">&laquo;</span>
            </a>
        `;
        prevLi.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage > 1) {
                goToPage(currentPage - 1);
            }
        });
        ul.appendChild(prevLi);
        
        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, startPage + 4);
        
        for (let i = startPage; i <= endPage; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${i === currentPage ? 'active' : ''}`;
            li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            li.addEventListener('click', function(e) {
                e.preventDefault();
                goToPage(i);
            });
            ul.appendChild(li);
        }
        
        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `
            <a class="page-link" href="#" aria-label="Next" ${currentPage === totalPages ? 'tabindex="-1"' : ''}>
                <span aria-hidden="true">&raquo;</span>
            </a>
        `;
        nextLi.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage < totalPages) {
                goToPage(currentPage + 1);
            }
        });
        ul.appendChild(nextLi);
        
        paginationContainer.appendChild(ul);
    }
    
    function goToPage(page) {
        currentPage = page;
        fetchData();
        
        // Scroll to top of table
        historyTableBody.closest('.card').scrollIntoView({ behavior: 'smooth' });
    }
    
    function clearHistory() {
        if (confirm('Are you sure you want to clear all conversion history?')) {
            // API call to clear history
            fetch('/api/conversion/history/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    conversionHistory = [];
                    filterAndRenderHistory();
                    showNotification('Conversion history cleared successfully', 'success');
                } else {
                    showNotification('Failed to clear history: ' + data.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error clearing history:', error);
                showNotification('Failed to clear history. Please try again.', 'danger');
            });
        }
    }
    
    function exportHistory() {
        // Create CSV content
        let csvContent = 'data:text/csv;charset=utf-8,';
        csvContent += 'File Name,Output Format,Timestamp,Duration,Status\n';
        
        conversionHistory.forEach(item => {
            csvContent += `"${item.file_name}","${item.output_format}","${formatTimestamp(item.timestamp)}","${formatDuration(item.duration)}","${item.status}"\n`;
        });
        
        // Create download link
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', `conversion_history_${formatDateForFilename(new Date())}.csv`);
        document.body.appendChild(link);
        
        // Trigger download
        link.click();
        
        // Clean up
        document.body.removeChild(link);
        showNotification('Export completed successfully', 'success');
    }
    
    function showNotification(message, type) {
        const alert = document.createElement('div');
        alert.className = `custom-alert alert-${type}`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="close-btn" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;
        
        // Add event listener to close button
        alert.querySelector('.close-btn').addEventListener('click', function() {
            alert.remove();
        });
        
        // Add to container
        alertContainer.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.add('fade-out');
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 500);
            }
        }, 5000);
    }
    
    // Utility functions
    function getFileIcon(fileName) {
        const extension = fileName.split('.').pop().toLowerCase();
        
        switch (extension) {
            case 'md':
                return 'fa-file-alt';
            case 'pdf':
                return 'fa-file-pdf';
            case 'docx':
            case 'doc':
                return 'fa-file-word';
            case 'html':
                return 'fa-file-code';
            case 'txt':
                return 'fa-file-alt';
            case 'epub':
                return 'fa-book';
            default:
                return 'fa-file';
        }
    }
    
    function getStatusBadgeClass(status) {
        switch (status.toLowerCase()) {
            case 'completed':
                return 'bg-success';
            case 'failed':
                return 'bg-danger';
            case 'processing':
                return 'bg-warning';
            case 'pending':
                return 'bg-secondary';
            default:
                return 'bg-info';
        }
    }
    
    function getProgressBarClass(status) {
        switch (status.toLowerCase()) {
            case 'completed':
                return 'bg-success';
            case 'failed':
                return 'bg-danger';
            case 'processing':
                return 'bg-warning';
            case 'pending':
                return 'bg-secondary';
            default:
                return 'bg-info';
        }
    }
    
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    }
    
    function formatDateForFilename(date) {
        return date.toISOString().split('T')[0];
    }
    
    function formatDuration(duration) {
        // Convert duration in milliseconds to readable format
        if (!duration) return '-';
        
        const seconds = Math.floor(duration / 1000);
        if (seconds < 60) {
            return `${seconds}s`;
        }
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds}s`;
    }
    
    function formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = seconds % 60;
        
        let result = '';
        if (days > 0) result += `${days}d `;
        if (hours > 0 || days > 0) result += `${hours}h `;
        if (minutes > 0 || hours > 0 || days > 0) result += `${minutes}m `;
        result += `${remainingSeconds}s`;
        
        return result;
    }
    
    // Global functions (exposing these to window for button onclick handlers)
    window.cancelConversion = function(id) {
        if (confirm('Are you sure you want to cancel this conversion?')) {
            fetch(`/api/conversion/${id}/cancel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Conversion cancelled successfully', 'success');
                    fetchData(); // Refresh data
                } else {
                    showNotification('Failed to cancel conversion: ' + data.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error cancelling conversion:', error);
                showNotification('Failed to cancel conversion. Please try again.', 'danger');
            });
        }
    };
    
    window.downloadFile = function(id) {
        window.location.href = `/api/files/${id}/download`;
    };
    
    window.retryConversion = function(id) {
        fetch(`/api/conversion/${id}/retry`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Conversion retry initiated successfully', 'success');
                fetchData(); // Refresh data
            } else {
                showNotification('Failed to retry conversion: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error retrying conversion:', error);
            showNotification('Failed to retry conversion. Please try again.', 'danger');
        });
    };
    
    window.viewDetails = function(id) {
        // Find the item in history
        const item = conversionHistory.find(i => i.id === id);
        if (!item) return;
        
        // Create modal with details
        const modalContent = `
            <div class="modal fade" id="detailsModal" tabindex="-1" aria-labelledby="detailsModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="detailsModalLabel">Conversion Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-md-4"><strong>File Name:</strong></div>
                                <div class="col-md-8">${item.file_name}</div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-md-4"><strong>Output Format:</strong></div>
                                <div class="col-md-8">${item.output_format}</div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-md-4"><strong>Status:</strong></div>
                                <div class="col-md-8">
                                    <span class="badge ${getStatusBadgeClass(item.status)}">${item.status}</span>
                                </div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-md-4"><strong>Started At:</strong></div>
                                <div class="col-md-8">${formatTimestamp(item.timestamp)}</div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-md-4"><strong>Duration:</strong></div>
                                <div class="col-md-8">${formatDuration(item.duration)}</div>
                            </div>
                            ${item.error ? `
                                <div class="row mb-3">
                                    <div class="col-md-4"><strong>Error:</strong></div>
                                    <div class="col-md-8">
                                        <div class="alert alert-danger">${item.error}</div>
                                    </div>
                                </div>
                            ` : ''}
                            <div class="row mb-3">
                                <div class="col-md-4"><strong>Conversion Options:</strong></div>
                                <div class="col-md-8">
                                    <pre class="bg-light p-3 rounded"><code>${JSON.stringify(item.options || {}, null, 2)}</code></pre>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            ${item.status === 'Completed' ? `
                                <button type="button" class="btn btn-primary" onclick="downloadFile('${item.id}')">Download</button>
                            ` : ''}
                            ${item.status === 'Failed' ? `
                                <button type="button" class="btn btn-warning" onclick="retryConversion('${item.id}')">Retry</button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        const modalDiv = document.createElement('div');
        modalDiv.innerHTML = modalContent;
        document.body.appendChild(modalDiv);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('detailsModal'));
        modal.show();
        
        // Clean up on modal close
        document.getElementById('detailsModal').addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(modalDiv);
        });
    };
    
    window.removeHistoryItem = function(id) {
        if (confirm('Are you sure you want to remove this item from history?')) {
            fetch(`/api/conversion/history/${id}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remove from local history
                    conversionHistory = conversionHistory.filter(item => item.id !== id);
                    filterAndRenderHistory();
                    showNotification('History item removed successfully', 'success');
                } else {
                    showNotification('Failed to remove history item: ' + data.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error removing history item:', error);
                showNotification('Failed to remove history item. Please try again.', 'danger');
            });
        }
    };
}); 