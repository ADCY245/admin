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
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # Store the user's role in the session for template loading
    if hasattr(current_user, 'role'):
        session['user_role'] = current_user.role
    
    # Redirect to the appropriate dashboard based on user role
    if current_user.role == 'admin':
        return redirect(url_for('dashboard.admin_dashboard'))
    elif current_user.role == 'dealer':
        return redirect(url_for('dashboard.dealer_dashboard'))
    else:
        # Default to user dashboard for any other roles
        return redirect(url_for('dashboard.user_dashboard'))

# Alias for backward compatibility
bp.add_url_rule('/dashboard', 'dashboard', index)

@bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard view."""
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Ensure the role is set correctly in the session
    session['user_role'] = 'admin'
    
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
    
    # Log the template being rendered
    current_app.logger.info(f'Rendering test template for role: {role}')
    
    # Render the template using our role-based template utility
    return render_role_template('test_template.html', **test_data)

@bp.route('/test-role-template')
@login_required
def test_role_template():
    """
    Test route to verify role-based template loading.
    This will render a test template specific to the user's role.
    """
    # Get the current user's role (default to 'user' if not set)
    role = getattr(current_user, 'role', 'user')
    
    # Create test data to pass to the template
    test_data = {
        'user': {
            'name': current_user.name if hasattr(current_user, 'name') else 'Test User',
            'email': current_user.email if hasattr(current_user, 'email') else 'test@example.com',
            'role': role,
            'join_date': '2023-01-01'  # Default join date for testing
        },
        'now': datetime.utcnow(),
        'role': role
    }
    
    # Try to render the role-specific template
    try:
        return render_role_template('test_template.html', **test_data)
    except Exception as e:
        # If there's an error, render a fallback template with the error
        current_app.logger.error(f"Error rendering role template: {str(e)}")
        return render_template('error.html', 
                             error_message=f"Error loading {role} template: {str(e)}",
                             **test_data)

# Add any additional dashboard-related routes below
