import frappe
from shoppingapp.cart_utils import clear_cart


def create_order_from_cart(cart):
    """
    Create order from cart with Pending status
    Stock is NOT reduced here - only when confirmed
    """
    # Check if cart has items
    if not cart.cart_items or len(cart.cart_items) == 0:
        frappe.throw("Cart is empty")
    
    # Create order
    order = frappe.new_doc("Order")
    order.customer = cart.customer
    order.order_status = "Pending" 
    
    # Copy cart items to order
    for cart_item in cart.cart_items:
        order.append("order_items", {
            "product": cart_item.product,
            "quantity": cart_item.quantity,
            "rate": cart_item.rate,
            "amount": cart_item.amount
        })
    
    # Just save the order (no submit, no stock reduction)
    order.insert(ignore_permissions=True)
    
    # Log order creation
    frappe.log_error(
        message=f"Order created: {order.name} for customer {cart.customer}",
        title="Order Created"
    )
    
    # Clear cart
    clear_cart(cart)
    
    return order



def create_order_from_cart(cart):
    """Create order from shopping cart with rollback support"""
    
    try:
        # Check if cart has items
        if not cart.cart_items or len(cart.cart_items) == 0:
            frappe.throw("Cart is empty")
        
        
        # Create order
        order = frappe.new_doc("Order")
        order.customer = cart.customer
        order.order_status = "Pending"
        
        for cart_item in cart.cart_items:
            order.append("order_items", {
                "product": cart_item.product,
                "quantity": cart_item.quantity,
                "rate": cart_item.rate,
                "amount": cart_item.amount
            })
        
        order.insert(ignore_permissions=True)
        print(f"✅ Order created: {order.name}")
        
        # FORCE AN ERROR HERE TO TEST ROLLBACK!
        raise Exception("Testing rollback - intentional error!")
        
        # This code won't run because of error above
        clear_cart(cart)
        frappe.db.commit()
        
        return order
    
    except Exception as e:
        # Rollback happens here!
        frappe.db.rollback()
        print("❌ Rolled back! Order was NOT saved.")
        frappe.throw(f"Order failed: {str(e)}")

def cancel_order_internal(order_name, customer):
    """Internal function to cancel order"""
    order = frappe.get_doc("Order", order_name)
    
    # Check permission
    if order.customer != customer:
        frappe.throw("Permission denied")
    
    # Check status - can only cancel Pending orders
    if order.order_status != "Pending":
        frappe.throw(f"Cannot cancel order with status: {order.order_status}")
    
    # Cancel
    order.order_status = "Cancelled"
    order.save()
    
    return f"Order {order_name} cancelled successfully"