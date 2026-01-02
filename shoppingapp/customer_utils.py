
import frappe


def get_or_create_customer(user):

    # Try to find customer by email field if it exists
    customer = None

    if frappe.db.has_column("Customer", "email"):
        customer = frappe.db.get_value("Customer", {"email": user}, "name")

    # Try by customer_name
    if not customer:
        customer = frappe.db.get_value("Customer", {"customer_name": user}, "name")

    if customer:
        return customer

    # Create new customer
    customer_doc = frappe.new_doc("Customer")
    customer_doc.customer_name = frappe.db.get_value("User", user, "full_name") or user

    # Add email only if the field exists
    if frappe.db.has_column("Customer", "email"):
        customer_doc.email = user

    customer_doc.insert(ignore_permissions=True)

    return customer_doc.name