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