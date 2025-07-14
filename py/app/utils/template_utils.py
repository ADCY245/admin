from flask import render_template, current_app, session, request
from functools import wraps

def get_role_template(template_name, role=None):
    """
    Get the appropriate template path based on the user's role.
    
    Args:
        template_name (str): The base name of the template
        role (str, optional): The role to use. If None, will try to determine from current user/session.
        
    Returns:
        str: The full template path for the role
    """
    if role is None:
        # Try to get role from request, session, or current_user
        if hasattr(request, 'user_roles') and request.user_roles:
            role = request.user_roles[0]
        elif 'user_role' in session:
            role = session['user_role']
        elif hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            role = getattr(current_user, 'role', 'user')
        else:
            role = 'user'  # Default role
    
    # Only allow valid roles
    if role not in ['admin', 'dealer', 'user']:
        role = 'user'
    
    # Return the role-specific template path
    return f"{role}/{template_name}"

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
