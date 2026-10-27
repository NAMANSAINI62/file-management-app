import os
import uuid
import datetime
from flask import Blueprint, jsonify, current_app, send_from_directory, redirect
from psycopg2.extras import RealDictCursor

from database import get_db
from utils.auth import get_current_user_id
from services.storage_service import get_file_download_url

share_bp = Blueprint('share', __name__)

@share_bp.route('/api/files/<int:file_id>/share', methods=['POST'])
def share_file(file_id):
    uid = get_current_user_id()
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM files WHERE id = %s AND user_id = %s', (file_id, uid))
    row = cur.fetchone()
    if not row:
        return jsonify({'error': 'File not found or access denied'}), 404

    share_token = row.get('share_token')
    if not share_token:
        share_token = uuid.uuid4().hex

    # Set expiration to 24 hours from now
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)

    cur.execute(
        'UPDATE files SET share_token = %s, share_expires_at = %s WHERE id = %s RETURNING *',
        (share_token, expires_at, file_id)
    )
    updated_row = cur.fetchone()
    db.commit()

    return jsonify({
        'id': updated_row['id'],
        'original_name': updated_row['original_name'],
        'file_size': updated_row['file_size'],
        'created_at': updated_row['created_at'].isoformat() if hasattr(updated_row['created_at'], 'isoformat') else updated_row['created_at'],
        'summary': updated_row['summary'],
        'share_token': updated_row['share_token'],
        'share_expires_at': updated_row['share_expires_at'].isoformat() if updated_row['share_expires_at'] else None
    }), 200

@share_bp.route('/api/files/<int:file_id>/unshare', methods=['POST'])
def unshare_file(file_id):
    uid = get_current_user_id()
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM files WHERE id = %s AND user_id = %s', (file_id, uid))
    row = cur.fetchone()
    if not row:
        return jsonify({'error': 'File not found or access denied'}), 404

    cur.execute(
        'UPDATE files SET share_token = NULL, share_expires_at = NULL WHERE id = %s',
        (file_id,)
    )
    db.commit()
    return jsonify({'ok': True, 'message': 'File is now private'}), 200

@share_bp.route('/api/share/<share_token>', methods=['GET'])
def get_shared_file_info(share_token):
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM files WHERE share_token = %s', (share_token,))
    row = cur.fetchone()

    if not row:
        return jsonify({'error': 'File not found or link is invalid'}), 404

    if row['share_expires_at']:
        expires = row['share_expires_at']
        now = datetime.datetime.now(datetime.timezone.utc)
        if expires < now:
            return jsonify({'error': 'This share link has expired'}), 410

    return jsonify({
        'original_name': row['original_name'],
        'file_size': row['file_size'],
        'summary': row['summary'],
        'share_expires_at': row['share_expires_at'].isoformat() if row['share_expires_at'] else None
    }), 200

@share_bp.route('/api/share/<share_token>/download', methods=['GET'])
def download_shared_file(share_token):
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM files WHERE share_token = %s', (share_token,))
    row = cur.fetchone()

    if not row:
        return jsonify({'error': 'File not found or link is invalid'}), 404

    if row['share_expires_at']:
        expires = row['share_expires_at']
        now = datetime.datetime.now(datetime.timezone.utc)
        if expires < now:
            return jsonify({'error': 'This share link has expired'}), 410

    signed_url = get_file_download_url(row['stored_name'])
    if signed_url:
        return redirect(signed_url)

    uploads_dir = os.path.join(current_app.root_path, 'uploads')
    return send_from_directory(uploads_dir, row['stored_name'], as_attachment=True, download_name=row['original_name'])
