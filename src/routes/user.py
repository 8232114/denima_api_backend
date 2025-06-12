from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from src.models.user import User, Service, db
import os
import uuid
from functools import wraps

user_bp = Blueprint('user', __name__)

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
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        payload = User.verify_token(token)
        if payload is None:
            return jsonify({'message': 'Token is invalid or expired'}), 401
        
        current_user = User.query.get(payload['user_id'])
        if not current_user:
            return jsonify({'message': 'User not found'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'message': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    
    return decorated

# Authentication routes
@user_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        token = user.generate_token()
        return jsonify({
            'token': token,
            'user': user.to_dict()
        }), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

@user_bp.route('/auth/verify', methods=['POST'])
@token_required
def verify_token(current_user):
    return jsonify({
        'user': current_user.to_dict()
    }), 200

@user_bp.route('/auth/change_password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'message': 'Old password and new password are required'}), 400
    
    if not current_user.check_password(old_password):
        return jsonify({'message': 'Current password is incorrect'}), 400
    
    if len(new_password) < 6:
        return jsonify({'message': 'New password must be at least 6 characters long'}), 400
    
    current_user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200

# Services routes
@user_bp.route('/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([service.to_dict() for service in services])

@user_bp.route('/services', methods=['POST'])
@token_required
@admin_required
def create_service(current_user):
    data = request.get_json()
    
    service = Service(
        name=data.get('name'),
        description=data.get('description'),
        price=data.get('price'),
        original_price=data.get('original_price'),
        features=data.get('features', []),
        color=data.get('color', 'bg-blue-500'),
        logo_url=data.get('logo_url')
    )
    
    db.session.add(service)
    db.session.commit()
    
    return jsonify(service.to_dict()), 201

@user_bp.route('/services/<int:service_id>', methods=['PUT'])
@token_required
@admin_required
def update_service(current_user, service_id):
    service = Service.query.get_or_404(service_id)
    data = request.get_json()
    
    service.name = data.get('name', service.name)
    service.description = data.get('description', service.description)
    service.price = data.get('price', service.price)
    service.original_price = data.get('original_price', service.original_price)
    service.features = data.get('features', service.features)
    service.color = data.get('color', service.color)
    service.logo_url = data.get('logo_url', service.logo_url)
    
    db.session.commit()
    
    return jsonify(service.to_dict())

@user_bp.route('/services/<int:service_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_service(current_user, service_id):
    service = Service.query.get_or_404(service_id)
    
    # Delete associated image file if exists
    if service.logo_url:
        try:
            file_path = os.path.join(current_app.static_folder, 'uploads', os.path.basename(service.logo_url))
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
    
    db.session.delete(service)
    db.session.commit()
    
    return '', 204

# File upload route
@user_bp.route('/upload', methods=['POST'])
@token_required
@admin_required
def upload_file(current_user):
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        file_path = os.path.join(uploads_dir, unique_filename)
        file.save(file_path)
        
        # Return relative URL
        file_url = f"/uploads/{unique_filename}"
        return jsonify({'url': file_url}), 200
    
    return jsonify({'message': 'Invalid file type'}), 400

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# CORS support
@user_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@user_bp.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'API is working!'}), 200


# Static file serving route
@user_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    uploads_dir = os.path.join(current_app.static_folder, 'uploads')
    return send_from_directory(uploads_dir, filename)

