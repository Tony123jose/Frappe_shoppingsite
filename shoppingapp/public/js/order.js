/**
 * My Orders Page JavaScript
 * 
 * NOTE: This is a standalone JS file version.
 * If you use this, REMOVE the inline <script> from my_orders.html
 * Place this file in: shoppingapp/public/js/my_orders.js
 * And include it in your HTML with: {% block script %}{% endblock %}
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // View Order Details Buttons
    document.querySelectorAll('.view-order-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            let orderId = this.getAttribute('data-order');
            viewOrderDetails(orderId);
        });
    });
    
    // Cancel Order Buttons
    document.querySelectorAll('.cancel-order-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            let orderId = this.getAttribute('data-order');
            cancelOrder(orderId);
        });
    });
});

/**
 * View order details
 * @param {string} orderId - Order name/ID
 */
function viewOrderDetails(orderId) {
    frappe.msgprint({
        title: 'Order Details',
        message: 'Viewing details for order: <strong>' + orderId + '</strong><br><br>' +
                 '<em>This feature can be enhanced to show detailed tracking, delivery info, etc.</em>',
        indicator: 'blue'
    });
}

/**
 * Cancel an order
 * @param {string} orderId - Order name/ID
 */
function cancelOrder(orderId) {
    frappe.confirm(
        'Are you sure you want to cancel order <strong>' + orderId + '</strong>?',
        function() {
            // User confirmed - disable button and show loading
            let button = document.querySelector('.cancel-order-btn[data-order="' + orderId + '"]');
            if (button) {
                button.disabled = true;
                button.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Cancelling...';
            }
            
            // Call API
            frappe.call({
                method: 'shoppingapp.api.cancel_order',
                args: {
                    order_name: orderId
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: r.message.message,
                            indicator: 'orange'
                        });
                        
                        // Reload page after 1.5 seconds to show updated status
                        setTimeout(function() {
                            window.location.reload();
                        }, 1500);
                    } else {
                        frappe.show_alert({
                            message: r.message.message || 'Error cancelling order',
                            indicator: 'red'
                        });
                        
                        // Re-enable button
                        if (button) {
                            button.disabled = false;
                            button.innerHTML = '<i class="fa fa-times"></i> Cancel Order';
                        }
                    }
                },
                error: function(err) {
                    console.error('Cancel order error:', err);
                    frappe.show_alert({
                        message: 'Error cancelling order. Please try again.',
                        indicator: 'red'
                    });
                    
                    // Re-enable button
                    if (button) {
                        button.disabled = false;
                        button.innerHTML = '<i class="fa fa-times"></i> Cancel Order';
                    }
                }
            });
        },
        function() {
            // User cancelled - do nothing
        }
    );
}