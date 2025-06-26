
/**
 * Dashboard JavaScript for Security Bot
 * Handles real-time updates, animations, and interactive features
 */

class SecurityDashboard {
    constructor() {
        this.updateInterval = 15000; // 15 seconds
        this.updateTimer = null;
        this.charts = {};
        this.isUpdating = false;
        this.chartsInitialized = false;
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
        
        this.init();
    }
    
    cleanup() {
        console.log('Dashboard destroyed');
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        this.destroyExistingCharts();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.startRealTimeUpdates();
        this.setupAnimations();
        
        console.log('Security Dashboard initialized');
    }
    
    setupEventListeners() {
        // Refresh button functionality
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-refresh]')) {
                this.refreshData();
            }
        });
        
        // Table row hover effects
        this.setupTableEffects();
        
        // Form auto-submit on filter change
        this.setupFilterAutoSubmit();
        
        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
    }
    
    setupTableEffects() {
        const tables = document.querySelectorAll('.cyber-table');
        
        tables.forEach(table => {
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                row.addEventListener('mouseenter', () => {
                    this.animateRowHover(row, true);
                });
                
                row.addEventListener('mouseleave', () => {
                    this.animateRowHover(row, false);
                });
                
                // Add click effect
                row.addEventListener('click', () => {
                    this.animateRowClick(row);
                });
            });
        });
    }
    
    animateRowHover(row, isEntering) {
        if (isEntering) {
            row.style.transform = 'translateX(8px) scale(1.01)';
            row.style.boxShadow = '0 8px 25px rgba(0, 255, 255, 0.3)';
            row.style.borderLeft = '3px solid var(--accent-cyan)';
        } else {
            row.style.transform = '';
            row.style.boxShadow = '';
            row.style.borderLeft = '';
        }
    }
    
    animateRowClick(row) {
        row.style.transform = 'scale(0.98)';
        setTimeout(() => {
            row.style.transform = '';
        }, 150);
    }
    
    setupFilterAutoSubmit() {
        const filterSelects = document.querySelectorAll('.filter-form select');
        
        filterSelects.forEach(select => {
            select.addEventListener('change', () => {
                // Add loading state
                this.showFilterLoading(true);
                
                // Submit form after short delay for better UX
                setTimeout(() => {
                    select.closest('form').submit();
                }, 300);
            });
        });
    }
    
    showFilterLoading(show) {
        const filterForm = document.querySelector('.filter-form');
        
        if (show) {
            filterForm.style.opacity = '0.7';
            filterForm.style.pointerEvents = 'none';
        } else {
            filterForm.style.opacity = '';
            filterForm.style.pointerEvents = '';
        }
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R - Refresh dashboard
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.refreshData();
            }
            
            // Ctrl/Cmd + F - Focus filter
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                const firstFilter = document.querySelector('.filter-form select');
                if (firstFilter) {
                    firstFilter.focus();
                }
            }
        });
    }
    
    initializeCharts() {
        // Only run once to prevent canvas conflicts
        if (this.chartsInitialized) return;
        
        try {
            // Destroy existing charts to prevent canvas conflicts
            this.destroyExistingCharts();
            
            // Initialize charts with error handling
            const tierChartCanvas = document.getElementById('tierChart');
            if (tierChartCanvas && window.Chart) {
                this.initTierChart(tierChartCanvas);
            }
            
            const timelineChartCanvas = document.getElementById('threatTimeline');
            if (timelineChartCanvas && window.Chart) {
                this.initTimelineChart(timelineChartCanvas);
            }
            
            this.chartsInitialized = true;
        } catch (error) {
            console.warn('Chart initialization warning:', error.message);
        }
    }
    
    destroyExistingCharts() {
        // Destroy any existing Chart.js instances
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }
    
    initTierChart(canvas) {
        const ctx = canvas.getContext('2d');
        
        // Get data from data attributes or global variables
        const tierData = this.getTierData();
        
        // Destroy existing chart if it exists
        if (this.charts.tierChart) {
            this.charts.tierChart.destroy();
        }
        
        // Initialize new chart
        this.charts.tierChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Free', 'Monthly', 'Premium', 'Enterprise'],
                    datasets: [{
                        data: tierData,
                        backgroundColor: [
                            'rgba(108, 117, 125, 0.8)',
                            'rgba(0, 255, 255, 0.8)', 
                            'rgba(0, 255, 136, 0.8)',
                            'rgba(255, 193, 7, 0.8)'
                        ],
                        borderColor: [
                            '#6c757d',
                            '#00ffff',
                            '#00ff88',
                            '#ffc107'
                        ],
                        borderWidth: 3,
                        hoverBorderWidth: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#e0e0e0',
                                font: {
                                    family: 'Exo 2',
                                    size: 12
                                },
                                padding: 20,
                                usePointStyle: true
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#00ffff',
                            bodyColor: '#e0e0e0',
                            borderColor: '#00ffff',
                            borderWidth: 1
                        }
                    },
                    elements: {
                        arc: {
                            borderWidth: 2
                        }
                    },
                    animation: {
                        animateRotate: true,
                        animateScale: true,
                        duration: 2000
                    }
                }
            });
        }
    }
    
    getTierData() {
        // Try to get data from window globals set by template
        if (window.tierDistribution) {
            return [
                window.tierDistribution.free || 0,
                window.tierDistribution.monthly || 0,
                window.tierDistribution.premium || 0,
                window.tierDistribution.enterprise || 0
            ];
        }
        
        // Fallback to parsing from template or return zeros
        return [0, 0, 0, 0];
    }
    
    initTimelineChart(canvas) {
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.charts.timelineChart) {
            this.charts.timelineChart.destroy();
        }
        
        // Initialize new chart
        this.charts.timelineChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: this.getTimelineLabels(),
                    datasets: [{
                        label: 'Threats Detected',
                        data: this.getTimelineData(),
                        borderColor: '#ff3030',
                        backgroundColor: 'rgba(255, 48, 48, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: '#e0e0e0'
                            },
                            grid: {
                                color: 'rgba(0, 255, 255, 0.1)'
                            }
                        },
                        x: {
                            ticks: {
                                color: '#e0e0e0'
                            },
                            grid: {
                                color: 'rgba(0, 255, 255, 0.1)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                color: '#e0e0e0'
                            }
                        }
                    }
                }
            });
        }
    }
    
    getTimelineLabels() {
        // Generate last 24 hours labels
        const labels = [];
        for (let i = 23; i >= 0; i--) {
            const date = new Date();
            date.setHours(date.getHours() - i);
            labels.push(date.getHours().toString().padStart(2, '0') + ':00');
        }
        return labels;
    }
    
    getTimelineData() {
        // Fetch real-time data from backend API
        return this.fetchTimelineFromAPI();
    }
    
    async fetchTimelineFromAPI() {
        try {
            const response = await fetch('/api/timeline-data');
            if (response.ok) {
                const data = await response.json();
                return data.timeline || new Array(24).fill(0);
            }
        } catch (error) {
            console.warn('Timeline API unavailable, using empty data');
        }
        return new Array(24).fill(0);
    }
    
    startRealTimeUpdates() {
        // Initial update after page load
        setTimeout(() => {
            this.updateDashboardStats();
        }, 2000);
        
        // Set up recurring updates
        this.updateTimer = setInterval(() => {
            this.updateDashboardStats();
        }, this.updateInterval);
        
        console.log('Real-time updates started');
    }
    
    async updateDashboardStats() {
        if (this.isUpdating) return;
        
        this.isUpdating = true;
        this.showUpdateIndicator(true);
        
        try {
            const response = await fetch('/api/realtime-stats', {
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.updateStatCards(data.stats);
                this.updateLastUpdateTime();
                this.showUpdateSuccess();
            } else {
                throw new Error(data.message || 'Update failed');
            }
            
        } catch (error) {
            console.error('Dashboard update failed:', error);
            this.showUpdateError(error.message);
        } finally {
            this.isUpdating = false;
            this.showUpdateIndicator(false);
        }
    }
    
    updateStatCards(stats) {
        const updates = [
            { id: 'total-groups', value: stats.total_groups },
            { id: 'active-groups', value: stats.active_groups },
            { id: 'total-scans', value: stats.total_scans },
            { id: 'threats-blocked', value: stats.threats_blocked },
            { id: 'total-users', value: stats.total_users },
            { id: 'total-credits-purchased', value: stats.total_credits_purchased },
            { id: 'total-credits-used', value: stats.total_credits_used },
            { id: 'active-credit-users', value: stats.active_credit_users }
        ];
        
        updates.forEach(update => {
            this.updateStatWithAnimation(update.id, update.value);
        });
    }
    
    updateStatWithAnimation(elementId, newValue) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const currentValue = parseInt(element.textContent) || 0;
        
        if (currentValue !== newValue) {
            // Animate the change
            element.style.color = '#00ffff';
            element.style.transform = 'scale(1.1)';
            element.style.textShadow = '0 0 30px #00ffff';
            
            // Counter animation
            this.animateCounter(element, currentValue, newValue, 800);
            
            setTimeout(() => {
                element.style.color = '';
                element.style.transform = '';
                element.style.textShadow = '';
            }, 1000);
        }
    }
    
    animateCounter(element, start, end, duration) {
        const startTime = Date.now();
        const diff = end - start;
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function
            const easeOutCubic = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (diff * easeOutCubic));
            
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    updateLastUpdateTime() {
        const updateElement = document.getElementById('last-update');
        if (updateElement) {
            const now = new Date().toLocaleTimeString();
            updateElement.innerHTML = `<i class="fas fa-check text-success"></i> Updated ${now}`;
        }
    }
    
    showUpdateIndicator(show) {
        const updateElement = document.getElementById('last-update');
        if (updateElement && show) {
            updateElement.innerHTML = '<i class="fas fa-sync-alt fa-spin text-info"></i> Updating...';
        }
    }
    
    showUpdateSuccess() {
        // Flash success indicator
        const indicators = document.querySelectorAll('.status-indicator');
        indicators.forEach(indicator => {
            indicator.style.color = '#00ff88';
            setTimeout(() => {
                indicator.style.color = '';
            }, 1000);
        });
    }
    
    showUpdateError(message) {
        const updateElement = document.getElementById('last-update');
        if (updateElement) {
            updateElement.innerHTML = `<i class="fas fa-exclamation-triangle text-warning"></i> ${message}`;
        }
        
        // Show error notification
        this.showNotification('Update failed: ' + message, 'error');
    }
    
    refreshData() {
        // Force immediate update
        this.updateDashboardStats();
        
        // Show loading state on refresh buttons
        const refreshButtons = document.querySelectorAll('[data-refresh]');
        refreshButtons.forEach(btn => {
            const originalContent = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            btn.disabled = true;
            
            setTimeout(() => {
                btn.innerHTML = originalContent;
                btn.disabled = false;
            }, 2000);
        });
    }
    
    setupAnimations() {
        // Animate cards on page load
        this.animateCardsOnLoad();
        
        // Setup scroll animations
        this.setupScrollAnimations();
        
        // Setup pulse animations for threat indicators
        this.setupThreatIndicators();
    }
    
    animateCardsOnLoad() {
        const cards = document.querySelectorAll('.glass-card, .stat-card');
        
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.6s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }
    
    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);
        
        // Observe elements that should animate on scroll
        const animateElements = document.querySelectorAll('.activity-item, .revenue-item');
        animateElements.forEach(el => observer.observe(el));
    }
    
    setupThreatIndicators() {
        const threatStats = document.querySelectorAll('.threat-stat .stat-value');
        
        threatStats.forEach(stat => {
            const value = parseInt(stat.textContent);
            if (value > 0) {
                stat.classList.add('pulse-glow');
                
                // Add random pulse delays for variety
                const delay = Math.random() * 2000;
                stat.style.animationDelay = `${delay}ms`;
            }
        });
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Add styles
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: 'rgba(0, 0, 0, 0.9)',
            color: '#fff',
            padding: '15px 20px',
            borderRadius: '10px',
            border: `1px solid ${this.getNotificationColor(type)}`,
            boxShadow: `0 0 20px ${this.getNotificationColor(type)}`,
            zIndex: '9999',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Auto remove
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    }
    
    getNotificationColor(type) {
        const colors = {
            success: '#00ff88',
            error: '#ff3030',
            warning: '#ffa500',
            info: '#00ffff'
        };
        return colors[type] || colors.info;
    }
    
    destroy() {
        // Clean up timers and event listeners
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        
        console.log('Dashboard destroyed');
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Initialize dashboard when DOM is ready
let dashboardInstance = null;

document.addEventListener('DOMContentLoaded', function() {
    // Clean up existing instance
    if (dashboardInstance && typeof dashboardInstance.cleanup === 'function') {
        dashboardInstance.cleanup();
    }
    dashboardInstance = new SecurityDashboard();
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (dashboardInstance) {
        dashboardInstance.destroy();
    }
});

// Export for potential external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SecurityDashboard;
}
