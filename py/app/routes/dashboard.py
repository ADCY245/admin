from flask import Blueprint, render_template, redirect, url_for, flash, current_app, jsonify, request, session, g
from flask_login import login_required, current_user
from datetime import datetime
from ..models import User
from ..utils.template_utils import render_role_template, role_template

bp = Blueprint('dashboard', __name__)

def get_user_role():
    """Get and cache the user's role for the current request."""
    if not hasattr(g, '_user_role'):
        if hasattr(current_user, 'role') and current_user.role:
            g._user_role = current_user.role.lower()
        elif 'user_role' in session:
            g._user_role = session['user_role'].lower()
        else:
            g._user_role = 'user'  # Default role
            
        # Ensure role is valid
        if g._user_role not in ['admin', 'dealer', 'user']:
            g._user_role = 'user'
            
    return g._user_role

@bp.route('/')
@login_required
def index():
    """
    Main dashboard route that redirects users to their respective role-based dashboards.
    Optimized to minimize database queries and use cached role information.
    """
    try:
        # Get user role (cached per request)
        user_role = get_user_role()
        
        # Log access (rate limited in production)
        if current_app.debug:
            current_app.logger.debug(f"Dashboard access - User ID: {getattr(current_user, 'id', 'unknown')}, Role: {user_role}")
        
        # Determine the appropriate dashboard endpoint
        dashboard_endpoint = f'dashboard.{user_role}_dashboard'
        
        try:
            # Generate URL for the dashboard
            dashboard_url = url_for(dashboard_endpoint)
            return redirect(dashboard_url)
            
        except Exception as e:
            current_app.logger.error(f"Error generating URL for {dashboard_endpoint}: {str(e)}")
            current_app.logger.exception("Dashboard URL generation failed")
            # Fallback to user dashboard on error
            return redirect(url_for('dashboard.user_dashboard'))
            
    except Exception as e:
        current_app.logger.error(f"Error in dashboard index: {str(e)}", exc_info=True)
        # Default to user dashboard on any error
        return redirect(url_for('dashboard.user_dashboard'))

# Alias for backward compatibility
bp.add_url_rule('/dashboard', 'dashboard', index)

@bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard view with optimized queries and caching."""
    try:
        # Check permissions using cached role
        if get_user_role() != 'admin':
            if current_app.debug:
                current_app.logger.debug(f"Access denied to admin dashboard for role: {get_user_role()}")
            flash('Insufficient privileges. Redirecting to user dashboard.', 'warning')
            return redirect(url_for('dashboard.user_dashboard'))
        
        # Set role in session if not set
        if session.get('user_role') != 'admin':
            session['user_role'] = 'admin'
        
        # Initialize stats with default values
        stats = {
            'total_users': 0,
            'active_sessions': 0,
            'recent_activity': []
        }
        
        # Fetch recent users with projection to only get needed fields
        recent_users = []
        try:
            recent_users = User.objects.only('username', 'email', 'created_at', 'last_login')\
                               .order_by('-created_at')\
                               .limit(5)
        except Exception as e:
            current_app.logger.error(f"Error fetching recent users: {str(e)}")
            if current_app.debug:
                current_app.logger.exception("Recent users query failed")
        
        # Only calculate counts if needed
        if request.args.get('stats') != 'false':
            try:
                stats['total_users'] = User.objects.count()
                # Add other expensive queries here only if necessary
            except Exception as e:
                current_app.logger.error(f"Error fetching stats: {str(e)}")
        
        # Use cached template rendering
        return render_role_template(
            'dashboard.html',
            title='Admin Dashboard',
            stats=stats,
            recent_users=recent_users,
            role='admin',
            now=datetime.utcnow(),
            # Add cache control headers
            cache_timeout=60  # Cache for 1 minute
        )
        
    except Exception as e:
        current_app.logger.error(f"Error in admin dashboard: {str(e)}")
        if current_app.debug:
            current_app.logger.exception("Admin dashboard error")
        flash('An error occurred while loading the admin dashboard.', 'error')
        return redirect(url_for('dashboard.user_dashboard'))

@bp.route('/dealer')
@login_required
def dealer_dashboard():
    """Dealer dashboard view with optimized queries and caching."""
    try:
        # Check permissions using cached role
        if get_user_role() != 'dealer':
            if current_app.debug:
                current_app.logger.debug(f"Access denied to dealer dashboard for role: {get_user_role()}")
            flash('Insufficient privileges. Redirecting to user dashboard.', 'warning')
            return redirect(url_for('dashboard.user_dashboard'))
        
        # Set role in session if not set
        if session.get('user_role') != 'dealer':
            session['user_role'] = 'dealer'
        
        # Initialize stats with default values
        stats = {
            'total_orders': 0,
            'pending_orders': 0,
            'completed_orders': 0,
            'total_products': 0
        }
        
        # Only fetch orders if needed
        recent_orders = []
        if request.args.get('show_orders') != 'false':
            try:
                # Use projection to only fetch needed fields
                recent_orders = Order.objects.only('order_id', 'status', 'created_at', 'total_amount')\
                                           .filter(dealer_id=current_user.id)\
                                           .order_by('-created_at')\
                                           .limit(5)
                
                # Update stats if orders are being fetched anyway
                stats['total_orders'] = Order.objects(dealer_id=current_user.id).count()
                stats['pending_orders'] = Order.objects(dealer_id=current_user.id, status='pending').count()
                stats['completed_orders'] = Order.objects(dealer_id=current_user.id, status='completed').count()
                
            except Exception as e:
                current_app.logger.error(f"Error fetching dealer orders: {str(e)}")
                if current_app.debug:
                    current_app.logger.exception("Dealer orders query failed")
        
        # Use cached template rendering
        return render_role_template(
            'dashboard.html',
            title='Dealer Dashboard',
            stats=stats,
            recent_orders=recent_orders,
            role='dealer',
            now=datetime.utcnow(),
            # Add cache control headers
            cache_timeout=30  # Cache for 30 seconds
        )
        
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
        
        # Prepare user data
        user_data = {
            'name': current_user.username,
            'email': current_user.email,
            'join_date': current_user.created_at.strftime('%B %d, %Y') if hasattr(current_user, 'created_at') and current_user.created_at else 'N/A',
            'avatar': url_for('static', filename='images/default-avatar.png')
        }
        
        # Only fetch orders if needed
        recent_orders = []
        if request.args.get('show_orders') != 'false':
            try:
                # Use projection to only fetch needed fields
                recent_orders = Order.objects.only('order_id', 'status', 'created_at', 'total_amount')\
                                           .filter(user_id=current_user.id)\
                                           .order_by('-created_at')\
                                           .limit(5)
                
                # Update stats if orders are being fetched anyway
                stats['total_orders'] = Order.objects(user_id=current_user.id).count()
                stats['pending_orders'] = Order.objects(user_id=current_user.id, status='pending').count()
                stats['completed_orders'] = Order.objects(user_id=current_user.id, status='completed').count()
                
                # Calculate total spent if needed
                if request.args.get('calculate_total') == 'true':
                    pipeline = [
                        {'$match': {'user_id': current_user.id, 'status': 'completed'}},
                        {'$group': {'_id': None, 'total': {'$sum': '$total_amount'}}}
                    ]
                    result = list(Order.objects.aggregate(*pipeline))
                    if result:
                        stats['total_spent'] = float(result[0]['total'])
                
            except Exception as e:
                current_app.logger.error(f"Error fetching user orders: {str(e)}")
                if current_app.debug:
                    current_app.logger.exception("User orders query failed")
        
        # Use cached template rendering
        return render_role_template(
            'dashboard.html',
            title='My Dashboard',
            stats=stats,
            recent_orders=recent_orders,
            user=user_data,
            role='user',
            now=datetime.utcnow(),
            # Add cache control headers
            cache_timeout=60  # Cache for 1 minute
        )
        
    except Exception as e:
        current_app.logger.error(f"Error in user dashboard: {str(e)}")
        if current_app.debug:
            current_app.logger.exception("User dashboard error")
        flash('An error occurred while loading your dashboard. Please try again.', 'error')
        return redirect(url_for('auth.login'))

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
