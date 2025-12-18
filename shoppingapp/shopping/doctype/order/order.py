# Copyright (c) 2025, tj and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Order(Document):
	pass
### Task 14: Reduce Stock on Order Submit
import frappe
from frappe.model.document import Document
from frappe import _

class Order(Document):
    def on_submit(self):
        self.reduce_stock()
    
    def reduce_stock(self):
        for item in self.order_items:
            product = frappe.get_doc('Product', item.product)
            
            if product.stock_qty < item.quantity:
                frappe.throw(
                    _('Insufficient stock for {0}. Available: {1}').format(
                        item.product, product.stock_qty
                    )
                )
            
            product.stock_qty -= item.quantity
            product.save()