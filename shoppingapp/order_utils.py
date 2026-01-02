import frappe
from shoppingapp.cart_utils import clear_cart


def create_order_from_cart(cart):
    """Create order from shopping cart"""
    
    try:
        # Check if cart has items
        if not cart.cart_items or len(cart.cart_items) == 0:
            frappe.throw("Cart is empty")
        
        print(f"📦 Creating order for customer: {cart.customer}")
        print(f"📦 Cart has {len(cart.cart_items)} items")
        
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
        
        # Save order
        order.insert(ignore_permissions=True)
        print(f"✅ Order created: {order.name}")
        
        # Clear cart after successful order
        clear_cart(cart)
        print(f"🧹 Cart cleared")
        
        # Commit the transaction
        frappe.db.commit()
        print(f"💾 Order saved to database")
        
        return order
    
    except Exception as e:
        # Rollback on error
        frappe.db.rollback()
        print(f"❌ Error creating order: {str(e)}")
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Order Creation Failed"
        )
        frappe.throw(f"Failed to create order: {str(e)}")


def cancel_order_internal(order_name, customer):
    """Internal function to cancel order"""
    
    print(f"🚫 Cancelling order: {order_name}")
    
    try:
        order = frappe.get_doc("Order", order_name)
        
        # ✅ FIXED: Added proper spacing
        # Check permission
        if order.customer != customer:
            frappe.throw("You don't have permission to cancel this order")
        
        # Check status - can only cancel Pending orders
        if order.order_status != "Pending":
            frappe.throw(f"Cannot cancel order with status: {order.order_status}")
        
        # Cancel order
        order.order_status = "Cancelled"
        order.save(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"✅ Order cancelled: {order_name}")
        
        return {
            "success": True,
            "message": f"Order {order_name} cancelled successfully"
        }
    
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error cancelling order: {str(e)}")
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"Order Cancellation Failed - {order_name}"
        )
        return {
            "success": False,
            "message": str(e)
        }