from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import User
from ..forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from ..utils.email import send_password_reset_email, send_verification_email
from datetime import datetime, timedelta
import uuid
import jwt

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'redirect': url_for('main.index')
            })
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_verified:
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': 'Please verify your email before logging in.'
                    }), 403
                flash('Please verify your email before logging in.', 'warning')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'redirect': url_for('auth.welcome', next=next_page) if not next_page else next_page
                })
                
            return redirect(url_for('auth.welcome', next=next_page))
        
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
    # Determine the appropriate dashboard URL based on user role
    if current_user.role == 'admin':
        dashboard_url = url_for('admin.dashboard')
    elif current_user.role == 'dealer':
        dashboard_url = url_for('dealer.dashboard')
    else:
        dashboard_url = url_for('user.dashboard')
    
    # If it's an AJAX request, return JSON with redirect URL
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'redirect': dashboard_url
        })
    
    # For regular requests, render the welcome template
    return render_template('auth/welcome.html', 
                         current_user=current_user,
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
