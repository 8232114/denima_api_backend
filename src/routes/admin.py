from flask import Blueprint, request, jsonify
from src.models.user import User, db
from src.models.product import Product, ProductImage
from functools import wraps
import os

admin_bp = Blueprint('admin', __name__)

# Middleware للتحقق من صلاحيات المسؤول
def admin_required(f):
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
            
        if not current_user.is_admin:
            return jsonify({'message': 'غير مسموح لك بالوصول لهذه الصفحة'}), 403
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# إدارة المستخدمين
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users(current_user):
    """جلب جميع المستخدمين للمسؤول"""
    try:
        users = User.query.all()
        users_data = []
        
        for user in users:
            user_dict = user.to_dict()
            # إضافة عدد المنتجات لكل مستخدم
            user_dict['products_count'] = Product.query.filter_by(seller_id=user.id).count()
            users_data.append(user_dict)
        
        return jsonify({
            'users': users_data,
            'total': len(users_data)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب المستخدمين: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>/ban', methods=['POST'])
@admin_required
def ban_user(current_user, user_id):
    """حظر مستخدم"""
    try:
        user = User.query.get_or_404(user_id)
        
        # منع حظر المسؤولين
        if user.is_admin:
            return jsonify({'message': 'لا يمكن حظر المسؤولين'}), 403
        
        # منع المستخدم من حظر نفسه
        if user.id == current_user.id:
            return jsonify({'message': 'لا يمكنك حظر نفسك'}), 403
        
        data = request.get_json()
        reason = data.get('reason', 'لم يتم تحديد السبب')
        
        user.ban_user(reason)
        db.session.commit()
        
        return jsonify({
            'message': f'تم حظر المستخدم {user.username} بنجاح',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في حظر المستخدم: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>/unban', methods=['POST'])
@admin_required
def unban_user(current_user, user_id):
    """إلغاء حظر مستخدم"""
    try:
        user = User.query.get_or_404(user_id)
        
        user.unban_user()
        db.session.commit()
        
        return jsonify({
            'message': f'تم إلغاء حظر المستخدم {user.username} بنجاح',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في إلغاء حظر المستخدم: {str(e)}'}), 500

# إدارة المنتجات
@admin_bp.route('/products', methods=['GET'])
@admin_required
def get_all_products_admin(current_user):
    """جلب جميع المنتجات للمسؤول"""
    try:
        products = Product.query.all()
        products_data = []
        
        for product in products:
            product_dict = product.to_dict()
            # إضافة معلومات البائع
            seller = User.query.get(product.seller_id)
            product_dict['seller'] = {
                'id': seller.id,
                'username': seller.username,
                'email': seller.email,
                'is_banned': seller.is_banned
            } if seller else None
            products_data.append(product_dict)
        
        return jsonify({
            'products': products_data,
            'total': len(products_data)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب المنتجات: {str(e)}'}), 500

@admin_bp.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product_admin(current_user, product_id):
    """حذف منتج (للمسؤول فقط)"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # حذف جميع صور المنتج من النظام
        for image in product.images:
            # حذف الملف من النظام
            if image.image_url:
                filename = image.image_url.split('/')[-1]
                file_path = os.path.join('src', 'static', 'product_images', filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass  # تجاهل أخطاء حذف الملفات
            
            # حذف سجل الصورة من قاعدة البيانات
            db.session.delete(image)
        
        # حذف المنتج
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'message': 'تم حذف المنتج بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في حذف المنتج: {str(e)}'}), 500

# إحصائيات المسؤول
@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_admin_stats(current_user):
    """جلب إحصائيات شاملة للمسؤول"""
    try:
        from datetime import datetime, timedelta
        
        # إحصائيات المستخدمين
        total_users = User.query.count()
        banned_users = User.query.filter_by(is_banned=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        
        # إحصائيات المنتجات
        total_products = Product.query.count()
        active_products = Product.query.filter_by(is_active=True).count()
        
        # المنتجات الجديدة (آخر 7 أيام)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_products = Product.query.filter(Product.created_at >= week_ago).count()
        
        # المستخدمين الجدد (آخر 7 أيام)
        recent_users = User.query.filter(User.created_at >= week_ago).count()
        
        stats = {
            'users': {
                'total': total_users,
                'banned': banned_users,
                'admins': admin_users,
                'recent': recent_users
            },
            'products': {
                'total': total_products,
                'active': active_products,
                'recent': recent_products
            }
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب الإحصائيات: {str(e)}'}), 500

