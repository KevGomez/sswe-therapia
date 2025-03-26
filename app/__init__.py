from flask import Flask
from pathlib import Path
import os

from app.routes import appointment_bp


def create_app(test_config=None):
    """Create and configure the Flask application"""
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Ensure data directory exists
    data_dir = Path(app.instance_path) / '../data'
    data_dir.mkdir(exist_ok=True)

    # Register blueprints
    app.register_blueprint(appointment_bp)

    # Simple index route
    @app.route('/')
    def index():
        return {
            "message": "Welcome to the Therapist-Client Scheduling API",
            "endpoints": {
                "Create slot": "POST /api/appointments/therapist/slots",
                "List slots": "GET /api/appointments/therapist/{therapist_id}/slots?date=YYYY-MM-DD",
                "Book slot": "POST /api/appointments/book",
                "Cancel booking": "POST /api/appointments/cancel"
            }
        }

    return app
