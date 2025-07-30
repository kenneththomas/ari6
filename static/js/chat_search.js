// Chat Search JavaScript
class ChatSearch {
    constructor() {
        this.currentPage = 1;
        this.currentLimit = 100;
        this.searchQuery = '';
        this.senderFilter = '';
        this.channelFilter = '';
        this.dateFrom = '';
        this.dateTo = '';
        
        this.initializeElements();
        this.bindEvents();
        this.loadStats();
    }

    initializeElements() {
        // Search elements
        this.searchQueryEl = document.getElementById('search-query');
        this.senderFilterEl = document.getElementById('sender-filter');
        this.channelFilterEl = document.getElementById('channel-filter');
        this.dateFromEl = document.getElementById('date-from');
        this.dateToEl = document.getElementById('date-to');
        this.limitSelectEl = document.getElementById('limit-select');
        
        // Buttons
        this.searchBtn = document.getElementById('search-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.prevPageBtn = document.getElementById('prev-page');
        this.nextPageBtn = document.getElementById('next-page');
        
        // Results elements
        this.resultsListEl = document.getElementById('results-list');
        this.resultsCountEl = document.getElementById('results-count');
        this.loadingSpinnerEl = document.getElementById('loading-spinner');
        this.paginationEl = document.getElementById('pagination');
        this.pageInfoEl = document.getElementById('page-info');
        
        // Stats elements
        this.totalMessagesEl = document.getElementById('total-messages');
        this.uniqueUsersEl = document.getElementById('unique-users');
        this.uniqueChannelsEl = document.getElementById('unique-channels');
    }

    bindEvents() {
        // Search button
        this.searchBtn.addEventListener('click', () => this.performSearch());
        
        // Clear button
        this.clearBtn.addEventListener('click', () => this.clearFilters());
        
        // Pagination buttons
        this.prevPageBtn.addEventListener('click', () => this.previousPage());
        this.nextPageBtn.addEventListener('click', () => this.nextPage());
        
        // Enter key on search input
        this.searchQueryEl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
        
        // Auto-search on filter changes (with debounce)
        let searchTimeout;
        const debouncedSearch = () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => this.performSearch(), 500);
        };
        
        this.senderFilterEl.addEventListener('input', debouncedSearch);
        this.channelFilterEl.addEventListener('input', debouncedSearch);
        this.dateFromEl.addEventListener('change', debouncedSearch);
        this.dateToEl.addEventListener('change', debouncedSearch);
        this.limitSelectEl.addEventListener('change', debouncedSearch);
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.success) {
                this.updateStats(data.stats);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    updateStats(stats) {
        this.totalMessagesEl.textContent = this.formatNumber(stats.total_messages);
        this.uniqueUsersEl.textContent = this.formatNumber(stats.unique_senders);
        this.uniqueChannelsEl.textContent = this.formatNumber(stats.unique_channels);
    }

    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }

    async performSearch() {
        this.showLoading(true);
        
        // Update current filters
        this.searchQuery = this.searchQueryEl.value.trim();
        this.senderFilter = this.senderFilterEl.value.trim();
        this.channelFilter = this.channelFilterEl.value.trim();
        this.dateFrom = this.dateFromEl.value;
        this.dateTo = this.dateToEl.value;
        this.currentLimit = parseInt(this.limitSelectEl.value);
        
        // Reset to first page
        this.currentPage = 1;
        
        try {
            const params = new URLSearchParams({
                query: this.searchQuery,
                sender: this.senderFilter,
                channel: this.channelFilter,
                date_from: this.dateFrom,
                date_to: this.dateTo,
                limit: this.currentLimit,
                offset: (this.currentPage - 1) * this.currentLimit
            });
            
            const response = await fetch(`/api/search?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayResults(data.logs, data.count);
            } else {
                this.showError('Search failed: ' + data.error);
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Search failed. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    displayResults(logs, totalCount) {
        this.resultsListEl.innerHTML = '';
        
        if (logs.length === 0) {
            this.resultsListEl.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>No messages found matching your criteria</p>
                </div>
            `;
            this.resultsCountEl.textContent = '0 results';
            this.paginationEl.style.display = 'none';
            return;
        }
        
        // Display results
        logs.forEach(log => {
            const messageEl = this.createMessageElement(log);
            this.resultsListEl.appendChild(messageEl);
        });
        
        // Update results count
        this.resultsCountEl.textContent = `${logs.length} results`;
        
        // Update pagination
        this.updatePagination(totalCount);
    }

    createMessageElement(log) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-item';
        
        const highlightedMessage = this.highlightSearchTerms(log.message);
        const highlightedSender = this.highlightSearchTerms(log.sender);
        const highlightedChannel = this.highlightSearchTerms(log.channel);
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <div class="message-sender">${highlightedSender}</div>
                <div class="message-channel">${highlightedChannel}</div>
                <div class="message-timestamp">${this.formatTimestamp(log.timestamp)}</div>
            </div>
            <div class="message-content">${highlightedMessage}</div>
        `;
        
        return messageDiv;
    }

    highlightSearchTerms(text) {
        if (!this.searchQuery) return this.escapeHtml(text);
        
        const regex = new RegExp(`(${this.escapeRegex(this.searchQuery)})`, 'gi');
        return this.escapeHtml(text).replace(regex, '<span class="highlight">$1</span>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    formatTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleString();
        } catch (error) {
            return timestamp;
        }
    }

    updatePagination(totalCount) {
        const totalPages = Math.ceil(totalCount / this.currentLimit);
        
        if (totalPages <= 1) {
            this.paginationEl.style.display = 'none';
            return;
        }
        
        this.paginationEl.style.display = 'flex';
        this.pageInfoEl.textContent = `Page ${this.currentPage} of ${totalPages}`;
        
        // Update button states
        this.prevPageBtn.disabled = this.currentPage <= 1;
        this.nextPageBtn.disabled = this.currentPage >= totalPages;
    }

    async previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            await this.loadPage();
        }
    }

    async nextPage() {
        this.currentPage++;
        await this.loadPage();
    }

    async loadPage() {
        this.showLoading(true);
        
        try {
            const params = new URLSearchParams({
                query: this.searchQuery,
                sender: this.senderFilter,
                channel: this.channelFilter,
                date_from: this.dateFrom,
                date_to: this.dateTo,
                limit: this.currentLimit,
                offset: (this.currentPage - 1) * this.currentLimit
            });
            
            const response = await fetch(`/api/search?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayResults(data.logs, data.count);
            }
        } catch (error) {
            console.error('Page load error:', error);
            this.showError('Failed to load page. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    clearFilters() {
        this.searchQueryEl.value = '';
        this.senderFilterEl.value = '';
        this.channelFilterEl.value = '';
        this.dateFromEl.value = '';
        this.dateToEl.value = '';
        this.limitSelectEl.value = '100';
        
        this.currentPage = 1;
        this.searchQuery = '';
        this.senderFilter = '';
        this.channelFilter = '';
        this.dateFrom = '';
        this.dateTo = '';
        this.currentLimit = 100;
        
        this.resultsListEl.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <p>Enter search criteria to find messages</p>
            </div>
        `;
        this.resultsCountEl.textContent = '0 results';
        this.paginationEl.style.display = 'none';
    }

    showLoading(show) {
        this.loadingSpinnerEl.style.display = show ? 'block' : 'none';
        this.searchBtn.disabled = show;
    }

    showError(message) {
        this.resultsListEl.innerHTML = `
            <div class="no-results">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
            </div>
        `;
    }
}

// Initialize the chat search when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatSearch();
}); 