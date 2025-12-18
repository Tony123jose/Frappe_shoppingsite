// Copyright (c) 2025, tj and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shopping Cart", {
refresh(frm) {

//Task 10: Auto-fill Product Price in Cart Items
frappe.ui.form.on('Cart Item', {
  product: function(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.product) {
      frappe.db.get_doc('Product', row.product).then(doc => {
        row.rate = doc.price;
        row.amount = row.rate * (row.quantity || 1);
        frm.refresh_field('cart_items');
      });
    }
  },
  quantity: function(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.rate) {
      row.amount = row.rate * (row.quantity || 0);
      frm.refresh_field('cart_items');
    }
  }
});

//11: Auto-calculation of Cart Total


function recalc_cart_total(frm) {
  let total = 0;
  frm.doc.cart_items.forEach(item => {
    total += item.amount || 0;
  });
  frm.set_value('total_amount', total);
}

frappe.ui.form.on('Cart Item', {
  product: function(frm, cdt, cdn) { recalc_cart_total(frm); },
  quantity: function(frm, cdt, cdn) { recalc_cart_total(frm); }
});

// Task 13: Create "Place Order" Button

frappe.ui.form.on('Shopping Cart', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Place Order'), function() {
                place_order(frm);
            }).addClass('btn-primary');
        }
    }
});

function place_order(frm) {
    frappe.call({
        method: 'shoppingapp.shopping.doctype.shopping_cart.shopping_cart.place_order',
        args: {
            cart_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                frappe.msgprint(
                    __('Order ' + r.message.product_name + ' created successfully!')
                );
                frm.reload_doc();
            }
        }
    });
}


	},
 });
