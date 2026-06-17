import os
from flask import Flask, jsonify
from dotenv import load_dotenv

from app.database import db
from app.extensions import bcrypt, login_manager
from app.config import config_by_name
from app.models import User

# Load environment variables
load_dotenv()

def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__)
    
    # Resolve configuration environment
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config_by_name.get(config_name, config_by_name['development']))
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    # Configure user loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # AWS health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """AWS ALB Target Group health check endpoint."""
        return jsonify({"status": "healthy"}), 200

    # Register Blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.students import students_bp
    from app.blueprints.courses import courses_bp
    from app.blueprints.attendance import attendance_bp
    from app.blueprints.marks import marks_bp
    from app.blueprints.documents import documents_bp
    from app.blueprints.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(courses_bp, url_prefix='/courses')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(marks_bp, url_prefix='/marks')
    app.register_blueprint(documents_bp, url_prefix='/documents')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Ensure database tables are created (especially helpful for local SQLite)
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.error(f"Error creating database tables: {e}")

    # Register template context processor for storage URLs
    @app.context_processor
    def inject_storage():
        from app.services.storage_service import get_storage_service
        storage = get_storage_service(app.config)
        return dict(storage_url=storage.get_file_url)
        
    return app
