from flask import Blueprint, request, jsonify, session
from src.models.product import db, Admin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import functools

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin authentication"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        admin = Admin.query.filter_by(username=username, is_active=True).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            
            # Update last login
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'admin': admin.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/admin/logout', methods=['POST'])
@admin_required
def admin_logout():
    """Admin logout"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/admin/profile', methods=['GET'])
@admin_required
def get_admin_profile():
    """Get current admin profile"""
    try:
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return jsonify({'success': False, 'error': 'Admin not found'}), 404
        
        return jsonify({
            'success': True,
            'admin': admin.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/admin/create', methods=['POST'])
def create_admin():
    """Create a new admin (for initial setup)"""
    try:
        data = request.get_json()
        
        # Check if any admin exists (for security)
        existing_admin_count = Admin.query.count()
        if existing_admin_count > 0:
            return jsonify({'success': False, 'error': 'Admin creation not allowed'}), 403
        
        required_fields = ['username', 'password', 'email']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Check if username or email already exists
        if Admin.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        if Admin.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        admin = Admin(
            username=data['username'],
            password_hash=generate_password_hash(data['password']),
            email=data['email']
        )
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Admin created successfully',
            'admin': admin.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/admin/dashboard/stats', methods=['GET'])
@admin_required
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        from src.models.product import Product, Order
        
        # Get statistics
        total_products = Product.query.count()
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()
        completed_orders = Order.query.filter_by(status='completed').count()
        
        # Get recent orders
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        
        # Get popular products
        popular_products = Product.query.filter_by(is_popular=True, is_active=True).limit(5).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_products': total_products,
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'completed_orders': completed_orders
            },
            'recent_orders': [order.to_dict() for order in recent_orders],
            'popular_products': [product.to_dict() for product in popular_products]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/admin/check-auth', methods=['GET'])
def check_admin_auth():
    """Check if admin is authenticated"""
    try:
        if 'admin_id' in session:
            admin = Admin.query.get(session['admin_id'])
            if admin and admin.is_active:
                return jsonify({
                    'success': True,
                    'authenticated': True,
                    'admin': admin.to_dict()
                })
        
        return jsonify({
            'success': True,
            'authenticated': False
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@admin_bp.route("/admin/products", methods=["GET"])
@admin_required
def get_all_products_admin():
    """Get all products for admin panel (including inactive ones)"""
    try:
        products = Product.query.all()
        return jsonify({
            "success": True,
            "products": [product.to_dict() for product in products]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




from src.models.user import User

@admin_bp.route("/admin/users/count", methods=["GET"])
@admin_required
def get_total_users():
    """Get total number of users"""
    try:
        total_users = User.query.count()
        return jsonify({
            "success": True,
            "total_users": total_users
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@admin_bp.route("/admin/revenue", methods=["GET"])
@admin_required
def get_total_revenue():
    """Get total revenue from completed orders"""
    try:
        from src.models.order import Order
        total_revenue = db.session.query(db.func.sum(Order.total_price)).filter_by(status='completed').scalar()
        if total_revenue is None:
            total_revenue = 0
        return jsonify({
            "success": True,
            "total_revenue": float(total_revenue)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


