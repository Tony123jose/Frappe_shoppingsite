# Copyright (c) 2025, tj and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ShoppingCart(Document):
	pass

# Task 12: Validate Stock Availability



import frappe
from frappe import _

def validate_stock(doc):
    for item in doc.cart_items:
        product = frappe.get_doc('Product', item.product)
        if product.stock_qty < item.quantity:
            frappe.throw(
                _('Insufficient stock for {0}. Available: {1}, Requested: {2}').format(
                    item.product, product.stock_qty, item.quantity
                )
            )


# @frappe.whitelist()
# def place_order(cart_name):
#     cart = frappe.get_doc('Shopping Cart', cart_name)
    
#     # Validate stock
#     for item in cart.cart_items:
#         product = frappe.get_doc('Product', item.product)
#         if product.stock_qty < item.quantity:
#             frappe.throw(
#                 _('Insufficient stock for {0}').format(item.product)
#             )
    
@frappe.whitelist()
def place_order(cart_name):
    cart = frappe.get_doc('Shopping Cart', cart_name)

    product_names = []

    # Validate stock
    for item in cart.cart_items:
        product = frappe.get_doc('Product', item.product)

        if product.stock_qty < item.quantity:
            frappe.throw(
                _('Insufficient stock for {0}').format(product.product_name)
            )

        # collect product names
        product_names.append(product.product_name)

    return {
        "product_name": ", ".join(product_names)
    }



    # Create order
    order = frappe.get_doc({
        'doctype': 'Order',
        'customer': cart.customer,
        'order_date': frappe.utils.today(),
        'total_amount': cart.total_amount,
        'order_status': 'Pending ',
        'order_items': []
    })
    
    for item in cart.cart_items:
        order.append('order_items', {
            'product': item.product,
            'quantity': item.quantity,
            'rate': item.rate,
            'amount': item.amount
        })
    
    order.insert()
    
    # Reduce stock
    for item in cart.cart_items:
        product = frappe.get_doc('Product', item.product)
        product.stock_qty -= item.quantity
        product.save()
    
    # Clear cart
    cart.cart_items = []
    cart.total_amount = 0
    cart.save()
    
    return order.name


