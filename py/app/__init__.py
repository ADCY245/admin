import os
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_login import LoginManager, current_user

from mongoengine import connect, disconnect
from pymongo import MongoClient
from .config import Config
from .models import User
from .utils.logging import setup_logging
from .template_loader import setup_template_loader
from flask_session import Session

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
    
    # Configure static file serving
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto-reload templates in development
    
    # Set up template loader for role-based template resolution
    setup_template_loader(app)
    
    # Configure static files URL rules with role-based support
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        # First try to serve the file directly
        file_path = os.path.join(app.static_folder, filename)
        if os.path.exists(file_path):
            return app.send_static_file(filename)
        
        # Try to serve from the static folder root if not found in subdirectories
        filename_only = os.path.basename(filename)
        root_file_path = os.path.join(app.static_folder, filename_only)
        if os.path.exists(root_file_path):
            return app.send_static_file(filename_only)
        
        # Try to serve from js directory
        js_file_path = os.path.join(app.static_folder, 'js', filename_only)
        if os.path.exists(js_file_path):
            return app.send_static_file(f'js/{filename_only}')
            
        # Try to serve from styles directory
        styles_file_path = os.path.join(app.static_folder, 'styles', filename_only)
        if os.path.exists(styles_file_path):
            return app.send_static_file(f'styles/{filename_only}')
            
        # Try role-based paths
        parts = filename.split('/')
        if len(parts) > 1 and parts[0] in ['user', 'dealer', 'admin']:
            role = parts[0]
            remaining_path = '/'.join(parts[1:])
            role_file_path = os.path.join(app.static_folder, role, remaining_path)
            if os.path.exists(role_file_path):
                return app.send_static_file(f'{role}/{remaining_path}')
        
        # Log the 404 for debugging
        app.logger.warning(f'Static file not found: {filename}')
        return 'Not Found', 404
    
    app.logger.info(f"Template directory set to: {template_dir}")
    app.logger.info(f"Static files directory set to: {static_dir}")
    app.config.from_object(config_class)
    
    # Initialize MongoDB connection after fork
    def init_mongodb():
        try:
            # Close any existing connections to avoid issues
            disconnect()
            
            # Use MONGO_URI for connection
            mongo_uri = app.config.get('MONGO_URI')
            if not mongo_uri:
                raise ValueError("MONGO_URI environment variable is not set")
                
            # Connect using URI with MongoEngine
            connect(host=mongo_uri)
            
            # Configure Flask-Session with MongoDB
            app.config['SESSION_TYPE'] = 'mongodb'
            app.config['SESSION_MONGODB'] = MongoClient(app.config.get('MONGO_URI'))
            app.config['SESSION_MONGODB_DB'] = app.config.get('DB_NAME', 'moneda_db')
            app.config['SESSION_MONGODB_COLLECT'] = 'sessions'
            app.config['SESSION_USE_SIGNER'] = False
            app.config['SESSION_PERMANENT'] = True
            Session(app)
            
            app.logger.info("MongoDB connection initialized successfully")
            
        except Exception as e:
            app.logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    # Initialize MongoDB connection
    init_mongodb()
    
    # Configure Gunicorn to initialize MongoDB after fork
    if 'gunicorn' in os.environ.get('SERVER_SOFTWARE', ''):
        from gunicorn.app.base import Application
        
        class FlaskApplication(Application):
            def init(self, parser, opts, args):
                return {
                    'bind': f"0.0.0.0:{app.config.get('PORT', 5000)}",
                    'workers': 2,
                    'post_fork': init_mongodb
                }
        
        FlaskApplication().run()

    # Register Jinja filters
    @app.template_filter('datetimeformat')
    def datetimeformat(value, fmt='%b %d, %Y'):
        """Format a datetime value in templates."""
        if value is None:
            return ''
        return value.strftime(fmt)

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
