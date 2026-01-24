"""
CORS Configuration Module

Handles Cross-Origin Resource Sharing (CORS) configuration with security headers
"""
import os
from typing import List, Dict, Any
from flask import Flask, request, Response
from flask_cors import CORS


class CORSConfig:
    """
    CORS configuration class with environment-based settings
    """
    
    def __init__(self, app: Flask = None):
        """
        Initialize CORS configuration
        
        Args:
            app: Flask application instance (optional)
        """
        self.app = app
        if app is not None:
            self.init_cors(app)
    
    @staticmethod
    def get_cors_origins() -> List[str]:
        """
        Get allowed CORS origins from environment variables
        
        Returns:
            List of allowed origins
        """
        cors_origins = os.environ.get('CORS_ORIGINS', '*')
        if cors_origins == '*':
            return ['*']
        
        # Split and clean origins
        origins = [origin.strip() for origin in cors_origins.split(',')]
        return [origin for origin in origins if origin]
    
    @staticmethod
    def get_cors_methods() -> List[str]:
        """
        Get allowed CORS methods from environment variables
        
        Returns:
            List of allowed HTTP methods
        """
        cors_methods = os.environ.get('CORS_METHODS', 'GET,POST,PUT,DELETE,OPTIONS')
        methods = [method.strip() for method in cors_methods.split(',')]
        return [method for method in methods if method]
    
    @staticmethod
    def get_cors_headers() -> List[str]:
        """
        Get allowed CORS headers from environment variables
        
        Returns:
            List of allowed headers
        """
        cors_headers = os.environ.get('CORS_HEADERS', 'Content-Type,Authorization')
        headers = [header.strip() for header in cors_headers.split(',')]
        return [header for header in headers if header]
    
    @staticmethod
    def get_cors_max_age() -> int:
        """
        Get CORS preflight cache max age from environment variables
        
        Returns:
            Max age in seconds (default: 3600)
        """
        try:
            return int(os.environ.get('CORS_MAX_AGE', '3600'))
        except ValueError:
            return 3600
    
    @staticmethod
    def get_cors_credentials() -> bool:
        """
        Get CORS credentials support from environment variables
        
        Returns:
            Whether to support credentials (default: True)
        """
        return os.environ.get('CORS_CREDENTIALS', 'true').lower() == 'true'
    
    def get_cors_config(self) -> Dict[str, Any]:
        """
        Get complete CORS configuration dictionary
        
        Returns:
            Dictionary with CORS configuration
        """
        return {
            'origins': self.get_cors_origins(),
            'methods': self.get_cors_methods(),
            'allow_headers': self.get_cors_headers(),
            'supports_credentials': self.get_cors_credentials(),
            'max_age': self.get_cors_max_age()
        }
    
    def init_cors(self, app: Flask) -> None:
        """
        Initialize CORS with Flask application
        
        Args:
            app: Flask application instance
        """
        # Get CORS configuration
        cors_config = self.get_cors_config()
        
        # Initialize Flask-CORS
        CORS(app, **cors_config)
        
        # Add security headers after each request
        @app.after_request
        def add_security_headers(response: Response) -> Response:
            """
            Add security headers to all responses
            
            Args:
                response: Flask response object
                
            Returns:
                Response with added security headers
            """
            # Prevent MIME type sniffing
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # Prevent clickjacking
            response.headers['X-Frame-Options'] = 'DENY'
            
            # Enable XSS protection
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Add Referrer Policy for privacy
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Add Content Security Policy (basic)
            csp_policy = os.environ.get('CSP_POLICY', "default-src 'self'")
            response.headers['Content-Security-Policy'] = csp_policy
            
            return response
        
        # Handle preflight requests explicitly
        @app.before_request
        def handle_preflight():
            """
            Handle CORS preflight requests
            """
            if request.method == 'OPTIONS':
                # Get origin from request
                origin = request.headers.get('Origin')
                allowed_origins = self.get_cors_origins()
                
                # Check if origin is allowed
                if origin and allowed_origins != ['*'] and origin not in allowed_origins:
                    # Origin not allowed, return 403
                    response = Response()
                    response.status_code = 403
                    return response
                
                # Create preflight response
                response = Response()
                response.status_code = 200
                
                # Add CORS headers
                if origin:
                    response.headers['Access-Control-Allow-Origin'] = origin
                elif allowed_origins == ['*']:
                    response.headers['Access-Control-Allow-Origin'] = '*'
                
                response.headers['Access-Control-Allow-Methods'] = ','.join(self.get_cors_methods())
                response.headers['Access-Control-Allow-Headers'] = ','.join(self.get_cors_headers())
                response.headers['Access-Control-Max-Age'] = str(self.get_cors_max_age())
                
                if self.get_cors_credentials():
                    response.headers['Access-Control-Allow-Credentials'] = 'true'
                
                return response
    
    @staticmethod
    def validate_origin(origin: str) -> bool:
        """
        Validate if an origin is allowed
        
        Args:
            origin: Origin to validate
            
        Returns:
            True if origin is allowed, False otherwise
        """
        allowed_origins = CORSConfig.get_cors_origins()
        
        # Allow all origins if wildcard is set
        if allowed_origins == ['*']:
            return True
        
        # Check if origin is in allowed list
        return origin in allowed_origins
    
    @staticmethod
    def is_cors_enabled() -> bool:
        """
        Check if CORS is enabled
        
        Returns:
            True if CORS is enabled, False otherwise
        """
        return os.environ.get('CORS_ENABLED', 'true').lower() == 'true'