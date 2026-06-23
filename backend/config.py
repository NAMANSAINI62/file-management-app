"""
Secure configuration management for the File Management App.
All sensitive values are loaded from .env file, not hardcoded.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Config:
    """Base configuration - all values from environment variables"""
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')  # Supabase connection string (full URI)
    
    # If DATABASE_URL not provided, build from individual components
    if not DATABASE_URL:
        DB_HOST = os.environ.get('DB_HOST')
        DB_PORT = os.environ.get('DB_PORT')
        DB_NAME = os.environ.get('DB_NAME')
        DB_USER = os.environ.get('DB_USER')
        DB_PASS = os.environ.get('DB_PASS')
        
        # Build connection URI if all components are present
        if all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS]):
            DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # API Keys & Secrets
    JWT_SECRET = os.environ.get('JWT_SECRET')
    if not JWT_SECRET:
        raise ValueError("ERROR: JWT_SECRET not set in .env file! This is required for security.")
    
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    # Ensure the API key is set and not a placeholder value. This prevents accidental exposure of a dummy or empty key.
    if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == '' or 'YOUR_' in GEMINI_API_KEY:
        raise ValueError("ERROR: GEMINI_API_KEY not set or contains placeholder. Set a valid key in .env.")
    
    # Keep the old GROQ key line commented for reference (do not expose the value)
    # GROQ_API_KEY = os.environ.get('GROQ_API_KEY')    
    # Supabase Configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')
    SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'uploads')
    
    # Frontend Configuration
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
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


# Validate critical configuration on import
if not Config.DATABASE_URL:
    raise ValueError(
        "ERROR: DATABASE_URL not configured!\n"
        "Set DATABASE_URL in .env or provide DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS"
    )
