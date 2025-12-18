import frappe

def get_context(context):
    if frappe.session.user == 'Guest':
        frappe.throw('Please login to view cart')
    
    customer = frappe.db.get_value('Customer', {'email': frappe.session.user})
    
    if customer:
        cart = frappe.db.get_value('Shopping Cart', {'customer': customer})
        if cart:
            context.cart = frappe.get_doc('Shopping Cart', cart)
        else:
            context.cart = None
    else:
        context.cart = None
    
    return context