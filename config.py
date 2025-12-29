import os

# Base directory for the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# File Storage & Management
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
REPORT_FOLDER = os.path.join(BASE_DIR, 'reports')
ALLOWED_EXTENSIONS = {'xlsx', 'xls'} # Excel formats

# Database Configuration
# Use PostgreSQL for production (Render), SQLite for local development
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')

# Fix for Render PostgreSQL URL format
# Render provides postgres:// but SQLAlchemy 1.4+ requires postgresql://
if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)