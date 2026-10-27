import psycopg2
from psycopg2.extras import RealDictCursor
from flask import g
from config import Config

DATABASE_URL = Config.DATABASE_URL

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        if 'supabase' in DATABASE_URL.lower():
            db = g._database = psycopg2.connect(DATABASE_URL, sslmode='require')
        else:
            db = g._database = psycopg2.connect(DATABASE_URL)
    return db

def close_db(exception=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    try:
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
                share_token VARCHAR(64) UNIQUE,
                share_expires_at TIMESTAMPTZ,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        try:
            cur.execute("ALTER TABLE files ADD COLUMN IF NOT EXISTS summary TEXT")
            cur.execute("ALTER TABLE files ADD COLUMN IF NOT EXISTS category VARCHAR(50)")
            cur.execute("ALTER TABLE files ADD COLUMN IF NOT EXISTS share_token VARCHAR(64) UNIQUE")
            cur.execute("ALTER TABLE files ADD COLUMN IF NOT EXISTS share_expires_at TIMESTAMPTZ")
        except Exception as e:
            print(f"[Schema Update Info] {e}")
        db.commit()
    except Exception as e:
        print(f"[DB Init Warning] Could not connect to database on startup: {e}")
