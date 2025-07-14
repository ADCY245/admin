from functools import wraps
from flask import jsonify, session, redirect, url_for, flash, request
from flask_login import current_user

# -------------------- Company Selection Decorator --------------------

def company_required(view_func):
    """Decorator to ensure a company is selected before accessing product/cart pages.
    
    If a `company_id` query parameter is present, it will set the selected company
    in the session on-the-fly so that the request can proceed seamlessly.
    """
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        # Get the current app logger
        from flask import current_app
        logger = current_app.logger
        
        logger.info("[DEBUG] company_required decorator called for %s", request.path)
        
        # If session already has a selected company, allow
        selected_company = session.get('selected_company', {})
        logger.info("[DEBUG] Current selected_company from session: %s", selected_company)
        
        if selected_company.get('id'):
            logger.info("[DEBUG] Company already selected, allowing access")
            return view_func(*args, **kwargs)

        # Check for company_name and company_email in session as fallback
        if session.get('company_name') or session.get('company_email'):
            logger.info("[DEBUG] Found company_name/email in session, creating selected_company")
            session['selected_company'] = {
                'id': session.get('company_id'),
                'name': session.get('company_name', ''),
                'email': session.get('company_email', '')
            }
            session.modified = True
            return view_func(*args, **kwargs)

        # Attempt to use company_id from query parameters (first-time access)
        company_id = request.args.get('company_id')
        logger.info("[DEBUG] No company in session, checking for company_id in query params: %s", company_id)
        
        if company_id:
            # Lazy import to avoid circular dependencies
            from ..models import Company
            company = Company.objects(id=company_id).first()
            
            if company:
                session['selected_company'] = {
                    'id': str(company.id),
                    'name': company.name,
                    'email': company.email
                }
                session['company_name'] = company.name
                session['company_email'] = company.email
                session['company_id'] = str(company.id)  # Ensure company_id is set in session
                session.modified = True
                logger.info("[DEBUG] Updated session with company details")
                return view_func(*args, **kwargs)

        # Otherwise, redirect to company selection
        logger.warning("[DEBUG] No company selected, redirecting to company selection")
        flash('Please select a company first.', 'warning')
        return redirect(url_for('main.company_selection'))
    
    return wrapped_view

# -------------------- Admin Required Decorator --------------------

def admin_required(view_func):
    """Decorator to ensure the current user is an admin."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
            
        if not getattr(current_user, 'is_admin', False):
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
            
        return view_func(*args, **kwargs)
    
    return wrapped_view

# -------------------- JSON API Decorators --------------------

def json_response(view_func):
    """Decorator to convert the returned dictionary into a JSON response."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        result = view_func(*args, **kwargs)
        
        # If the view already returned a response, return it as is
        if hasattr(result, 'headers') or isinstance(result, tuple):
            return result
            
        # Otherwise, convert the result to a JSON response
        response = jsonify({
            'success': True,
            'data': result
        })
        
        return response
    
    return wrapped_view

def handle_errors(view_func):
    """Decorator to handle errors and return appropriate JSON responses."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
            
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error in {view_func.__name__}: {str(e)}", exc_info=True)
            
            response = {
                'success': False,
                'error': str(e)
            }
            
            # Add more details in development
            if current_app.config.get('DEBUG'):
                import traceback
                response['traceback'] = traceback.format_exc()
            
            return jsonify(response), 500
    
    return wrapped_view

# -------------------- Role-Based Access Control --------------------

def role_required(*roles):
    """Decorator to restrict access to users with specific roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
                
            user_roles = getattr(current_user, 'roles', [])
            
            # Check if user has any of the required roles
            if not any(role in user_roles for role in roles):
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.index'))
                
            return view_func(*args, **kwargs)
        
        return wrapped_view
    
    return decorator
