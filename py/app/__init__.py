import os
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_login import LoginManager, current_user
from mongoengine import connect, disconnect
from .config import Config
from .models import User
from .utils.logging import setup_logging
from .template_loader import setup_template_loader

def create_app(config_class=Config):
    """
    Create and configure the Flask application.
    
    Args:
        config_class: Configuration class to use (defaults to Config)
        
    Returns:
        Flask: Configured Flask application instance
    """
    # Point to the project root directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Set template directory
    template_dir = os.path.join(base_dir, 'templates')
    if not os.path.exists(template_dir):
        # Try alternative location (for Render deployment)
        template_dir = os.path.join(base_dir, '..', 'templates')
        if not os.path.exists(template_dir):
            raise RuntimeError(f"Template directory not found. Tried: {template_dir}")
    
    # Set static files directory
    static_dir = os.path.join(base_dir, 'static')
    if not os.path.exists(static_dir):
        # Try alternative location (for Render deployment)
        static_dir = os.path.join(base_dir, '..', 'static')
        if not os.path.exists(static_dir):
            raise RuntimeError(f"Static files directory not found. Tried: {static_dir}")
    
    # Initialize Flask with both template and static folders
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir,
                static_url_path='/static')
    
    # Set up template loader for role-based template resolution
    setup_template_loader(app)
    
    # Configure static files URL rules with role-based support
    @app.route('/static/<path:role>/<path:filename>')
    def serve_role_static(role, filename):
        # Only allow known roles
        if role not in ['user', 'dealer', 'admin']:
            return app.send_static_file(filename)
        return app.send_static_file(f'{role}/{filename}')
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        # If the file exists directly, serve it
        if os.path.exists(os.path.join(app.static_folder, filename)):
            return app.send_static_file(filename)
        
        # Otherwise check if it's a role-specific request
        parts = filename.split('/')
        if len(parts) > 1 and parts[0] in ['user', 'dealer', 'admin']:
            role = parts[0]
            remaining_path = '/'.join(parts[1:])
            return app.send_static_file(f'{role}/{remaining_path}')
        
        # If not found, return 404
        return 'Not Found', 404
    
    app.logger.info(f"Template directory set to: {template_dir}")
    app.logger.info(f"Static files directory set to: {static_dir}")
    app.config.from_object(config_class)
    
    # Initialize MongoDB connection
    try:
        # Close any existing connections to avoid issues
        disconnect()
        
        # Connect to MongoDB using the URI from config
        connect(
            db=app.config['MONGODB_DB'],
            host=app.config['MONGODB_HOST'],
            port=int(app.config.get('MONGODB_PORT', 27017)),
            username=app.config.get('MONGODB_USERNAME'),
            password=app.config.get('MONGODB_PASSWORD'),
            authentication_source=app.config.get('MONGODB_AUTH_SOURCE', 'admin')
        )
    except Exception as e:
        app.logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise
    
    # Setup CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "supports_credentials": True
        }
    })
    
    # Setup login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            user = User.objects.get(id=user_id)
            # Store the user's role in the session for template loading
            if hasattr(user, 'role'):
                session['user_role'] = user.role
            return user
        except User.DoesNotExist:
            return None
    
    # Register blueprints
    register_blueprints(app)
    
    # Setup logging
    setup_logging(app)
    
    return app

def register_blueprints(app):
    """Register all blueprints with the Flask application."""
    # Import blueprints
    from .routes.auth import bp as auth_bp
    from .routes.main import bp as main_bp
    from .routes.api import bp as api_bp
    from .routes.dashboard import bp as dashboard_bp
    from .routes.cart_routes import cart_bp
    from .routes.quotation_routes import quotation_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(cart_bp, url_prefix='/api/v1/cart')
    app.register_blueprint(quotation_bp, url_prefix='/api/v1/quotations')
