
import frappe

from shoppingapp.customer_utils import get_or_create_customer
from shoppingapp.cart_utils import (
    get_or_create_cart,
    add_product_to_cart,
    update_cart_item_quantity,
    remove_cart_item
)
from shoppingapp.product_utils import get_all_products
from shoppingapp.order_utils import (create_order_from_cart,
    cancel_order_internal)

# Get Product List API
@frappe.whitelist(allow_guest=True)
def get_products():

    try:
        products = get_all_products()

        return {
            "success": True,
            "data": products,
            "message": "Products fetched successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"Error: {str(e)}"
        }

# Add to Cart API
@frappe.whitelist()
def add_to_cart(product, quantity=1):
   
    print("🛒 ADD TO CART FUNCTION CALLED")
    print(f"User: {frappe.session.user}")
   
    try:
        # Get current user
        user = frappe.session.user


        if user == "Guest":
            frappe.throw("Please login to add items to cart")

        # Find or create customer for this user
        customer = get_or_create_customer(user)

        # Find or create cart for this customer
        cart = get_or_create_cart(customer)

        # Add product to cart
        cart = add_product_to_cart(cart, product, quantity)

        # Get product name for response
        product_doc = frappe.get_doc("Product", product)
        # print("🛑 BREAKPOINT: Checking product quantity")
        # breakpoint() 
        return {
            "success": True,
            "message": f"{product_doc.product_name} added to cart successfully",
            "cart_total": cart.total_amount
        }

    except Exception as e:
        frappe.log_error(f"Error adding to cart: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@frappe.whitelist()
def place_order(cart_name=None):
    """Place order and send confirmation email in background"""

    try:
        # Get current user
        user = frappe.session.user

        if user == "Guest":
            frappe.throw("Please login to place order")

        # Get cart
        if cart_name:
            cart = frappe.get_doc("Shopping Cart", cart_name)
        else:
            # Find customer and cart for current user
            customer = get_or_create_customer(user)
            cart = get_or_create_cart(customer)

        # Check if cart has items
        if not cart.cart_items or len(cart.cart_items) == 0:
            return {
                "success": False,
                "message": "Cart is empty"
            }

        # Create order from cart
        order = create_order_from_cart(cart)


    except Exception as e:
        frappe.log_error(
            title="Place Order Failed",
            message=frappe.get_traceback()
        )
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

# Update Cart Item Quantity API
@frappe.whitelist()
def update_cart_quantity(product, quantity):

    try:
        user = frappe.session.user

        if user == "Guest":
            frappe.throw("Please login")

        # Get customer and cart
        customer = get_or_create_customer(user)
        cart = get_or_create_cart(customer)

        # Update item quantity
        cart = update_cart_item_quantity(cart, product, quantity)

        return {
            "success": True,
            "message": "Cart updated successfully",
            "cart_total": cart.total_amount
        }

    except Exception as e:
        frappe.log_error(f"Error updating cart: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

# Remove Item from Cart API
@frappe.whitelist()
def remove_from_cart(product):

    try:
        user = frappe.session.user

        if user == "Guest":
            frappe.throw("Please login")

        # Get customer and cart
        customer = get_or_create_customer(user)
        cart = get_or_create_cart(customer)

        # Remove item from cart
        cart = remove_cart_item(cart, product)

        return {
            "success": True,
            "message": "Item removed from cart",
            "cart_total": cart.total_amount
        }

    except Exception as e:
        frappe.log_error(f"Error removing from cart: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

#cancel order
@frappe.whitelist()
def cancel_order(order_name):

    try:
        user = frappe.session.user
        if user == "Guest":
            frappe.throw("Please login")

        customer = get_or_create_customer(user)
        result = cancel_order_internal(order_name, customer)

        return {
            "success": True,
            "message": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }