from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from flask import current_app

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Changed from password_hash
    phone = db.Column(db.String(20), nullable=True)  # Added phone field
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def generate_token(self):
        payload = {
            'sub': str(self.id),  # Flask-JWT-Extended requires 'sub' claim
            'user_id': self.id,
            'username': self.username,
            'is_admin': self.is_admin,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        # Use JWT_SECRET_KEY instead of SECRET_KEY for consistency
        secret_key = current_app.config.get('JWT_SECRET_KEY', current_app.config['SECRET_KEY'])
        return jwt.encode(payload, secret_key, algorithm='HS256')

    @staticmethod
    def verify_token(token):
        try:
            # Use JWT_SECRET_KEY instead of SECRET_KEY for consistency
            secret_key = current_app.config.get('JWT_SECRET_KEY', current_app.config['SECRET_KEY'])
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            print("JWT Error: Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"JWT Error: Invalid token - {str(e)}")
            return None
        except Exception as e:
            print(f"JWT Error: Unexpected error - {str(e)}")
            return None

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.String(20), nullable=False)
    original_price = db.Column(db.String(20))
    features = db.Column(db.JSON)
    color = db.Column(db.String(50), default='bg-blue-500')
    logo_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Service {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'original_price': self.original_price,
            'features': self.features or [],
            'color': self.color,
            'logo_url': self.logo_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

