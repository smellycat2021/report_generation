from flask import Flask, request, jsonify, send_from_directory, render_template
# Import database components
from database import db, Report, ProductMapping, BrandMapping, KnownProductName, init_db
from data_processor import process_manufacturer_data
from report_generator import generate_summary_report
from werkzeug.utils import secure_filename
import os
import uuid
import json
from config import UPLOAD_FOLDER, REPORT_FOLDER, ALLOWED_EXTENSIONS
# Import other modules
# from database import db
# from report_generator import generate_summary_report

app = Flask(__name__, static_folder='client')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Or use a separate config file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = False # CRITICAL for security
app.config['ENV'] = 'production'

init_db(app) # Initialize database tables

# Ensure upload and report folders exist (important for deployment)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- This is the critical part ---
@app.route('/')
def index():
    # Flask looks in the /templates folder for index.html
    return render_template('index.html')

@app.route('/products')
def products_manager_page():
    # Serve the products manager landing page
    return render_template('products-manager.html')

@app.route('/products/mappings')
def product_mappings_page():
    # Serve the product mappings management page
    return render_template('product-mappings.html')

@app.route('/products/brands')
def brand_mappings_page():
    # Serve the brand mappings management page
    return render_template('brand-mappings.html')

@app.route('/products/known-names')
def known_names_page():
    # Serve the known product names management page
    return render_template('known-names.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """
    Handles multiple file uploads from manufacturers.
    """
    if 'files[]' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    uploaded_files = request.files.getlist('files[]')
    
    # List to store the paths of saved files
    file_paths = []
    
    for file in uploaded_files:
        if file and allowed_file(file.filename):
            # Secure the filename to prevent path traversal attacks
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            file_paths.append(file_path)
        
    # Trigger the processing job asynchronously for a real application
    # For a simple skeleton, we can call the processing function directly:
    # report_id = generate_summary_report(file_paths, request.form.get('date_range'))
    
    return jsonify({
        "message": f"Successfully uploaded {len(file_paths)} files.", 
        "file_paths": file_paths
    }), 202 # 202 Accepted, as processing may take time

@app.route('/api/report/generate', methods=['POST'])
def generate_report_endpoint():
    """
    Triggers the data processing and report generation.
    Takes parameters (e.g., date range, filter) from the request body.
    """
    data = request.get_json()
    uploaded_file_paths = data.get('file_paths', [])
    report_params = data.get('params', {})
    
    # 1. Generate a unique ID for the report
    report_id = str(uuid.uuid4())[:8].upper()

    # 2. Log the report entry in the database (Status: PENDING)
    new_report = Report(
        id=report_id,
        status='PENDING',
        parameters=json.dumps(report_params),
        source_files=json.dumps(uploaded_file_paths)
    )

    try:
        db.session.add(new_report)
        db.session.commit()
        
        # 3. Process Data and Generate Report
        
        # --- Start Data Processing ---
        summary_data = process_manufacturer_data(uploaded_file_paths, {}) # Pass actual config
        
        # This function returns the physical filename (e.g., 'BOARD-S-1234.xlsx')
        report_filename = generate_summary_report(summary_data, report_params) 
        
        # --- Update Database (Status: COMPLETE) ---
        new_report.status = 'COMPLETE'
        new_report.filename = report_filename
        db.session.commit()
        
        download_url = f"/api/report/download/{report_id}"
        
        return jsonify({
            "report_id": report_id,
            "status": "Processing complete (download available)",
            "download_url": download_url,
            "message": "Report generated successfully."
        }), 201

    except Exception as e:
        # 4. Handle Errors: Update status to ERROR if anything goes wrong
        db.session.rollback()
        new_report.status = 'ERROR'
        # Log the error message (optional, but good practice)
        new_report.filename = f"ERROR: {str(e)[:200]}" 
        db.session.commit()
    
        return jsonify({
            "report_id": report_id,
            "status": "ERROR",
            "message": f"Report generation failed. Error: {e}"
        }), 500


@app.route('/api/report/download/<report_id>', methods=['GET'])
def download_report(report_id):
    """
    Allows the user to download the final generated report.
    """
    # 1. Look up the report in the database
    report = Report.query.filter_by(id=report_id).first()

    if not report or report.status != 'COMPLETE':
        return jsonify({"error": "Report not found or not yet complete."}), 404

    # 2. Use the recorded filename to serve the file
    filename = report.filename

    return send_from_directory(REPORT_FOLDER, filename, as_attachment=True)

# ===== Product Mapping API Endpoints =====

@app.route('/api/product-mappings', methods=['GET'])
def get_product_mappings():
    """
    Get all product mappings with optional search/filter.
    Query params:
    - search: Search by product name
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50)
    """
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = ProductMapping.query

    if search:
        query = query.filter(ProductMapping.product_name.contains(search))

    query = query.order_by(ProductMapping.product_name)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200

@app.route('/api/product-mappings/<int:mapping_id>', methods=['GET'])
def get_product_mapping(mapping_id):
    """
    Get a specific product mapping by ID.
    """
    mapping = ProductMapping.query.get(mapping_id)

    if not mapping:
        return jsonify({"error": "Product mapping not found"}), 404

    return jsonify(mapping.to_dict()), 200

@app.route('/api/product-mappings', methods=['POST'])
def create_product_mapping():
    """
    Create a new product mapping.
    Request body: {"product_name": "...", "box_weight": 12.5, "box_size": "41*36*25"}
    """
    data = request.get_json()

    if not data or 'product_name' not in data:
        return jsonify({"error": "product_name is required"}), 400

    product_name = data['product_name'].strip()

    # Check if product already exists
    existing = ProductMapping.query.filter_by(product_name=product_name).first()
    if existing:
        return jsonify({"error": "Product mapping already exists"}), 409

    try:
        box_weight = float(data.get('box_weight')) if data.get('box_weight') else None
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid box_weight format"}), 400

    box_size = data.get('box_size', '').strip() if data.get('box_size') else None

    new_mapping = ProductMapping(
        product_name=product_name,
        box_weight=box_weight,
        box_size=box_size
    )

    try:
        db.session.add(new_mapping)
        db.session.commit()
        return jsonify(new_mapping.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create product mapping: {str(e)}"}), 500

@app.route('/api/product-mappings/<int:mapping_id>', methods=['PUT'])
def update_product_mapping(mapping_id):
    """
    Update an existing product mapping.
    Request body: {"product_name": "...", "box_weight": 12.5, "box_size": "41*36*25"}
    """
    mapping = ProductMapping.query.get(mapping_id)

    if not mapping:
        return jsonify({"error": "Product mapping not found"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update product name if provided
    if 'product_name' in data:
        new_name = data['product_name'].strip()
        # Check if new name conflicts with another product
        if new_name != mapping.product_name:
            existing = ProductMapping.query.filter_by(product_name=new_name).first()
            if existing:
                return jsonify({"error": "Product name already exists"}), 409
            mapping.product_name = new_name

    # Update box weight if provided
    if 'box_weight' in data:
        try:
            mapping.box_weight = float(data['box_weight']) if data['box_weight'] else None
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid box_weight format"}), 400

    # Update box size if provided
    if 'box_size' in data:
        mapping.box_size = data['box_size'].strip() if data['box_size'] else None

    try:
        db.session.commit()
        return jsonify(mapping.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update product mapping: {str(e)}"}), 500

@app.route('/api/product-mappings/<int:mapping_id>', methods=['DELETE'])
def delete_product_mapping(mapping_id):
    """
    Delete a product mapping.
    """
    mapping = ProductMapping.query.get(mapping_id)

    if not mapping:
        return jsonify({"error": "Product mapping not found"}), 404

    try:
        db.session.delete(mapping)
        db.session.commit()
        return jsonify({"message": "Product mapping deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete product mapping: {str(e)}"}), 500

# ===== Brand Mapping API Endpoints =====

@app.route('/api/brand-mappings', methods=['GET'])
def get_brand_mappings():
    """
    Get all brand mappings with optional search/filter.
    Query params:
    - search: Search by brand name or reference name
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50)
    """
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = BrandMapping.query

    if search:
        query = query.filter(
            db.or_(
                BrandMapping.brand_name.contains(search),
                BrandMapping.reference_name.contains(search)
            )
        )

    query = query.order_by(BrandMapping.brand_name)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200

@app.route('/api/brand-mappings/<int:mapping_id>', methods=['GET'])
def get_brand_mapping(mapping_id):
    """
    Get a specific brand mapping by ID.
    """
    mapping = BrandMapping.query.get(mapping_id)

    if not mapping:
        return jsonify({"error": "Brand mapping not found"}), 404

    return jsonify(mapping.to_dict()), 200

@app.route('/api/brand-mappings', methods=['POST'])
def create_brand_mapping():
    """
    Create a new brand mapping.
    Request body: {"brand_name": "...", "reference_name": "..."}
    """
    data = request.get_json()

    if not data or 'brand_name' not in data or 'reference_name' not in data:
        return jsonify({"error": "brand_name and reference_name are required"}), 400

    brand_name = data['brand_name'].strip()
    reference_name = data['reference_name'].strip()

    # Check if brand already exists
    existing = BrandMapping.query.filter_by(brand_name=brand_name).first()
    if existing:
        return jsonify({"error": "Brand mapping already exists"}), 409

    new_mapping = BrandMapping(
        brand_name=brand_name,
        reference_name=reference_name
    )

    try:
        db.session.add(new_mapping)
        db.session.commit()
        return jsonify(new_mapping.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create brand mapping: {str(e)}"}), 500

@app.route('/api/brand-mappings/<int:mapping_id>', methods=['PUT'])
def update_brand_mapping(mapping_id):
    """
    Update an existing brand mapping.
    Request body: {"brand_name": "...", "reference_name": "..."}
    """
    mapping = BrandMapping.query.get(mapping_id)

    if not mapping:
        return jsonify({"error": "Brand mapping not found"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update brand name if provided
    if 'brand_name' in data:
        new_name = data['brand_name'].strip()
        if new_name != mapping.brand_name:
            existing = BrandMapping.query.filter_by(brand_name=new_name).first()
            if existing:
                return jsonify({"error": "Brand name already exists"}), 409
            mapping.brand_name = new_name

    # Update reference name if provided
    if 'reference_name' in data:
        mapping.reference_name = data['reference_name'].strip()

    try:
        db.session.commit()
        return jsonify(mapping.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update brand mapping: {str(e)}"}), 500

@app.route('/api/brand-mappings/<int:mapping_id>', methods=['DELETE'])
def delete_brand_mapping(mapping_id):
    """
    Delete a brand mapping.
    """
    mapping = BrandMapping.query.get(mapping_id)

    if not mapping:
        return jsonify({"error": "Brand mapping not found"}), 404

    try:
        db.session.delete(mapping)
        db.session.commit()
        return jsonify({"message": "Brand mapping deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete brand mapping: {str(e)}"}), 500

# ===== Known Product Names API Endpoints =====

@app.route('/api/known-product-names', methods=['GET'])
def get_known_product_names():
    """
    Get all known product names with optional search/filter.
    Query params:
    - search: Search by product name
    - page: Page number (default: 1)
    - per_page: Items per page (default: 100)
    """
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)

    query = KnownProductName.query

    if search:
        query = query.filter(KnownProductName.product_name.contains(search))

    query = query.order_by(KnownProductName.product_name)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200

@app.route('/api/known-product-names/<int:name_id>', methods=['GET'])
def get_known_product_name(name_id):
    """
    Get a specific known product name by ID.
    """
    name = KnownProductName.query.get(name_id)

    if not name:
        return jsonify({"error": "Known product name not found"}), 404

    return jsonify(name.to_dict()), 200

@app.route('/api/known-product-names', methods=['POST'])
def create_known_product_name():
    """
    Create a new known product name.
    Request body: {"product_name": "..."}
    """
    data = request.get_json()

    if not data or 'product_name' not in data:
        return jsonify({"error": "product_name is required"}), 400

    product_name = data['product_name'].strip()

    # Check if product name already exists
    existing = KnownProductName.query.filter_by(product_name=product_name).first()
    if existing:
        return jsonify({"error": "Product name already exists"}), 409

    new_name = KnownProductName(product_name=product_name)

    try:
        db.session.add(new_name)
        db.session.commit()
        return jsonify(new_name.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create known product name: {str(e)}"}), 500

@app.route('/api/known-product-names/<int:name_id>', methods=['PUT'])
def update_known_product_name(name_id):
    """
    Update an existing known product name.
    Request body: {"product_name": "..."}
    """
    name = KnownProductName.query.get(name_id)

    if not name:
        return jsonify({"error": "Known product name not found"}), 404

    data = request.get_json()

    if not data or 'product_name' not in data:
        return jsonify({"error": "product_name is required"}), 400

    new_product_name = data['product_name'].strip()

    if new_product_name != name.product_name:
        existing = KnownProductName.query.filter_by(product_name=new_product_name).first()
        if existing:
            return jsonify({"error": "Product name already exists"}), 409
        name.product_name = new_product_name

    try:
        db.session.commit()
        return jsonify(name.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update known product name: {str(e)}"}), 500

@app.route('/api/known-product-names/<int:name_id>', methods=['DELETE'])
def delete_known_product_name(name_id):
    """
    Delete a known product name.
    """
    name = KnownProductName.query.get(name_id)

    if not name:
        return jsonify({"error": "Known product name not found"}), 404

    try:
        db.session.delete(name)
        db.session.commit()
        return jsonify({"message": "Known product name deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete known product name: {str(e)}"}), 500