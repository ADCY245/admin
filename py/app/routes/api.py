from flask import Blueprint, jsonify, request, current_app, session
from flask_login import login_required, current_user
from ..models import User, Company, Product, Order
from ..utils.decorators import company_required
import json
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
import jwt

bp = Blueprint('api', __name__)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, ObjectId)):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

@bp.route('/companies', methods=['GET'])
def get_companies():
    """Get all active companies."""
    try:
        companies = Company.objects(status='active').order_by('name')
        return jsonify({
            'success': True,
            'data': [{
                'id': str(company.id),
                'name': company.name,
                'email': company.email,
                'phone': company.phone,
                'address': company.address
            } for company in companies]
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching companies: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch companies'
        }), 500

@bp.route('/machines', methods=['GET'])
@login_required
def get_machines():
    """Get all machines for the selected company."""
    try:
        company_id = session.get('selected_company', {}).get('id')
        if not company_id:
            return jsonify({
                'success': False,
                'message': 'No company selected'
            }), 400
            
        machines = Machine.objects(company=company_id, status='active').order_by('name')
        return jsonify({
            'success': True,
            'data': [{
                'id': str(machine.id),
                'name': machine.name,
                'model': machine.model,
                'status': machine.status,
                'specifications': machine.specifications
            } for machine in machines]
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching machines: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch machines'
        }), 500

@bp.route('/products', methods=['GET'])
@login_required
def get_products():
    """Get all products for the selected company."""
    try:
        company_id = session.get('selected_company', {}).get('id')
        if not company_id:
            return jsonify({
                'success': False,
                'message': 'No company selected'
            }), 400
            
        products = Product.objects(company=company_id, status='active').order_by('name')
        return jsonify({
            'success': True,
            'data': [{
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'category': product.category,
                'price': product.price,
                'stock': product.stock,
                'specifications': product.specifications,
                'images': product.images
            } for product in products]
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching products: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch products'
        }), 500

@bp.route('/cart', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def handle_cart():
    """Handle shopping cart operations."""
    try:
        if request.method == 'GET':
            # Get cart
            return jsonify({
                'success': True,
                'data': current_user.cart or []
            })
            
        elif request.method == 'POST':
            # Add to cart
            data = request.get_json()
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            
            if not product_id:
                return jsonify({
                    'success': False,
                    'message': 'Product ID is required'
                }), 400
                
            product = Product.objects(id=product_id).first()
            if not product:
                return jsonify({
                    'success': False,
                    'message': 'Product not found'
                }), 404
                
            # Check if product is already in cart
            cart = current_user.cart or []
            item_exists = False
            
            for item in cart:
                if item.get('product_id') == str(product.id):
                    item['quantity'] += quantity
                    item_exists = True
                    break
                    
            if not item_exists:
                cart.append({
                    'product_id': str(product.id),
                    'name': product.name,
                    'price': float(product.price),
                    'quantity': quantity,
                    'image': product.images[0] if product.images else ''
                })
            
            current_user.cart = cart
            current_user.save()
            
            return jsonify({
                'success': True,
                'message': 'Product added to cart',
                'cart_count': len(cart)
            })
            
        elif request.method == 'PUT':
            # Update cart item quantity
            data = request.get_json()
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            
            if not product_id:
                return jsonify({
                    'success': False,
                    'message': 'Product ID is required'
                }), 400
                
            cart = current_user.cart or []
            updated = False
            
            for item in cart:
                if item.get('product_id') == product_id:
                    item['quantity'] = quantity
                    updated = True
                    break
                    
            if not updated:
                return jsonify({
                    'success': False,
                    'message': 'Product not found in cart'
                }), 404
                
            current_user.cart = cart
            current_user.save()
            
            return jsonify({
                'success': True,
                'message': 'Cart updated'
            })
            
        elif request.method == 'DELETE':
            # Remove from cart
            product_id = request.args.get('product_id')
            
            if not product_id:
                return jsonify({
                    'success': False,
                    'message': 'Product ID is required'
                }), 400
                
            cart = current_user.cart or []
            new_cart = [item for item in cart if item.get('product_id') != product_id]
            
            if len(new_cart) == len(cart):
                return jsonify({
                    'success': False,
                    'message': 'Product not found in cart'
                }), 404
                
            current_user.cart = new_cart
            current_user.save()
            
            return jsonify({
                'success': True,
                'message': 'Product removed from cart',
                'cart_count': len(new_cart)
            })
            
    except Exception as e:
        current_app.logger.error(f"Error in cart operation: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your request'
        }), 500

@bp.route('/orders', methods=['GET', 'POST'])
@login_required
def handle_orders():
    """Handle order operations."""
    try:
        if request.method == 'GET':
            # Get user's orders
            orders = Order.objects(user=current_user.id).order_by('-created_at')
            
            return jsonify({
                'success': True,
                'data': [{
                    'id': str(order.id),
                    'order_number': order.order_number,
                    'status': order.status,
                    'total_amount': order.total_amount,
                    'created_at': order.created_at,
                    'item_count': len(order.items)
                } for order in orders]
            })
            
        elif request.method == 'POST':
            # Create new order
            data = request.get_json()
            
            if not current_user.cart:
                return jsonify({
                    'success': False,
                    'message': 'Your cart is empty'
                }), 400
                
            company_id = session.get('selected_company', {}).get('id')
            if not company_id:
                return jsonify({
                    'success': False,
                    'message': 'No company selected'
                }), 400
                
            # Calculate total amount
            cart = current_user.cart or []
            subtotal = sum(item.get('price', 0) * item.get('quantity', 0) for item in cart)
            tax = subtotal * 0.1  # 10% tax
            total = subtotal + tax
            
            # Create order
            order = Order(
                order_number=f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                user=current_user.id,
                company=company_id,
                items=cart,
                total_amount=total,
                shipping_address=data.get('shipping_address', {}),
                payment_method=data.get('payment_method', 'credit_card'),
                status='pending'
            )
            order.save()
            
            # Clear cart
            current_user.cart = []
            current_user.save()
            
            return jsonify({
                'success': True,
                'message': 'Order placed successfully',
                'order_id': str(order.id),
                'order_number': order.order_number
            })
            
    except Exception as e:
        current_app.logger.error(f"Error in order operation: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your order'
        }), 500

@bp.route('/orders/<order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """Get order details."""
    try:
        order = Order.objects(id=order_id, user=current_user.id).first()
        if not order:
            return jsonify({
                'success': False,
                'message': 'Order not found'
            }), 404
            
        return jsonify({
            'success': True,
            'data': {
                'id': str(order.id),
                'order_number': order.order_number,
                'status': order.status,
                'total_amount': order.total_amount,
                'created_at': order.created_at,
                'items': order.items,
                'shipping_address': order.shipping_address,
                'payment_method': order.payment_method,
                'payment_status': order.payment_status
            }
        })
        
    except InvalidId:
        return jsonify({
            'success': False,
            'message': 'Invalid order ID'
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error fetching order: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch order details'
        }), 500

@bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def user_profile():
    """Get or update user profile."""
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'data': {
                    'id': str(current_user.id),
                    'email': current_user.email,
                    'username': current_user.username,
                    'is_verified': current_user.is_verified,
                    'company_id': current_user.company_id
                }
            })
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            # Update user profile
            if 'username' in data:
                current_user.username = data['username']
                
            if 'email' in data and data['email'] != current_user.email:
                # Check if email is already in use
                if User.objects(email=data['email']).first():
                    return jsonify({
                        'success': False,
                        'message': 'Email already in use'
                    }), 400
                current_user.email = data['email']
                current_user.is_verified = False
                # TODO: Send verification email
                
            if 'current_password' in data and 'new_password' in data:
                if not current_user.check_password(data['current_password']):
                    return jsonify({
                        'success': False,
                        'message': 'Current password is incorrect'
                    }), 400
                current_user.set_password(data['new_password'])
                
            current_user.save()
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully'
            })
            
    except Exception as e:
        current_app.logger.error(f"Error in profile operation: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating your profile'
        }), 500
