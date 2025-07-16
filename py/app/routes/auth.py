from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app
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
    try:
        # Handle already authenticated users
        if current_user.is_authenticated:
            flash('You are already logged in.', 'info')
            return redirect(url_for('dashboard.index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            # Try to get user by email or username
            identifier = form.email.data
            user = User.objects.filter(email=identifier).first() or \
                   User.objects.filter(username=identifier).first()
            
            if not user:
                flash('User not found.', 'danger')
                return render_template('auth/login.html', form=form)
            
            if not user.check_password(form.password.data):
                flash('Invalid password.', 'danger')
                return render_template('auth/login.html', form=form)
            
            if not user.is_verified:
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': 'Please verify your email before logging in.'
                    }), 403
                flash('Please verify your email before logging in.', 'warning')
                return render_template('auth/login.html', form=form)
            
            # Ensure we have the username and role before logging in
            update_needed = False
            
            # Only update if username is not set
            if not user.username:
                user.username = user.email.split('@')[0]
                update_needed = True
                
            # Ensure role is set
            if not user.role:
                user.role = 'user'  # Default to 'user' if role is not set
                update_needed = True
            
            # Only save if updates are needed
            if update_needed:
                # Use update_one to avoid validation errors
                User.objects(id=user.id).update_one(
                    set__username=user.username,
                    set__role=user.role
                )
            
            # Set role in session
            session['user_role'] = user.role
            
            # Log the user in
            login_user(user, remember=True, force=True)
            
            # Debug logging
            current_app.logger.info(f"User {user.email} logged in with role: {user.role}")
            current_app.logger.info(f"User object before redirect: {user.to_json()}")
            
            # Get the role after login to ensure it's set correctly
            user_role = getattr(user, 'role', 'user').lower()
            current_app.logger.info(f"Resolved role for redirection: {user_role}")
            
            # Ensure the role is in the session
            session['user_role'] = user_role
            
            # Redirect to the appropriate dashboard based on role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # Force a session commit
            session.modified = True
            
            # Debug: List all routes for verification
            current_app.logger.info("Available routes: %s", 
                                 [str(rule) for rule in current_app.url_map.iter_rules()])
            
            # Redirect to welcome page first
            try:
                current_app.logger.info(f"Redirecting to welcome page for role: {user_role}")
                return redirect(url_for('auth.welcome'))
            except Exception as e:
                current_app.logger.error(f"Error during welcome redirection: {str(e)}")
                current_app.logger.exception("Full traceback:")
                flash('An error occurred during redirection. Please try again.', 'error')
                # Fallback to direct dashboard redirect if welcome page fails
                if user_role == 'admin':
                    return redirect(url_for('dashboard.admin_dashboard'))
                elif user_role == 'dealer':
                    return redirect(url_for('dashboard.dealer_dashboard'))
                else:
                    return redirect(url_for('dashboard.user_dashboard'))
        
        # Handle AJAX GET requests
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': 'Please provide login credentials'
            }), 400
        
        return render_template('auth/login.html', form=form)
        
    except Exception as e:
        current_app.logger.error(f"Error in login: {str(e)}")
        flash('An error occurred. Please try again.', 'error')
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
    """Welcome page that shows a brief welcome message and redirects to the appropriate dashboard."""
    try:
        # Ensure user is authenticated
        if not current_user.is_authenticated:
            current_app.logger.warning("Unauthenticated user attempted to access welcome page")
            return redirect(url_for('auth.login'))
            
        # Get user data from current_user (Flask-Login)
        user_data = {
            'id': getattr(current_user, 'id', ''),
            'username': getattr(current_user, 'username', ''),
            'email': getattr(current_user, 'email', ''),
            'role': getattr(current_user, 'role', 'user'),
            'is_verified': getattr(current_user, 'is_verified', False),
            'created_at': getattr(current_user, 'created_at', datetime.utcnow())
        }
        
        # Ensure role is valid
        user_role = user_data['role'].lower()
        if user_role not in ['admin', 'dealer', 'user']:
            user_role = 'user'
            user_data['role'] = 'user'
        
        # Update session role if needed
        if session.get('user_role') != user_role:
            session['user_role'] = user_role
        
        # Determine the target dashboard
        dashboard_endpoint = f'dashboard.{user_role}_dashboard'
        
        # For AJAX requests, return JSON with redirect URL
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'redirect': url_for(dashboard_endpoint)
            })
        
        # For regular requests, render the welcome template with a short timeout
        return render_template('auth/welcome.html', 
                            user=user_data,
                            redirect_url=url_for(dashboard_endpoint)), 200, {
                                'Cache-Control': 'no-cache, no-store, must-revalidate',
                                'Pragma': 'no-cache',
                                'Expires': '0'
                            }
        
    except Exception as e:
        current_app.logger.error(f"Error in welcome route: {str(e)}", exc_info=True)
        # Instead of redirecting to login (which could cause loops), go directly to the user dashboard
        try:
            return redirect(url_for('dashboard.user_dashboard'))
        except Exception as redirect_error:
            current_app.error(f"Critical error in welcome redirect: {str(redirect_error)}")
            # Last resort - show error page
            return "An error occurred. Please try refreshing the page or contact support.", 500

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
