import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
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

    # Enable CORS
    CORS(app)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Import blueprints here to avoid circular imports
    from src.routes.user import user_bp
    from src.routes.offer import offer_bp
    from src.routes.digital_product import digital_product_bp
    from src.routes.product import product_bp
    from src.routes.auth import auth_bp
    from src.routes.admin import admin_bp

    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(offer_bp, url_prefix='/api')
    app.register_blueprint(digital_product_bp, url_prefix='/api')
    app.register_blueprint(product_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

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

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "API is running", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

