from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User
from src.models.digital_product import DigitalProduct, MenuSection

digital_product_bp = Blueprint("digital_product", __name__)

# Digital Products Routes
@digital_product_bp.route("/digital-products", methods=["GET"])
def get_digital_products():
    """Get all active digital products"""
    try:
        products = DigitalProduct.query.filter_by(is_active=True).all()
        return jsonify({
            "success": True,
            "products": [product.to_dict() for product in products]
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error fetching digital products: {str(e)}"
        }), 500

@digital_product_bp.route("/digital-products", methods=["POST"])
@jwt_required()
def create_digital_product():
    """Create a new digital product (Admin only)"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["name", "description", "price", "category", "features"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Ensure features is a list and filter out empty strings
        features = [f.strip() for f in data.get("features", []) if f.strip()]

        # Create new digital product
        product = DigitalProduct(
            name=data["name"],
            description=data["description"],
            price=data["price"],
            original_price=data.get("original_price"),
            category=data["category"],
            icon=data.get("icon", "Monitor"),
            features=features,
            rating=data.get("rating", 4.5)
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Digital product created successfully",
            "product": product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error creating digital product: {str(e)}"
        }), 500

@digital_product_bp.route("/digital-products/<int:product_id>", methods=["PUT"])
@jwt_required()
def update_digital_product(product_id):
    """Update a digital product (Admin only)"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403
        
        product = DigitalProduct.query.get(product_id)
        if not product:
            return jsonify({
                "success": False,
                "message": "Digital product not found"
            }), 404
        
        data = request.get_json()
        
        # Update fields
        if "name" in data:
            product.name = data["name"]
        if "description" in data:
            product.description = data["description"]
        if "price" in data:
            product.price = data["price"]
        if "original_price" in data:
            product.original_price = data["original_price"]
        if "category" in data:
            product.category = data["category"]
        if "icon" in data:
            product.icon = data["icon"]
        if "features" in data:
            # Ensure features is a list and filter out empty strings
            product.features = [f.strip() for f in data.get("features", []) if f.strip()]
        if "rating" in data:
            product.rating = data["rating"]
        if "is_active" in data:
            product.is_active = data["is_active"]
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Digital product updated successfully",
            "product": product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error updating digital product: {str(e)}"
        }), 500

@digital_product_bp.route("/digital-products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_digital_product(product_id):
    """Delete a digital product (Admin only)"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403
        
        product = DigitalProduct.query.get(product_id)
        if not product:
            return jsonify({
                "success": False,
                "message": "Digital product not found"
            }), 404
        
        # Soft delete by setting is_active to False
        product.is_active = False
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Digital product deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error deleting digital product: {str(e)}"
        }), 500

# Menu Sections Routes
@digital_product_bp.route("/menu-sections", methods=["GET"])
def get_menu_sections():
    """Get all active menu sections"""
    try:
        sections = MenuSection.query.filter_by(is_active=True).order_by(MenuSection.order_index).all()
        return jsonify({
            "success": True,
            "sections": [section.to_dict() for section in sections]
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error fetching menu sections: {str(e)}"
        }), 500

@digital_product_bp.route("/menu-sections", methods=["POST"])
@jwt_required()
def create_menu_section():
    """Create a new menu section (Admin only)"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["name", "label_ar", "label_en"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Create new menu section
        section = MenuSection(
            name=data["name"],
            label_ar=data["label_ar"],
            label_en=data["label_en"],
            icon=data.get("icon", "Monitor"),
            path=data.get("path"),
            action=data.get("action"),
            order_index=data.get("order_index", 0)
        )
        
        db.session.add(section)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Menu section created successfully",
            "section": section.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error creating menu section: {str(e)}"
        }), 500



