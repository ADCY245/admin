"""
Cart Routes
==========
This module contains all cart-related routes.
"""
from flask import Blueprint, jsonify, request, session, current_app
from flask_login import login_required, current_user
from ..models import Cart, Product
from ..utils.decorators import company_required

# Create cart blueprint
cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('', methods=['GET'])
@login_required
@company_required
def get_cart():
    """Get the current user's cart."""
    cart = Cart.get_or_create(user_id=current_user.id)
    return jsonify(cart.to_dict())

@cart_bp.route('/add', methods=['POST'])
@login_required
@company_required
def add_to_cart():
    """Add an item to the cart."""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    try:
        product = Product.objects.get(id=product_id)
        cart = Cart.get_or_create(user_id=current_user.id)
        cart.add_item(product, quantity)
        return jsonify({'status': 'success', 'cart': cart.to_dict()})
    except Product.DoesNotExist:
        return jsonify({'error': 'Product not found'}), 404

@cart_bp.route('/remove/<item_id>', methods=['DELETE'])
@login_required
def remove_from_cart(item_id):
    """Remove an item from the cart."""
    cart = Cart.get_or_create(user_id=current_user.id)
    if cart.remove_item(item_id):
        return jsonify({'status': 'success', 'cart': cart.to_dict()})
    return jsonify({'error': 'Item not found in cart'}), 404

@cart_bp.route('/update/<item_id>', methods=['PUT'])
@login_required
def update_cart_item(item_id):
    """Update the quantity of an item in the cart."""
    data = request.get_json()
    quantity = data.get('quantity', 1)
    
    cart = Cart.get_or_create(user_id=current_user.id)
    if cart.update_item_quantity(item_id, quantity):
        return jsonify({'status': 'success', 'cart': cart.to_dict()})
    return jsonify({'error': 'Item not found in cart'}), 404

@cart_bp.route('/clear', methods=['DELETE'])
@login_required
def clear_cart():
    """Clear the current user's cart."""
    cart = Cart.get_or_create(user_id=current_user.id)
    cart.clear()
    return jsonify({'status': 'success', 'message': 'Cart cleared'})
