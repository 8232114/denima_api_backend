from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from src.models.user import User, db
from src.models.product import Product, ProductImage
import os
import uuid
from functools import wraps

product_bp = Blueprint('product', __name__)

@product_bp.after_request
def after_request(response):
    """Add CORS headers to all product route responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Middleware for authentication
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'صيغة الرمز المميز غير صحيحة'}), 401
        
        if not token:
            return jsonify({'message': 'الرمز المميز مفقود'}), 401
        
        payload = User.verify_token(token)
        if payload is None:
            return jsonify({'message': 'الرمز المميز غير صحيح أو منتهي الصلاحية'}), 401
        
        current_user = User.query.get(payload['user_id'])
        if not current_user:
            return jsonify({'message': 'المستخدم غير موجود'}), 401
        
        # التحقق من حالة الحظر
        if current_user.is_banned:
            return jsonify({'message': 'تم حظر حسابك من استخدام السوق'}), 403
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# إعدادات رفع الصور
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'product_images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """إنشاء مجلد الرفع إذا لم يكن موجوداً"""
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # التحقق من صلاحيات الكتابة
        test_file = os.path.join(UPLOAD_FOLDER, 'test_write.tmp')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            raise Exception(f'لا يمكن الكتابة في مجلد الرفع: {str(e)}')
            
    except Exception as e:
        raise Exception(f'فشل في إنشاء مجلد الرفع: {str(e)}')

# مسارات المنتجات

@product_bp.route('/products', methods=['GET'])
def get_products():
    """الحصول على جميع المنتجات النشطة"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'products': [product.to_dict() for product in products.items],
            'total': products.total,
            'pages': products.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error fetching products: {str(e)}'}), 500

@product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """الحصول على منتج محدد"""
    try:
        product = Product.query.get_or_404(product_id)
        if not product.is_active:
            return jsonify({'message': 'Product not found'}), 404
            
        return jsonify({'product': product.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error fetching product: {str(e)}'}), 500

@product_bp.route('/products', methods=['POST'])
@token_required
def create_product(current_user):
    """إضافة منتج جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['name', 'description', 'price', 'seller_phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'الحقل {field} مطلوب'}), 400
        
        # إنشاء المنتج
        product = Product(
            name=data['name'],
            description=data['description'],
            price=float(data['price']),
            additional_details=data.get('additional_details', ''),
            seller_phone=data['seller_phone'],
            seller_id=current_user.id
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'message': 'تم إنشاء المنتج بنجاح',
            'product': product.to_dict()
        }), 201
        
    except ValueError:
        return jsonify({'message': 'صيغة السعر غير صحيحة'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في إنشاء المنتج: {str(e)}'}), 500

@product_bp.route('/products/<int:product_id>', methods=['PUT'])
@token_required
def update_product(current_user, product_id):
    """تحديث منتج"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # التحقق من أن المستخدم هو صاحب المنتج أو مدير
        if product.seller_id != current_user.id and not current_user.is_admin:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        
        # تحديث البيانات
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = float(data['price'])
        if 'additional_details' in data:
            product.additional_details = data['additional_details']
        if 'seller_phone' in data:
            product.seller_phone = data['seller_phone']
        if 'is_active' in data and current_user.is_admin:
            product.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'message': 'تم تحديث المنتج بنجاح',
            'product': product.to_dict()
        }), 200
        
    except ValueError:
        return jsonify({'message': 'صيغة السعر غير صحيحة'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في تحديث المنتج: {str(e)}'}), 500

@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(current_user, product_id):
    """حذف منتج"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # التحقق من أن المستخدم هو صاحب المنتج أو مدير
        if product.seller_id != current_user.id and not current_user.is_admin:
            return jsonify({'message': 'Access denied'}), 403
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'message': 'Product deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting product: {str(e)}'}), 500

@product_bp.route('/products/<int:product_id>/images', methods=['POST'])
@token_required
def upload_product_image(current_user, product_id):
    """رفع صورة للمنتج"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # التحقق من أن المستخدم هو صاحب المنتج
        if product.seller_id != current_user.id and not current_user.is_admin:
            return jsonify({'message': 'غير مسموح لك برفع صور لهذا المنتج'}), 403
        
        if 'image' not in request.files:
            return jsonify({'message': 'لم يتم إرسال ملف صورة'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'message': 'لم يتم اختيار ملف'}), 400
        
        # التحقق من نوع الملف
        if not allowed_file(file.filename):
            return jsonify({'message': 'نوع الملف غير مدعوم. يُسمح فقط بـ PNG, JPG, JPEG, GIF, WEBP'}), 400
        
        # التحقق من حجم الملف (10MB)
        file.seek(0, 2)  # الانتقال لنهاية الملف
        file_size = file.tell()
        file.seek(0)  # العودة لبداية الملف
        
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return jsonify({'message': f'حجم الملف كبير جداً. الحد الأقصى {max_size // (1024*1024)}MB'}), 400
        
        # التحقق من عدد الصور الحالية
        current_images_count = ProductImage.query.filter_by(product_id=product_id).count()
        if current_images_count >= 5:
            return jsonify({'message': 'تم الوصول للحد الأقصى من الصور (5 صور)'}), 400
        
        # إنشاء مجلد الرفع إذا لم يكن موجوداً
        ensure_upload_folder()
        
        # إنشاء اسم ملف فريد
        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # حفظ الملف
        file.save(filepath)
        
        # التحقق من أن الملف تم حفظه بنجاح
        if not os.path.exists(filepath):
            return jsonify({'message': 'فشل في حفظ الملف'}), 500
        
        # إنشاء سجل الصورة في قاعدة البيانات
        image_url = f'/api/static/product_images/{filename}'
        is_primary = current_images_count == 0  # الصورة الأولى تكون أساسية
        
        product_image = ProductImage(
            product_id=product_id,
            image_url=image_url,
            is_primary=is_primary
        )
        
        db.session.add(product_image)
        db.session.commit()
        
        return jsonify({
            'message': 'تم رفع الصورة بنجاح',
            'image': product_image.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # حذف الملف إذا تم إنشاؤه
        if 'filepath' in locals() and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        return jsonify({'message': f'خطأ في رفع الصورة: {str(e)}'}), 500

@product_bp.route('/products/<int:product_id>/images/<int:image_id>', methods=['DELETE'])
@token_required
def delete_product_image(current_user, product_id, image_id):
    """حذف صورة منتج"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # التحقق من أن المستخدم هو صاحب المنتج
        if product.seller_id != current_user.id and not current_user.is_admin:
            return jsonify({'message': 'Access denied'}), 403
        
        image = ProductImage.query.filter_by(id=image_id, product_id=product_id).first_or_404()
        
        # حذف الملف من النظام
        filename = image.image_url.split('/')[-1]
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'message': 'Image deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting image: {str(e)}'}), 500

@product_bp.route('/my-products', methods=['GET'])
@token_required
def get_my_products(current_user):
    """الحصول على منتجات المستخدم الحالي"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        products = Product.query.filter_by(seller_id=current_user.id).order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'products': [product.to_dict() for product in products.items],
            'total': products.total,
            'pages': products.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error fetching products: {str(e)}'}), 500



@product_bp.route('/products/stats', methods=['GET'])
@token_required
def get_marketplace_stats(current_user):
    """جلب إحصائيات السوق"""
    try:
        from datetime import datetime, timedelta
        
        # إجمالي المنتجات النشطة في السوق
        total_products = Product.query.filter_by(is_active=True).count()
        
        # منتجات المستخدم الحالي
        my_products = Product.query.filter_by(
            seller_id=current_user.id,
            is_active=True
        ).count()
        
        # المنتجات الجديدة (آخر 7 أيام)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_products = Product.query.filter(
            Product.created_at >= week_ago,
            Product.is_active == True
        ).count()
        
        stats = {
            'totalProducts': total_products,
            'myProducts': my_products,
            'recentProducts': recent_products
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب الإحصائيات: {str(e)}'}), 500

