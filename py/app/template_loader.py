import os
from jinja2 import FileSystemLoader, ChoiceLoader
from flask import current_app, session, request

def setup_template_loader(app):
    """Set up the template loader to handle role-based template loading."""
    # Get the base template directory
    template_dir = app.template_folder
    
    # Create loaders for each role and the base directory
    loaders = [
        FileSystemLoader(os.path.join(template_dir, 'admin')),
        FileSystemLoader(os.path.join(template_dir, 'dealer')),
        FileSystemLoader(os.path.join(template_dir, 'user')),
        FileSystemLoader(template_dir)  # Fallback to base templates
    ]
    
    # Set up the choice loader with all loaders
    app.jinja_loader = ChoiceLoader(loaders)
    
    # Add a context processor to make the current role available in all templates
    @app.context_processor
    def inject_role():
        role = 'user'  # Default role
        if hasattr(current_user, 'role') and current_user.is_authenticated:
            role = current_user.role
        elif 'user_role' in session:
            role = session.get('user_role', 'user')
        return {'current_role': role}

    # Add a before_request handler to set user roles
    @app.before_request
    def before_request():
        # Ensure we have a session
        if not hasattr(request, 'session'):
            request.session = session
            
        # Set user role in session if not already set
        if current_user.is_authenticated and 'user_role' not in session:
            session['user_role'] = current_user.role
            
        # Set user_roles in request for template context
        if hasattr(current_user, 'role') and current_user.is_authenticated:
            request.user_roles = [current_user.role]
        elif 'user_id' in session:
            request.user_roles = [session.get('user_role', 'user')]
        else:
            request.user_roles = ['guest']
