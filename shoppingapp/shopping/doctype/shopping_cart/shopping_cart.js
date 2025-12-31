// Copyright (c) 2025, tj
// License: MIT

frappe.ui.form.on('Shopping Cart', {
    refresh(frm) {

        // Always setup grid properly
        setup_cart_items_grid(frm);

        if (frm.doc.order_placed) {

            show_status_headline(frm);

            if (frm.doc.order_status !== 'Cancelled') {
                freeze_cart(frm);
            } else {
                unfreeze_cart(frm);
                add_place_order_button(frm);
            }

            frm.add_custom_button(__('Refresh Status'), () => {
                frm.reload_doc();
            });

        } else {
            unfreeze_cart(frm);
            add_place_order_button(frm);
        }
    },

    onload(frm) {
        setup_cart_items_grid(frm);
        // Listen for realtime updates to this Shopping Cart and reload when changed
        try {
            frappe.realtime.on('doc_update', (data) => {
                if (!frm.doc || !data) return;
                if (data.doctype === 'Shopping Cart' && data.name === frm.doc.name) {
                    // Only reload if document actually exists and isn't currently dirty
                    if (!frm.doc.__unsaved) {
                        frm.reload_doc();
                    }
                }
            });
        } catch (e) {
            // noop: realtime may not be available in all contexts
        }
    }
});

// --------------------------------------------------
// CART ITEM EVENTS
// --------------------------------------------------

frappe.ui.form.on('Cart Item', {

    product(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.product) {
            fetch_product_details(frm, cdt, cdn, row.product);
        }
    },

    quantity(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.quantity || row.quantity <= 0) {
            frappe.model.set_value(cdt, cdn, 'quantity', 1);
        }
        calculate_amount(frm, cdt, cdn);
    },

    rate(frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    },

    cart_items_add(frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, 'quantity', 1);
    },

    cart_items_remove(frm) {
        calculate_total(frm);
    }
});

// --------------------------------------------------
// GRID SETUP
// --------------------------------------------------

function setup_cart_items_grid(frm) {
    let grid = frm.fields_dict.cart_items.grid;

    if (!frm.doc.order_placed) {
        grid.df.cannot_add_rows = false;
        grid.df.cannot_delete_rows = false;
        grid.df.read_only = 0;
    }

    frm.refresh_field('cart_items');
}

// --------------------------------------------------
// PLACE ORDER BUTTON
// --------------------------------------------------

function add_place_order_button(frm) {
    if (
        !frm.is_new() &&
        frm.doc.cart_items?.length &&
        !frm.doc.order_placed
    ) {
        frm.add_custom_button(__('Place Order'), () => place_order(frm))
            .addClass('btn-primary');
    }
}

// --------------------------------------------------
// PLACE ORDER
// --------------------------------------------------

function place_order(frm) {

    if (!frm.doc.cart_items?.length) {
        frappe.msgprint(__('Add items before placing order'));
        return;
    }

    frappe.confirm(
        `Place order for ₹${frm.doc.total_amount || 0}?`,
        () => {
            frappe.call({
                method: 'place_order',
                doc: frm.doc,
                freeze: true,
                freeze_message: __('Placing order...'),
                callback(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Order placed successfully'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
        }
    );
}

// --------------------------------------------------
// FREEZE CART (NO GLOBAL READ ONLY ❗)
// --------------------------------------------------

function freeze_cart(frm) {

    let grid = frm.fields_dict.cart_items.grid;

    grid.df.cannot_add_rows = true;
    grid.df.cannot_delete_rows = true;
    grid.df.read_only = 1;

    grid.wrapper
        .find('.grid-add-row, .grid-remove-rows, .grid-remove-all-rows')
        .hide();

    // Lock child table fields only
    ['product', 'quantity', 'rate', 'amount'].forEach(field => {
        frappe.meta.get_docfield('Cart Item', field).read_only = 1;
    });

    frm.clear_custom_buttons();
    frm.refresh_field('cart_items');
}

// --------------------------------------------------
// UNFREEZE CART
// --------------------------------------------------

function unfreeze_cart(frm) {

    let grid = frm.fields_dict.cart_items.grid;

    grid.df.cannot_add_rows = false;
    grid.df.cannot_delete_rows = false;
    grid.df.read_only = 0;

    grid.wrapper
        .find('.grid-add-row, .grid-remove-rows, .grid-remove-all-rows')
        .show();

    ['product', 'quantity', 'rate', 'amount'].forEach(field => {
        frappe.meta.get_docfield('Cart Item', field).read_only = 0;
    });

    frm.refresh_field('cart_items');
}

// --------------------------------------------------
// STATUS HEADLINE
// --------------------------------------------------

function show_status_headline(frm) {

    if (!frm.doc.order_status) return;

    let colors = {
        Pending : 'orange',
        Confirmed : 'green',
        Packed : 'blue',
        Shipped : 'purple',
        Delivered : 'green',
        Cancelled : 'red'
    };

    frm.dashboard.set_headline(`
        <div class="alert alert-${colors[frm.doc.order_status]}">
            <b>Order Status:</b> ${frm.doc.order_status}
        </div>
    `);
}

// --------------------------------------------------
// PRODUCT FETCH
// --------------------------------------------------

function fetch_product_details(frm, cdt, cdn, product) {
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Product',
            name: product
        },
        callback(r) {
            if (r.message) {
                frappe.model.set_value(cdt, cdn, 'rate', r.message.price || 0);
                calculate_amount(frm, cdt, cdn);
            }
        }
    });
}

// --------------------------------------------------
// CALCULATIONS
// --------------------------------------------------

function calculate_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    frappe.model.set_value(
        cdt,
        cdn,
        'amount',
        (row.quantity || 0) * (row.rate || 0)
    );
    calculate_total(frm);
}

function calculate_total(frm) {
    let total = 0;
    (frm.doc.cart_items || []).forEach(row => {
        total += row.amount || 0;
    });
    frm.set_value('total_amount', total);
}
