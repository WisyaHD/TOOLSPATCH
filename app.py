from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import threading
from datetime import datetime
from werkzeug.utils import secure_filename
import subprocess
from config import Config
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Global variables for tracking progress
processing_status = {
    'is_processing': False,
    'progress': 0,
    'message': 'Ready',
    'output_file': None,
    'error': None
}

# Force reset status on startup
processing_status['is_processing'] = False

# Track processed files history
processed_files = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'json'

@app.route('/')
def index():
    # Get list of JSON files in current directory
    json_files = [f for f in os.listdir('.') if f.endswith('.json')]
    
    # Get current config
    config_dict = {
        'MONGODB_URI': Config.MONGODB_URI,
        'DB_MEMBER': Config.DB_MEMBER,
        'DB_JUAL': Config.DB_JUAL,
        'DB_BELI': Config.DB_BELI,
        'COLLECTION_TT_MEMBER': Config.COLLECTION_TT_MEMBER,
        'COLLECTION_TT_JUAL_DETAIL': Config.COLLECTION_TT_JUAL_DETAIL,
        'COLLECTION_TT_BELI_DETAIL': Config.COLLECTION_TT_BELI_DETAIL,
        'COLLECTION_TT_HUTANG_DETAIL': Config.COLLECTION_TT_HUTANG_DETAIL
    }
    
    return render_template('index.html', json_files=json_files, config=config_dict)

@app.route('/api/files')
def get_files():
    json_files = [f for f in os.listdir('.') if f.endswith('.json')]
    return jsonify({'files': json_files})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'success': True, 'filename': filename})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/patch', methods=['POST'])
def run_patch():
    global processing_status
    
    if processing_status['is_processing']:
        return jsonify({'error': 'Another process is running'}), 400
    
    data = request.json
    input_file = data.get('input_file')
    
    if not input_file or not os.path.exists(input_file):
        return jsonify({'error': 'Invalid input file'}), 400
    
    # Start processing in background
    def process():
        global processing_status
        processing_status['is_processing'] = True
        processing_status['progress'] = 0
        processing_status['message'] = 'Starting patch process...'
        processing_status['error'] = None
        
        try:
            # Update patch_ultra_fast.py to use the input file
            output_file = input_file.replace('.json', '_patched.json')
            
            # Run the script
            processing_status['message'] = 'Running patch script...'
            processing_status['progress'] = 10
            
            # Execute patch_ultra_fast.py with modified input
            result = subprocess.run(
                ['python3', 'patch_ultra_fast.py', input_file, output_file],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                processing_status['progress'] = 100
                processing_status['message'] = 'Patch completed successfully!'
                processing_status['output_file'] = output_file
                
                # Add to processed files history
                file_info = {
                    'filename': os.path.basename(output_file),
                    'filepath': output_file,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'patch',
                    'size': os.path.getsize(output_file) if os.path.exists(output_file) else 0
                }
                processed_files.insert(0, file_info)  # Insert at beginning for newest first
                # Keep only last 20 files
                if len(processed_files) > 20:
                    processed_files.pop()
            else:
                processing_status['error'] = result.stderr
                processing_status['message'] = 'Patch failed'
        
        except Exception as e:
            processing_status['error'] = str(e)
            processing_status['message'] = f'Error: {str(e)}'
        
        finally:
            processing_status['is_processing'] = False
    
    thread = threading.Thread(target=process)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Processing started'})

@app.route('/api/transform', methods=['POST'])
def run_transform():
    global processing_status
    
    if processing_status['is_processing']:
        return jsonify({'error': 'Another process is running'}), 400
    
    data = request.json
    input_file = data.get('input_file')
    
    # Default to FINAL_COMPLETE if not specified
    if not input_file:
        input_file = 'tmsambassg.tt_member_FINAL_COMPLETE.json'
    
    if not os.path.exists(input_file):
        return jsonify({'error': 'Invalid input file'}), 400
    
    # Start processing in background
    def process():
        global processing_status
        processing_status['is_processing'] = True
        processing_status['progress'] = 0
        processing_status['message'] = 'Starting transform process...'
        processing_status['error'] = None
        
        try:
            output_file = input_file.replace('.json', '_transformed.json')
            
            processing_status['message'] = 'Running transform script...'
            processing_status['progress'] = 10
            
            result = subprocess.run(
                ['python3', 'transform_arjuna_structure.py', input_file, output_file],
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode == 0:
                processing_status['progress'] = 100
                processing_status['message'] = 'Transform completed successfully!'
                processing_status['output_file'] = output_file
                
                # Add to processed files history
                file_info = {
                    'filename': os.path.basename(output_file),
                    'filepath': output_file,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'transform',
                    'size': os.path.getsize(output_file) if os.path.exists(output_file) else 0
                }
                processed_files.insert(0, file_info)  # Insert at beginning for newest first
                # Keep only last 20 files
                if len(processed_files) > 20:
                    processed_files.pop()
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                processing_status['error'] = error_msg
                processing_status['message'] = 'Transform failed'
                processing_status['error'] = result.stderr
                processing_status['message'] = 'Transform failed'
        
        except Exception as e:
            processing_status['error'] = str(e)
            processing_status['message'] = f'Error: {str(e)}'
        
        finally:
            processing_status['is_processing'] = False
    
    thread = threading.Thread(target=process)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Processing started'})

@app.route('/api/patch-upload', methods=['POST'])
def patch_upload():
    """Upload and patch a JSON file"""
    global processing_status
    
    if processing_status['is_processing']:
        return jsonify({'error': 'Another process is running'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Start processing in background
    def process():
        global processing_status
        processing_status['is_processing'] = True
        processing_status['progress'] = 0
        processing_status['message'] = 'Starting patch process...'
        processing_status['error'] = None
        
        try:
            output_file = filepath.replace('.json', '_patched.json')
            
            processing_status['message'] = 'Running patch script...'
            processing_status['progress'] = 10
            
            result = subprocess.run(
                ['python3', 'patch_ultra_fast.py', filepath, output_file],
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode == 0:
                processing_status['progress'] = 100
                processing_status['message'] = 'Patch completed successfully!'
                processing_status['output_file'] = output_file
                
                file_info = {
                    'filename': os.path.basename(output_file),
                    'filepath': output_file,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'patch',
                    'size': os.path.getsize(output_file) if os.path.exists(output_file) else 0
                }
                processed_files.insert(0, file_info)
                if len(processed_files) > 20:
                    processed_files.pop()
            else:
                processing_status['error'] = result.stderr
                processing_status['message'] = 'Patch failed'
        
        except Exception as e:
            processing_status['error'] = str(e)
            processing_status['message'] = f'Error: {str(e)}'
        
        finally:
            processing_status['is_processing'] = False
    
    thread = threading.Thread(target=process)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Processing started'})

@app.route('/api/transform-upload', methods=['POST'])
def transform_upload():
    """Upload and transform a JSON file"""
    global processing_status
    
    if processing_status['is_processing']:
        return jsonify({'error': 'Another process is running'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Start processing in background
    def process():
        global processing_status
        processing_status['is_processing'] = True
        processing_status['progress'] = 0
        processing_status['message'] = 'Starting transform process...'
        processing_status['error'] = None
        
        try:
            output_file = filepath.replace('.json', '_transformed.json')
            
            processing_status['message'] = 'Running transform script...'
            processing_status['progress'] = 10
            
            result = subprocess.run(
                ['python3', 'transform_arjuna_structure.py', filepath, output_file],
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode == 0:
                processing_status['progress'] = 100
                processing_status['message'] = 'Transform completed successfully!'
                processing_status['output_file'] = output_file
                
                file_info = {
                    'filename': os.path.basename(output_file),
                    'filepath': output_file,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'transform',
                    'size': os.path.getsize(output_file) if os.path.exists(output_file) else 0
                }
                processed_files.insert(0, file_info)
                if len(processed_files) > 20:
                    processed_files.pop()
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                processing_status['error'] = error_msg
                processing_status['message'] = 'Transform failed'
        
        except Exception as e:
            processing_status['error'] = str(e)
            processing_status['message'] = f'Error: {str(e)}'
        
        finally:
            processing_status['is_processing'] = False
    
    thread = threading.Thread(target=process)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Processing started'})

@app.route('/api/get-config')
def get_config():
    """Get current configuration"""
    # Load database jual branches from .env
    db_jual_branches = {}
    for key, value in os.environ.items():
        if key.startswith('DB_JUAL_') and key != 'DB_JUAL':
            # Extract branch code (e.g., DB_JUAL_AN1 -> AN1)
            branch_code = key.replace('DB_JUAL_', '')
            db_jual_branches[branch_code] = value
    
    config_dict = {
        'MONGODB_URI': Config.MONGODB_URI,
        'DB_MEMBER': Config.DB_MEMBER,
        'DB_JUAL': Config.DB_JUAL,
        'DB_BELI': Config.DB_BELI,
        'COLLECTION_TT_MEMBER': Config.COLLECTION_TT_MEMBER,
        'COLLECTION_TT_JUAL_DETAIL': Config.COLLECTION_TT_JUAL_DETAIL,
        'COLLECTION_TT_BELI_DETAIL': Config.COLLECTION_TT_BELI_DETAIL,
        'COLLECTION_TT_HUTANG_DETAIL': Config.COLLECTION_TT_HUTANG_DETAIL,
        'DB_JUAL_BRANCHES': db_jual_branches
    }
    return jsonify({'success': True, 'config': config_dict})

@app.route('/api/save-config', methods=['POST'])
def save_config():
    """Save configuration to .env file"""
    try:
        data = request.json
        
        # Get or create .env file path
        env_path = os.path.join(os.getcwd(), '.env')
        
        # Create .env if it doesn't exist
        if not os.path.exists(env_path):
            with open(env_path, 'w') as f:
                f.write('# MongoDB Configuration\n')
        
        # Update basic config
        set_key(env_path, 'MONGODB_URI', data.get('mongodb_uri', ''))
        set_key(env_path, 'DB_MEMBER', data.get('db_member', ''))
        set_key(env_path, 'DB_JUAL', data.get('db_jual', ''))
        set_key(env_path, 'DB_BELI', data.get('db_beli', ''))
        set_key(env_path, 'COLLECTION_TT_MEMBER', data.get('collection_member', ''))
        set_key(env_path, 'COLLECTION_TT_JUAL_DETAIL', data.get('collection_jual', ''))
        set_key(env_path, 'COLLECTION_TT_BELI_DETAIL', data.get('collection_beli', ''))
        set_key(env_path, 'COLLECTION_TT_HUTANG_DETAIL', data.get('collection_hutang', ''))
        
        # Handle multiple database jual branches
        db_jual_branches = data.get('db_jual_branches', {})
        
        # First, remove all existing DB_JUAL_* entries (except DB_JUAL)
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            with open(env_path, 'w') as f:
                for line in lines:
                    # Keep line if it's not DB_JUAL_* or if it's just DB_JUAL
                    if not line.startswith('DB_JUAL_') or line.startswith('DB_JUAL='):
                        f.write(line)
        
        # Add new branch databases
        if db_jual_branches:
            # Add a comment section for branch databases
            with open(env_path, 'a') as f:
                f.write('\n# Database Jual per Cabang/Toko\n')
                for branch_code, db_name in db_jual_branches.items():
                    f.write(f'DB_JUAL_{branch_code}={db_name}\n')
        
        # Reload config
        load_dotenv(override=True)
        
        # Update Config class attributes
        Config.MONGODB_URI = data.get('mongodb_uri', Config.MONGODB_URI)
        Config.DB_MEMBER = data.get('db_member', Config.DB_MEMBER)
        Config.DB_JUAL = data.get('db_jual', Config.DB_JUAL)
        Config.DB_BELI = data.get('db_beli', Config.DB_BELI)
        Config.COLLECTION_TT_MEMBER = data.get('collection_member', Config.COLLECTION_TT_MEMBER)
        Config.COLLECTION_TT_JUAL_DETAIL = data.get('collection_jual', Config.COLLECTION_TT_JUAL_DETAIL)
        Config.COLLECTION_TT_BELI_DETAIL = data.get('collection_beli', Config.COLLECTION_TT_BELI_DETAIL)
        Config.COLLECTION_TT_HUTANG_DETAIL = data.get('collection_hutang', Config.COLLECTION_TT_HUTANG_DETAIL)
        
        return jsonify({
            'success': True, 
            'message': f'Configuration saved successfully with {len(db_jual_branches)} branch databases'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """Test MongoDB connection"""
    try:
        data = request.json
        mongodb_uri = data.get('mongodb_uri', '')
        
        if not mongodb_uri:
            return jsonify({'success': False, 'error': 'MongoDB URI is required'}), 400
        
        # Import pymongo here to avoid import errors if not installed
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
        
        # Test connection with longer timeout for replica sets
        # Use 30 seconds timeout to allow proper primary selection
        client = MongoClient(
            mongodb_uri, 
            serverSelectionTimeoutMS=30000,  # 30 seconds - enough for replica set
            connectTimeoutMS=20000,          # 20 seconds connection timeout
            socketTimeoutMS=120000           # 2 minutes socket timeout
        )
        
        # Force connection
        client.admin.command('ping')
        
        # Get list of databases
        databases = client.list_database_names()
        
        client.close()
        
        return jsonify({
            'success': True, 
            'message': 'Connection successful',
            'databases': databases
        })
    
    except ConnectionFailure as e:
        return jsonify({'success': False, 'error': f'Connection failed: {str(e)}'}), 500
    except ServerSelectionTimeoutError as e:
        return jsonify({'success': False, 'error': 'Connection timeout. Please check your MongoDB URI and ensure MongoDB is running.'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/list-collections', methods=['POST'])
def list_collections():
    """List collections for a given database"""
    try:
        data = request.json
        mongodb_uri = data.get('mongodb_uri', '')
        db_name = data.get('db_name', '')

        if not mongodb_uri or not db_name:
            return jsonify({'success': False, 'error': 'MongoDB URI and database name are required'}), 400

        from pymongo import MongoClient

        client = MongoClient(
            mongodb_uri,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=20000,
            socketTimeoutMS=120000
        )

        collections = client[db_name].list_collection_names()
        client.close()

        return jsonify({
            'success': True,
            'collections': collections
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/patch-no-faktur', methods=['POST'])
def patch_no_faktur():
    """Patch no_faktur dengan lookup kode_barcode ke tt_jual_detail"""
    global processing_status
    
    if processing_status['is_processing']:
        return jsonify({'error': 'Another process is running'}), 400
    
    # Get input file from request
    data = request.json
    input_file = data.get('input_file') if data else None
    
    if not input_file or not os.path.exists(input_file):
        return jsonify({'error': f'Input file {input_file or "not specified"} not found. Please run Transform first.'}), 400
    
    # Start processing in background
    def process():
        global processing_status
        processing_status['is_processing'] = True
        processing_status['progress'] = 0
        processing_status['message'] = 'Starting patch no_faktur process...'
        processing_status['error'] = None
        
        try:
            # Generate output filename from input filename
            output_file = input_file.replace('_transformed.json', '_no_faktur_COMPLETE.json')
            if output_file == input_file:
                # If pattern doesn't match, use default suffix
                output_file = input_file.replace('.json', '_no_faktur_COMPLETE.json')
            
            processing_status['message'] = 'Running patch no_faktur script...'
            processing_status['progress'] = 10
            
            result = subprocess.run(
                ['python3', 'patch_no_faktur_FINAL.py', input_file, output_file],
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode == 0:
                # Verify output file exists and has content
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    processing_status['progress'] = 100
                    processing_status['message'] = 'Patch no_faktur completed successfully!'
                    processing_status['output_file'] = output_file
                    
                    # Add to processed files history
                    file_info = {
                        'filename': os.path.basename(output_file),
                        'filepath': output_file,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'patch_no_faktur',
                        'size': os.path.getsize(output_file)
                    }
                    processed_files.insert(0, file_info)
                    if len(processed_files) > 20:
                        processed_files.pop()
                else:
                    processing_status['error'] = 'Output file is empty or not created'
                    processing_status['message'] = 'Patch no_faktur failed: No output generated'
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                processing_status['error'] = error_msg
                processing_status['message'] = 'Patch no_faktur failed'
        
        except Exception as e:
            processing_status['error'] = str(e)
            processing_status['message'] = f'Error: {str(e)}'
        
        finally:
            processing_status['is_processing'] = False
    
    thread = threading.Thread(target=process)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Processing started'})

@app.route('/api/patch-no-faktur-upload', methods=['POST'])
def patch_no_faktur_upload():
    """Upload and patch no_faktur dari JSON file"""
    global processing_status
    
    if processing_status['is_processing']:
        return jsonify({'error': 'Another process is running'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Start processing in background
    def process():
        global processing_status
        processing_status['is_processing'] = True
        processing_status['progress'] = 0
        processing_status['message'] = 'Starting patch no_faktur process...'
        processing_status['error'] = None
        
        try:
            # Generate output filename from input filename
            output_file = filepath.replace('_transformed.json', '_no_faktur_COMPLETE.json')
            if output_file == filepath:
                # If pattern doesn't match, use default suffix
                output_file = filepath.replace('.json', '_no_faktur_COMPLETE.json')
            
            processing_status['message'] = 'Running patch no_faktur script...'
            processing_status['progress'] = 10
            
            result = subprocess.run(
                ['python3', 'patch_no_faktur_FINAL.py', filepath, output_file],
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode == 0:
                # Verify output file exists and has content
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    processing_status['progress'] = 100
                    processing_status['message'] = 'Patch no_faktur completed successfully!'
                    processing_status['output_file'] = output_file
                    
                    # Add to processed files history
                    file_info = {
                        'filename': os.path.basename(output_file),
                        'filepath': output_file,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'patch_no_faktur',
                        'size': os.path.getsize(output_file)
                    }
                    processed_files.insert(0, file_info)
                    if len(processed_files) > 20:
                        processed_files.pop()
                else:
                    processing_status['error'] = f'Output file not created or empty: {output_file}'
                    processing_status['message'] = 'Patch no_faktur failed - no output'
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                processing_status['error'] = error_msg
                processing_status['message'] = 'Patch no_faktur failed'
        
        except Exception as e:
            processing_status['error'] = str(e)
            processing_status['message'] = f'Error: {str(e)}'
        
        finally:
            processing_status['is_processing'] = False
    
    thread = threading.Thread(target=process)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Processing started', 'filename': filepath})

@app.route('/api/patch-no-faktur-optimized', methods=['POST'])
def patch_no_faktur_optimized():
    """Patch no_faktur with OPTIMIZED script (for large files 400MB+)"""
    global processing_status
    
    if processing_status['is_processing']:
        # Auto-reset if stuck
        processing_status['is_processing'] = False
        processing_status['message'] = 'Auto-reset stuck process'
    
    data = request.json
    input_file = data.get('input_file')
    batch_size = data.get('batch_size', 2000)
    
    # Check if file exists (support both absolute and relative paths)
    if not input_file:
        return jsonify({'error': 'No input file provided'}), 400
    
    # Handle both absolute paths and filenames
    if not os.path.isabs(input_file):
        # Try uploads folder first
        test_path = os.path.join('uploads', input_file)
        if os.path.exists(test_path):
            input_file = test_path
    
    if not os.path.exists(input_file):
        return jsonify({'error': f'File not found: {input_file}'}), 400
    
    # Start processing in background
    def process():
        global processing_status
        processing_status['is_processing'] = True
        processing_status['progress'] = 0
        processing_status['message'] = 'Starting optimized patch process...'
        processing_status['error'] = None
        
        try:
            # Generate output filename
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}_no_faktur_OPTIMIZED.json"
            
            processing_status['message'] = 'Running optimized patch script...'
            processing_status['progress'] = 10
            
            # Execute patch_no_faktur_FINAL.py (auto-reads DB mapping from .env)
            result = subprocess.run(
                ['python3', 'patch_no_faktur_FINAL.py', input_file, output_file],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    processing_status['progress'] = 100
                    processing_status['message'] = 'Optimized patch completed successfully!'
                    processing_status['output_file'] = output_file
                    
                    # Add to processed files history
                    file_info = {
                        'filename': os.path.basename(output_file),
                        'filepath': output_file,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'patch_no_faktur_optimized',
                        'size': os.path.getsize(output_file),
                        'stdout': result.stdout[-500:] if result.stdout else ''  # Last 500 chars
                    }
                    processed_files.insert(0, file_info)
                    if len(processed_files) > 20:
                        processed_files.pop()
                else:
                    processing_status['error'] = f'Output file not created or empty'
                    processing_status['message'] = 'Patch failed - no output'
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                processing_status['error'] = error_msg
                processing_status['message'] = 'Optimized patch failed'
        
        except subprocess.TimeoutExpired:
            processing_status['error'] = 'Process timeout (1 hour exceeded)'
            processing_status['message'] = 'Process timeout'
        except Exception as e:
            processing_status['error'] = str(e)
            processing_status['message'] = f'Error: {str(e)}'
        
        finally:
            processing_status['is_processing'] = False
    
    thread = threading.Thread(target=process)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Optimized patch processing started'})

@app.route('/api/reset-status', methods=['POST'])
def reset_status():
    """Reset processing status when stuck"""
    global processing_status
    processing_status = {
        'is_processing': False,
        'progress': 0,
        'message': 'Status reset by user',
        'output_file': None,
        'error': None
    }
    return jsonify({'success': True, 'message': 'Status reset'})

@app.route('/api/status')
def get_status():
    return jsonify(processing_status)

@app.route('/api/processed-files')
def get_processed_files():
    """Get list of processed files"""
    return jsonify({'success': True, 'files': processed_files})

@app.route('/api/download/<path:filename>')
def download_file(filename):
    try:
        # Decode the filepath
        filepath = filename
        
        # Check if file exists
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Check if file is empty
        if os.path.getsize(filepath) == 0:
            return jsonify({'error': 'File is empty'}), 400
        
        # Get the original filename for download
        original_filename = os.path.basename(filepath)
        
        return send_file(filepath, as_attachment=True, download_name=original_filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 TT Member Processing Tool")
    print("=" * 80)
    print("Server running at: http://localhost:5002")
    print("Press Ctrl+C to stop")
    print("=" * 80)
    app.run(host='0.0.0.0', port=5002, debug=True)
