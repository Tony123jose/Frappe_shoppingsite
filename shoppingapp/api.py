

import frappe
from frappe.utils import nowdate


import frappe
from frappe import _

@frappe.whitelist()
def get_products():
    """Get list of all products with stock"""
    products = frappe.get_all(
        'Product',
        fields=['name', 'product_name', 'description', 'price', 'stock_qty', 'product_image', 'category'],
        filters={'stock_qty': ['>', 0]},
        order_by='product_name'
    )
    return products

@frappe.whitelist()
def add_to_cart(product, quantity=1):
    """Add product to cart"""
    if frappe.session.user == 'Guest':
        frappe.throw(_('Please login to add items to cart'))
    
    customer = frappe.db.get_value('Customer', {'email': frappe.session.user})
    
    if not customer:
        frappe.throw(_('Customer record not found'))
    
    # Get or create cart
    cart_name = frappe.db.get_value('Shopping Cart', {'customer': customer})
    
    if cart_name:
        cart = frappe.get_doc('Shopping Cart', cart_name)
    else:
        cart = frappe.get_doc({
            'doctype': 'Shopping Cart',
            'customer': customer
        })
        cart.insert()
    
    # Check if product already in cart
    existing_item = None
    for item in cart.cart_items:
        if item.product == product:
            existing_item = item
            break
    
    if existing_item:
        existing_item.quantity += int(quantity)
    else:
        product_doc = frappe.get_doc('Product', product)
        cart.append('cart_items', {
            'product': product,
            'quantity': int(quantity),
            'rate': product_doc.price,
            'amount': product_doc.price * int(quantity)
        })
    
    cart.save()
    
    return {'success': True, 'cart': cart.name}

@frappe.whitelist()
def place_order():
    """Place order from cart"""
    if frappe.session.user == 'Guest':
        frappe.throw(_('Please login to place order'))
    
    customer = frappe.db.get_value('Customer', {'email': frappe.session.user})
    
    if not customer:
        frappe.throw(_('Customer record not found'))
    
    cart_name = frappe.db.get_value('Shopping Cart', {'customer': customer})
    
    if not cart_name:
        frappe.throw(_('Cart is empty'))
    
    cart = frappe.get_doc('Shopping Cart', cart_name)
    
    if not cart.cart_items:
        frappe.throw(_('Cart is empty'))
    
    # Validate stock
    for item in cart.cart_items:
        product = frappe.get_doc('Product', item.product)
        if product.stock_qty < item.quantity:
            frappe.throw(
                _('Insufficient stock for {0}. Available: {1}').format(
                    item.product, product.stock_qty
                )
            )
    
    # Create order
    order = frappe.get_doc({
        'doctype': 'Order',
        'customer': customer,
        'order_date': frappe.utils.today(),
        'total_amount': cart.total_amount,
        'order_status': 'Pending',
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
    
    return {'success': True, 'order': order.name}