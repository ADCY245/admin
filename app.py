"""
Moneda - Main application entry point.
This file serves as the entry point for running the Flask application.
"""
from py.app import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)