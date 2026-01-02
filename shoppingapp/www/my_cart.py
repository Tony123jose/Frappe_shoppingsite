import frappe
from frappe import _

def get_context(context):
    """Display user's shopping cart"""
    
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to view your cart"), frappe.PermissionError)
    
    # Get current user
    user = frappe.session.user
    
    # Get real cart data
    cart_data = get_user_cart(user)
    print("🛒 Cart Data:", cart_data)
    
    if cart_data:
        context.cart = cart_data
        context.cart_items = cart_data.get("cart_items", [])
        context.total_amount = cart_data.get("total_amount", 0)
    else:
        # Empty cart
        context.cart = None
        context.cart_items = []
        context.total_amount = 0
    
    # Set page title
    context.title = "My Cart"
    
    return context


def get_user_cart(user):
    """Get shopping cart for logged in user"""
    
    # Find customer - FIXED: Removed spaces before "Customer"
    customer = None
    
    # Try to find by email field
    if frappe.db.has_column("Customer", "email"):
        customer = frappe.db.get_value("Customer", {"email": user}, "name")
        print(f"🔍 Found customer by email: {customer}")
    
    # If not found, try matching with customer_name
    if not customer:
        customer = frappe.db.get_value("Customer", {"customer_name": user}, "name")
        print(f"🔍 Found customer by customer_name: {customer}")
    
    # If still not found, try finding by partial match
    if not customer:
        customers = frappe.get_all("Customer", filters={}, fields=["name", "customer_name", "email"])
        print(f"📋 All customers: {customers}")
        for cust in customers:
            if user in str(cust.get('customer_name', '')) or user in str(cust.get('email', '')):
                customer = cust.name
                print(f"✅ Found customer by partial match: {customer}")
                break
    
    if not customer:
        print(f"❌ No customer found for user: {user}")
        return None
    
    # Find cart for this customer
    cart_name = frappe.db.get_value("Shopping Cart", {"customer": customer}, "name")
    print(f"🛒 Cart name: {cart_name}")
    
    if not cart_name:
        print(f"❌ No cart found for customer: {customer}")
        return None
    
    # Get the cart document with all items
    cart = frappe.get_doc("Shopping Cart", cart_name)
    print(f"📦 Cart items count: {len(cart.cart_items)}")
    
    # Prepare cart data with product details
    cart_items = []
    for item in cart.cart_items:
        # Get product details
        product = frappe.get_doc("Product", item.product)
        
        cart_items.append({
            "product": item.product,
            "product_name": product.product_name,
            "quantity": item.quantity,
            "rate": item.rate,
            "amount": item.amount,
            "product_image": product.product_image
        })
    
    print(f"✅ Returning {len(cart_items)} cart items")
    
    return {
        "name": cart.name,
        "customer": cart.customer,
        "total_amount": cart.total_amount,
        "cart_items": cart_items
    }