"""
Configuration Validator

Validates environment configuration and required variables
"""
import os
from typing import List, Tuple
from .base_validator import ValidationResult


class ConfigValidator:
    """Validates application configuration"""
    
    @staticmethod
    def validate_environment_config() -> ValidationResult:
        """
        Validate that all required environment variables are present
        
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        
        # Check for SECRET_KEY in production
        flask_env = os.environ.get('FLASK_ENV', 'development')
        if flask_env == 'production':
            if not os.environ.get('SECRET_KEY'):
                errors.append("SECRET_KEY is required in production environment")
            
            if not os.environ.get('DATABASE_URL'):
                errors.append("DATABASE_URL is required in production environment")
        
        # Validate SECRET_KEY strength if present
        secret_key = os.environ.get('SECRET_KEY')
        if secret_key:
            if len(secret_key) < 32:
                errors.append("SECRET_KEY should be at least 32 characters long")
            
            if secret_key in ['your-secret-key-here', 'change-me', 'dev-key']:
                errors.append("SECRET_KEY should not use default/example values")
        
        # Validate CORS origins format
        cors_origins = os.environ.get('CORS_ORIGINS', '*')
        if cors_origins != '*':
            origins = cors_origins.split(',')
            for origin in origins:
                origin = origin.strip()
                if origin and not (origin.startswith('http://') or origin.startswith('https://')):
                    errors.append(f"Invalid CORS origin format: {origin}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    @staticmethod
    def validate_startup_config() -> ValidationResult:
        """
        Validate configuration required for application startup
        
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        
        # Get environment
        flask_env = os.environ.get('FLASK_ENV', 'development')
        
        # Environment-specific validations
        if flask_env == 'production':
            # Production requires critical variables
            required_vars = ['SECRET_KEY', 'DATABASE_URL']
            for var in required_vars:
                if not os.environ.get(var):
                    errors.append(f"Required environment variable missing: {var}")
        
        elif flask_env == 'testing':
            # Testing environment validation
            pass  # Testing has minimal requirements
        
        else:
            # Development environment validation
            # Check if SECRET_KEY is set for security awareness
            if not os.environ.get('SECRET_KEY'):
                errors.append("SECRET_KEY should be set even in development for consistency")
        
        # Validate CORS configuration
        cors_enabled = os.environ.get('CORS_ENABLED', 'true').lower()
        if cors_enabled not in ['true', 'false']:
            errors.append("CORS_ENABLED must be 'true' or 'false'")
        
        # Validate CORS origins if CORS is enabled
        if cors_enabled == 'true':
            cors_origins = os.environ.get('CORS_ORIGINS', '*')
            if cors_origins != '*':
                origins = cors_origins.split(',')
                for origin in origins:
                    origin = origin.strip()
                    if origin and not (origin.startswith('http://') or origin.startswith('https://')):
                        errors.append(f"Invalid CORS origin format: {origin}")
        
        # Validate CORS methods
        cors_methods = os.environ.get('CORS_METHODS', 'GET,POST,PUT,DELETE,OPTIONS')
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH', 'HEAD']
        methods = [method.strip() for method in cors_methods.split(',')]
        for method in methods:
            if method and method not in valid_methods:
                errors.append(f"Invalid CORS method: {method}")
        
        # Validate CORS max age
        cors_max_age = os.environ.get('CORS_MAX_AGE', '3600')
        try:
            max_age_int = int(cors_max_age)
            if max_age_int < 0:
                errors.append("CORS_MAX_AGE must be a non-negative integer")
        except ValueError:
            errors.append("CORS_MAX_AGE must be a valid integer")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    @staticmethod
    def validate_database_config() -> ValidationResult:
        """
        Validate database configuration
        
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            # Basic URL format validation
            if not (database_url.startswith('sqlite://') or 
                   database_url.startswith('postgresql://') or
                   database_url.startswith('postgres://')):
                errors.append("DATABASE_URL must start with sqlite://, postgresql://, or postgres://")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    @staticmethod
    def validate_oauth_config() -> ValidationResult:
        """
        Validate OAuth configuration
        
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        
        # Google OAuth validation
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
        google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        
        if google_client_id and not google_client_secret:
            errors.append("GOOGLE_CLIENT_SECRET is required when GOOGLE_CLIENT_ID is set")
        elif google_client_secret and not google_client_id:
            errors.append("GOOGLE_CLIENT_ID is required when GOOGLE_CLIENT_SECRET is set")
        
        # GitHub OAuth validation
        github_client_id = os.environ.get('GITHUB_CLIENT_ID')
        github_client_secret = os.environ.get('GITHUB_CLIENT_SECRET')
        
        if github_client_id and not github_client_secret:
            errors.append("GITHUB_CLIENT_SECRET is required when GITHUB_CLIENT_ID is set")
        elif github_client_secret and not github_client_id:
            errors.append("GITHUB_CLIENT_ID is required when GITHUB_CLIENT_SECRET is set")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    @staticmethod
    def validate_all() -> ValidationResult:
        """
        Run all configuration validations
        
        Returns:
            ValidationResult with combined validation status and errors
        """
        all_errors = []
        
        # Run all validations
        env_result = ConfigValidator.validate_environment_config()
        startup_result = ConfigValidator.validate_startup_config()
        db_result = ConfigValidator.validate_database_config()
        oauth_result = ConfigValidator.validate_oauth_config()
        
        # Combine errors
        all_errors.extend(env_result.errors)
        all_errors.extend(startup_result.errors)
        all_errors.extend(db_result.errors)
        all_errors.extend(oauth_result.errors)
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors
        )
    
    @staticmethod
    def check_startup_requirements() -> None:
        """
        Check startup requirements and raise exception if validation fails
        
        Raises:
            EnvironmentError: If required configuration is missing or invalid
        """
        result = ConfigValidator.validate_startup_config()
        
        if not result.is_valid:
            error_message = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in result.errors)
            raise EnvironmentError(error_message)