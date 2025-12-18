
import frappe

def get_context(context):
    context.products = frappe.get_all(
        'Product',
        fields=['name', 'product_name', 'description', 'price', 'product_image', 'stock_qty'],
        filters={'stock_qty': ['>', 0]},
        order_by='product_name'
    )
    return context