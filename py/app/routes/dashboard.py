from flask import Blueprint, render_template, abort, redirect, url_for, flash, current_app, jsonify, request, session
from flask_login import login_required, current_user
from datetime import datetime
import os
from ..utils.template_utils import render_role_template, role_template

bp = Blueprint('dashboard', __name__)

def get_role_template(role, template_name):
    """Helper function to get the correct template path based on role."""
    # Check if the role-specific template exists
    role_template = f"{role}/{template_name}"
    template_path = os.path.join(current_app.root_path, 'templates', role, template_name)
    
    if os.path.exists(template_path):
        return role_template
    
    # Fallback to user template if role-specific template doesn't exist
    if role != 'user':
        user_template = f"user/{template_name}"
        user_path = os.path.join(current_app.root_path, 'templates', 'user', template_name)
        if os.path.exists(user_path):
            return user_template
    
    # If no template found, return None
    return None

@bp.route('/')
@login_required
def index():
    """
    Main dashboard route that redirects users to their respective role-based dashboards.
    """
    # Get user role from current_user first, then session
    user_role = getattr(current_user, 'role', None)
    if not user_role:
        user_role = session.get('user_role', 'user')
    
    # Ensure role is valid
    if user_role not in ['admin', 'dealer', 'user']:
        user_role = 'user'
    
    session['user_role'] = user_role
    
    # Get the target dashboard URL
    target_url = url_for(f'dashboard.{user_role}_dashboard')
    
    # If there's a next URL parameter, use it
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    
    # If it's an AJAX request, return JSON with redirect URL
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'redirect': target_url
        })
    
    # For regular requests, redirect to the target dashboard
    return redirect(target_url)

# Alias for backward compatibility
bp.add_url_rule('/dashboard', 'dashboard', index)

@bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard view."""
    # Ensure user is admin
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Ensure the role is set correctly in the session first
    session['user_role'] = 'admin'
    
    # Verify user has admin role
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Add any admin-specific data here
    stats = {
        'total_users': 0,  # Replace with actual data
        'total_products': 0,  # Replace with actual data
        'total_orders': 0,  # Replace with actual data
        'revenue': 0,  # Replace with actual data
        'pending_orders': 0,
        'completed_orders': 0
    }
    
    recent_orders = []  # Replace with actual data
    
    return render_role_template('dashboard.html',
                             title='Admin Dashboard',
                             stats=stats,
                             recent_orders=recent_orders,
                             role='admin',
                             now=datetime.utcnow())

@bp.route('/dealer')
@login_required
def dealer_dashboard():
    """Dealer dashboard view."""
    if current_user.role != 'dealer':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Ensure the role is set correctly in the session
    session['user_role'] = 'dealer'
    
    # Add any dealer-specific data here
    stats = {
        'total_orders': 0,  # Replace with actual data
        'pending_orders': 0,  # Replace with actual data
        'completed_orders': 0,  # Replace with actual data
        'total_spent': 0,  # Replace with actual data
        'revenue': 0  # For backward compatibility
    }
    
    recent_orders = []  # Replace with actual data
    
    return render_role_template('dashboard.html',
                             title='Dealer Dashboard',
                             stats=stats,
                             recent_orders=recent_orders,
                             user={
                                 'name': current_user.username,
                                 'email': current_user.email,
                                 'join_date': current_user.created_at.strftime('%B %d, %Y') if hasattr(current_user, 'created_at') and current_user.created_at else 'N/A',
                                 'avatar': url_for('static', filename='images/default-avatar.png')
                             },
                             role='dealer',
                             now=datetime.utcnow())

@bp.route('/user')
@login_required
def user_dashboard():
    """User dashboard view."""
    if current_user.role not in ['user', 'admin', 'dealer']:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Ensure the role is set correctly in the session
    session['user_role'] = 'user'
    
    # Add any user-specific data here
    user_data = {
        'name': current_user.username,
        'email': current_user.email,
        'join_date': current_user.created_at.strftime('%B %d, %Y') if hasattr(current_user, 'created_at') and current_user.created_at else 'N/A',
        'avatar': url_for('static', filename='images/default-avatar.png')
    }
    
    # User stats
    stats = {
        'total_orders': 0,  # Replace with actual data
        'pending_orders': 0,  # Replace with actual data
        'completed_orders': 0,  # Replace with actual data
        'total_spent': 0  # Replace with actual data
    }
    
    recent_orders = []  # Replace with actual data
    
    return render_role_template('dashboard.html',
                             title='My Dashboard',
                             user=user_data,
                             stats=stats,
                             recent_orders=recent_orders,
                             role='user',
                             now=datetime.utcnow())

@bp.route('/test-role-template')
@login_required
def test_role_template():
    """Test route to verify role-based template loading."""
    # Get the current role from the user or default to 'user'
    role = getattr(current_user, 'role', 'user')
    
    # Set the role in the session for template loading
    session['user_role'] = role
    
    # Prepare test data
    test_data = {
        'title': f'Test Template for {role.capitalize()}',
        'message': f'This is a test template for the {role} role.',
        'user': {
            'name': current_user.username,
            'email': current_user.email,
            'role': role,
            'join_date': current_user.created_at.strftime('%B %d, %Y') if hasattr(current_user, 'created_at') and current_user.created_at else 'N/A'
        },
        'now': datetime.utcnow(),
        'role': role
    }
    
# API routes for role-specific dashboard data

@bp.route('/api/user/dashboard')
@login_required
def api_user_dashboard():
    """Return JSON data for user dashboard JS."""
    if current_user.role != 'user':
        abort(403)
    
    # Placeholder data – replace with real queries
    user_obj = {
        'username': current_user.username,
        'email': current_user.email,
        'created_at': getattr(current_user, 'created_at', datetime.utcnow()).isoformat(),
        'avatar_url': url_for('static', filename='images/default-avatar.png', _external=False)
    }
    stats = {
        'order_count': 0,
        'total_spent': 0.0,
        'loyalty_points': 0
    }
    orders = []
    return jsonify({'success': True, 'user': user_obj, 'stats': stats, 'orders': orders})

@bp.route('/api/admin/dashboard')
@login_required
def api_admin_dashboard():
    """Return JSON data for admin dashboard JS."""
    if current_user.role != 'admin':
        abort(403)
    
    # Admin-specific data
    stats = {
        'total_users': 0,  # Replace with actual data
        'total_products': 0,
        'total_orders': 0,
        'revenue': 0,
        'pending_orders': 0,
        'completed_orders': 0
    }
    
    recent_orders = []  # Replace with actual data
    
    return jsonify({
        'success': True,
        'stats': stats,
        'recent_orders': recent_orders
    })

# Add any additional dashboard-related routes below
