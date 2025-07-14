"""
Calculation Service
==================
This module handles all calculation-related business logic.
"""
from decimal import Decimal, ROUND_HALF_UP

def calculate_subtotal(items):
    """
    Calculate the subtotal of items.
    
    Args:
        items: List of items with 'price' and 'quantity' keys
        
    Returns:
        Decimal: Calculated subtotal
    """
    return sum(
        Decimal(str(item['price'])) * Decimal(str(item['quantity']))
        for item in items
    )

def calculate_tax(subtotal, tax_rate):
    """
    Calculate tax amount based on subtotal and tax rate.
    
    Args:
        subtotal: Subtotal amount
        tax_rate: Tax rate as a decimal (e.g., 0.1 for 10%)
        
    Returns:
        Decimal: Calculated tax amount
    """
    return (Decimal(str(subtotal)) * Decimal(str(tax_rate))).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )

def calculate_discount(subtotal, discount_percent):
    """
    Calculate discount amount based on subtotal and discount percentage.
    
    Args:
        subtotal: Subtotal amount
        discount_percent: Discount percentage (e.g., 10 for 10%)
        
    Returns:
        Decimal: Calculated discount amount
    """
    if not discount_percent:
        return Decimal('0')
        
    discount = (Decimal(str(subtotal)) * Decimal(str(discount_percent)) / 100).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )
    
    return min(discount, subtotal)  # Ensure discount doesn't exceed subtotal

def calculate_total(subtotal, tax_amount, discount_amount=0):
    """
    Calculate total amount including tax and discount.
    
    Args:
        subtotal: Subtotal amount
        tax_amount: Tax amount
        discount_amount: Discount amount (default: 0)
        
    Returns:
        Decimal: Calculated total amount
    """
    total = Decimal(str(subtotal)) + Decimal(str(tax_amount)) - Decimal(str(discount_amount))
    return max(total, Decimal('0'))  # Ensure total is not negative

def calculate_item_totals(items, tax_rate=0.10, discount_percent=0):
    """
    Calculate all totals for a set of items.
    
    Args:
        items: List of items with 'price' and 'quantity' keys
        tax_rate: Tax rate as a decimal (default: 0.10 for 10%)
        discount_percent: Discount percentage (default: 0%)
        
    Returns:
        dict: Dictionary containing all calculated amounts
    """
    subtotal = calculate_subtotal(items)
    tax_amount = calculate_tax(subtotal, tax_rate)
    discount_amount = calculate_discount(subtotal, discount_percent)
    total = calculate_total(subtotal, tax_amount, discount_amount)
    
    return {
        'subtotal': subtotal,
        'tax_rate': tax_rate * 100,  # Convert to percentage
        'tax_amount': tax_amount,
        'discount_percent': discount_percent,
        'discount_amount': discount_amount,
        'total': total,
        'items': [
            {
                **item,
                'total': Decimal(str(item['price'])) * Decimal(str(item['quantity']))
            }
            for item in items
        ]
    }
