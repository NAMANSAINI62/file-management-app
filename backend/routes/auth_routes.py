from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2.extras import RealDictCursor
from database import get_db
from utils.auth import create_token, get_current_user_id

auth_bp = Blueprint('auth', __name__)

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

@auth_bp.route('/api/signup', methods=['POST'])
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

@auth_bp.route('/api/login', methods=['POST'])
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
    return jsonify({'token': token, 'id': user['id'], 'email': user['email'], 'name': user['name']}), 200

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({'ok': True})

@auth_bp.route('/api/me', methods=['GET'])
def me():
    uid = get_current_user_id()
    if not uid:
        return jsonify({'user': None}), 200
    user = get_user_by_id(uid)
    if not user:
        return jsonify({'user': None}), 200
    return jsonify({'user': {'id': user['id'], 'email': user['email'], 'name': user['name']}}), 200
