import frappe
from frappe import _
from frappe.utils import format_datetime
from shoppingapp.customer_utils import get_or_create_customer


def get_context(context):
    """Display user's order history"""

    # Guest check
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to view your orders"), frappe.PermissionError)

    user = frappe.session.user

    try:
        order_list = get_user_orders(user)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "My Orders Page Error")
        order_list = []

    context.orders = order_list
    context.title = "My Orders"
    
    # ✅ Correct: No return statement needed for web pages


def get_user_orders(user):
    """Get all orders for logged in user"""

    try:
        customer = get_or_create_customer(user)
    except Exception:
        return []

    if not customer:
        return []

    orders = frappe.get_all(
        "Order",
        filters={"customer": customer},
        fields=["name", "order_status", "creation"],
        order_by="creation desc"
    )

    order_list = []

    for order_info in orders:
        try:
            order = frappe.get_doc("Order", order_info.name)

            items = []
            total = 0

            for item in order.order_items:
                product = frappe.get_doc("Product", item.product)
                items.append({
                    "product_name": product.product_name,
                    "quantity": item.quantity,
                    "rate": float(item.rate),
                    "amount": float(item.amount),
                    "product_image": product.product_image
                })
                total += float(item.amount)

            order_list.append({
                "name": order.name,
                "order_status": order.order_status,
                "creation": format_datetime(order.creation, "dd MMM yyyy, hh:mm a"),
                "order_items": items,   # ✅ renamed
                "total_amount": total
                })

        except Exception as e:
            frappe.log_error(f"Error processing order {order_info.name}: {str(e)}")
            continue

    return order_list