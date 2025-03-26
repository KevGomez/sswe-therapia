"""
Application Configuration Module
"""
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

class Config:
    """Base configuration class for the application."""
    
    # Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key-please-change-in-production')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Firebase settings
    FIREBASE_CONFIG = {
        "project_id": "sansa-sswe-kevin",
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
        "database_url": "https://sansa-sswe-kevin-default-rtdb.firebaseio.com/"
    }
    
    @classmethod
    def get_firebase_credentials(cls) -> Dict[str, Any]:
        """Return Firebase credentials dictionary."""
        return {
            "type": "service_account",
            "project_id": cls.FIREBASE_CONFIG["project_id"],
            "private_key_id": cls.FIREBASE_CONFIG["private_key_id"],
            "private_key": cls.FIREBASE_CONFIG["private_key"],
            "client_email": cls.FIREBASE_CONFIG["client_email"],
            "client_id": cls.FIREBASE_CONFIG["client_id"],
            "auth_uri": cls.FIREBASE_CONFIG["auth_uri"],
            "token_uri": cls.FIREBASE_CONFIG["token_uri"],
            "auth_provider_x509_cert_url": cls.FIREBASE_CONFIG["auth_provider_x509_cert_url"],
            "client_x509_cert_url": cls.FIREBASE_CONFIG["client_x509_cert_url"]
        }
    
    @classmethod
    def get_database_url(cls) -> str:
        """Return the Firebase database URL."""
        return cls.FIREBASE_CONFIG["database_url"]


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Select the appropriate configuration based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Active configuration
active_config = config[os.getenv('FLASK_ENV', 'default')] 