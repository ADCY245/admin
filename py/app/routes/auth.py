from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import User
from ..forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from ..utils.email import send_password_reset_email, send_verification_email
from mongo_users import find_user_by_id
from datetime import datetime, timedelta
import uuid
import jwt

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Handle already authenticated users
    if current_user.is_authenticated:
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Try to get user by email or username
        identifier = form.email.data  # This could be email or username
        user = User.objects.filter(email=identifier).first() or \
               User.objects.filter(username=identifier).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_verified:
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': 'Please verify your email before logging in.'
                    }), 403
                flash('Please verify your email before logging in.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Ensure we have the username and role before logging in
            user.username = user.username or user.email.split('@')[0]
            user.role = user.role or 'user'
            
            # Set role in session
            session['user_role'] = user.role
            
            login_user(user, remember=True, force=True)
            next_page = request.args.get('next')
            
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'redirect': next_page or url_for('auth.welcome')
                })
                
            # For regular requests, redirect directly to the next page or welcome page
            return redirect(next_page or url_for('auth.welcome'))
        
        error_msg = 'Invalid email or password'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': error_msg
            }), 401
            
        flash(error_msg, 'danger')
    
    # Handle AJAX GET requests
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': False,
            'message': 'Please provide login credentials'
        }), 400
    
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        if User.objects(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))
            
        if User.objects(username=form.username.data).first():
            flash('Username already taken', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        user = User(
            email=form.email.data,
            username=form.username.data,
            is_verified=False
        )
        user.set_password(form.password.data)
        user.save()
        
        # Send verification email
        send_verification_email(user)
        
        flash('Registration successful! Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))
    
    # Use absolute path to ensure template is found
    return render_template('auth/register.html', form=form)

@bp.route('/verify-email/<token>')
def verify_email(token):
    if current_user.is_authenticated and current_user.is_verified:
        return redirect(url_for('main.index'))
    
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.objects(id=data['user_id']).first()
        
        if not user:
            flash('Invalid verification link', 'danger')
            return redirect(url_for('auth.login'))
            
        if user.is_verified:
            flash('Account already verified. Please login.', 'info')
            return redirect(url_for('auth.login'))
            
        user.is_verified = True
        user.save()
        
        flash('Email verified successfully! You can now login.', 'success')
        return redirect(url_for('auth.login'))
        
    except jwt.ExpiredSignatureError:
        flash('The verification link has expired.', 'danger')
    except (jwt.InvalidTokenError, KeyError):
        flash('Invalid verification link', 'danger')
    
    return redirect(url_for('auth.login'))

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user:
            # Generate reset token
            token = user.generate_reset_token()
            
            # Send password reset email
            send_password_reset_email(user, token)
            
        flash('If an account exists with that email, you will receive a password reset link.', 'info')
        return redirect(url_for('auth.login'))
    
    # Use absolute path to ensure template is found
    return render_template('auth/forgot_password.html', form=form)

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.objects(id=data['user_id']).first()
        
        if not user:
            flash('Invalid or expired password reset link', 'danger')
            return redirect(url_for('auth.forgot_password'))
            
        form = ResetPasswordForm()
        if form.validate_on_submit():
            user.set_password(form.password.data)
            user.save()
            flash('Your password has been reset. You can now login with your new password.', 'success')
            return redirect(url_for('auth.login'))
        
        # Use absolute path to ensure template is found
        return render_template('auth/reset_password.html', form=form, token=token)
        
    except jwt.ExpiredSignatureError:
        flash('The password reset link has expired.', 'danger')
    except (jwt.InvalidTokenError, KeyError):
        flash('Invalid or expired password reset link', 'danger')
    
    return redirect(url_for('auth.forgot_password'))

@bp.route('/welcome')
@login_required
def welcome():
    # Get the current user's ID from Flask-Login
    user_id = str(current_user.get_id())
    
    # Fetch user data from MongoDB
    user = find_user_by_id(user_id)
    
    if not user:
        flash('User not found in database', 'error')
        return redirect(url_for('auth.logout'))
    
    # Ensure role is consistent between user and session
    if user['role'] != session.get('user_role'):
        session['user_role'] = user['role']
    
    # Get the next page from URL parameter
    next_page = request.args.get('next')
    
    # If there's a next page specified, redirect directly to it
    if next_page:
        return redirect(next_page)
    
    # Determine the appropriate dashboard URL based on user role
    dashboard_url = url_for(f'dashboard.{user["role"]}_dashboard')
    
    # If it's an AJAX request, return JSON with redirect URL
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'redirect': dashboard_url
        })
    
    # For regular requests, render the welcome template
    return render_template('auth/welcome.html', 
                         user=user,
                         redirect_url=dashboard_url)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')
