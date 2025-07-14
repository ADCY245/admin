import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from flask import current_app

def setup_logging(app):
    """Configure logging for the application.
    
    Args:
        app: The Flask application instance
    """
    # Set log level from config or default to INFO
    log_level = app.config.get('LOG_LEVEL', 'INFO').upper()
    log_format = app.config.get('LOG_FORMAT', 
                              '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(app.root_path, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set up file handler for logging to file
    log_file = os.path.join(log_dir, 'moneda.log')
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=1024 * 1024 * 10,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    file_handler.setLevel(log_level)
    
    # Set up console handler for logging to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    console_handler.setLevel(log_level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure Flask's logger
    app.logger.handlers = []
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    # Log application startup
    app.logger.info('Application logging initialized')
    app.logger.info(f'Log level set to: {log_level}')

class RequestIdFilter(logging.Filter):
    """Add request ID to log records."""
    def filter(self, record):
        from flask import request
        record.request_id = request.headers.get('X-Request-Id', 'none')
        return True

def get_logger(name):
    """Get a logger instance with the given name.
    
    Args:
        name (str): The name of the logger
        
    Returns:
        logging.Logger: A configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure the logger if it hasn't been configured yet
    if not logger.handlers:
        # Set log level from config or default to INFO
        log_level = logging.INFO
        if current_app:
            log_level = getattr(logging, current_app.config.get('LOG_LEVEL', 'INFO').upper())
        
        logger.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Add file handler if running in production
        if current_app and current_app.config.get('ENV') == 'production':
            log_dir = os.path.join(current_app.root_path, 'logs')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            log_file = os.path.join(log_dir, f'{name}.log')
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=1024 * 1024 * 10,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger
