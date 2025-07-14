// Dealer Dashboard JavaScript
console.log('Dealer dashboard loaded');

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dealer dashboard functionality
    setupDealerEventListeners();
    loadDealerData();
});

function setupDealerEventListeners() {
    console.log('Setting up dealer dashboard event listeners');
    
    // Order status filter
    const statusFilters = document.querySelectorAll('.status-filter');
    statusFilters.forEach(filter => {
        filter.addEventListener('click', function(e) {
            e.preventDefault();
            const status = this.getAttribute('data-status');
            filterOrdersByStatus(status);
        });
    });
    
    // Date range filter
    const dateRangePicker = document.getElementById('date-range-picker');
    if (dateRangePicker) {
        if (typeof flatpickr !== 'undefined') {
            flatpickr(dateRangePicker, {
                mode: 'range',
                dateFormat: 'Y-m-d',
                onChange: function(selectedDates, dateStr) {
                    if (selectedDates.length === 2) {
                        filterOrdersByDateRange(selectedDates[0], selectedDates[1]);
                    }
                }
            });
        }
    }
    
    // Initialize any dealer-specific UI components
    initializeDealerComponents();
}

function loadDealerData() {
    console.log('Loading dealer data...');
    // Fetch and load dealer-specific data
    
    // Example: Load recent orders
    fetch('/api/dealer/orders?limit=5')
        .then(response => response.json())
        .then(data => {
            updateOrdersTable(data.orders);
            updateSalesStats(data.stats);
        })
        .catch(error => {
            console.error('Error loading dealer data:', error);
            showNotification('Failed to load dealer data', 'error');
        });
}

function updateOrdersTable(orders) {
    const tbody = document.querySelector('#orders-table tbody');
    if (!tbody) return;
    
    if (!orders || orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4">No orders found</td></tr>';
        return;
    }
    
    tbody.innerHTML = orders.map(order => `
        <tr>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">#${order.order_number}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${new Date(order.created_at).toLocaleDateString()}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${order.customer_name}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">$${order.amount.toFixed(2)}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                    ${getStatusClass(order.status)}">
                    ${order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                </span>
            </td>
        </tr>
    `).join('');
}

function updateSalesStats(stats) {
    if (!stats) return;
    
    // Update sales total
    const salesTotal = document.getElementById('sales-total');
    if (salesTotal) salesTotal.textContent = `$${stats.total_sales.toFixed(2)}`;
    
    // Update order count
    const orderCount = document.getElementById('order-count');
    if (orderCount) orderCount.textContent = stats.order_count;
    
    // Update customer count
    const customerCount = document.getElementById('customer-count');
    if (customerCount) customerCount.textContent = stats.customer_count;
}

function filterOrdersByStatus(status) {
    console.log('Filtering orders by status:', status);
    // Add filtering logic here
    
    // Update active filter button
    document.querySelectorAll('.status-filter').forEach(btn => {
        btn.classList.remove('bg-green-700', 'text-white');
        btn.classList.add('text-green-100', 'hover:bg-green-700');
    });
    
    const activeBtn = document.querySelector(`.status-filter[data-status="${status}"]`);
    if (activeBtn) {
        activeBtn.classList.remove('text-green-100', 'hover:bg-green-700');
        activeBtn.classList.add('bg-green-700', 'text-white');
    }
    
    // Reload orders with status filter
    fetch(`/api/dealer/orders?status=${status}`)
        .then(response => response.json())
        .then(data => updateOrdersTable(data.orders))
        .catch(console.error);
}

function filterOrdersByDateRange(startDate, endDate) {
    console.log('Filtering orders by date range:', startDate, endDate);
    // Add date range filtering logic here
    
    const start = startDate.toISOString().split('T')[0];
    const end = endDate.toISOString().split('T')[0];
    
    fetch(`/api/dealer/orders?start_date=${start}&end_date=${end}`)
        .then(response => response.json())
        .then(data => updateOrdersTable(data.orders))
        .catch(console.error);
}

function getStatusClass(status) {
    const statusClasses = {
        'completed': 'bg-green-100 text-green-800',
        'pending': 'bg-yellow-100 text-yellow-800',
        'processing': 'bg-blue-100 text-blue-800',
        'cancelled': 'bg-red-100 text-red-800',
        'shipped': 'bg-purple-100 text-purple-800'
    };
    
    return statusClasses[status] || 'bg-gray-100 text-gray-800';
}

function showNotification(message, type = 'info') {
    // Implement notification system
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Example: Show a toast notification
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded shadow-lg text-white ${
        type === 'error' ? 'bg-red-500' : 
        type === 'success' ? 'bg-green-500' : 'bg-blue-500'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Export any functions that need to be used elsewhere
window.DealerDashboard = {
    refreshOrders: function() {
        console.log('Refreshing dealer orders...');
        loadDealerData();
    }
};
