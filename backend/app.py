from flask import Flask, request, jsonify, session, g, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import mimetypes
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import threading
import json
import re
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from openai import OpenAI
import pypdf

# Load environment variables from .env
load_dotenv()

try:
    import magic  # type: ignore[import-not-found]
except ImportError:
    magic = None

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXT = {'.png', '.jpg', '.jpeg', '.pdf', '.doc', '.docx', '.txt'}

ALLOWED_MIME_BY_EXT = {
    '.png': {'image/png'},
    '.jpg': {'image/jpeg'},
    '.jpeg': {'image/jpeg'},
    '.pdf': {'application/pdf'},
    '.doc': {'application/msword', 'application/octet-stream'},
    '.docx': {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/zip',
    },
    '.txt': {'text/plain'},
}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# secret key for sessions (change for production)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Allow requests from frontend dev server.
CORS(app, supports_credentials=True)

# Configure Groq client (using openai SDK wrapper)
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
if GROQ_API_KEY:
    groq_client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
else:
    groq_client = None

# PostgreSQL DB setup
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'file_management')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'root')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
    return db


def init_db():
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS files (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            original_name TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            summary TEXT,
            category VARCHAR(50),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        '''
    )
    # Safely alter existing database tables if they already exist
    try:
        cur.execute("ALTER TABLE files ADD COLUMN IF NOT EXISTS summary TEXT")
        cur.execute("ALTER TABLE files ADD COLUMN IF NOT EXISTS category VARCHAR(50)")
    except Exception as e:
        print(f"[Schema Update Info] Columns might already exist or error: {e}")
        
    db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


with app.app_context():
    init_db()


def allowed_extension(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXT


def detect_mime(file_obj, filename):
    # Read a small chunk and reset cursor so save() still works.
    chunk = file_obj.stream.read(2048)
    file_obj.stream.seek(0)

    if magic is not None:
        try:
            return magic.from_buffer(chunk, mime=True)
        except Exception:
            pass

    guessed = mimetypes.guess_type(filename)[0]
    return guessed or 'application/octet-stream'


def allowed_mime(filename, mime_value):
    ext = os.path.splitext(filename)[1].lower()
    # strip parameters like charset from mime (e.g. 'text/plain; charset=utf-8')
    mime_main = mime_value.split(';', 1)[0].strip().lower() if mime_value else ''
    expected = ALLOWED_MIME_BY_EXT.get(ext, set())
    if not expected:
        return False
    return mime_main in {m.lower() for m in expected}


def get_user_by_email(email):
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM users WHERE email = %s', (email,))
    return cur.fetchone()


def get_user_by_id(uid):
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT id, email, name, created_at FROM users WHERE id = %s', (uid,))
    return cur.fetchone()


@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    name = data.get('name') or ''

    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400

    if get_user_by_email(email):
        return jsonify({'error': 'email already registered'}), 400

    pw_hash = generate_password_hash(password)
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s) RETURNING id', (email, name, pw_hash))
    db.commit()
    user_id = cur.fetchone()['id']
    # session['user_id'] = user_id  # Ab direct login nahi karwana
    user = get_user_by_id(user_id)
    return jsonify({'id': user['id'], 'email': user['email'], 'name': user['name'], 'message': 'Account created successfully'}), 201 # data ko JSON me banata hai.


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400

    row = get_user_by_email(email)
    if not row:
        return jsonify({'error': 'invalid credentials'}), 401

    if not check_password_hash(row['password_hash'], password):
        return jsonify({'error': 'invalid credentials'}), 401

    session['user_id'] = row['id']
    user = get_user_by_id(row['id'])
    return jsonify({'id': user['id'], 'email': user['email'], 'name': user['name']}), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'ok': True})


@app.route('/api/me', methods=['GET'])
def me():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'user': None}), 200
    user = get_user_by_id(uid)
    if not user:
        return jsonify({'user': None}), 200
    return jsonify({'user': {'id': user['id'], 'email': user['email'], 'name': user['name']}}), 200



def process_file_ai(file_id, file_path, original_name, mime_type):
    # Since we are in a background thread, we must manage its own DB connection
    db = None
    try:
        db = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = db.cursor(cursor_factory=RealDictCursor)
        
        if not GROQ_API_KEY or not groq_client:
            cur.execute(
                "UPDATE files SET summary = %s WHERE id = %s",
                ("Groq API key not configured in .env", file_id)
            )
            db.commit()
            return

        summary = "No summary available"
        new_name = original_name
        
        ext = os.path.splitext(original_name)[1].lower()
        extracted_text = ""
        
        # 1. Extract text if applicable
        if ext == '.pdf':
            try:
                reader = pypdf.PdfReader(file_path)
                num_pages = min(len(reader.pages), 5)
                for i in range(num_pages):
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
            except Exception as e:
                print(f"Error reading PDF {original_name}: {e}")
        elif ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    extracted_text = f.read(10000)
            except Exception as e:
                print(f"Error reading TXT {original_name}: {e}")
                
        # 2. Call Groq API in a separate thread with a 2-second timeout
        response_text = ""
        
        prompt = f"""You are a file management assistant. Please analyze the following file and provide a concise, clear 1-2 sentence explanation summary of what is in the file.
Original Name: '{original_name}'
Mime Type: '{mime_type}'
"""
        if extracted_text.strip():
            prompt += f"\nFile content snippet:\n{extracted_text[:6000]}"
        else:
            prompt += "\nNo text content could be extracted from this file."

        def call_groq():
            nonlocal response_text
            import urllib.request
            import json
            
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            def make_request(model_name):
                data = {
                    "messages": [{"role": "user", "content": prompt}],
                    "model": model_name,
                    "temperature": 0.2,
                    "max_tokens": 150,
                    "user": "file-management-system"
                }
                req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=10) as response:
                    return json.loads(response.read().decode('utf-8'))

            try:
                result = make_request("llama-3.1-8b-instant")
                msg = result["choices"][0]["message"]
                if msg.get('refusal'):
                    print(f"API refusal: {msg['refusal']}")
                else:
                    response_text = msg.get('content', '')
            except Exception as api_err:
                print(f"Failed with llama-3.1-8b-instant: {api_err}. Trying fallback model...")
                try:
                    result = make_request("llama-3.3-70b-versatile")
                    msg = result["choices"][0]["message"]
                    if msg.get('refusal'):
                        print(f"Fallback API refusal: {msg['refusal']}")
                    else:
                        response_text = msg.get('content', '')
                except Exception as fallback_err:
                    print(f"Fallback model failed: {fallback_err}")

        # Start Groq thread
        groq_thread = threading.Thread(target=call_groq)
        groq_thread.start()
        groq_thread.join(timeout=2.0)  # Wait for maximum 2 seconds

        if groq_thread.is_alive() or not response_text:
            print("[Timeout] Groq API took longer than 2 seconds. Switching to fast local summary model...")
            # Local summaries using a high performance, very lightweight distilbart summary or rule-based fallback
            try:
                from transformers import pipeline
                # Initialize summarizer (very small and cached model)
                summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-6-6", device=-1)
                text_to_summarize = extracted_text.strip()[:1024] if extracted_text.strip() else f"Metadata check for {original_name} of type {mime_type}."
                if len(text_to_summarize) < 30:
                    text_to_summarize = text_to_summarize + " (supplementary text to reach minimum context length for model summary)"
                local_res = summarizer(text_to_summarize, max_length=50, min_length=15, do_sample=False)
                summary = local_res[0]['summary_text']
                print(f"[Local AI Processor] Generated local model summary: {summary}")
            except Exception as local_err:
                print(f"[Local Fallback Error] {local_err}. Using rule-based local extractor...")
                # High-performance rule-based semantic extractor to guarantee immediate output
                if extracted_text.strip():
                    summary = f"Local Scan: The file contains text starting with: '{extracted_text.strip()[:100]}...'"
                else:
                    summary = f"Local Scan: Metadata check for {original_name} of type {mime_type}."
        else:
            summary = response_text.strip()
                
        # 4. Save to Database
        cur.execute(
            "UPDATE files SET summary = %s WHERE id = %s",
            (summary, file_id)
        )
        db.commit()
        print(f"[AI Processor] Successfully generated summary for file ID {file_id}: {summary}")
        
    except Exception as e:
        error_msg = f"AI Error: {str(e)[:50]}"
        print(f"[AI Processor Error] {e}")
        try:
            cur.execute(
                "UPDATE files SET summary = %s WHERE id = %s",
                (error_msg, file_id)
            )
            db.commit()
        except Exception:
            pass
    finally:
        if db:
            db.close()


@app.route('/api/upload', methods=['POST'])
def upload():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Unauthorized, please login first'}), 401

    files = []
    # support both 'files' (multiple) and single 'file'
    if 'files' in request.files:
        files = request.files.getlist('files') # get() single item nikalta hai
    elif 'file' in request.files:
        files = [request.files.get('file')]   # getlist() same key ke saare items ki list deta hai.
    else:
        return jsonify({'error': 'no file provided'}), 400

    saved = []
    errors = []

    for f in files:   # f is just a file object variable 
        if not f or f.filename == '':
            errors.append('empty filename')
            continue

        filename = secure_filename(f.filename) # user ke uploaded file name ko safe banata hai. unsafe characters, spaces, aur path ko remove krta hh or normalise krta hh
        if not allowed_extension(filename):
            errors.append(f"{filename}: invalid extension")
            continue

        # detect_mime() file ka MIME type identify karta hai,
        # aur allowed_mime() verify karta hai ki wo type permitted hai ya nahi
        # Agar mismatch ho to file reject kar di jaati hai.

        detected_mime = detect_mime(f, filename)
        if not allowed_mime(filename, detected_mime):
            errors.append(f"{filename}: invalid mime ({detected_mime})")
            continue

        ext = os.path.splitext(filename)[1].lower()
        file_uuid = uuid.uuid4().hex
        save_name = f"{file_uuid}{ext}"
        dest = os.path.join(app.config['UPLOAD_FOLDER'], save_name)  # folder path aur filename ko jod kar full path banata hai.
        try:
            f.save(dest)
            f_size = os.path.getsize(dest)
            
            # Database mein file ki details save karein (with default AI status values)
            db = get_db()
            cur = db.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                'INSERT INTO files (user_id, original_name, stored_name, file_size, summary, category) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id', 
                (uid, filename, save_name, f_size, 'Processing...', 'Detecting...')
            )
            file_id = cur.fetchone()['id']
            db.commit()
            
            # Start background AI processing
            threading.Thread(
                target=process_file_ai,
                args=(file_id, dest, filename, detected_mime)
            ).start()
            
            saved.append({'original': filename, 'stored': save_name, 'size': f_size})
        except Exception as e:
            errors.append(f"{filename}: save error")

    return jsonify({'saved': saved, 'errors': errors}), (400 if errors and not saved else 200)

@app.route('/api/files', methods=['GET'])
def get_user_files():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401
    
    db = get_db() # database connection milta hai.
    cur = db.cursor(cursor_factory=RealDictCursor) # ekk cursor banaya jata hh jisse SQL query execute karne ke liye.
    cur.execute('SELECT * FROM files WHERE user_id = %s ORDER BY created_at DESC', (uid,))
    files = cur.fetchall() # 
    
    result = []
    for row in files:
        result.append({
            'id': row['id'],
            'original_name': row['original_name'],
            'file_size': row['file_size'],
            'created_at': row['created_at'].isoformat() if hasattr(row['created_at'], 'isoformat') else row['created_at'],
            'summary': row['summary'],
            'category': row['category']
        })
    return jsonify(result), 200

@app.route('/api/files/<int:file_id>/download', methods=['GET'])
def download_file(file_id):
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM files WHERE id = %s', (file_id,))
    row = cur.fetchone()
    
    if not row:
        return "File not found", 404
        
    return send_from_directory(app.config['UPLOAD_FOLDER'], row['stored_name'], as_attachment=True, download_name=row['original_name'])

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_user_file(file_id):
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401
        
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM files WHERE id = %s AND user_id = %s', (file_id, uid))
    row = cur.fetchone()
    
    if not row:
        return jsonify({'error': 'File not found or access denied'}), 404
        
    # Delete from filesystem
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], row['stored_name'])
    if os.path.exists(filepath):
        os.remove(filepath)
        
    # Delete from database
    cur.execute('DELETE FROM files WHERE id = %s', (file_id,))
    db.commit()
    
    return jsonify({'ok': True}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
