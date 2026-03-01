"""
Database models for DSP Eco Tracker production deployment
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """User authentication and management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('user', 'admin', name='user_roles'), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    scraped_products = db.relationship('ScrapedProduct', backref='user', lazy=True)
    reviews = db.relationship('AdminReview', backref='reviewer', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

class Product(db.Model):
    """Training dataset products (migrated from CSV)"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    material = db.Column(db.String(100))
    weight = db.Column(db.Numeric(10, 2))
    transport = db.Column(db.String(50))
    recyclability = db.Column(db.String(50))
    true_eco_score = db.Column(db.String(10))
    co2_emissions = db.Column(db.Numeric(10, 2))
    origin = db.Column(db.String(100))
    category = db.Column(db.String(100))
    search_term = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes for common queries
    __table_args__ = (
        db.Index('idx_material', 'material'),
        db.Index('idx_origin', 'origin'),
        db.Index('idx_category', 'category'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'material': self.material,
            'weight': float(self.weight) if self.weight else None,
            'transport': self.transport,
            'recyclability': self.recyclability,
            'true_eco_score': self.true_eco_score,
            'co2_emissions': float(self.co2_emissions) if self.co2_emissions else None,
            'origin': self.origin,
            'category': self.category,
            'search_term': self.search_term
        }

class ScrapedProduct(db.Model):
    """Products scraped from Amazon by users"""
    __tablename__ = 'scraped_products'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    amazon_url = db.Column(db.String(1000), nullable=False)
    asin = db.Column(db.String(20))
    title = db.Column(db.String(500))
    price = db.Column(db.Numeric(10, 2))
    weight = db.Column(db.Numeric(10, 2))
    material = db.Column(db.String(100))
    brand = db.Column(db.String(200))
    origin_country = db.Column(db.String(100))
    confidence_score = db.Column(db.Numeric(3, 2))
    scraping_status = db.Column(db.Enum('success', 'partial', 'failed', name='scraping_status'), default='success')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    emissions = db.relationship('EmissionCalculation', backref='scraped_product', lazy=True)
    reviews = db.relationship('AdminReview', backref='scraped_product', lazy=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_asin', 'asin'),
        db.Index('idx_brand', 'brand'),
        db.Index('idx_created_at', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amazon_url': self.amazon_url,
            'asin': self.asin,
            'title': self.title,
            'price': float(self.price) if self.price else None,
            'weight': float(self.weight) if self.weight else None,
            'material': self.material,
            'brand': self.brand,
            'origin_country': self.origin_country,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'scraping_status': self.scraping_status,
            'created_at': self.created_at.isoformat()
        }

class EmissionCalculation(db.Model):
    """Carbon emission calculations and ML predictions"""
    __tablename__ = 'emission_calculations'
    
    id = db.Column(db.Integer, primary_key=True)
    scraped_product_id = db.Column(db.Integer, db.ForeignKey('scraped_products.id'), nullable=False)
    user_postcode = db.Column(db.String(20))
    transport_distance = db.Column(db.Numeric(10, 2))
    transport_mode = db.Column(db.String(50))
    ml_prediction = db.Column(db.Numeric(10, 2))
    rule_based_prediction = db.Column(db.Numeric(10, 2))
    final_emission = db.Column(db.Numeric(10, 2))
    confidence_level = db.Column(db.Numeric(3, 2))
    calculation_method = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_postcode', 'user_postcode'),
        db.Index('idx_created_at', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'scraped_product_id': self.scraped_product_id,
            'user_postcode': self.user_postcode,
            'transport_distance': float(self.transport_distance) if self.transport_distance else None,
            'transport_mode': self.transport_mode,
            'ml_prediction': float(self.ml_prediction) if self.ml_prediction else None,
            'rule_based_prediction': float(self.rule_based_prediction) if self.rule_based_prediction else None,
            'final_emission': float(self.final_emission) if self.final_emission else None,
            'confidence_level': float(self.confidence_level) if self.confidence_level else None,
            'calculation_method': self.calculation_method,
            'created_at': self.created_at.isoformat()
        }

class AdminReview(db.Model):
    """Admin review queue for scraped products"""
    __tablename__ = 'admin_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    scraped_product_id = db.Column(db.Integer, db.ForeignKey('scraped_products.id'), nullable=False)
    review_status = db.Column(db.Enum('pending', 'approved', 'rejected', name='review_status'), default='pending')
    admin_notes = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'scraped_product_id': self.scraped_product_id,
            'review_status': self.review_status,
            'admin_notes': self.admin_notes,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat()
        }

# Helper functions for database operations
def create_tables(app):
    """Create all database tables"""
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully")

def get_products_by_material(material):
    """Get all products by material type"""
    return Product.query.filter_by(material=material).all()

def save_scraped_product(product_data, user_id=None):
    """Save a new scraped product to database"""
    scraped_product = ScrapedProduct(
        user_id=user_id,
        amazon_url=product_data.get('amazon_url'),
        asin=product_data.get('asin'),
        title=product_data.get('title'),
        price=product_data.get('price'),
        weight=product_data.get('weight'),
        material=product_data.get('material'),
        brand=product_data.get('brand'),
        origin_country=product_data.get('origin_country'),
        confidence_score=product_data.get('confidence_score'),
        scraping_status=product_data.get('scraping_status', 'success')
    )
    
    db.session.add(scraped_product)
    db.session.commit()
    return scraped_product

def save_emission_calculation(calculation_data):
    """Save emission calculation to database"""
    emission = EmissionCalculation(
        scraped_product_id=calculation_data.get('scraped_product_id'),
        user_postcode=calculation_data.get('user_postcode'),
        transport_distance=calculation_data.get('transport_distance'),
        transport_mode=calculation_data.get('transport_mode'),
        ml_prediction=calculation_data.get('ml_prediction'),
        rule_based_prediction=calculation_data.get('rule_based_prediction'),
        final_emission=calculation_data.get('final_emission'),
        confidence_level=calculation_data.get('confidence_level'),
        calculation_method=calculation_data.get('calculation_method')
    )
    
    db.session.add(emission)
    db.session.commit()
    return emission