from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_required, current_user
from ..models import User, Company, Product, Order
from ..forms import CompanySelectionForm, ProductSelectionForm, CheckoutForm
from ..utils.decorators import company_required, role_required
from datetime import datetime
import json
import os

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Redirect to login page."""
    return redirect(url_for('auth.login'))

def get_role_template(role, template_name):
    """Helper function to get the correct template path based on role."""
    # Check if the role-specific template exists
    role_template = f"{role}/{template_name}"
    template_path = os.path.join(current_app.root_path, 'templates', role, template_name)
    
    if os.path.exists(template_path):
        return role_template
    
    # Fallback to user template if role-specific template doesn't exist
    if role != 'user':
        user_template = f"user/{template_name}"
        user_path = os.path.join(current_app.root_path, 'templates', 'user', template_name)
        if os.path.exists(user_path):
            return user_template
    
    # If no template found, return the original template path
    return template_name

@bp.route('/company-selection', methods=['GET', 'POST'])
@login_required
@role_required('user')
def company_selection():
    """Company selection page."""
    form = CompanySelectionForm()
    companies = Company.objects(status='active').order_by('name')
    
    if form.validate_on_submit():
        company = Company.objects(id=form.company_id.data).first()
        if company:
            session['selected_company'] = {
                'id': str(company.id),
                'name': company.name,
                'email': company.email
            }
            flash(f'Selected company: {company.name}', 'success')
            return redirect(url_for('main.product_selection'))
    
    # Get the appropriate template based on user role
    template = get_role_template(current_user.role, 'company_selection.html')
    return render_template(template, form=form, companies=companies)

@bp.route('/product-selection')
@login_required
@role_required('user')
@company_required
def product_selection():
    """Product selection page."""
    company_id = session.get('selected_company', {}).get('id')
    if not company_id:
        flash('Please select a company first', 'warning')
        return redirect(url_for('main.company_selection'))
    
    products = Product.objects(company=company_id, status='active').order_by('name')
    
    # Get the appropriate template based on user role
    template = get_role_template(current_user.role, 'product_selection.html')
    return render_template(template, products=products)

@bp.route('/cart')
@login_required
@role_required('user')
def cart():
    """Shopping cart page."""
    cart = session.get('cart', {})
    products = []
    total = 0
    
    for product_id, item in cart.items():
        product = Product.objects(id=product_id).first()
        if product:
            # Apply dealer pricing if user is a dealer
            price = product.dealer_price if hasattr(current_user, 'role') and current_user.role == 'dealer' else product.price
            item_total = price * item['quantity']
            products.append({
                'id': str(product.id),
                'name': product.name,
                'price': price,
                'quantity': item['quantity'],
                'total': item_total
            })
            total += item_total
    
    # Get the appropriate template based on user role
    template = get_role_template(current_user.role, 'cart.html')
    return render_template(template, products=products, total=total)

@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
@company_required
def checkout():
    """Checkout process."""
    if not current_user.cart:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('main.product_selection'))
    
    form = CheckoutForm()
    
    # Calculate order total
    cart = current_user.cart or []
    subtotal = sum(item.get('price', 0) * item.get('quantity', 0) for item in cart)
    tax = subtotal * 0.1  # 10% tax
    total = subtotal + tax
    
    if form.validate_on_submit():
        # Create order
        order = Order(
            order_number=f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            user=current_user.id,
            company=session['selected_company']['id'],
            items=cart,
            total_amount=total,
            shipping_address={
                'name': form.name.data,
                'email': form.email.data,
                'phone': form.phone.data,
                'address': form.address.data,
                'city': form.city.data,
                'state': form.state.data,
                'postal_code': form.postal_code.data,
                'country': form.country.data
            },
            payment_method=form.payment_method.data
        )
        order.save()
        
        # Clear cart
        current_user.cart = []
        current_user.save()
        
        flash('Your order has been placed successfully!', 'success')
        return redirect(url_for('main.order_confirmation', order_id=str(order.id)))
    
    return render_template('checkout.html', 
                         form=form,
                         cart=cart,
                         subtotal=subtotal,
                         tax=tax,
                         total=total)

@bp.route('/order-confirmation/<order_id>')
@login_required
def order_confirmation(order_id):
    """Order confirmation page."""
    order = Order.objects(id=order_id).first_or_404()
    if str(order.user.id) != str(current_user.id) and current_user.role != 'admin':
        flash('You do not have permission to view this order', 'error')
        return redirect(url_for('main.index'))
    
    # Get the appropriate template based on user role
    template = get_role_template(current_user.role, 'order_confirmation.html')
    return render_template(template, order=order)

@bp.route('/orders')
@login_required
def orders():
    """View order history."""
    user_orders = Order.objects(user=current_user.id).order_by('-created_at')
    
    # Get the appropriate template based on user role
    template = get_role_template(current_user.role, 'orders.html')
    return render_template(template, orders=user_orders)

@bp.route('/orders/<order_id>')
@login_required
def order_details(order_id):
    """View order details."""
    order = Order.objects(id=order_id).first_or_404()
    if str(order.user.id) != str(current_user.id) and current_user.role != 'admin':
        flash('You do not have permission to view this order', 'error')
        return redirect(url_for('main.orders'))
    
    # Get the appropriate template based on user role
    template = get_role_template(current_user.role, 'order_details.html')
    return render_template(template, order=order)

@bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page."""
    if request.method == 'POST':
        # Process contact form
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # TODO: Send email to admin
        flash('Thank you for your message. We will get back to you soon!', 'success')
        return redirect(url_for('main.contact'))
    
    return render_template('contact.html')
