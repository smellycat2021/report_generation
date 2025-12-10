from flask import Flask, request, jsonify, send_from_directory, render_template
# Import database components
from database import db, Report, init_db
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

# --- This is the critical part ---
@app.route('/')
def index():
    # Flask looks in the /templates folder for index.html
    return render_template('index.html')

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