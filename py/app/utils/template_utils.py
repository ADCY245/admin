from flask import render_template, current_app, session, request, g
from functools import wraps, lru_cache
import os

# Cache template existence checks
@lru_cache(maxsize=128)
def _template_exists(template_path):
    full_path = os.path.join(current_app.root_path, 'templates', template_path)
    return os.path.exists(full_path)

def get_role_template(template_name, role=None):
    """
    Get the appropriate template path based on the user's role with caching.
    
    Args:
        template_name (str): The base name of the template
        role (str, optional): The role to use. If None, will try to determine from current user/session.
        
    Returns:
        str: The full template path for the role
    """
    # Try to get role from request context first (cached per request)
    if not hasattr(g, '_user_role'):
        if hasattr(request, 'user_roles') and request.user_roles:
            g._user_role = request.user_roles[0]
        elif 'user_role' in session:
            g._user_role = session['user_role']
        elif hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            g._user_role = getattr(current_user, 'role', 'user')
        else:
            g._user_role = 'user'  # Default role
    
    role = role or g._user_role
    
    # Only allow valid roles
    if role not in ['admin', 'dealer', 'user']:
        role = 'user'
    
    # Check for role-specific template with caching
    role_template = f"{role}/{template_name}"
    if _template_exists(role_template):
        return role_template
        
    # Fallback to user template if role-specific doesn't exist
    if role != 'user':
        user_template = f"user/{template_name}"
        if _template_exists(user_template):
            return user_template
    
    return role_template  # Return the original path even if it doesn't exist (will 404)

def render_role_template(template_name, **context):
    """
    Render a template with role-based template resolution.
    
    Args:
        template_name (str): The base name of the template
        **context: Additional context to pass to the template
        
    Returns:
        str: The rendered template
    """
    role_template = get_role_template(template_name)
    return render_template(role_template, **context)

def role_template(template_name):
    """
    Decorator to render a template with role-based resolution.
    
    Usage:
        @app.route('/some-route')
        @role_template('template_name.html')
        def some_route():
            return {'key': 'value'}  # This will be passed to the template
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # Call the view function to get the context
            context = view_func(*args, **kwargs) or {}
            # Render the template with the context
            return render_role_template(template_name, **context)
        return wrapper
    return decorator
