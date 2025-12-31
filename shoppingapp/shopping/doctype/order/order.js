// Copyright (c) 2025, tj and contributors
// For license information, please see license.txt

frappe.ui.form.on('Order', {
    refresh: function(frm) {
        // Show status badge with indicator
        show_status_indicator(frm);
        
        // Add button to view Shopping Cart if linked
        if (frm.doc.shopping_cart && !frm.is_new()) {
            frm.add_custom_button(__('View Shopping Cart'), function() {
                frappe.set_route('Form', 'Shopping Cart', frm.doc.shopping_cart);
            }, __('Actions'));
        }
        
        // Store current status for change detection
        frm.doc.__previous_status = frm.doc.order_status;
    },

    before_save: function(frm) {
        // Warn user about critical status changes
        if (frm.doc.__previous_status && frm.doc.__previous_status !== frm.doc.order_status) {
            return validate_status_change(frm, frm.doc.__previous_status, frm.doc.order_status);
        }
    },

    order_status: function(frm) {
        // Show immediate feedback when status changes
        let old_status = frm.doc.__previous_status || 'Pending';
        let new_status = frm.doc.order_status;
        
        // Provide contextual information for each status change
        show_status_change_info(frm, old_status, new_status);
    }
});

// --------------------------------------------------
// Order Item child table handlers
// --------------------------------------------------

frappe.ui.form.on('Order Item', {
    product: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.product) {
            fetch_product_details(frm, cdt, cdn, row.product);
        }
    },

    quantity: function(frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },

    rate: function(frm, cdt, cdn) {
        calculate_item_amount(frm, cdt, cdn);
    },

    order_items_remove: function(frm) {
        calculate_order_total(frm);
    }
});

// --------------------------------------------------
// HELPER FUNCTIONS
// --------------------------------------------------

// Show status indicator on dashboard
function show_status_indicator(frm) {
    if (!frm.doc.order_status) {
        return;
    }

    let status_config = {
        'Pending': { color: 'orange', message: 'Awaiting confirmation' },
        'Confirmed': { color: 'green', message: 'Order confirmed, stock reduced' },
        'Packed': { color: 'blue', message: 'Order packed for shipment' },
        'Shipped': { color: 'purple', message: 'Order shipped to customer' },
        'Delivered': { color: 'green', message: 'Order delivered successfully' },
        'Cancelled': { color: 'red', message: 'Order cancelled, stock restored' }
    };

    let config = status_config[frm.doc.order_status] || { color: 'gray', message: '' };
    
    frm.dashboard.add_indicator(
        frm.doc.order_status + (config.message ? ' - ' + config.message : ''), 
        config.color
    );
}

// Show status change information
function show_status_change_info(frm, old_status, new_status) {
    let messages = {
        'Confirmed': {
            from: 'Pending',
            title: 'Confirming Order',
            message: 'Stock will be reduced when you save this order.',
            indicator: 'orange'
        },
        'Cancelled': {
            from: 'Confirmed',
            title: 'Cancelling Order',
            message: 'Stock will be restored and Shopping Cart will be unlocked when you save.',
            indicator: 'orange'
        },
        'Packed': {
            from: 'Confirmed',
            title: 'Order Ready',
            message: 'Order is now packed and ready for shipment.',
            indicator: 'blue'
        },
        'Shipped': {
            from: 'Packed',
            title: 'Order Shipped',
            message: 'Order has been shipped to the customer.',
            indicator: 'purple'
        },
        'Delivered': {
            from: 'Shipped',
            title: 'Order Complete',
            message: 'Order has been successfully delivered.',
            indicator: 'green'
        }
    };

    let info = messages[new_status];
    if (info && old_status === info.from) {
        frappe.show_alert({
            message: '<b>' + info.title + '</b><br>' + info.message,
            indicator: info.indicator
        }, 7);
    }
}

// Validate critical status changes
function validate_status_change(frm, old_status, new_status) {
    return new Promise((resolve) => {
        // Critical change: Confirming order (will reduce stock)
        if (old_status === 'Pending' && new_status === 'Confirmed') {
            frappe.confirm(
                '<b>Confirm Order?</b><br><br>' +
                'This will reduce stock for all items in this order.<br>' +
                'Total Amount: ₹' + (frm.doc.total_amount || 0).toFixed(2) + '<br>' +
                'Items: ' + (frm.doc.order_items?.length || 0) + '<br><br>' +
                'Do you want to continue?',
                function() {
                    resolve(true);
                },
                function() {
                    // Revert status change
                    frm.set_value('order_status', old_status);
                    frappe.show_alert({
                        message: __('Status change cancelled'),
                        indicator: 'orange'
                    }, 3);
                    resolve(false);
                }
            );
            return;
        }

        // Critical change: Cancelling confirmed order (will restore stock)
        if (old_status === 'Confirmed' && new_status === 'Cancelled') {
            frappe.confirm(
                '<b>Cancel Order?</b><br><br>' +
                'This will restore stock and unlock the Shopping Cart.<br>' +
                'Customer will be able to place a new order.<br><br>' +
                'Are you sure you want to cancel this order?',
                function() {
                    resolve(true);
                },
                function() {
                    // Revert status change
                    frm.set_value('order_status', old_status);
                    frappe.show_alert({
                        message: __('Cancellation aborted'),
                        indicator: 'orange'
                    }, 3);
                    resolve(false);
                }
            );
            return;
        }

        // No validation needed for other changes
        resolve(true);
    });
}

// Fetch product details when product is selected
function fetch_product_details(frm, cdt, cdn, product_id) {
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Product',
            name: product_id
        },
        callback: function(r) {
            if (r.message) {
                let product = r.message;
                let row = locals[cdt][cdn];
                
                // Set rate from product price
                frappe.model.set_value(cdt, cdn, 'rate', product.price || 0);
                
                // Warn if quantity exceeds available stock
                if (product.stock_qty !== undefined && row.quantity > product.stock_qty) {
                    frappe.show_alert({
                        message: __('Warning: Only {0} units available for {1}', 
                            [product.stock_qty, product.product_name || product_id]),
                        indicator: 'orange'
                    }, 5);
                }
                
                calculate_item_amount(frm, cdt, cdn);
            }
        },
        error: function() {
            frappe.msgprint({
                title: __('Error'),
                indicator: 'red',
                message: __('Failed to fetch product details')
            });
        }
    });
}

// Calculate amount for individual item
function calculate_item_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    if (row.quantity && row.rate) {
        let amount = row.quantity * row.rate;
        frappe.model.set_value(cdt, cdn, 'amount', amount);
    }

    calculate_order_total(frm);
}

// Calculate total order amount
function calculate_order_total(frm) {
    let total = 0;

    if (frm.doc.order_items) {
        frm.doc.order_items.forEach(function(item) {
            total += item.amount || 0;
        });
    }

    frm.set_value('total_amount', total);
}