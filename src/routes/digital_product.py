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

@digital_product_bp.route("/digital-products/test", methods=["POST"])
@jwt_required()
def test_digital_product():
    """Test endpoint for debugging digital product creation"""
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
        
        # Log everything for debugging
        print(f"=== TEST ENDPOINT ===")
        print(f"Raw request data: {data}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request method: {request.method}")
        print(f"Request content type: {request.content_type}")
        
        # Return the received data for inspection
        return jsonify({
            "success": True,
            "message": "Test endpoint - data received successfully",
            "received_data": data,
            "user_id": current_user_id,
            "user_is_admin": user.is_admin if user else False
        }), 200
        
    except Exception as e:
        print(f"Error in test endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Test endpoint error: {str(e)}"
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
        
        # Log the received data for debugging
        print(f"Received data for creating product: {data}")
        
        # Validate required fields
        required_fields = ["name", "description", "price", "category"]
        missing_fields = []
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                missing_fields.append(field)
        
        if missing_fields:
            print(f"Missing required fields: {missing_fields}")
            return jsonify({
                "success": False,
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 422
        
        # Process features - ensure it's always a list
        features = data.get("features", [])
        if not isinstance(features, list):
            features = []
        features = [str(f).strip() for f in features if f and str(f).strip()]
        
        # Validate and process rating
        try:
            rating = float(data.get("rating", 4.5))
            if rating < 0 or rating > 5:
                rating = 4.5
        except (ValueError, TypeError):
            rating = 4.5

        # Create new digital product with explicit field assignment
        try:
            product = DigitalProduct()
            product.name = str(data["name"]).strip()
            product.description = str(data["description"]).strip()
            product.price = str(data["price"]).strip()
            product.original_price = str(data.get("original_price", "")).strip() if data.get("original_price") else None
            product.category = str(data["category"]).strip()
            product.icon = str(data.get("icon", "Monitor")).strip()
            product.features = features
            product.rating = rating
            product.is_active = True
            
            print(f"Creating product with features: {product.features}")
            
            db.session.add(product)
            db.session.commit()
            
            print(f"Product created successfully with ID: {product.id}")
            
            return jsonify({
                "success": True,
                "message": "Digital product created successfully",
                "product": product.to_dict()
            }), 201
            
        except Exception as db_error:
            db.session.rollback()
            print(f"Database error during product creation: {str(db_error)}")
            return jsonify({
                "success": False,
                "message": f"Database error: {str(db_error)}"
            }), 500
        
    except Exception as e:
        db.session.rollback()
        print(f"General error creating digital product: {str(e)}")
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
        
        # Log the received data for debugging
        print(f"Updating product {product_id} with data: {data}")
        
        # Validate required fields if they are provided
        required_fields = ["name", "description", "price", "category"]
        for field in required_fields:
            if field in data and not str(data[field]).strip():
                print(f"Field '{field}' is empty")
                return jsonify({
                    "success": False,
                    "message": f"Field '{field}' cannot be empty"
                }), 422
        
        try:
            # Update fields with proper validation
            if "name" in data:
                product.name = str(data["name"]).strip()
            if "description" in data:
                product.description = str(data["description"]).strip()
            if "price" in data:
                product.price = str(data["price"]).strip()
            if "original_price" in data:
                product.original_price = str(data["original_price"]).strip() if data["original_price"] else None
            if "category" in data:
                product.category = str(data["category"]).strip()
            if "icon" in data:
                product.icon = str(data["icon"]).strip()
            if "features" in data:
                # Process features - ensure it's always a list
                features = data.get("features", [])
                if not isinstance(features, list):
                    features = []
                product.features = [str(f).strip() for f in features if f and str(f).strip()]
                print(f"Updated features: {product.features}")
            if "rating" in data:
                try:
                    rating = float(data["rating"])
                    if 0 <= rating <= 5:
                        product.rating = rating
                except (ValueError, TypeError):
                    pass  # Keep existing rating if invalid
            if "is_active" in data:
                product.is_active = bool(data["is_active"])
            
            print(f"About to commit update for product {product_id}")
            db.session.commit()
            print(f"Product {product_id} updated successfully")
            
            return jsonify({
                "success": True,
                "message": "Digital product updated successfully",
                "product": product.to_dict()
            }), 200
            
        except Exception as db_error:
            db.session.rollback()
            print(f"Database error during product update: {str(db_error)}")
            return jsonify({
                "success": False,
                "message": f"Database error: {str(db_error)}"
            }), 500
        
    except Exception as e:
        db.session.rollback()
        print(f"General error updating digital product: {str(e)}")
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



