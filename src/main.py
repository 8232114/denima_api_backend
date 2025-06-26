import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash
from src.models.user import db, User, Service
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

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['JWT_SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'  # Use same key for consistency

# Initialize JWT
jwt = JWTManager(app)

# Enable CORS
CORS(app)

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(offer_bp, url_prefix='/api')
app.register_blueprint(digital_product_bp, url_prefix='/api')
app.register_blueprint(product_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def create_default_data():
    """Create default admin user and sample services"""
    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@denima.com',
            password=generate_password_hash('admin123'),
            phone='',
            is_admin=True
        )
        db.session.add(admin)
        print("Created default admin user: admin/admin123")
    
    # Create sample services if none exist
    if Service.query.count() == 0:
        services = [
            {
                'name': 'Netflix Premium',
                'description': 'حساب Netflix مميز مع جودة 4K',
                'price': '90',
                'original_price': '150',
                'features': [
                    'جودة 4K Ultra HD',
                    'مشاهدة على 4 أجهزة',
                    'تحميل للمشاهدة دون اتصال',
                    'مكتبة ضخمة من الأفلام والمسلسلات'
                ],
                'color': 'bg-red-500'
            },
            {
                'name': 'Spotify Premium',
                'description': 'حساب Spotify مميز بدون إعلانات',
                'price': '90',
                'original_price': '120',
                'features': [
                    'موسيقى بدون إعلانات',
                    'جودة صوت عالية',
                    'تحميل للاستماع دون اتصال',
                    'تخطي غير محدود'
                ],
                'color': 'bg-green-500'
            },
            {
                'name': 'Shahid VIP',
                'description': 'حساب شاهد VIP للمحتوى العربي',
                'price': '90',
                'original_price': '100',
                'features': [
                    'محتوى عربي حصري',
                    'أفلام ومسلسلات بدون إعلانات',
                    'جودة HD',
                    'مشاهدة على عدة أجهزة'
                ],
                'color': 'bg-blue-500'
            },
            {
                'name': 'Amazon Prime Video',
                'description': 'حساب Amazon Prime Video',
                'price': '90',
                'original_price': '130',
                'features': [
                    'أفلام ومسلسلات حصرية',
                    'جودة 4K',
                    'تحميل للمشاهدة دون اتصال',
                    'محتوى متنوع'
                ],
                'color': 'bg-purple-500'
            },
            {
                'name': 'Crunchyroll Premium',
                'description': 'حساب أنمي مميز بدون إعلانات',
                'price': '90',
                'original_price': '140',
                'features': [
                    'مكتبة ضخمة من الأنمي المترجم',
                    'حلقات جديدة بعد ساعة من صدورها',
                    'تحميل للمشاهدة دون اتصال',
                    'جودة Full HD بدون إعلانات'
                ],
                'color': 'bg-orange-500'
            },
            {
                'name': 'Disney+ Premium',
                'description': 'حساب Disney+ مميز لجميع العائلة',
                'price': '90',
                'original_price': '130',
                'features': [
                    'محتوى حصري من ديزني، مارفل، بيكسار',
                    'جودة مشاهدة عالية 4K',
                    'مشاهدة بدون إنترنت',
                    'تحميل للمشاهدة دون اتصال'
                ],
                'color': 'bg-blue-600'
            }
        ]
        
        for service_data in services:
            service = Service(**service_data)
            db.session.add(service)
        
        print("Created sample services")
    
    # Create default offer if none exists
    if Offer.query.count() == 0:
        offer = Offer(
            is_active=True,
            price='200',
            whatsapp_message='مرحبًا 👋\nأود طلب عرض المنتجات التالية:\n\n{products}\n\nالمجموع: {price} درهم\n\nشكرًا لك 🙏'
        )
        db.session.add(offer)
        db.session.flush()  # Get the offer ID
        
        # Add first 4 services to the offer by default
        services = Service.query.limit(4).all()
        for service in services:
            offer_product = OfferProduct(offer_id=offer.id, service_id=service.id)
            db.session.add(offer_product)
        
        print("Created default offer with first 4 services")
    
    # Create default digital products if none exist
    if DigitalProduct.query.count() == 0:
        digital_products = [
            {
                'name': 'Netflix Premium',
                'description': 'حساب Netflix مميز لمدة شهر كامل مع إمكانية المشاهدة بجودة 4K',
                'price': '$15',
                'original_price': '$25',
                'category': 'streaming',
                'icon': 'Monitor',
                'features': [
                    'جودة 4K',
                    'مشاهدة على 4 أجهزة',
                    'محتوى حصري',
                    'بدون إعلانات'
                ],
                'rating': 4.9
            },
            {
                'name': 'Spotify Premium',
                'description': 'استمتع بالموسيقى بدون إعلانات مع جودة عالية',
                'price': '$12',
                'original_price': '$20',
                'category': 'music',
                'icon': 'Headphones',
                'features': [
                    'بدون إعلانات',
                    'جودة عالية',
                    'تحميل للاستماع بدون إنترنت',
                    'قوائم تشغيل مخصصة'
                ],
                'rating': 4.8
            },
            {
                'name': 'PlayStation Plus',
                'description': 'اشتراك PlayStation Plus مع ألعاب مجانية شهرية',
                'price': '$20',
                'original_price': '$30',
                'category': 'gaming',
                'icon': 'Gamepad2',
                'features': [
                    'ألعاب مجانية شهرية',
                    'خصومات حصرية',
                    'لعب أونلاين',
                    'تخزين سحابي'
                ],
                'rating': 4.7
            }
        ]
        
        for product_data in digital_products:
            product = DigitalProduct(**product_data)
            db.session.add(product)
        
        print("Created default digital products")
    
    # Create default menu sections if none exist
    if MenuSection.query.count() == 0:
        menu_sections = [
            {
                'name': 'home',
                'label_ar': 'الصفحة الرئيسية',
                'label_en': 'Home',
                'icon': 'Home',
                'path': '/',
                'order_index': 1
            },
            {
                'name': 'offers',
                'label_ar': 'العروض الخاصة',
                'label_en': 'Special Offers',
                'icon': 'Gift',
                'action': 'scrollToOffers',
                'order_index': 2
            },
            {
                'name': 'services',
                'label_ar': 'خدمات الترفيه',
                'label_en': 'Entertainment Services',
                'icon': 'Monitor',
                'action': 'scrollToServices',
                'order_index': 3
            },
            {
                'name': 'web-design',
                'label_ar': 'تصميم المواقع',
                'label_en': 'Web Design',
                'icon': 'Monitor',
                'action': 'scrollToWebDesign',
                'order_index': 4
            },
            {
                'name': 'digital-products',
                'label_ar': 'المنتجات الرقمية',
                'label_en': 'Digital Products',
                'icon': 'Smartphone',
                'path': '/digital-products',
                'order_index': 5
            }
        ]
        
        for section_data in menu_sections:
            section = MenuSection(**section_data)
            db.session.add(section)
        
        print("Created default menu sections")
    
    db.session.commit()

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

