"""
Global Error Handlers

Centralized error handling for the Flask application with standardized JSON responses
"""
from flask import jsonify, request, current_app
from werkzeug.exceptions import HTTPException
import logging
import traceback
from typing import Tuple, Dict, Any

from .exceptions import (
    HabitTrackerException, ValidationError, AuthorizationError, 
    AuthenticationError, BusinessLogicError, ResourceNotFoundError,
    ConflictError, RateLimitError, ExternalServiceError, ConfigurationError
)

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register all error handlers with the Flask application"""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> Tuple[Dict[str, Any], int]:
        """Handle validation errors with 400 Bad Request"""
        logger.warning(f"Validation error: {error.message} - Details: {error.details}")
        
        return jsonify({
            'error': error.to_dict(),
            'path': request.path,
            'method': request.method
        }), 400
    
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error: AuthenticationError) -> Tuple[Dict[str, Any], int]:
        """Handle authentication errors with 401 Unauthorized"""
        logger.warning(f"Authentication error: {error.message} - IP: {request.remote_addr}")
        
        return jsonify({
            'error': error.to_dict(),
            'path': request.path,
            'method': request.method
        }), 401
    
    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error: AuthorizationError) -> Tuple[Dict[str, Any], int]:
        """Handle authorization errors with 403 Forbidden"""
        logger.warning(f"Authorization error: {error.message} - User: {getattr(request, 'user_id', 'unknown')} - Resource: {error.resource}")
        
        return jsonify({
            'error': error.to_dict(),
            'path': request.path,
            'method': request.method
        }), 403
    
    @app.errorhandler(ResourceNotFoundError)
    def handle_not_found_error(error: ResourceNotFoundError) -> Tuple[Dict[str, Any], int]:
        """Handle resource not found errors with 404 Not Found"""
        logger.info(f"Resource not found: {error.message} - Path: {request.path}")
        
        return jsonify({
            'error': error.to_dict(),
            'path': request.path,
            'method': request.method
        }), 404
    
    @app.errorhandler(ConflictError)
    def handle_conflict_error(error: ConflictError) -> Tuple[Dict[str, Any], int]:
        """Handle conflict errors with 409 Conflict"""
        logger.warning(f"Conflict error: {error.message} - Resource: {error.conflicting_resource}")
        
        return jsonify({
            'error': error.to_dict(),
            'path': request.path,
            'method': request.method
        }), 409
    
    @app.errorhandler(BusinessLogicError)
    def handle_business_logic_error(error: BusinessLogicError) -> Tuple[Dict[str, Any], int]:
        """Handle business logic errors with 422 Unprocessable Entity"""
        logger.warning(f"Business logic error: {error.message} - Rule: {error.rule}")
        
        return jsonify({
            'error': error.to_dict(),
            'path': request.path,
            'method': request.method
        }), 422
    
    @app.errorhandler(RateLimitError)
    def handle_rate_limit_error(error: RateLimitError) -> Tuple[Dict[str, Any], int]:
        """Handle rate limit errors with 429 Too Many Requests"""
        logger.warning(f"Rate limit exceeded: {error.message} - IP: {request.remote_addr}")
        
        response = jsonify({
            'error': error.to_dict(),
            'path': request.path,
            'method': request.method
        })
        
        # Add Retry-After header if specified
        if error.retry_after:
            response.headers['Retry-After'] = str(error.retry_after)
        
        return response, 429
    
    @app.errorhandler(ExternalServiceError)
    def handle_external_service_error(error: ExternalServiceError) -> Tuple[Dict[str, Any], int]:
        """Handle external service errors with 502 Bad Gateway"""
        logger.error(f"External service error: {error.message} - Service: {error.service} - Status: {error.status_code}")
        
        return jsonify({
            'error': error.to_dict(),
            'path': request.path,
            'method': request.method
        }), 502
    
    @app.errorhandler(ConfigurationError)
    def handle_configuration_error(error: ConfigurationError) -> Tuple[Dict[str, Any], int]:
        """Handle configuration errors with 500 Internal Server Error"""
        logger.error(f"Configuration error: {error.message} - Setting: {error.setting}")
        
        return jsonify({
            'error': error.to_dict(),
            'path': request.path,
            'method': request.method
        }), 500
    
    @app.errorhandler(HabitTrackerException)
    def handle_habit_tracker_exception(error: HabitTrackerException) -> Tuple[Dict[str, Any], int]:
        """Handle generic application exceptions with 500 Internal Server Error"""
        logger.error(f"Application error: {error.message} - Code: {error.error_code}")
        
        return jsonify({
            'error': error.to_dict(),
            'path': request.path,
            'method': request.method
        }), 500
    
    @app.errorhandler(400)
    def handle_bad_request(error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """Handle HTTP 400 Bad Request errors"""
        logger.warning(f"Bad request: {error.description} - Path: {request.path}")
        
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': error.description or 'Bad request',
                'timestamp': current_app.config.get('TESTING') and '2024-01-01T00:00:00' or None
            },
            'path': request.path,
            'method': request.method
        }), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """Handle HTTP 401 Unauthorized errors"""
        logger.warning(f"Unauthorized access: {request.path} - IP: {request.remote_addr}")
        
        return jsonify({
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'Authentication required',
                'timestamp': current_app.config.get('TESTING') and '2024-01-01T00:00:00' or None
            },
            'path': request.path,
            'method': request.method
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """Handle HTTP 403 Forbidden errors"""
        logger.warning(f"Forbidden access: {request.path} - IP: {request.remote_addr}")
        
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Access forbidden',
                'timestamp': current_app.config.get('TESTING') and '2024-01-01T00:00:00' or None
            },
            'path': request.path,
            'method': request.method
        }), 403
    
    @app.errorhandler(404)
    def handle_not_found(error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """Handle HTTP 404 Not Found errors"""
        logger.info(f"Not found: {request.path}")
        
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'The requested resource was not found',
                'timestamp': current_app.config.get('TESTING') and '2024-01-01T00:00:00' or None
            },
            'path': request.path,
            'method': request.method
        }), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """Handle HTTP 405 Method Not Allowed errors"""
        logger.warning(f"Method not allowed: {request.method} {request.path}")
        
        return jsonify({
            'error': {
                'code': 'METHOD_NOT_ALLOWED',
                'message': f'Method {request.method} not allowed for this resource',
                'timestamp': current_app.config.get('TESTING') and '2024-01-01T00:00:00' or None
            },
            'path': request.path,
            'method': request.method
        }), 405
    
    @app.errorhandler(413)
    def handle_payload_too_large(error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """Handle HTTP 413 Payload Too Large errors"""
        logger.warning(f"Payload too large: {request.path} - Content-Length: {request.content_length}")
        
        return jsonify({
            'error': {
                'code': 'PAYLOAD_TOO_LARGE',
                'message': 'Request payload is too large',
                'timestamp': current_app.config.get('TESTING') and '2024-01-01T00:00:00' or None
            },
            'path': request.path,
            'method': request.method
        }), 413
    
    @app.errorhandler(415)
    def handle_unsupported_media_type(error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """Handle HTTP 415 Unsupported Media Type errors"""
        logger.warning(f"Unsupported media type: {request.content_type} - Path: {request.path}")
        
        return jsonify({
            'error': {
                'code': 'UNSUPPORTED_MEDIA_TYPE',
                'message': 'Unsupported media type',
                'timestamp': current_app.config.get('TESTING') and '2024-01-01T00:00:00' or None
            },
            'path': request.path,
            'method': request.method
        }), 415
    
    @app.errorhandler(429)
    def handle_too_many_requests(error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """Handle HTTP 429 Too Many Requests errors"""
        logger.warning(f"Too many requests: {request.path} - IP: {request.remote_addr}")
        
        return jsonify({
            'error': {
                'code': 'TOO_MANY_REQUESTS',
                'message': 'Too many requests',
                'timestamp': current_app.config.get('TESTING') and '2024-01-01T00:00:00' or None
            },
            'path': request.path,
            'method': request.method
        }), 429
    
    @app.errorhandler(500)
    def handle_internal_server_error(error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """Handle HTTP 500 Internal Server Error"""
        # Log the full traceback for debugging
        logger.error(f"Internal server error: {request.path}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Don't expose internal error details in production
        if current_app.config.get('DEBUG'):
            message = str(error) if str(error) != '500 Internal Server Error: The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.' else 'An internal server error occurred'
        else:
            message = 'An internal server error occurred'
        
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': message,
                'timestamp': current_app.config.get('TESTING') and '2024-01-01T00:00:00' or None
            },
            'path': request.path,
            'method': request.method
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> Tuple[Dict[str, Any], int]:
        """Handle unexpected exceptions"""
        # Log the full traceback for debugging
        logger.error(f"Unexpected error: {request.path}")
        logger.error(f"Error type: {type(error).__name__}")
        logger.error(f"Error message: {str(error)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Don't expose internal error details in production
        if current_app.config.get('DEBUG'):
            message = f"Unexpected error: {str(error)}"
        else:
            message = 'An unexpected error occurred'
        
        return jsonify({
            'error': {
                'code': 'UNEXPECTED_ERROR',
                'message': message,
                'timestamp': current_app.config.get('TESTING') and '2024-01-01T00:00:00' or None
            },
            'path': request.path,
            'method': request.method
        }), 500


def log_request_info():
    """Log request information for debugging"""
    if current_app.config.get('DEBUG'):
        logger.debug(f"Request: {request.method} {request.path}")
        logger.debug(f"Headers: {dict(request.headers)}")
        if request.is_json:
            try:
                json_data = request.get_json(silent=True)
                if json_data:
                    logger.debug(f"JSON data: {json_data}")
            except Exception:
                logger.debug("JSON data: <failed to parse>")
        elif request.form:
            logger.debug(f"Form data: {dict(request.form)}")


def setup_request_logging(app):
    """Set up request logging for debugging"""
    
    @app.before_request
    def before_request():
        """Log request information before processing"""
        log_request_info()
    
    @app.after_request
    def after_request(response):
        """Log response information after processing"""
        if current_app.config.get('DEBUG'):
            logger.debug(f"Response: {response.status_code}")
        return response