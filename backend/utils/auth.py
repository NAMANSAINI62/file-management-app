import datetime
import functools
import jwt
from flask import request, jsonify, g
from config import Config

JWT_SECRET = Config.JWT_SECRET

def create_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def get_current_user_id():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload.get('user_id')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        uid = get_current_user_id()
        if not uid:
            return jsonify({'error': 'Unauthorized, please login first'}), 401
        g.user_id = uid
        return f(*args, **kwargs)
    return decorated_function
