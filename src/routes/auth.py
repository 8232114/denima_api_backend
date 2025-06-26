from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.user import User
from src.models.user import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug print
        
        # التحقق من البيانات المطلوبة
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'جميع الحقول مطلوبة'}), 400
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone', '')
        
        print(f"Creating user: {username}, {email}")  # Debug print
        
        # التحقق من وجود المستخدم
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'error': 'اسم المستخدم موجود بالفعل'}), 400
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({'error': 'البريد الإلكتروني موجود بالفعل'}), 400
        
        # إنشاء مستخدم جديد
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            phone=phone
        )
        
        print(f"Adding user to database...")  # Debug print
        db.session.add(new_user)
        db.session.commit()
        print(f"User created successfully with ID: {new_user.id}")  # Debug print
        
        # إنشاء رمز الوصول
        access_token = create_access_token(identity=new_user.id)
        
        return jsonify({
            'message': 'تم إنشاء الحساب بنجاح',
            'access_token': access_token,
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email,
                'phone': new_user.phone
            }
        }), 201
        
    except Exception as e:
        print(f"Error in register: {str(e)}")  # Debug print
        import traceback
        traceback.print_exc()  # Print full traceback
        db.session.rollback()
        return jsonify({'error': f'حدث خطأ في الخادم: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'اسم المستخدم وكلمة المرور مطلوبان'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # البحث عن المستخدم بالاسم أو البريد الإلكتروني
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not check_password_hash(user.password, password):
            return jsonify({'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401
        
        # إنشاء رمز الوصول
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'تم تسجيل الدخول بنجاح',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'حدث خطأ في الخادم'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'المستخدم غير موجود'}), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'حدث خطأ في الخادم'}), 500

