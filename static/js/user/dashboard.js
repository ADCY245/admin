// User Dashboard JavaScript
console.log('User dashboard loaded');

document.addEventListener('DOMContentLoaded', function() {
    // Initialize user dashboard functionality
    setupUserEventListeners();
    loadUserData();
});

function setupUserEventListeners() {
    console.log('Setting up user dashboard event listeners');
    
    // Order history navigation
    const orderLinks = document.querySelectorAll('[data-order-details]');
    orderLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const orderId = this.getAttribute('data-order-id');
            showOrderDetails(orderId);
        });
    });
    
    // Account settings form
    const accountForm = document.getElementById('account-settings-form');
    if (accountForm) {
        accountForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveAccountSettings(this);
        });
    }
    
    // Password change form
    const passwordForm = document.getElementById('change-password-form');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            changePassword(this);
        });
    }
    
    // Initialize any user-specific UI components
    initializeUserComponents();
}

function loadUserData() {
    console.log('Loading user data...');
    
    // Fetch and load user-specific data
    fetch('/api/user/dashboard')
        .then(response => response.json())
        .then(data => {
            updateUserProfile(data.user);
            updateOrderHistory(data.orders);
            updateAccountStats(data.stats);
        })
        .catch(error => {
            console.error('Error loading user data:', error);
            showNotification('Failed to load your data. Please try again later.', 'error');
        });
}

function updateUserProfile(userData) {
    // Update profile information in the UI
    const elements = {
        username: document.getElementById('user-username'),
        email: document.getElementById('user-email'),
        joinDate: document.getElementById('user-join-date'),
        avatar: document.querySelector('.user-avatar')
    };
    
    if (elements.username) elements.username.textContent = userData.username;
    if (elements.email) elements.email.textContent = userData.email;
    if (elements.joinDate) {
        const joinDate = new Date(userData.created_at);
        elements.joinDate.textContent = joinDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
    if (elements.avatar && userData.avatar_url) {
        elements.avatar.src = userData.avatar_url;
        elements.avatar.alt = `${userData.username}'s avatar`;
    }
}

function updateOrderHistory(orders) {
    const orderList = document.getElementById('order-history');
    if (!orderList) return;
    
    if (!orders || orders.length === 0) {
        orderList.innerHTML = `
            <div class="text-center py-8">
                <p class="text-gray-500 mb-4">You haven't placed any orders yet.</p>
                <a href="/products" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    Start Shopping
                </a>
            </div>
        `;
        return;
    }
    
    orderList.innerHTML = orders.map(order => `
        <div class="bg-white shadow overflow-hidden rounded-lg mb-4">
            <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
                <div>
                    <h3 class="text-lg leading-6 font-medium text-gray-900">
                        Order #${order.order_number}
                    </h3>
                    <p class="mt-1 max-w-2xl text-sm text-gray-500">
                        Placed on ${new Date(order.created_at).toLocaleDateString()}
                    </p>
                </div>
                <div>
                    <span class="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium ${getStatusClass(order.status).join(' ')}">
                        ${order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                    </span>
                </div>
            </div>
            <div class="border-t border-gray-200 px-4 py-5 sm:px-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <h4 class="text-sm font-medium text-gray-500">Delivery Address</h4>
                        <p class="mt-1 text-sm text-gray-900">
                            ${order.shipping_address?.line1 || 'N/A'}<br>
                            ${order.shipping_address?.line2 || ''}
                            ${order.shipping_address?.city}, ${order.shipping_address?.state || ''} ${order.shipping_address?.postal_code || ''}<br>
                            ${order.shipping_address?.country || ''}
                        </p>
                    </div>
                    <div>
                        <h4 class="text-sm font-medium text-gray-500">Order Summary</h4>
                        <div class="mt-1">
                            <p class="text-sm text-gray-900">
                                ${order.items.length} ${order.items.length === 1 ? 'item' : 'items'}<br>
                                Total: $${order.total_amount.toFixed(2)}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="mt-4 flex justify-end">
                    <a href="/orders/${order.id}" class="text-sm font-medium text-blue-600 hover:text-blue-500">
                        View Order Details <span aria-hidden="true">&rarr;</span>
                    </a>
                </div>
            </div>
        </div>
    `).join('');
}

function updateAccountStats(stats) {
    if (!stats) return;
    
    // Update order count
    const orderCount = document.getElementById('order-count');
    if (orderCount) orderCount.textContent = stats.order_count || 0;
    
    // Update total spent
    const totalSpent = document.getElementById('total-spent');
    if (totalSpent) {
        totalSpent.textContent = stats.total_spent ? `$${stats.total_spent.toFixed(2)}` : '$0.00';
    }
    
    // Update loyalty points if available
    const loyaltyPoints = document.getElementById('loyalty-points');
    if (loyaltyPoints && typeof stats.loyalty_points !== 'undefined') {
        loyaltyPoints.textContent = stats.loyalty_points || 0;
    }
}

function showOrderDetails(orderId) {
    console.log('Showing order details for:', orderId);
    // Implement order details modal or page navigation
    window.location.href = `/orders/${orderId}`;
}

function saveAccountSettings(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    fetch('/api/user/profile', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Profile updated successfully', 'success');
            updateUserProfile(data.user);
        } else {
            throw new Error(data.message || 'Failed to update profile');
        }
    })
    .catch(error => {
        console.error('Error updating profile:', error);
        showNotification(error.message || 'Failed to update profile', 'error');
    });
}

function changePassword(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    if (data.new_password !== data.confirm_password) {
        showNotification('New passwords do not match', 'error');
        return;
    }
    
    fetch('/api/user/change-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            current_password: data.current_password,
            new_password: data.new_password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Password changed successfully', 'success');
            form.reset();
        } else {
            throw new Error(data.message || 'Failed to change password');
        }
    })
    .catch(error => {
        console.error('Error changing password:', error);
        showNotification(error.message || 'Failed to change password', 'error');
    });
}

function getStatusClass(status) {
    const baseClasses = ['px-2.5', 'py-0.5', 'rounded-full', 'text-xs', 'font-medium'];
    
    const statusClasses = {
        'completed': ['bg-green-100', 'text-green-800'],
        'pending': ['bg-yellow-100', 'text-yellow-800'],
        'processing': ['bg-blue-100', 'text-blue-800'],
        'shipped': ['bg-purple-100', 'text-purple-800'],
        'delivered': ['bg-green-100', 'text-green-800'],
        'cancelled': ['bg-red-100', 'text-red-800']
    };
    
    return [...baseClasses, ...(statusClasses[status] || ['bg-gray-100', 'text-gray-800'])];
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg transform transition-all duration-300 ease-in-out ${
        type === 'error' ? 'bg-red-500' :
        type === 'success' ? 'bg-green-500' :
        'bg-blue-500'
    } text-white`;
    
    notification.innerHTML = `
        <div class="flex items-center">
            <svg class="h-5 w-5 mr-2 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                ${type === 'error' ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />' :
                type === 'success' ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />' :
                '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />'}
            </svg>
            <span>${message}</span>
            <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                <span class="sr-only">Close</span>
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    `;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function initializeUserComponents() {
    // Initialize any user-specific UI components here
    console.log('Initializing user components');
    
    // Example: Initialize a date picker for order filtering
    if (typeof flatpickr !== 'undefined') {
        const dateFilter = document.getElementById('order-date-filter');
        if (dateFilter) {
            flatpickr(dateFilter, {
                mode: 'range',
                dateFormat: 'Y-m-d',
                onChange: function(selectedDates, dateStr) {
                    if (selectedDates.length === 2) {
                        filterOrdersByDate(selectedDates[0], selectedDates[1]);
                    }
                }
            });
        }
    }
    
    // Initialize any other user interface components
    initializeUserInterface();
}

function initializeUserInterface() {
    // Initialize any additional UI components
    console.log('Initializing user interface components');
    
    // Example: Initialize tooltips
    if (typeof tippy !== 'undefined') {
        tippy('[data-tippy-content]');
    }
    
    // Initialize any other third-party libraries or custom components
}

// Export any functions that need to be used elsewhere
window.UserDashboard = {
    refreshData: function() {
        console.log('Refreshing user dashboard data...');
        loadUserData();
    },
    showNotification: showNotification
};
