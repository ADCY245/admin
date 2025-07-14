# This file makes the routes directory a Python package
# Import all route blueprints here to make them easily accessible
from .main import bp as main_bp
from .auth import bp as auth_bp
from .api import bp as api_bp

# Export all blueprints
__all__ = ['main_bp', 'auth_bp', 'api_bp']
