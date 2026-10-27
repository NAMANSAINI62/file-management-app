import os
import concurrent.futures
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from database import init_db, close_db
from routes.auth_routes import auth_bp
from routes.file_routes import file_bp
from routes.share_routes import share_bp

def create_app():
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.config['JWT_SECRET'] = Config.JWT_SECRET

    # Thread Pool for background AI document processing
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    app.config['EXECUTOR'] = executor

    # Rate Limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    # Apply auth route rate limits
    limiter.limit("5 per minute")(auth_bp)

    # CORS configuration
    CORS(
        app,
        supports_credentials=True,
        origins=[Config.FRONTEND_URL],
        allow_headers=['Authorization', 'Content-Type']
    )

    # Database teardown registration
    app.teardown_appcontext(close_db)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(share_bp)

    with app.app_context():
        init_db()

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)