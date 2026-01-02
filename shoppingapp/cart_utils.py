import frappe

logger = frappe.logger(
    "shoppingapp.cart",
    allow_site=True
)

def get_or_create_cart(customer):
    """Get or create shopping cart for customer"""
    
    print(f"🛒 Getting/Creating cart for customer: {customer}")
    
    # Check if cart exists
    cart_name = frappe.db.get_value("Shopping Cart", {"customer": customer}, "name")
    
    if cart_name:
        print(f"✅ Found existing cart: {cart_name}")
        cart = frappe.get_doc("Shopping Cart", cart_name)
        print(f"📦 Cart has {len(cart.cart_items)} items")
        return cart
    
    # Create new cart
    print("🆕 Creating new cart")
    cart = frappe.new_doc("Shopping Cart")
    cart.customer = customer
    cart.total_amount = 0
    cart.insert(ignore_permissions=True)
    frappe.db.commit()  # Explicitly commit
    
    print(f"✅ New cart created: {cart.name}")
    return cart


def add_product_to_cart(cart, product, quantity):
    """Add product to cart or update quantity if exists"""
    
    print(f"\n{'='*50}")
    print(f"📦 ADD PRODUCT TO CART")
    print(f"Cart: {cart.name}")
    print(f"Product: {product}")
    print(f"Quantity: {quantity}")
    print(f"Current items in cart: {len(cart.cart_items)}")
    
    # Get product details
    product_doc = frappe.get_doc("Product", product)
    logger.warning(f"Product details: {product_doc.product_name}, Price: {product_doc.price}, Stock: {product_doc.stock_qty}")
    
    print(f"📦 Product Name: {product_doc.product_name}")
    print(f"💰 Price: {product_doc.price}")
    
    # Check if product already exists in cart
    existing_item = find_cart_item(cart, product)
    
    if existing_item:
        print(f"🔄 Product already in cart, updating quantity")
        print(f"   Old Quantity: {existing_item.quantity}")
        existing_item.quantity += int(quantity)
        print(f"   New Quantity: {existing_item.quantity}")
        existing_item.amount = existing_item.quantity * existing_item.rate
        print(f"   New Amount: {existing_item.amount}")
    else:
        print(f"➕ Adding new product to cart")
        cart.append("cart_items", {
            "product": product,
            "quantity": int(quantity),
            "rate": product_doc.price,
            "amount": product_doc.price * int(quantity)
        })
        print(f"   Items in cart after append: {len(cart.cart_items)}")
    
    # Recalculate total
    old_total = cart.total_amount
    recalculate_cart_total(cart)
    print(f"💵 Total: {old_total} → {cart.total_amount}")
    
    # Save cart
    print(f"💾 Saving cart...")
    cart.save(ignore_permissions=True)
    frappe.db.commit()  # Explicitly commit
    
    # Verify save
    print(f"🔍 Verifying save...")
    saved_cart = frappe.get_doc("Shopping Cart", cart.name)
    print(f"✅ Cart saved with {len(saved_cart.cart_items)} items")
    print(f"✅ Total amount: {saved_cart.total_amount}")
    
    # List all items
    for idx, item in enumerate(saved_cart.cart_items):
        print(f"   Item {idx+1}: {item.product} | Qty: {item.quantity} | Amount: {item.amount}")
    
    print(f"{'='*50}\n")
    
    return saved_cart


def find_cart_item(cart, product):
    """Find product in cart items"""
    for item in cart.cart_items:
        if item.product == product:
            return item
    return None


def update_cart_item_quantity(cart, product, quantity):
    """Update cart item quantity"""
    
    print(f"🔄 Updating quantity for {product} to {quantity}")
    
    item_found = False
    item_to_remove = None
    
    for item in cart.cart_items:
        if item.product == product:
            item_found = True
            new_qty = int(quantity)
            
            if new_qty <= 0:
                print(f"🗑️ Marking item for removal")
                item_to_remove = item
            else:
                print(f"   Old Qty: {item.quantity} → New Qty: {new_qty}")
                item.quantity = new_qty
                item.amount = item.quantity * item.rate
            
            break
    
    # Remove item if needed
    if item_to_remove:
        cart.cart_items.remove(item_to_remove)
        print(f"✅ Item removed")
    
    if not item_found:
        frappe.throw("Product not found in cart")
    
    # Recalculate total
    recalculate_cart_total(cart)
    cart.save(ignore_permissions=True)
    frappe.db.commit()
    
    print(f"✅ Cart updated successfully")
    return cart


def remove_cart_item(cart, product):
    """Remove item from cart"""
    
    print(f"🗑️ Removing {product} from cart")
    
    item_to_remove = None
    
    for item in cart.cart_items:
        if item.product == product:
            item_to_remove = item
            break
    
    if item_to_remove:
        cart.cart_items.remove(item_to_remove)
        print(f"✅ Item removed")
    else:
        print(f"⚠️ Item not found in cart")
    
    # Recalculate total
    recalculate_cart_total(cart)
    cart.save(ignore_permissions=True)
    frappe.db.commit()
    
    return cart


def recalculate_cart_total(cart):
    """Recalculate cart total amount"""
    total = sum(item.amount for item in cart.cart_items)
    cart.total_amount = total
    print(f"💰 Recalculated total: {total}")


def clear_cart(cart):
    """Clear all items from cart"""
    print(f"🧹 Clearing cart {cart.name}")
    cart.cart_items = []
    cart.total_amount = 0
    cart.save(ignore_permissions=True)
    frappe.db.commit()
    return cart