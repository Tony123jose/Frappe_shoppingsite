// Copyright (c) 2025, tj and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Product", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Product", {
    validate: function (frm) {
        if (frm.doc.price === 0) {
            frappe.throw("Price cannot be zero");
        }
    }
});

