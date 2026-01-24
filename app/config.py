"""
Flask Application Configuration
Supports environment-based configuration with validation
"""
import os
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class"""
    
    # Flask core settings
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_HEADERS = ['Content-Type', 'Authorization']
    
    # OAuth settings
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
    
    @classmethod
    def validate_required_vars(cls) -> tuple[bool, List[str]]:
        """
        Validate that all required environment variables are present
        
        Returns:
            tuple: (is_valid, missing_vars)
        """
        required_vars = ['SECRET_KEY']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        return len(missing_vars) == 0, missing_vars


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL', 'sqlite:///dev.db')
    
    @classmethod
    def validate_required_vars(cls) -> tuple[bool, List[str]]:
        """Development has relaxed requirements"""
        required_vars = []  # No required vars for development
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        return len(missing_vars) == 0, missing_vars


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'test-secret-key-for-testing-purposes-only')
    
    @classmethod
    def validate_required_vars(cls) -> tuple[bool, List[str]]:
        """Testing has minimal requirements"""
        required_vars = []  # No required vars for testing
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        return len(missing_vars) == 0, missing_vars


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    @classmethod
    def validate_required_vars(cls) -> tuple[bool, List[str]]:
        """Production requires all critical environment variables"""
        required_vars = ['SECRET_KEY', 'DATABASE_URL']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        return len(missing_vars) == 0, missing_vars


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: Optional[str] = None) -> Config:
    """
    Get configuration class based on environment
    
    Args:
        config_name: Configuration name ('development', 'testing', 'production')
                    If None, uses FLASK_ENV environment variable
    
    Returns:
        Configuration class instance
    
    Raises:
        EnvironmentError: If required environment variables are missing
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_class = config.get(config_name, config['default'])
    
    # Validate required environment variables
    is_valid, missing_vars = config_class.validate_required_vars()
    if not is_valid:
        raise EnvironmentError(
            f"Missing required environment variables for {config_name}: {missing_vars}"
        )
    
    return config_class