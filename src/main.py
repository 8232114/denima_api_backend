import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db, User, Service
# Import offer models after user models to ensure proper foreign key resolution
from src.models.offer import Offer, OfferProduct
from src.routes.user import user_bp
from src.routes.offer import offer_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS
CORS(app)

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(offer_bp, url_prefix='/api')

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
            is_admin=True
        )
        admin.set_password('admin123')  # Default password
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

