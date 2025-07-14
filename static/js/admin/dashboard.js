// Admin Dashboard JavaScript
console.log('Admin dashboard loaded');

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any admin-specific functionality here
    setupEventListeners();
});

function setupEventListeners() {
    // Add any event listeners for admin dashboard
    console.log('Setting up admin dashboard event listeners');
    
    // Example: Confirmation for admin actions
    const adminActions = document.querySelectorAll('[data-admin-action]');
    adminActions.forEach(action => {
        action.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to perform this action?')) {
                e.preventDefault();
            }
        });
    });
    
    // Initialize any admin-specific UI components
    initializeAdminComponents();
}

function initializeAdminComponents() {
    // Initialize any admin UI components here
    console.log('Initializing admin components');
    
    // Example: Initialize a date picker for admin reports
    if (typeof flatpickr !== 'undefined') {
        flatpickr("[data-date-picker]", {
            dateFormat: "Y-m-d",
            allowInput: true
        });
    }
    
    // Initialize any charts or data visualizations
    initializeAdminCharts();
}

function initializeAdminCharts() {
    // Example: Initialize admin dashboard charts using Chart.js
    if (typeof Chart === 'undefined') return;
    
    const ctx = document.getElementById('adminChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['January', 'February', 'March', 'April', 'May', 'June'],
                datasets: [{
                    label: 'Users',
                    data: [12, 19, 3, 5, 2, 3],
                    backgroundColor: 'rgba(59, 130, 246, 0.5)',
                    borderColor: 'rgb(59, 130, 246)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// Export any functions that need to be used elsewhere
window.AdminDashboard = {
    refreshData: function() {
        console.log('Refreshing admin dashboard data...');
        // Add data refresh logic here
    }
};
