from src.extensions import db
from src.models.user import Service

class Offer(db.Model):
    __tablename__ = 'offers'
    
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    price = db.Column(db.String(10), default='200', nullable=False)
    whatsapp_message = db.Column(db.Text, default='مرحبًا 👋\nأود طلب عرض المنتجات التالية:\n\n{products}\n\nالمجموع: {price} درهم\n\nشكرًا لك 🙏', nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationship with offer products
    offer_products = db.relationship('OfferProduct', backref='offer', lazy=True, cascade='all, delete-orphan')

class OfferProduct(db.Model):
    __tablename__ = 'offer_products'
    
    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationship with service
    service = db.relationship('Service', backref='offer_products', lazy=True)

