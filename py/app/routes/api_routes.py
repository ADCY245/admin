"""
API Routes
==========
This module contains all API endpoints for the application.
"""
from flask import Blueprint, jsonify, request, current_app, session
from flask_login import login_required, current_user
from functools import wraps
import os
import json
from datetime import datetime, timedelta
import uuid
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from bson.objectid import ObjectId, InvalidId
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import User, Company, Product, Order
from ..utils.decorators import admin_required
from ..utils.email import send_email

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Company API Endpoints
@api_bp.route('/companies', methods=['GET'])
def get_companies():
    """Get all companies."""
    companies = Company.objects().all()
    return jsonify([{
        'id': str(company.id),
        'name': company.name,
        'email': company.email
    } for company in companies])

@api_bp.route('/companies/<company_id>', methods=['GET'])
def get_company(company_id):
    """Get a specific company by ID."""
    try:
        company = Company.objects.get(id=company_id)
        return jsonify({
            'id': str(company.id),
            'name': company.name,
            'email': company.email
        })
    except Company.DoesNotExist:
        return jsonify({'error': 'Company not found'}), 404

# User API Endpoints
@api_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users (admin only)."""
    users = User.objects().all()
    return jsonify([{
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin
    } for user in users])

# Add more API endpoints as needed...

# Error handlers
@api_bp.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
