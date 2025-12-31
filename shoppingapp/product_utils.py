import frappe


def get_all_products():
   
    products = frappe.get_all(
        "Product",
        fields=["name", "product_name", "description", "price", "stock_qty", "product_image"],
        order_by="name"
    )
    return products


def get_product(product_name):
    
    if not frappe.db.exists("Product", product_name):
        frappe.throw(f"Product {product_name} not found")
    
    return frappe.get_doc("Product", product_name)