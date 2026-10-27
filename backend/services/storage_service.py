import os
import mimetypes
from config import Config

try:
    import magic
except ImportError:
    magic = None

try:
    from supabase import create_client, Client as SupabaseClient
except ImportError:
    create_client = None
    SupabaseClient = None

ALLOWED_EXT = Config.ALLOWED_EXTENSIONS
ALLOWED_MIME_BY_EXT = Config.ALLOWED_MIME_BY_EXT
SUPABASE_BUCKET = Config.SUPABASE_BUCKET

supabase_client = None
if Config.SUPABASE_URL and Config.SUPABASE_SERVICE_KEY and create_client:
    supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

def allowed_extension(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXT

def detect_mime(file_obj, filename):
    chunk = file_obj.read(2048)
    file_obj.seek(0)
    if magic is not None:
        try:
            return magic.from_buffer(chunk, mime=True)
        except Exception:
            pass
    guessed = mimetypes.guess_type(filename)[0]
    return guessed or 'application/octet-stream'

def allowed_mime(filename, mime_value, file_obj=None):
    ext = os.path.splitext(filename)[1].lower()
    mime_main = mime_value.split(';', 1)[0].strip().lower() if mime_value else ''
    expected = ALLOWED_MIME_BY_EXT.get(ext, set())
    if not expected or mime_main not in {m.lower() for m in expected}:
        return False

    if file_obj is not None:
        header = file_obj.read(8)
        file_obj.seek(0)
        if ext == '.pdf' and not header.startswith(b'%PDF-'):
            return False
        if ext in {'.docx'} and not header.startswith(b'PK\x03\x04'):
            return False
        if ext in {'.png'} and not header.startswith(b'\x89PNG\r\n\x1a\n'):
            return False
        if ext in {'.jpg', '.jpeg'} and not header.startswith(b'\xff\xd8\xff'):
            return False

    return True

def save_file(save_name, file_bytes, detected_mime, root_path):
    if supabase_client:
        supabase_client.storage.from_(SUPABASE_BUCKET).upload(
            path=save_name,
            file=file_bytes,
            file_options={"content-type": detected_mime}
        )
    else:
        uploads_dir = os.path.join(root_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        with open(os.path.join(uploads_dir, save_name), 'wb') as local_file:
            local_file.write(file_bytes)

def delete_file(stored_name, root_path):
    if supabase_client:
        try:
            supabase_client.storage.from_(SUPABASE_BUCKET).remove([stored_name])
        except Exception as e:
            print(f"Storage delete error: {e}")
    else:
        try:
            uploads_dir = os.path.join(root_path, 'uploads')
            local_path = os.path.join(uploads_dir, stored_name)
            if os.path.exists(local_path):
                os.remove(local_path)
        except Exception as e:
            print(f"Local storage delete error: {e}")

def get_file_download_url(stored_name, expires_in=60):
    if supabase_client:
        signed = supabase_client.storage.from_(SUPABASE_BUCKET).create_signed_url(
            path=stored_name,
            expires_in=expires_in
        )
        return signed.get('signedURL')
    return None
