from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.user import User
from src.extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        print("=== REGISTER ENDPOINT CALLED ===")
        
        # التحقق من وجود البيانات
        if not request.is_json:
            print("ERROR: Request is not JSON")
            return jsonify({'error': 'يجب أن تكون البيانات بصيغة JSON'}), 400
        
        data = request.get_json()
        print(f"Received data: {data}")  # Debug print
        print(f"Data type: {type(data)}")
        
        # التحقق من البيانات المطلوبة
        if not data:
            print("ERROR: No data received")
            return jsonify({'error': 'لم يتم استلام أي بيانات'}), 400
            
        required_fields = ['username', 'email', 'password']
        missing_fields = []
        
        for field in required_fields:
            if not data.get(field):
                missing_fields.append(field)
                print(f"ERROR: Missing field: {field}")
        
        if missing_fields:
            return jsonify({'error': f'الحقول التالية مطلوبة: {", ".join(missing_fields)}'}), 400
        
        username = data.get('username').strip()
        email = data.get('email').strip()
        password = data.get('password')
        phone = data.get('phone', '').strip()
        
        print(f"Processed data - Username: {username}, Email: {email}, Phone: {phone}")
        
        # التحقق من صحة البيانات
        if len(username) < 3:
            print("ERROR: Username too short")
            return jsonify({'error': 'اسم المستخدم يجب أن يكون 3 أحرف على الأقل'}), 400
            
        if len(password) < 6:
            print("ERROR: Password too short")
            return jsonify({'error': 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'}), 400
        
        if '@' not in email:
            print("ERROR: Invalid email format")
            return jsonify({'error': 'صيغة البريد الإلكتروني غير صحيحة'}), 400
        
        print("=== CHECKING EXISTING USERS ===")
        
        # التحقق من وجود المستخدم
        try:
            existing_user = User.query.filter_by(username=username).first()
            print(f"Existing user check result: {existing_user}")
            if existing_user:
                print(f"ERROR: Username {username} already exists")
                return jsonify({'error': 'اسم المستخدم موجود بالفعل'}), 400
            
            existing_email = User.query.filter_by(email=email).first()
            print(f"Existing email check result: {existing_email}")
            if existing_email:
                print(f"ERROR: Email {email} already exists")
                return jsonify({'error': 'البريد الإلكتروني موجود بالفعل'}), 400
                
        except Exception as query_error:
            print(f"ERROR in database query: {str(query_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'خطأ في الاستعلام عن قاعدة البيانات'}), 500
        
        print("=== CREATING NEW USER ===")
        
        # إنشاء مستخدم جديد
        try:
            hashed_password = generate_password_hash(password)
            print(f"Password hashed successfully")
            
            new_user = User(
                username=username,
                email=email,
                password=hashed_password,
                phone=phone
            )
            print(f"User object created: {new_user}")
            
            print(f"Adding user to database session...")
            db.session.add(new_user)
            
            print(f"Committing to database...")
            db.session.commit()
            
            print(f"User created successfully with ID: {new_user.id}")
            
            # إنشاء رمز الوصول
            access_token = new_user.generate_token()
            print(f"Access token created successfully")
            
            response_data = {
                'message': 'تم إنشاء الحساب بنجاح',
                'token': access_token,
                'user': {
                    'id': new_user.id,
                    'username': new_user.username,
                    'email': new_user.email,
                    'phone': new_user.phone
                }
            }
            
            print(f"Returning success response: {response_data}")
            return jsonify(response_data), 201
            
        except Exception as create_error:
            print(f"ERROR in user creation: {str(create_error)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return jsonify({'error': f'خطأ في إنشاء المستخدم: {str(create_error)}'}), 500
        
    except Exception as e:
        print(f"GENERAL ERROR in register: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({'error': f'حدث خطأ عام في الخادم: {str(e)}'}), 500

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
        access_token = user.generate_token()
        
        return jsonify({
            'message': 'تم تسجيل الدخول بنجاح',
            'token': access_token,
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
def get_profile():
    try:
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'صيغة الرمز المميز غير صحيحة'}), 401
        
        if not token:
            return jsonify({'error': 'الرمز المميز مفقود'}), 401
        
        payload = User.verify_token(token)
        if payload is None:
            return jsonify({'error': 'الرمز المميز غير صحيح أو منتهي الصلاحية'}), 401
        
        user = User.query.get(payload['user_id'])
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

