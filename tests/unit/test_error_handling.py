"""
Unit Tests for Error Handling

Tests for custom exceptions and global error handlers
"""
import pytest
import json
from unittest.mock import Mock, patch
from flask import Flask

from app.exceptions import (
    HabitTrackerException, ValidationError, AuthorizationError,
    AuthenticationError, BusinessLogicError, ResourceNotFoundError,
    ConflictError, RateLimitError, ExternalServiceError, ConfigurationError
)
from app.error_handlers import register_error_handlers


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_habit_tracker_exception_base(self):
        """Test base HabitTrackerException functionality"""
        error = HabitTrackerException("Test error", "TEST_CODE", {"key": "value"})
        
        assert error.message == "Test error"
        assert error.error_code == "TEST_CODE"
        assert error.details == {"key": "value"}
        assert error.timestamp is not None
        
        error_dict = error.to_dict()
        assert error_dict['code'] == "TEST_CODE"
        assert error_dict['message'] == "Test error"
        assert error_dict['details'] == {"key": "value"}
        assert 'timestamp' in error_dict
    
    def test_validation_error(self):
        """Test ValidationError with multiple errors"""
        errors = ["Field is required", "Invalid format"]
        error = ValidationError(errors, "email")
        
        assert error.errors == errors
        assert error.field == "email"
        assert error.error_code == "VALIDATION_ERROR"
        assert "Validation failed for field 'email'" in error.message
        
        error_dict = error.to_dict()
        assert len(error_dict['details']) == 2
        assert error_dict['details'][0]['field'] == "email"
        assert error_dict['details'][0]['message'] == "Field is required"
    
    def test_validation_error_without_field(self):
        """Test ValidationError without specific field"""
        errors = ["General validation error"]
        error = ValidationError(errors)
        
        assert error.field is None
        assert "Data validation failed" in error.message
        
        error_dict = error.to_dict()
        assert 'field' not in error_dict['details'][0]
    
    def test_authorization_error(self):
        """Test AuthorizationError with resource and action"""
        error = AuthorizationError("Access denied", "habit", "delete")
        
        assert error.resource == "habit"
        assert error.action == "delete"
        assert error.error_code == "AUTHORIZATION_ERROR"
        
        error_dict = error.to_dict()
        assert error_dict['details']['resource'] == "habit"
        assert error_dict['details']['action'] == "delete"
    
    def test_authentication_error(self):
        """Test AuthenticationError"""
        error = AuthenticationError("Invalid credentials")
        
        assert error.message == "Invalid credentials"
        assert error.error_code == "AUTHENTICATION_ERROR"
    
    def test_business_logic_error(self):
        """Test BusinessLogicError with rule and context"""
        context = {"habit_type": "pleasant", "reward": "coffee"}
        error = BusinessLogicError("Pleasant habits cannot have rewards", "no_reward_for_pleasant", context)
        
        assert error.rule == "no_reward_for_pleasant"
        assert error.context == context
        assert error.error_code == "BUSINESS_LOGIC_ERROR"
        
        error_dict = error.to_dict()
        assert error_dict['details']['rule'] == "no_reward_for_pleasant"
        assert error_dict['details']['context'] == context
    
    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError with different parameters"""
        # With resource ID
        error1 = ResourceNotFoundError("habit", 123)
        assert error1.resource_type == "habit"
        assert error1.resource_id == 123
        assert "Habit with ID 123 not found" in error1.message
        
        # Without resource ID
        error2 = ResourceNotFoundError("user")
        assert error2.resource_type == "user"
        assert error2.resource_id is None
        assert "User not found" in error2.message
        
        # With custom message
        error3 = ResourceNotFoundError("habit", 456, "Custom not found message")
        assert error3.message == "Custom not found message"
    
    def test_conflict_error(self):
        """Test ConflictError"""
        error = ConflictError("Email already exists", "user@example.com")
        
        assert error.conflicting_resource == "user@example.com"
        assert error.error_code == "CONFLICT_ERROR"
        
        error_dict = error.to_dict()
        assert error_dict['details']['conflicting_resource'] == "user@example.com"
    
    def test_rate_limit_error(self):
        """Test RateLimitError with retry_after"""
        error = RateLimitError("Too many requests", 60)
        
        assert error.retry_after == 60
        assert error.error_code == "RATE_LIMIT_ERROR"
        
        error_dict = error.to_dict()
        assert error_dict['details']['retry_after'] == 60
    
    def test_external_service_error(self):
        """Test ExternalServiceError"""
        error = ExternalServiceError("payment_gateway", "Service unavailable", 503)
        
        assert error.service == "payment_gateway"
        assert error.status_code == 503
        assert error.error_code == "EXTERNAL_SERVICE_ERROR"
        
        error_dict = error.to_dict()
        assert error_dict['details']['service'] == "payment_gateway"
        assert error_dict['details']['status_code'] == 503
    
    def test_configuration_error(self):
        """Test ConfigurationError"""
        error = ConfigurationError("DATABASE_URL", "Invalid database URL format")
        
        assert error.setting == "DATABASE_URL"
        assert error.message == "Invalid database URL format"
        assert error.error_code == "CONFIGURATION_ERROR"
        
        error_dict = error.to_dict()
        assert error_dict['details']['setting'] == "DATABASE_URL"


class TestErrorHandlers:
    """Test global error handlers"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app with error handlers"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        
        # Register error handlers
        register_error_handlers(app)
        
        # Add a test route that can raise different exceptions
        @app.route('/test/validation')
        def test_validation():
            raise ValidationError(["Test validation error"], "test_field")
        
        @app.route('/test/authorization')
        def test_authorization():
            raise AuthorizationError("Test authorization error", "test_resource", "test_action")
        
        @app.route('/test/authentication')
        def test_authentication():
            raise AuthenticationError("Test authentication error")
        
        @app.route('/test/not_found')
        def test_not_found():
            raise ResourceNotFoundError("test_resource", 123)
        
        @app.route('/test/conflict')
        def test_conflict():
            raise ConflictError("Test conflict error", "test_resource")
        
        @app.route('/test/business_logic')
        def test_business_logic():
            raise BusinessLogicError("Test business logic error", "test_rule")
        
        @app.route('/test/rate_limit')
        def test_rate_limit():
            raise RateLimitError("Test rate limit error", 30)
        
        @app.route('/test/external_service')
        def test_external_service():
            raise ExternalServiceError("test_service", "Test service error", 502)
        
        @app.route('/test/configuration')
        def test_configuration():
            raise ConfigurationError("TEST_SETTING", "Test configuration error")
        
        @app.route('/test/generic_habit_tracker')
        def test_generic_habit_tracker():
            raise HabitTrackerException("Test generic error", "TEST_CODE")
        
        @app.route('/test/unexpected')
        def test_unexpected():
            raise ValueError("Test unexpected error")
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_validation_error_handler(self, client):
        """Test ValidationError handler returns 400"""
        response = client.get('/test/validation')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert 'Test validation error' in str(data['error']['details'])
        assert data['path'] == '/test/validation'
        assert data['method'] == 'GET'
    
    def test_authorization_error_handler(self, client):
        """Test AuthorizationError handler returns 403"""
        response = client.get('/test/authorization')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'AUTHORIZATION_ERROR'
        assert data['error']['message'] == 'Test authorization error'
        assert data['error']['details']['resource'] == 'test_resource'
        assert data['error']['details']['action'] == 'test_action'
    
    def test_authentication_error_handler(self, client):
        """Test AuthenticationError handler returns 401"""
        response = client.get('/test/authentication')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'AUTHENTICATION_ERROR'
        assert data['error']['message'] == 'Test authentication error'
    
    def test_resource_not_found_error_handler(self, client):
        """Test ResourceNotFoundError handler returns 404"""
        response = client.get('/test/not_found')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'RESOURCE_NOT_FOUND'
        assert 'Test_Resource with ID 123 not found' in data['error']['message']
    
    def test_conflict_error_handler(self, client):
        """Test ConflictError handler returns 409"""
        response = client.get('/test/conflict')
        
        assert response.status_code == 409
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'CONFLICT_ERROR'
        assert data['error']['message'] == 'Test conflict error'
    
    def test_business_logic_error_handler(self, client):
        """Test BusinessLogicError handler returns 422"""
        response = client.get('/test/business_logic')
        
        assert response.status_code == 422
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'BUSINESS_LOGIC_ERROR'
        assert data['error']['message'] == 'Test business logic error'
    
    def test_rate_limit_error_handler(self, client):
        """Test RateLimitError handler returns 429 with Retry-After header"""
        response = client.get('/test/rate_limit')
        
        assert response.status_code == 429
        assert response.headers.get('Retry-After') == '30'
        
        data = json.loads(response.data)
        assert data['error']['code'] == 'RATE_LIMIT_ERROR'
        assert data['error']['details']['retry_after'] == 30
    
    def test_external_service_error_handler(self, client):
        """Test ExternalServiceError handler returns 502"""
        response = client.get('/test/external_service')
        
        assert response.status_code == 502
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'EXTERNAL_SERVICE_ERROR'
        assert data['error']['details']['service'] == 'test_service'
        assert data['error']['details']['status_code'] == 502
    
    def test_configuration_error_handler(self, client):
        """Test ConfigurationError handler returns 500"""
        response = client.get('/test/configuration')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'CONFIGURATION_ERROR'
        assert data['error']['details']['setting'] == 'TEST_SETTING'
    
    def test_generic_habit_tracker_exception_handler(self, client):
        """Test generic HabitTrackerException handler returns 500"""
        response = client.get('/test/generic_habit_tracker')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'TEST_CODE'
        assert data['error']['message'] == 'Test generic error'
    
    def test_unexpected_error_handler(self, client):
        """Test unexpected exception handler returns 500"""
        response = client.get('/test/unexpected')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'UNEXPECTED_ERROR'
        # In non-debug mode, should not expose internal error details
        assert 'An unexpected error occurred' in data['error']['message']
    
    def test_http_404_handler(self, client):
        """Test HTTP 404 handler for non-existent routes"""
        response = client.get('/non/existent/route')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['message'] == 'The requested resource was not found'
        assert data['path'] == '/non/existent/route'
    
    def test_http_405_handler(self, client):
        """Test HTTP 405 handler for method not allowed"""
        # Try POST on a GET-only route
        response = client.post('/test/validation')
        
        assert response.status_code == 405
        data = json.loads(response.data)
        
        assert data['error']['code'] == 'METHOD_NOT_ALLOWED'
        assert 'Method POST not allowed' in data['error']['message']
    
    def test_error_response_format(self, client):
        """Test that all error responses follow the standard format"""
        response = client.get('/test/validation')
        data = json.loads(response.data)
        
        # Check required fields
        assert 'error' in data
        assert 'path' in data
        assert 'method' in data
        
        # Check error object structure
        error = data['error']
        assert 'code' in error
        assert 'message' in error
        assert 'timestamp' in error
        
        # Timestamp should be in ISO format
        from datetime import datetime
        datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00'))
    
    def test_debug_mode_error_details(self):
        """Test that debug mode exposes more error details"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        
        register_error_handlers(app)
        
        @app.route('/test/unexpected')
        def test_unexpected():
            raise ValueError("Detailed error message")
        
        with app.test_client() as client:
            response = client.get('/test/unexpected')
            data = json.loads(response.data)
            
            # In debug mode, should expose more details
            assert 'Detailed error message' in data['error']['message']