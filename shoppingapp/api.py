import frappe
from frappe import _
from shoppingapp.order_utils import cancel_order_internal
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
   
    print("\n" + "="*60)
    print("🛒 ADD TO CART FUNCTION CALLED")
    print(f"User: {frappe.session.user}")
    print(f"Product: {product}")
    print(f"Quantity: {quantity}")
    print("="*60)
   
    try:
        # Get current user
        user = frappe.session.user

        if user == "Guest":
            print("❌ User is Guest - throwing error")
            frappe.throw("Please login to add items to cart")

        print(f"✅ Step 1: User authenticated - {user}")

        # Find or create customer for this user
        print(f"🔍 Step 2: Getting/Creating customer...")
        customer = get_or_create_customer(user)
        print(f"✅ Step 2: Customer found/created - {customer}")

        # Find or create cart for this customer
        print(f"🔍 Step 3: Getting/Creating cart...")
        cart = get_or_create_cart(customer)
        print(f"✅ Step 3: Cart found/created - {cart.name}")
        print(f"   Current items in cart: {len(cart.cart_items)}")

        # Add product to cart
        print(f"🔍 Step 4: Adding product to cart...")
        print(f"   Calling add_product_to_cart(cart={cart.name}, product={product}, quantity={quantity})")
        
        cart = add_product_to_cart(cart, product, quantity)
        
        print(f"✅ Step 4: Product added successfully")
        print(f"   Items in cart now: {len(cart.cart_items)}")
        print(f"   Total amount: {cart.total_amount}")

        # Get product name for response
        print(f"🔍 Step 5: Getting product details...")
        product_doc = frappe.get_doc("Product", product)
        print(f"✅ Step 5: Product name - {product_doc.product_name}")

        response = {
            "success": True,
            "message": f"{product_doc.product_name} added to cart successfully",
            "cart_total": cart.total_amount
        }
        
        print(f"✅ FINAL: Returning success response")
        print(f"   Response: {response}")
        print("="*60 + "\n")
        
        return response

    except Exception as e:
        print(f"❌ ERROR OCCURRED!")
        print(f"   Error: {str(e)}")
        print(f"   Traceback: {frappe.get_traceback()}")
        print("="*60 + "\n")
        
        frappe.log_error(f"Error adding to cart: {str(e)}", "Add to Cart Error")
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
        
        return {
            "success": True,
            "message": f"Order {order.name} placed successfully!",
            "order_name": order.name
        }

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
    """
    API endpoint to cancel an order
    Called from frontend JavaScript
    """
    
    # Check if user is logged in
    if frappe.session.user == "Guest":
        return {
            "success": False,
            "message": "Please login to cancel orders"
        }
    
    try:
        # Get customer for current user
        customer = get_or_create_customer(frappe.session.user)
        
        if not customer:
            return {
                "success": False,
                "message": "Customer not found"
            }
        
        # Call internal cancel function
        result = cancel_order_internal(order_name, customer)
        
        return result
    
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"Cancel Order API Error - {order_name}"
        )
        return {
            "success": False,
            "message": str(e)
        }