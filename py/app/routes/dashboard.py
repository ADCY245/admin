from flask import Blueprint, render_template, abort, redirect, url_for, flash, current_app, jsonify, request, session
from flask_login import login_required, current_user
from datetime import datetime
import os
from ..models import User
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
    try:
        # Get user role with fallbacks
        if not hasattr(current_user, 'role') or not current_user.role:
            user_role = 'user'
            try:
                # Try to update the user's role in the database
                User.objects(id=current_user.id).update_one(set__role='user')
                current_user.role = 'user'
            except Exception as e:
                current_app.logger.error(f"Error updating user role: {str(e)}")
        else:
            user_role = current_user.role.lower()
        
        # Debug logging
        current_app.logger.info(f"Dashboard access - User: {getattr(current_user, 'email', 'unknown')}, Role: {user_role}")
        
        # Ensure role is valid, default to 'user' if invalid
        if user_role not in ['admin', 'dealer', 'user']:
            current_app.logger.warning(f"Invalid role '{user_role}' for user {getattr(current_user, 'email', 'unknown')}, defaulting to 'user'")
            user_role = 'user'
            session['user_role'] = user_role
            # Update the role in the database
            try:
                User.objects(id=current_user.id).update_one(set__role='user')
                current_user.role = 'user'
            except Exception as e:
                current_app.logger.error(f"Error updating user role: {str(e)}")
        
        # Ensure role is in session
        session['user_role'] = user_role
        session.modified = True
        
        # Debug: List all routes for verification
        current_app.logger.debug("Available routes: %s", 
                              [str(rule) for rule in current_app.url_map.iter_rules()])
        
        # Build the endpoint name for the dashboard
        dashboard_endpoint = f'dashboard.{user_role}_dashboard'
        current_app.logger.info(f"Attempting to redirect to: {dashboard_endpoint}")
        
        try:
            # Try to get the URL for the dashboard
            dashboard_url = url_for(dashboard_endpoint)
            current_app.logger.info(f"Redirecting to: {dashboard_url}")
            return redirect(dashboard_url)
        except Exception as e:
            current_app.logger.error(f"Error generating URL for {dashboard_endpoint}: {str(e)}")
            current_app.logger.exception("Full traceback:")
            flash('Error accessing dashboard. Please try again.', 'error')
            return redirect(url_for('dashboard.user_dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Error in dashboard index: {str(e)}", exc_info=True)
        flash('An error occurred while accessing the dashboard. Defaulting to user dashboard.', 'warning')
        # Default to user dashboard on error
        return redirect(url_for('dashboard.user_dashboard'))

# Alias for backward compatibility
bp.add_url_rule('/dashboard', 'dashboard', index)

@bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard view."""
    try:
        # Check if user is admin
        if not hasattr(current_user, 'role') or current_user.role != 'admin':
            flash('Insufficient privileges. Redirecting to user dashboard.', 'warning')
            return redirect(url_for('dashboard.user_dashboard'))
        
        # Set role in session
        session['user_role'] = 'admin'
        
        # Add admin-specific data
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
        
    except Exception as e:
        current_app.logger.error(f"Error in admin dashboard: {str(e)}")
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('auth.logout'))

@bp.route('/dealer')
@login_required
def dealer_dashboard():
    """Dealer dashboard view."""
    try:
        # Check if user is dealer, if not redirect to user dashboard
        if not hasattr(current_user, 'role') or current_user.role != 'dealer':
            flash('Insufficient privileges. Redirecting to user dashboard.', 'warning')
            return redirect(url_for('dashboard.user_dashboard'))
        
        # Set role in session
        session['user_role'] = 'dealer'
        
        # Add dealer-specific data
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
        
    except Exception as e:
        current_app.logger.error(f"Error in dealer dashboard: {str(e)}")
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('auth.logout'))

@bp.route('/user')
@login_required
def user_dashboard():
    """User dashboard view."""
    try:
        # Ensure user is a regular user
        if current_user.role != 'user':
            flash('Access denied. User privileges required.', 'danger')
            return redirect(url_for('auth.logout'))  # Redirect to logout instead of dashboard
        
        # Set role in session
        session['user_role'] = 'user'
        
        # Add user-specific data
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
        
    except Exception as e:
        current_app.logger.error(f"Error in user dashboard: {str(e)}")
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('auth.logout'))

@bp.route('/test-role-template')
@login_required
def test_role_template():
    """Test route to verify role-based template loading."""
    try:
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
        
        # Render template with test data
        return render_role_template('test_template.html', **test_data)
        
    except Exception as e:
        current_app.logger.error(f"Error in test role template: {str(e)}")
        flash('An error occurred in the test template.', 'error')
        return redirect(url_for('dashboard.index'))
    
# API routes for role-specific dashboard data

@bp.route('/api/user/dashboard')
@login_required
def api_user_dashboard():
    """Return JSON data for user dashboard JS."""
    try:
        if current_user.role != 'user':
            abort(403)
            
        # Get user-specific data
        stats = {
            'total_orders': 0,  # Replace with actual data
            'pending_orders': 0,  # Replace with actual data
            'completed_orders': 0,  # Replace with actual data
            'total_spent': 0  # Replace with actual data
        }
        
        recent_orders = []  # Replace with actual data
        
        return jsonify({
            'success': True,
            'stats': stats,
            'recent_orders': recent_orders,
            'user': {
                'name': current_user.username,
                'email': current_user.email,
                'role': current_user.role
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in user dashboard API: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching dashboard data'
        }), 500
    
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
