import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    SESSION_TYPE = 'filesystem'
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    
    # MongoDB Configuration
    MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
    MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
    MONGODB_DB = os.getenv('MONGODB_DB', 'moneda_db')
    MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', '')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', '')
    MONGODB_AUTH_SOURCE = os.getenv('MONGODB_AUTH_SOURCE', 'admin')
    
    # For backward compatibility
    MONGO_URI = os.getenv('MONGO_URI', '').strip() or f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}"
    
    # JWT Configuration
    JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION = 3600  # 1 hour
    
    # Email Configuration
    SMTP_SERVER = os.getenv('SMTP_HOST')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USER')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    EMAIL_FROM = os.getenv('EMAIL_FROM')
    EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME')
    ADMIN_ALERT_EMAIL = os.getenv('ADMIN_ALERT_EMAIL', 'athulnair3096@gmail.com')
    
    # Frontend URL for email links
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    # File Uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @staticmethod
    def init_app(app):
        """Initialize configuration."""
        # Create upload folder if it doesn't exist
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class ProductionConfig(Config):
    """Production configuration."""
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PREFERRED_URL_SCHEME = 'https'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
