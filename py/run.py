#!/usr/bin/env python
"""
Moneda - Main application entry point.
"""
import os
from app import create_app
from app.models import db, User, Company, Product, Order, Machine

# Create the Flask application
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """
    Add models to Flask shell context for easier access in the shell.
    """
    return {
        'db': db,
        'User': User,
        'Company': Company,
        'Product': Product,
        'Order': Order,
        'Machine': Machine
    }

if __name__ == '__main__':
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
