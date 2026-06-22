from flask import Flask, request, jsonify, g, send_from_directory
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
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from google.generativeai import GenerativeModel, configure
from google.generativeai.types import HarmCategory, HarmBlockThreshold, SafetySetting
import pypdf
from supabase import create_client, Client

# Import secure configuration (all credentials from .env)
from config import Config

try:
    import magic  # type: ignore[import-not-found]
except ImportError:
    magic = None

app = Flask(__name__)

# Load configuration from secure config module
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['JWT_SECRET'] = Config.JWT_SECRET

CORS(app, supports_credentials=True, origins=[Config.FRONTEND_URL], allow_headers=['Authorization', 'Content-Type'])

# Supabase Storage setup
supabase_client: Client = None
if Config.SUPABASE_URL and Config.SUPABASE_SERVICE_KEY:
    supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

ALLOWED_EXT = Config.ALLOWED_EXTENSIONS
ALLOWED_MIME_BY_EXT = Config.ALLOWED_MIME_BY_EXT
JWT_SECRET = Config.JWT_SECRET
DATABASE_URL = Config.DATABASE_URL
GEMINI_API_KEY = Config.GEMINI_API_KEY
if GEMINI_API_KEY:
    configure(api_key=GEMINI_API_KEY)
SUPABASE_BUCKET = Config.SUPABASE_BUCKET


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # DATABASE_URL is guaranteed to exist from Config validation
        # Check if it's a Supabase connection (contains SSL requirement)
        if 'supabase' in DATABASE_URL.lower():
            db = g._database = psycopg2.connect(DATABASE_URL, sslmode='require')
        else:
            db = g._database = psycopg2.connect(DATABASE_URL)
    return db


def init_db():
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('''
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
    ''')
    try:
        cur.execute("ALTER TABLE files ADD COLUMN IF NOT EXISTS summary TEXT")
        cur.execute("ALTER TABLE files ADD COLUMN IF NOT EXISTS category VARCHAR(50)")
    except Exception as e:
        print(f"[Schema Update Info] {e}")
    db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
 
with app.app_context(): 
    init_db() 

# ─── JWT HELPERS ─────────────────────────────────────────────────────────────

def create_token(user_id):
    """Create a JWT token for the given user_id, expires in 7 days."""
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def get_current_user_id():
    """Read Bearer token from Authorization header and return user_id, or None."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ─── FILE VALIDATION ──────────────────────────────────────────────────────────

def allowed_extension(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXT


def detect_mime(file_obj, filename):
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
    mime_main = mime_value.split(';', 1)[0].strip().lower() if mime_value else ''
    expected = ALLOWED_MIME_BY_EXT.get(ext, set())
    if not expected:
        return False
    return mime_main in {m.lower() for m in expected}


# ─── USER DB HELPERS ──────────────────────────────────────────────────────────

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


# ─── AUTH ROUTES ──────────────────────────────────────────────────────────────

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
    cur.execute(
        'INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s) RETURNING id',
        (email, name, pw_hash)
    )
    db.commit()
    user_id = cur.fetchone()['id']
    user = get_user_by_id(user_id)
    return jsonify({'id': user['id'], 'email': user['email'], 'name': user['name'], 'message': 'Account created successfully'}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400

    row = get_user_by_email(email)
    if not row or not check_password_hash(row['password_hash'], password):
        return jsonify({'error': 'invalid credentials'}), 401

    token = create_token(row['id'])
    user = get_user_by_id(row['id'])
    # Return token along with user data — frontend stores this in localStorage
    return jsonify({'token': token, 'id': user['id'], 'email': user['email'], 'name': user['name']}), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    # JWT is stateless — logout is handled on the frontend by deleting the token
    return jsonify({'ok': True})


@app.route('/api/me', methods=['GET'])
def me():
    uid = get_current_user_id()
    if not uid:
        return jsonify({'user': None}), 200
    user = get_user_by_id(uid)
    if not user:
        return jsonify({'user': None}), 200
    return jsonify({'user': {'id': user['id'], 'email': user['email'], 'name': user['name']}}), 200


# ─── AI SUMMARY PROCESSOR ─────────────────────────────────────────────────────

def process_file_ai(file_id, file_bytes, original_name, mime_type):
    """Background thread: extract text and summarize file."""
    db = None
    tmp_path = None
    try:
        # If GEMINI API key is missing, store a helpful message and exit early
        import tempfile
        ext = os.path.splitext(original_name)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        if DATABASE_URL:
            db = psycopg2.connect(DATABASE_URL, sslmode='require' if 'supabase' in DATABASE_URL.lower() else False)
        else:
            raise ValueError("DATABASE_URL must be configured in .env file")

        cur = db.cursor(cursor_factory=RealDictCursor)

        if not Config.GEMINI_API_KEY:
            cur.execute("UPDATE files SET summary = %s WHERE id = %s", ("Gemini API key not configured", file_id))
            db.commit()
            return

        extracted_text = ""
        if ext == '.pdf':
            try:
                reader = pypdf.PdfReader(tmp_path)
                for i in range(min(len(reader.pages), 5)):
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
            except Exception as e:
                print(f"Error reading PDF {original_name}: {e}")
        elif ext == '.docx':
            try:
                import zipfile
                import xml.etree.ElementTree as ET
                with zipfile.ZipFile(tmp_path) as docx:
                    xml_content = docx.read('word/document.xml')
                    tree = ET.XML(xml_content)
                    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    for paragraph in tree.iterfind('.//w:p', ns):
                        texts = [node.text for node in paragraph.iterfind('.//w:t', ns) if node.text]
                        if texts:
                            extracted_text += ''.join(texts) + "\n"
            except Exception as e:
                print(f"Error reading DOCX {original_name}: {e}")
        elif ext == '.txt':
            try:
                extracted_text = file_bytes.decode('utf-8', errors='ignore')[:10000]
            except Exception as e:
                print(f"Error reading TXT {original_name}: {e}")

        prompt = f"""You are an expert document analyzer. Read the provided file snippet and write a direct, concise 1-2 sentence summary of the actual content inside the file.
CRITICAL RULES:
- DO NOT start with "This file is a..." or "The file contains...".
- Just output the pure facts of what the text is about.
- Write EXACTLY ONE paragraph, nothing else.

File Name: '{original_name}'
Mime Type: '{mime_type}'
"""
        if extracted_text.strip():
            prompt += f"\nContent Snippet:\n{extracted_text[:6000]}"
        else:
            prompt += "\nNo text content could be extracted from this file."

        response_text = ""

        def call_gemini():
            nonlocal response_text
            try:
                model = GenerativeModel('gemini-1.5-flash')
                safety_settings = [
                    SafetySetting(category=HarmCategory.HARASSMENT, threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
                    SafetySetting(category=HarmCategory.HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
                    SafetySetting(category=HarmCategory.SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
                    SafetySetting(category=HarmCategory.DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE)
                ]
                response = model.generate_content(prompt, safety_settings=safety_settings)
                response_text = response.text if hasattr(response, 'text') else str(response)
            except Exception as e:
                print(f"Gemini API call failed: {e}")
                response_text = ''

        gemini_thread = threading.Thread(target=call_gemini)
        gemini_thread.start()
        gemini_thread.join(timeout=15.0)

        if response_text:
            summary = response_text.strip()
        elif extracted_text.strip():
            # Clean fallback if API fails
            clean_text = extracted_text.strip().replace('\n', ' ')
            summary = f"{clean_text[:150]}..."
        else:
            summary = f"No content could be extracted from this {ext} file."

        cur.execute("UPDATE files SET summary = %s WHERE id = %s", (summary, file_id))
        db.commit()
        print(f"[AI Processor] Summary saved for file ID {file_id}")

    except Exception as e:
        print(f"[AI Processor Error] {e}")
        # Safely attempt to record the error in DB only if cursor is available
        if 'cur' in locals() and cur is not None:
            try:
                cur.execute("UPDATE files SET summary = %s WHERE id = %s", (f"AI Error: {str(e)[:80]}", file_id))
                db.commit()
            except Exception:
                pass
    finally:
        if db:
            db.close()
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ─── FILE ROUTES ──────────────────────────────────────────────────────────────

@app.route('/api/upload', methods=['POST'])
def upload():
    uid = get_current_user_id()
    if not uid:
        return jsonify({'error': 'Unauthorized, please login first'}), 401

    files = []
    if 'files' in request.files:
        files = request.files.getlist('files')
    elif 'file' in request.files:
        files = [request.files.get('file')]
    else:
        return jsonify({'error': 'no file provided'}), 400

    saved = []
    errors = []

    for f in files:
        if not f or f.filename == '':
            errors.append('empty filename')
            continue

        filename = secure_filename(f.filename)
        if not allowed_extension(filename):
            errors.append(f"{filename}: invalid extension")
            continue

        detected_mime = detect_mime(f, filename)
        if not allowed_mime(filename, detected_mime):
            errors.append(f"{filename}: invalid mime ({detected_mime})")
            continue

        ext = os.path.splitext(filename)[1].lower()
        file_uuid = uuid.uuid4().hex
        save_name = f"{file_uuid}{ext}"

        try:
            file_bytes = f.read()
            f_size = len(file_bytes)

            # Upload to Supabase Storage
            if supabase_client:
                supabase_client.storage.from_(SUPABASE_BUCKET).upload(
                    path=save_name,
                    file=file_bytes,
                    file_options={"content-type": detected_mime}
                )
            else:
                errors.append(f"{filename}: Supabase storage not configured")
                continue

            # Save record to DB
            db = get_db()
            cur = db.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                'INSERT INTO files (user_id, original_name, stored_name, file_size, summary, category) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
                (uid, filename, save_name, f_size, 'Processing...', 'Detecting...')
            )
            file_id = cur.fetchone()['id']
            db.commit()

            # Background AI processing (pass bytes so we don't need local disk)
            threading.Thread(
                target=process_file_ai,
                args=(file_id, file_bytes, filename, detected_mime)
            ).start()

            saved.append({'original': filename, 'stored': save_name, 'size': f_size})
        except Exception as e:
            print(f"Upload error: {e}")
            errors.append(f"{filename}: save error")

    return jsonify({'saved': saved, 'errors': errors}), (400 if errors and not saved else 200)


@app.route('/api/files', methods=['GET'])
def get_user_files():
    uid = get_current_user_id()
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM files WHERE user_id = %s ORDER BY created_at DESC', (uid,))
    files = cur.fetchall()

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
    uid = get_current_user_id()
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM files WHERE id = %s AND user_id = %s', (file_id, uid))
    row = cur.fetchone()

    if not row:
        return jsonify({'error': 'File not found'}), 404

    if not supabase_client:
        return jsonify({'error': 'Storage not configured'}), 500

    # Generate a signed URL (valid for 60 seconds) — redirect user to it
    signed = supabase_client.storage.from_(SUPABASE_BUCKET).create_signed_url(
        path=row['stored_name'],
        expires_in=60
    )
    from flask import redirect
    return redirect(signed['signedURL'])


@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_user_file(file_id):
    uid = get_current_user_id()
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM files WHERE id = %s AND user_id = %s', (file_id, uid))
    row = cur.fetchone()

    if not row:
        return jsonify({'error': 'File not found or access denied'}), 404

    # Delete from Supabase Storage
    if supabase_client:
        try:
            supabase_client.storage.from_(SUPABASE_BUCKET).remove([row['stored_name']])
        except Exception as e:
            print(f"Storage delete error: {e}")

    # Delete from database
    cur.execute('DELETE FROM files WHERE id = %s', (file_id,))
    db.commit()

    return jsonify({'ok': True}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)