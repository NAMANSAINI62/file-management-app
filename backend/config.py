import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        DB_HOST = os.environ.get('DB_HOST')
        DB_PORT = os.environ.get('DB_PORT')
        DB_NAME = os.environ.get('DB_NAME')
        DB_USER = os.environ.get('DB_USER')
        DB_PASS = os.environ.get('DB_PASS')
        
        if all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS]):
            DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    JWT_SECRET = os.environ.get('JWT_SECRET')
    if not JWT_SECRET:
        raise ValueError("ERROR: JWT_SECRET not set in .env file! This is required for security.")
    
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == '' or 'YOUR_' in GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY not set or contains placeholder. AI summaries will be disabled.")
    
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')
    SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'uploads')
    
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.pdf', '.doc', '.docx', '.txt'}
    
    ALLOWED_MIME_BY_EXT = {
        '.png': {'image/png'},
        '.jpg': {'image/jpeg'},
        '.jpeg': {'image/jpeg'},
        '.pdf': {'application/pdf'},
        '.doc': {'application/msword', 'application/octet-stream', 'application/vnd.ms-word'},
        '.docx': {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/zip',
            'application/x-zip-compressed',
            'application/octet-stream',
            'application/msword'
        },
        '.txt': {'text/plain'},
    }

if not Config.DATABASE_URL:
    raise ValueError(
        "ERROR: DATABASE_URL not configured!\n"
        "Set DATABASE_URL in .env or provide DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS"
    )
