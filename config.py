import os

# Base directory for the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# File Storage & Management
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
REPORT_FOLDER = os.path.join(BASE_DIR, 'reports')
ALLOWED_EXTENSIONS = {'xlsx', 'xls'} # Excel formats

# Database (SQLite example)
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')