import os
import multiprocessing

bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'

# MongoDB connection initialization after fork
def post_fork(server, worker):
    from py.app import create_app
    app = create_app()
    try:
        from pymongo import MongoClient
        from mongoengine import disconnect
        disconnect()
        
        # Use MONGO_URI for connection
        mongo_uri = app.config.get('MONGO_URI')
        if not mongo_uri:
            raise ValueError("MONGO_URI environment variable is not set")
            
        # Connect using URI with MongoEngine
        from mongoengine import connect
        connect(host=mongo_uri)
        
        # Configure Flask-Session with MongoDB
        app.config['SESSION_TYPE'] = 'mongodb'
        app.config['SESSION_MONGODB'] = MongoClient(app.config.get('MONGO_URI'))
        app.config['SESSION_MONGODB_DB'] = app.config.get('DB_NAME', 'moneda_db')
        app.config['SESSION_MONGODB_COLLECT'] = 'sessions'
        app.config['SESSION_USE_SIGNER'] = False
        app.config['SESSION_PERMANENT'] = True
        
        app.logger.info("MongoDB connection initialized successfully")
        
    except Exception as e:
        app.logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise
