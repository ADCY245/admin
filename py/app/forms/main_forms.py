from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField, IntegerField, DecimalField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, Regexp, ValidationError
from ..models import Company, Product

class CompanySelectionForm(FlaskForm):
    """Form for selecting a company."""
    company_id = SelectField('Select Company', coerce=str, validators=[DataRequired()])
    submit = SubmitField('Continue')
    
    def __init__(self, *args, **kwargs):
        super(CompanySelectionForm, self).__init__(*args, **kwargs)
        # Populate company choices
        self.company_id.choices = [
            (str(company.id), company.name) 
            for company in Company.objects(status='active').order_by('name')
        ]
        if not self.company_id.choices:
            self.company_id.choices = [('', 'No companies available')]
            self.company_id.render_kw = {'disabled': 'disabled'}


class ProductSelectionForm(FlaskForm):
    """Form for selecting products."""
    product_id = SelectField('Select Product', coerce=str, validators=[DataRequired()])
    quantity = IntegerField('Quantity', default=1, validators=[
        NumberRange(min=1, message='Quantity must be at least 1.')
    ])
    submit = SubmitField('Add to Cart')
    
    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        super(ProductSelectionForm, self).__init__(*args, **kwargs)
        
        # Populate product choices based on company
        if company_id:
            self.product_id.choices = [
                (str(product.id), f"{product.name} - ${product.price:.2f}") 
                for product in Product.objects(company=company_id, status='active').order_by('name')
            ]
        else:
            self.product_id.choices = []
            
        if not self.product_id.choices:
            self.product_id.choices = [('', 'No products available')]
            self.product_id.render_kw = {'disabled': 'disabled'}
            self.quantity.render_kw = {'disabled': 'disabled'}
            self.submit.render_kw = {'disabled': 'disabled'}


class CheckoutForm(FlaskForm):
    """Form for checkout process."""
    # Contact Information
    name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    phone = StringField('Phone', validators=[
        DataRequired(),
        Regexp(r'^\+?[\d\s-]{10,}$', message='Please enter a valid phone number.')
    ])
    
    # Shipping Address
    address = StringField('Address', validators=[
        DataRequired(),
        Length(max=200)
    ])
    city = StringField('City', validators=[
        DataRequired(),
        Length(max=100)
    ])
    state = StringField('State/Province', validators=[
        DataRequired(),
        Length(max=100)
    ])
    postal_code = StringField('Postal Code', validators=[
        DataRequired(),
        Regexp(r'^[a-zA-Z0-9\s-]+$', message='Please enter a valid postal code.')
    ])
    country = StringField('Country', validators=[
        DataRequired(),
        Length(max=100)
    ])
    
    # Payment Method
    payment_method = SelectField('Payment Method', choices=[
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('cod', 'Cash on Delivery')
    ], validators=[DataRequired()])
    
    # Terms and Conditions
    terms = BooleanField('I agree to the Terms and Conditions', validators=[
        DataRequired(message='You must accept the terms and conditions.')
    ])
    
    submit = SubmitField('Place Order')


class ContactForm(FlaskForm):
    """Form for contact page."""
    name = StringField('Your Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    email = StringField('Your Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    subject = StringField('Subject', validators=[
        DataRequired(),
        Length(min=5, max=200)
    ])
    message = TextAreaField('Your Message', validators=[
        DataRequired(),
        Length(min=10, max=2000)
    ])
    submit = SubmitField('Send Message')


class ProductForm(FlaskForm):
    """Form for adding/editing products."""
    name = StringField('Product Name', validators=[
        DataRequired(),
        Length(min=2, max=200)
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=2000)
    ])
    category = StringField('Category', validators=[
        Optional(),
        Length(max=100)
    ])
    price = DecimalField('Price', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Price must be greater than 0.')
    ])
    stock = IntegerField('Stock Quantity', validators=[
        DataRequired(),
        NumberRange(min=0, message='Stock cannot be negative.')
    ])
    sku = StringField('SKU', validators=[
        Optional(),
        Length(max=50)
    ])
    weight = DecimalField('Weight (kg)', validators=[
        Optional(),
        NumberRange(min=0, message='Weight cannot be negative.')
    ])
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('draft', 'Draft')
    ], validators=[DataRequired()])
    
    # Image upload would be handled separately
    
    submit = SubmitField('Save Product')
    
    def validate_sku(self, field):
        """Validate that SKU is unique."""
        if field.data:
            product = Product.objects(sku=field.data).first()
            if product and (not hasattr(self, '_obj') or product != self._obj):
                raise ValidationError('This SKU is already in use. Please use a different one.')


class CompanyForm(FlaskForm):
    """Form for adding/editing companies."""
    name = StringField('Company Name', validators=[
        DataRequired(),
        Length(min=2, max=200)
    ])
    email = StringField('Contact Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    phone = StringField('Phone Number', validators=[
        Optional(),
        Regexp(r'^\+?[\d\s-]{10,}$', message='Please enter a valid phone number.')
    ])
    website = StringField('Website', validators=[
        Optional(),
        Length(max=200),
        Regexp(r'^https?://.+\..+$', message='Please enter a valid URL.')
    ])
    address = TextAreaField('Address', validators=[
        Optional(),
        Length(max=500)
    ])
    tax_id = StringField('Tax ID', validators=[
        Optional(),
        Length(max=50)
    ])
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Save Company')
