"""
Quotation Routes
===============
This module contains all quotation-related routes.
"""
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from ..services import quotation_service, calculation_service
from ..models import Quotation
from ..utils.decorators import company_required

# Create quotation blueprint
quotation_bp = Blueprint('quotation', __name__, url_prefix='/quotations')

@quotation_bp.route('/preview', methods=['GET'])
@login_required
@company_required
def preview_quotation():
    """Preview a quotation before finalizing."""
    cart_items = request.json.get('items', [])
    
    if not cart_items:
        return jsonify({'error': 'No items in cart'}), 400
    
    try:
        # Calculate quotation details
        quotation_data = quotation_service.calculate_quotation(
            cart_items=cart_items,
            company_id=current_user.company_id,
            user_id=current_user.id
        )
        
        return jsonify({
            'status': 'success',
            'quotation': quotation_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating quotation preview: {str(e)}")
        return jsonify({'error': 'Failed to generate quotation preview'}), 500

@quotation_bp.route('', methods=['POST'])
@login_required
@company_required
def create_quotation():
    """Create a new quotation."""
    try:
        cart_items = request.json.get('items', [])
        
        if not cart_items:
            return jsonify({'error': 'No items in cart'}), 400
        
        # Calculate quotation details
        quotation_data = quotation_service.calculate_quotation(
            cart_items=cart_items,
            company_id=current_user.company_id,
            user_id=current_user.id
        )
        
        # Create and save the quotation
        quotation = quotation_service.create_quotation(quotation_data)
        
        return jsonify({
            'status': 'success',
            'quotation_id': str(quotation.id),
            'message': 'Quotation created successfully'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating quotation: {str(e)}")
        return jsonify({'error': 'Failed to create quotation'}), 500

@quotation_bp.route('', methods=['GET'])
@login_required
def list_quotations():
    """List all quotations for the current user."""
    try:
        quotations = quotation_service.get_user_quotations(current_user.id)
        
        return jsonify({
            'status': 'success',
            'quotations': [{
                'id': str(q.id),
                'total': float(q.total),
                'created_at': q.created_at.isoformat(),
                'status': q.status
            } for q in quotations]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing quotations: {str(e)}")
        return jsonify({'error': 'Failed to retrieve quotations'}), 500

@quotation_bp.route('/<quotation_id>', methods=['GET'])
@login_required
def get_quotation(quotation_id):
    """Get details of a specific quotation."""
    try:
        quotation = quotation_service.get_quotation(quotation_id)
        
        if not quotation:
            return jsonify({'error': 'Quotation not found'}), 404
            
        if str(quotation.user_id) != str(current_user.id) and not current_user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
            
        return jsonify({
            'status': 'success',
            'quotation': {
                'id': str(quotation.id),
                'items': quotation.items,
                'subtotal': float(quotation.subtotal),
                'tax_rate': float(quotation.tax_rate),
                'tax_amount': float(quotation.tax_amount),
                'total': float(quotation.total),
                'status': quotation.status,
                'created_at': quotation.created_at.isoformat(),
                'updated_at': quotation.updated_at.isoformat() if hasattr(quotation, 'updated_at') else None
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving quotation {quotation_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve quotation'}), 500
