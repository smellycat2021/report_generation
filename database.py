# database.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Model for Report History
class Report(db.Model):
    __tablename__ = 'report_history'

    id = db.Column(db.String(50), primary_key=True) # e.g., REP-12345
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='PENDING') # PENDING, COMPLETE, ERROR
    filename = db.Column(db.String(255), nullable=True)

    parameters = db.Column(db.Text) # Store report parameters as JSON string
    # Stores the list of uploaded files that contributed to the report
    source_files = db.Column(db.Text)

    def __repr__(self):
        return f'<Report {self.id}>'
    
def init_db(app):
    """Initializes the database connection with the Flask app."""
    db.init_app(app)
    with app.app_context():
        # Create all tables defined in the models
        db.create_all()
    
# Model for Manufacturer Configuration Mapping
class ManufacturerMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manufacturer_name = db.Column(db.String(100), unique=True)

    # Stores JSON or text of column mapping rules
    # e.g., {'Manufacturer_SKU': 'product_sku', 'Sales_Volume': 'quantity'}
    column_map = db.Column(db.Text)

# Model for Product Weight and Size Mapping
class ProductMapping(db.Model):
    __tablename__ = 'product_mapping'

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), unique=True, nullable=False)  # 品名
    box_weight = db.Column(db.Float, nullable=True)  # 箱重量 in kg
    box_size = db.Column(db.String(100), nullable=True)  # 箱尺寸 (e.g., "41*36*25")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'product_name': self.product_name,
            'box_weight': self.box_weight,
            'box_size': self.box_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<ProductMapping {self.product_name}: {self.box_weight}kg, {self.box_size}>'

# Model for Brand Name Mapping (brand_name -> reference_name)
class BrandMapping(db.Model):
    __tablename__ = 'brand_mapping'

    id = db.Column(db.Integer, primary_key=True)
    brand_name = db.Column(db.String(100), unique=True, nullable=False)  # Original brand name
    reference_name = db.Column(db.String(100), nullable=False)  # Standardized reference name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'brand_name': self.brand_name,
            'reference_name': self.reference_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<BrandMapping {self.brand_name} → {self.reference_name}>'

# Model for Known Product Names Set
class KnownProductName(db.Model):
    __tablename__ = 'known_product_names'

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'product_name': self.product_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<KnownProductName {self.product_name}>'