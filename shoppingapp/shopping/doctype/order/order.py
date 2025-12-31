# Copyright (c) 2025, tj and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Order(Document):

    # --------------------------------------------------
    # BEFORE SAVE → CALCULATE TOTALS
    # --------------------------------------------------

    def before_save(self):
        self.calculate_totals()

    def calculate_totals(self):
        total = 0
        for item in self.order_items:
            item.amount = (item.quantity or 0) * (item.rate or 0)
            total += item.amount

        self.total_amount = total

    # --------------------------------------------------
    # VALIDATE → STATUS CHANGE HANDLING
    # --------------------------------------------------

    def validate(self):
        if self.is_new():
            return

        old_doc = self.get_doc_before_save()
        if not old_doc:
            return

        old_status = old_doc.order_status
        new_status = self.order_status

        # Pending → Confirmed → Reduce stock
        if old_status == "Pending" and new_status == "Confirmed":
            self.reduce_stock()

        # Confirmed → Cancelled → Restore stock
        elif old_status == "Confirmed" and new_status == "Cancelled":
            self.restore_stock()


    # --------------------------------------------------
    # STOCK FUNCTIONS
    # --------------------------------------------------

    def reduce_stock(self):
        """Reduce stock when order is confirmed"""
        
        stock_updates = []
        
        for item in self.order_items:
            product = frappe.get_doc("Product", item.product)

            # Check if sufficient stock is available
            if product.stock_qty < item.quantity:
                frappe.throw(
                    f"Insufficient stock for <b>{product.product_name}</b>.<br>"
                    f"Available: <b>{product.stock_qty}</b>, Required: <b>{item.quantity}</b>"
                )

            # Reduce stock
            product.stock_qty -= item.quantity
            product.save(ignore_permissions=True)
            
            # Track for notification
            stock_updates.append(f"{product.product_name}: -{item.quantity}")

        # Show consolidated success message
        if stock_updates:
            frappe.msgprint(
                msg="<b>Stock Reduced:</b><br>" + "<br>".join(stock_updates),
                title="Stock Updated",
                indicator="orange"
            )
            
            # Log for audit trail
            frappe.log_error(
                message=f"Stock reduced for Order {self.name}:\n" + "\n".join(stock_updates),
                title=f"Stock Reduced - {self.name}"
            )
# -----------------------------------------
            def after_save(self):
                """Sync Order status to Shopping Cart immediately"""
            self.update_shopping_cart_status()

    def update_shopping_cart_status(self):
        if not self.shopping_cart:
            return

        # Update Shopping Cart status safely
        frappe.db.set_value(
            "Shopping Cart",
            self.shopping_cart,
            {
                "order_status": self.order_status,
                "order_placed": 0 if self.order_status == "Cancelled" else 1
            }
        )

        # Ensure DB commit so list view updates instantly
        frappe.db.commit()
#---------------------------------------------
    def restore_stock(self):
        """Restore stock if order is cancelled"""
        
        stock_updates = []
        
        for item in self.order_items:
            product = frappe.get_doc("Product", item.product)
            
            # Restore stock
            product.stock_qty += item.quantity
            product.save(ignore_permissions=True)
            
            # Track for notification
            stock_updates.append(f"{product.product_name}: +{item.quantity}")

        # Show consolidated success message
        if stock_updates:
            frappe.msgprint(
                msg="<b>Stock Restored:</b><br>" + "<br>".join(stock_updates),
                title="Stock Updated",
                indicator="green"
            )
            
            # Log for audit trail
            frappe.log_error(
                message=f"Stock restored for Order {self.name}:\n" + "\n".join(stock_updates),
                title=f"Stock Restored - {self.name}"
            )