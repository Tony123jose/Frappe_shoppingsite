import frappe

def get_context(context):
    context.title = "My Cart"

    cart = frappe.call("shoppingapp.api.get_cart")
    context.cart_items = cart.get("items", [])
    context.total_amount = cart.get("total_amount", 0)
