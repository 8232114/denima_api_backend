import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, make_response
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash
from src.extensions import db
from src.models.user import User, Service
# Import offer models after user models to ensure proper foreign key resolution
from src.models.offer import Offer, OfferProduct
# Import digital product models
from src.models.digital_product import DigitalProduct, MenuSection
# Import product models for marketplace
from src.models.product import Product, ProductImage
from src.routes.user import user_bp
from src.routes.offer import offer_bp
from src.routes.digital_product import digital_product_bp
from src.routes.product import product_bp
from src.routes.auth import auth_bp

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
    app.config['JWT_SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
    
    # File upload configuration
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'product_images')

    # Initialize JWT
    JWTManager(app)

    # CORS is now handled by WSGI middleware in wsgi.py
    # Keeping minimal logging for debugging
    
    @app.before_request
    def log_request():
        print(f"Request: {request.method} {request.path}")
        
    @app.after_request
    def log_response(response):
        print(f"Response: {response.status_code} for {request.method} {request.path}")
        return response

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Register blueprints - auth first to ensure it gets priority
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(offer_bp, url_prefix='/api')
    app.register_blueprint(digital_product_bp, url_prefix='/api')
    app.register_blueprint(product_bp, url_prefix='/api')
    
    # Import admin blueprint here to avoid circular imports
    try:
        from src.routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
    except ImportError:
        print("Admin blueprint not found, skipping...")

    return app

def create_default_data():
    """Create default data if it doesn't exist"""
    try:
        # Check if default service exists
        if not Service.query.first():
            default_service = Service(
                name="خدمة افتراضية",
                description="وصف الخدمة الافتراضية",
                price=0.0
            )
            db.session.add(default_service)
            db.session.commit()
    except Exception as e:
        print(f"Error creating default data: {e}")
        db.session.rollback()

app = create_app()

with app.app_context():
    db.create_all()
    create_default_data()

@app.route('/')
def home():
    return "API is running", 200



@app.route('/api/static/product_images/<filename>')
def serve_product_image(filename):
    """Serve product images"""
    from flask import make_response
    images_dir = os.path.join(os.path.dirname(__file__), 'static', 'product_images')
    response = make_response(send_from_directory(images_dir, filename))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)