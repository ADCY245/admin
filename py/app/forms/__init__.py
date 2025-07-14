# Import all form classes here to make them easily accessible
from .auth_forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from .main_forms import CompanySelectionForm, ProductSelectionForm, CheckoutForm, ContactForm

# Make forms available at the package level
__all__ = [
    'LoginForm',
    'RegistrationForm',
    'ForgotPasswordForm',
    'ResetPasswordForm',
    'CompanySelectionForm',
    'ProductSelectionForm',
    'CheckoutForm',
    'ContactForm'
]
