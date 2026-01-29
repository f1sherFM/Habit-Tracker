"""
Habit Tracker Application Package

Flask application factory with environment-based configuration
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import get_config
from .utils.cors_config import CORSConfig
from .validators.config_validator import ConfigValidator
import logging
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """
    Application factory pattern with full component integration
    
    Args:
        config_name: Configuration environment ('development', 'testing', 'production')
    
    Returns:
        Flask application instance
        
    Raises:
        EnvironmentError: If configuration validation fails
    """
    logger.info(f"Creating Flask application with config: {config_name}")
    
    # Validate configuration before creating app
    ConfigValidator.check_startup_requirements()
    
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    logger.info(f"Loaded configuration: {config_class.__name__}")
    
    # Initialize extensions
    _init_extensions(app)
    
    # Initialize CORS with security headers
    _init_cors(app)
    
    # Initialize models and database
    _init_database(app)
    
    # Register error handlers
    _register_error_handlers(app)
    
    # Register blueprints
    _register_blueprints(app)
    
    # Initialize services
    _init_services(app)
    
    # Setup request logging
    _setup_request_logging(app)
    
    logger.info("Flask application created successfully")
    return app


def _init_extensions(app):
    """Initialize Flask extensions"""
    logger.info("Initializing Flask extensions")
    
    # Initialize database
    db.init_app(app)
    
    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = None  # Disable automatic redirects for API
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Custom unauthorized handler for API requests
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify
        if request.path.startswith('/api/'):
            return jsonify({
                'error': {
                    'code': 'AUTHENTICATION_REQUIRED',
                    'message': 'Authentication required to access this resource'
                }
            }), 401
        # For non-API requests, you could redirect to login page
        return jsonify({
            'error': {
                'code': 'AUTHENTICATION_REQUIRED', 
                'message': 'Authentication required'
            }
        }), 401
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return User.query.get(int(user_id))


def _init_cors(app):
    """Initialize CORS configuration"""
    logger.info("Initializing CORS configuration")
    
    if CORSConfig.is_cors_enabled():
        cors_config = CORSConfig(app)
        logger.info("CORS enabled and configured")
    else:
        logger.info("CORS disabled")


def _init_database(app):
    """Initialize database and models"""
    logger.info("Initializing database and models")
    
    # Initialize models with db instance
    from . import models
    models.init_db(db)
    
    # Create tables in application context
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.warning(f"Database table creation warning: {e}")


def _register_error_handlers(app):
    """Register global error handlers"""
    logger.info("Registering error handlers")
    
    from .error_handlers import register_error_handlers
    register_error_handlers(app)


def _register_blueprints(app):
    """Register application blueprints"""
    logger.info("Registering blueprints")
    
    # Register API blueprints
    from .api.habits import habits_bp
    from .api.users import users_bp
    from .api.categories import categories_bp
    from .api.tags import tags_bp
    from .api.comments import comments_bp
    from .api.analytics import analytics_bp
    
    app.register_blueprint(habits_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(analytics_bp)
    
    logger.info("API blueprints registered")


def _init_services(app):
    """Initialize application services"""
    logger.info("Initializing application services")
    
    # Services are initialized lazily when needed
    # This ensures proper application context
    with app.app_context():
        from .services.habit_service import HabitService
        from .services.user_service import UserService
        
        # Store service classes in app config for later use
        app.config['HABIT_SERVICE_CLASS'] = HabitService
        app.config['USER_SERVICE_CLASS'] = UserService
        
        logger.info("Service classes configured")


def _setup_request_logging(app):
    """Setup request logging for debugging and monitoring"""
    if app.config.get('DEBUG') or os.environ.get('ENABLE_REQUEST_LOGGING'):
        logger.info("Setting up request logging")
        
        from .error_handlers import setup_request_logging
        setup_request_logging(app)


# Convenience function for getting services
def get_habit_service():
    """Get HabitService instance with proper initialization"""
    from flask import current_app
    service_class = current_app.config.get('HABIT_SERVICE_CLASS')
    if service_class:
        return service_class()
    else:
        from .services.habit_service import HabitService
        return HabitService()


def get_user_service():
    """Get UserService instance with proper initialization"""
    from flask import current_app
    service_class = current_app.config.get('USER_SERVICE_CLASS')
    if service_class:
        return service_class()
    else:
        from .services.user_service import UserService
        return UserService()