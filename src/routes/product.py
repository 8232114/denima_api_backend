from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from src.models.user import User, db
from src.models.product import Product, ProductImage
import os
import uuid
from functools import wraps

product_bp = Blueprint('product', __name__)

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
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# إعدادات رفع الصور
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'product_images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

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
            return jsonify({'message': 'Access denied'}), 403
        
        if 'image' not in request.files:
            return jsonify({'message': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'message': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            ensure_upload_folder()
            
            # إنشاء اسم ملف فريد
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # إنشاء سجل الصورة في قاعدة البيانات
            image_url = f'/api/static/product_images/{filename}'
            is_primary = len(product.images) == 0  # الصورة الأولى تكون أساسية
            
            product_image = ProductImage(
                product_id=product_id,
                image_url=image_url,
                is_primary=is_primary
            )
            
            db.session.add(product_image)
            db.session.commit()
            
            return jsonify({
                'message': 'Image uploaded successfully',
                'image': product_image.to_dict()
            }), 201
        
        return jsonify({'message': 'Invalid file type'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error uploading image: {str(e)}'}), 500

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

@product_bp.route('/static/product_images/<filename>')
def serve_product_image(filename):
    """تقديم صور المنتجات"""
    return send_from_directory(UPLOAD_FOLDER, filename)

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

