# Copyright (c) 2025, tj and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
 
class ShoppingCart(Document):
   
    def validate(self):
        """Validate before saving"""
        # Don't set order_status on new carts
        if self.is_new() and not self.order_placed:
            self.order_status = None

    @frappe.whitelist()
   
    def place_order(self):
        """Create Order from Shopping Cart and freeze cart"""
        # Prevent duplicate order
        if self.order_placed:
            frappe.throw("Order already placed for this cart")

        # Validate we have items
        if not self.cart_items or len(self.cart_items) == 0:
            frappe.throw("Cannot place order - cart is empty")

        # Validate all items have products
        for item in self.cart_items:
            if not item.product:
                frappe.throw("All cart items must have a product selected")
            if not item.quantity or item.quantity <= 0:
                frappe.throw(f"Invalid quantity for {item.product}")

        # Step 1: Validate stock
        self.validate_stock()

        # Step 2: Create Order
        order = frappe.new_doc("Order")
        order.customer = self.customer
        order.order_status = "Pending"
        
        # Link the Order back to this Shopping Cart
        order.shopping_cart = self.name
        print("Creating Order from Shopping Cart:", self.name)

        # Step 3: Copy items
        for cart_item in self.cart_items:
            order.append("order_items", {
                "product": cart_item.product,
                "quantity": cart_item.quantity,
                "rate": cart_item.rate,
                "amount": cart_item.amount
            })

        # Step 4: Save Order
        order.insert(ignore_permissions=True)

        # Step 5: Freeze Cart and set initial status
        self.order_placed = 1
        self.order_status = "Pending"
        self.save(ignore_permissions=True)

        # Step 6: Return order reference
        return order.name

    # --------------------------------------------------

    def validate_stock(self):
        """Check if sufficient stock is available"""

        for item in self.cart_items:
            product = frappe.get_doc("Product", item.product)

            if product.stock_qty < item.quantity:

                # Log error
                frappe.log_error(
                    message=f"""
                    Stock Validation Failed
                    ----------------------
                    Product: {product.product_name} ({item.product})
                    Available Stock: {product.stock_qty}
                    Required Quantity: {item.quantity}
                    Shortage: {item.quantity - product.stock_qty}
                    Cart: {self.name}
                    Customer: {self.customer}
                    """,
                    title=f"Insufficient Stock - {product.product_name}"
                )

                # Stop execution
                frappe.throw(
                    f"Insufficient stock for {product.product_name}. "
                    f"Available: {product.stock_qty}, Required: {item.quantity}"
                )