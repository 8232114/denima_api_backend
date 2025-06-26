from src.extensions import db

class DigitalProduct(db.Model):
    __tablename__ = 'digital_products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.String(20), nullable=False)
    original_price = db.Column(db.String(20), nullable=True)
    category = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(50), nullable=False, default='Monitor')
    features = db.Column(db.JSON, nullable=True, default=list)  # Changed to nullable=True
    rating = db.Column(db.Float, nullable=False, default=4.5)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'original_price': self.original_price,
            'category': self.category,
            'icon': self.icon,
            'features': self.features or [],  # Ensure it's always a list
            'rating': self.rating,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MenuSection(db.Model):
    __tablename__ = 'menu_sections'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    label_ar = db.Column(db.String(100), nullable=False)
    label_en = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50), nullable=False, default='Monitor')
    path = db.Column(db.String(100), nullable=True)  # For external pages
    action = db.Column(db.String(100), nullable=True)  # For scroll actions
    order_index = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'label_ar': self.label_ar,
            'label_en': self.label_en,
            'icon': self.icon,
            'path': self.path,
            'action': self.action,
            'order_index': self.order_index,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

