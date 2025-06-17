from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from src.models.user import db, User, Service
from src.models.offer import Offer, OfferProduct
import jwt
import os

offer_bp = Blueprint('offer', __name__)

def verify_admin_token():
    """Verify admin token and return user"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT'), algorithms=['HS256'])
        user = User.query.get(payload['user_id'])
        if user and user.is_admin:
            return user
        return None
    except jwt.InvalidTokenError:
        return None

@offer_bp.route('/offer', methods=['GET'])
@cross_origin()
def get_offer():
    """Get current offer configuration"""
    try:
        offer = Offer.query.first()
        if not offer:
            # Create default offer if none exists
            offer = Offer()
            db.session.add(offer)
            db.session.commit()
        
        # Get offer products
        offer_products = []
        for op in offer.offer_products:
            offer_products.append({
                'id': op.service.id,
                'name': op.service.name,
                'description': op.service.description,
                'price': op.service.price,
                'original_price': op.service.original_price,
                'features': op.service.features,
                'color': op.service.color,
                'logo_url': op.service.logo_url
            })
        
        return jsonify({
            'id': offer.id,
            'is_active': offer.is_active,
            'price': offer.price,
            'whatsapp_message': offer.whatsapp_message,
            'products': offer_products
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching offer: {str(e)}'}), 500

@offer_bp.route('/offer', methods=['PUT'])
@cross_origin()
def update_offer():
    """Update offer configuration (admin only)"""
    user = verify_admin_token()
    if not user:
        return jsonify({'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        offer = Offer.query.first()
        if not offer:
            offer = Offer()
            db.session.add(offer)
        
        # Update offer fields
        if 'is_active' in data:
            offer.is_active = data['is_active']
        if 'price' in data:
            offer.price = data['price']
        if 'whatsapp_message' in data:
            offer.whatsapp_message = data['whatsapp_message']
        
        # Update offer products if provided
        if 'product_ids' in data:
            # Remove existing offer products
            OfferProduct.query.filter_by(offer_id=offer.id).delete()
            
            # Add new offer products
            for service_id in data['product_ids']:
                offer_product = OfferProduct(offer_id=offer.id, service_id=service_id)
                db.session.add(offer_product)
        
        db.session.commit()
        return jsonify({'message': 'Offer updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating offer: {str(e)}'}), 500

@offer_bp.route('/offer/products/available', methods=['GET'])
@cross_origin()
def get_available_products():
    """Get all available services for offer selection"""
    user = verify_admin_token()
    if not user:
        return jsonify({'message': 'Unauthorized'}), 401
    
    try:
        services = Service.query.all()
        services_data = []
        for service in services:
            services_data.append({
                'id': service.id,
                'name': service.name,
                'description': service.description,
                'price': service.price,
                'original_price': service.original_price,
                'features': service.features,
                'color': service.color,
                'logo_url': service.logo_url
            })
        
        return jsonify(services_data), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching services: {str(e)}'}), 500

