import frappe

def get_context(context):
    if frappe.session.user == 'Guest':
        frappe.throw('Please login to view orders')
    
    customer = frappe.db.get_value('Customer', {'email': frappe.session.user})
    
    if customer:
        context.orders = frappe.get_all(
            'Order',
            filters={'customer': customer},
            fields=['name', 'order_date', 'total_amount', 'order_status'],
            order_by='order_date desc'
        )
    else:
        context.orders = []
    
    return context
