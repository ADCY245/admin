from mongoengine import (
    Document, StringField, EmailField, DateTimeField, 
    ReferenceField, DictField, ListField, IntField, 
    FloatField, BooleanField, CASCADE, connect
)
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime, timedelta

# Database connection will be initialized in the app factory

class User(Document, UserMixin):
    """User model for authentication and profile information."""
    meta = {
        'collection': 'users',
        'indexes': [
            'email',
            'username',
            'reset_token',
            {'fields': ['reset_token_expiry'], 'expireAfterSeconds': 0}
        ]
    }
    
    id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    email = EmailField(required=True, unique=True)
    username = StringField(required=True, unique=True)
    password_hash = StringField(required=True)
    role = StringField(choices=['admin', 'dealer', 'user'], default='user')
    is_verified = BooleanField(default=False)
    otp_verified = BooleanField(default=False)
    reset_token = StringField()
    reset_token_expiry = DateTimeField()
    company_id = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    # Cart as an embedded document
    cart = ListField(DictField())
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.save()
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self, expires_in=3600):
        import jwt
        from app import app
        
        self.reset_token = jwt.encode(
            {'reset_password': self.id, 'exp': datetime.utcnow() + timedelta(seconds=expires_in)},
            app.config['SECRET_KEY'], algorithm='HS256'
        )
        self.reset_token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
        self.save()
        return self.reset_token


class Company(Document):
    """Company model for storing company information."""
    meta = {
        'collection': 'companies',
        'indexes': [
            'name',
            'email',
            'status'
        ]
    }
    
    name = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    phone = StringField()
    address = StringField()
    status = StringField(choices=['active', 'inactive'], default='active')
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)


class Machine(Document):
    """Machine model for storing machine information."""
    meta = {
        'collection': 'machines',
        'indexes': [
            'name',
            'company',
            'status'
        ]
    }
    
    name = StringField(required=True)
    company = ReferenceField(Company, reverse_delete_rule=CASCADE)
    model = StringField()
    status = StringField(choices=['active', 'maintenance', 'inactive'], default='active')
    specifications = DictField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)


class Product(Document):
    """Product model for storing product information."""
    meta = {
        'collection': 'products',
        'indexes': [
            'name',
            'category',
            'status',
            'company'
        ]
    }
    
    name = StringField(required=True)
    description = StringField()
    category = StringField()
    price = FloatField(required=True)
    stock = IntField(default=0)
    company = ReferenceField(Company, reverse_delete_rule=CASCADE)
    status = StringField(choices=['active', 'inactive'], default='active')
    specifications = DictField()
    images = ListField(StringField())
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)


class Cart(Document):
    """Cart model for storing user shopping cart information."""
    meta = {
        'collection': 'carts',
        'indexes': [
            'user_id',
            'created_at'
        ]
    }
    
    user_id = StringField(required=True, unique=True)
    items = ListField(DictField())
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    @classmethod
    def get_or_create(cls, user_id):
        """Get existing cart or create a new one for the user."""
        cart = cls.objects(user_id=user_id).first()
        if not cart:
            cart = cls(user_id=user_id, items=[])
            cart.save()
        return cart
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'items': self.items,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Quotation(Document):
    """Quotation model for storing quotation information."""
    meta = {
        'collection': 'quotations',
        'indexes': [
            'quotation_number',
            'user_id',
            'company_id',
            'status',
            'created_at'
        ]
    }
    
    quotation_number = StringField(required=True, unique=True)
    user_id = StringField(required=True)
    company_id = StringField(required=True)
    items = ListField(DictField())
    subtotal = FloatField(required=True)
    tax_amount = FloatField(default=0.0)
    total_amount = FloatField(required=True)
    status = StringField(choices=['draft', 'sent', 'accepted', 'rejected', 'expired'], default='draft')
    expiry_date = DateTimeField()
    notes = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    @classmethod
    def generate_quotation_number(cls):
        """Generate a unique quotation number."""
        prefix = 'QUO-'
        last_quote = cls.objects().order_by('-created_at').first()
        
        if last_quote and last_quote.quotation_number.startswith(prefix):
            try:
                last_num = int(last_quote.quotation_number.split('-')[-1])
                new_num = f"{prefix}{str(last_num + 1).zfill(5)}"
            except (ValueError, IndexError):
                new_num = f"{prefix}00001"
        else:
            new_num = f"{prefix}00001"
            
        return new_num
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'quotation_number': self.quotation_number,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'items': self.items,
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'total_amount': self.total_amount,
            'status': self.status,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Order(Document):
    """Order model for storing order information."""
    meta = {
        'collection': 'orders',
        'indexes': [
            'order_number',
            'user',
            'company',
            'status',
            'created_at'
        ]
    }
    
    order_number = StringField(required=True, unique=True)
    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    company = ReferenceField(Company, reverse_delete_rule=CASCADE)
    items = ListField(DictField())
    total_amount = FloatField(required=True)
    status = StringField(choices=['pending', 'processing', 'shipped', 'delivered', 'cancelled'], default='pending')
    shipping_address = DictField()
    payment_method = StringField()
    payment_status = StringField(choices=['pending', 'paid', 'failed', 'refunded'], default='pending')
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'order_number': self.order_number,
            'user_id': str(self.user.id),
            'company_id': str(self.company.id),
            'items': self.items,
            'total_amount': self.total_amount,
            'status': self.status,
            'shipping_address': self.shipping_address,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
