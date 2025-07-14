"""
Quotation Service
================
This module handles all quotation-related business logic.
"""
from datetime import datetime
from bson import ObjectId
from ..models import Quotation, User, Company, Product
def calculate_quotation(cart_items, company_id, user_id):
    """
    Calculate quotation details including subtotal, taxes, and total.
    
    Args:
        cart_items: List of items in the cart
        company_id: ID of the company for pricing
        user_id: ID of the user requesting the quote
        
    Returns:
        dict: Calculated quotation details
    """
    subtotal = 0
    items = []
    
    for item in cart_items:
        product = Product.objects.get(id=item['product_id'])
        item_total = product.price * item['quantity']
        subtotal += item_total
        
        items.append({
            'product_id': str(product.id),
            'name': product.name,
            'quantity': item['quantity'],
            'unit_price': product.price,
            'total': item_total
        })
    
    # Calculate taxes (example: 10% GST)
    tax_rate = 0.10
    tax_amount = subtotal * tax_rate
    total = subtotal + tax_amount
    
    return {
        'items': items,
        'subtotal': subtotal,
        'tax_rate': tax_rate * 100,  # Convert to percentage
        'tax_amount': tax_amount,
        'total': total,
        'company_id': str(company_id),
        'user_id': str(user_id),
        'created_at': datetime.utcnow()
    }

def create_quotation(quotation_data):
    """
    Create and save a new quotation.
    
    Args:
        quotation_data: Dictionary containing quotation details
        
    Returns:
        Quotation: The created quotation object
    """
    quotation = Quotation(**quotation_data)
    quotation.save()
    return quotation

def get_quotation(quotation_id):
    """
    Retrieve a quotation by ID.
    
    Args:
        quotation_id: ID of the quotation to retrieve
        
    Returns:
        Quotation: The requested quotation or None if not found
    """
    try:
        return Quotation.objects.get(id=quotation_id)
    except Quotation.DoesNotExist:
        return None

def get_user_quotations(user_id):
    """
    Get all quotations for a specific user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        QuerySet: List of user's quotations
    """
    return Quotation.objects(user_id=user_id).order_by('-created_at')
