import os
import uuid
from flask import Blueprint, request, jsonify, current_app, send_from_directory, redirect
from werkzeug.utils import secure_filename
from psycopg2.extras import RealDictCursor

from database import get_db
from utils.auth import get_current_user_id
from services.storage_service import (
    allowed_extension,
    detect_mime,
    allowed_mime,
    save_file,
    delete_file,
    get_file_download_url
)
from services.ai_service import process_file_ai

file_bp = Blueprint('files', __name__)

@file_bp.route('/api/upload', methods=['POST'])
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
    executor = current_app.config.get('EXECUTOR')

    for f in files:
        if not f or f.filename == '':
            errors.append('empty filename')
            continue

        filename = secure_filename(f.filename)
        if not allowed_extension(filename):
            errors.append(f"{filename}: invalid extension")
            continue

        detected_mime = detect_mime(f, filename)
        if not allowed_mime(filename, detected_mime, file_obj=f):
            errors.append(f"{filename}: invalid mime ({detected_mime})")
            continue

        ext = os.path.splitext(filename)[1].lower()
        file_uuid = uuid.uuid4().hex
        save_name = f"{file_uuid}{ext}"

        try:
            file_bytes = f.read()
            f_size = len(file_bytes)
            if f_size == 0:
                errors.append(f"{filename}: file is empty (0 bytes). Save the file first, then upload again.")
                continue

            save_file(save_name, file_bytes, detected_mime, current_app.root_path)

            db = get_db()
            cur = db.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                'INSERT INTO files (user_id, original_name, stored_name, file_size, summary, category) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
                (uid, filename, save_name, f_size, 'Processing...', 'Detecting...')
            )
            file_id = cur.fetchone()['id']
            db.commit()

            if executor:
                executor.submit(process_file_ai, file_id, file_bytes, filename, detected_mime)

            saved.append({'original': filename, 'stored': save_name, 'size': f_size})
        except Exception as e:
            print(f"Upload error: {e}")
            errors.append(f"{filename}: save error")

    return jsonify({'saved': saved, 'errors': errors}), (400 if errors and not saved else 200)

@file_bp.route('/api/files', methods=['GET'])
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

@file_bp.route('/api/files/<int:file_id>/download', methods=['GET'])
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

    signed_url = get_file_download_url(row['stored_name'])
    if signed_url:
        return redirect(signed_url)

    uploads_dir = os.path.join(current_app.root_path, 'uploads')
    return send_from_directory(uploads_dir, row['stored_name'], as_attachment=True, download_name=row['original_name'])

@file_bp.route('/api/files/<int:file_id>', methods=['DELETE'])
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

    delete_file(row['stored_name'], current_app.root_path)

    cur.execute('DELETE FROM files WHERE id = %s', (file_id,))
    db.commit()
    return jsonify({'ok': True}), 200
