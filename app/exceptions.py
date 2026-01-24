"""
Custom Exception Classes

Application-specific exceptions for standardized error handling
"""
from typing import List, Optional, Dict, Any
from datetime import datetime


class HabitTrackerException(Exception):
    """Base exception for all Habit Tracker application errors"""
    
    def __init__(self, message: str, error_code: str = None, details: Any = None):
        """
        Initialize base exception
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details
        self.timestamp = datetime.utcnow()
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization"""
        error_dict = {
            'code': self.error_code,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }
        
        if self.details:
            error_dict['details'] = self.details
            
        return error_dict


class ValidationError(HabitTrackerException):
    """Raised when data validation fails"""
    
    def __init__(self, errors: List[str], field: str = None):
        """
        Initialize validation error
        
        Args:
            errors: List of validation error messages
            field: Specific field that failed validation (optional)
        """
        self.errors = errors
        self.field = field
        
        if field:
            message = f"Validation failed for field '{field}'"
        else:
            message = "Data validation failed"
            
        details = []
        for error in errors:
            error_detail = {'message': error}
            if field:
                error_detail['field'] = field
            details.append(error_detail)
        
        super().__init__(message, 'VALIDATION_ERROR', details)


class AuthorizationError(HabitTrackerException):
    """Raised when user lacks permission for an operation"""
    
    def __init__(self, message: str = "Access denied", resource: str = None, action: str = None):
        """
        Initialize authorization error
        
        Args:
            message: Error message
            resource: Resource being accessed (optional)
            action: Action being attempted (optional)
        """
        self.resource = resource
        self.action = action
        
        details = {}
        if resource:
            details['resource'] = resource
        if action:
            details['action'] = action
            
        super().__init__(message, 'AUTHORIZATION_ERROR', details if details else None)


class AuthenticationError(HabitTrackerException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        """
        Initialize authentication error
        
        Args:
            message: Error message
        """
        super().__init__(message, 'AUTHENTICATION_ERROR')


class BusinessLogicError(HabitTrackerException):
    """Raised when business logic rules are violated"""
    
    def __init__(self, message: str, rule: str = None, context: Dict[str, Any] = None):
        """
        Initialize business logic error
        
        Args:
            message: Error message
            rule: Business rule that was violated (optional)
            context: Additional context about the violation (optional)
        """
        self.rule = rule
        self.context = context or {}
        
        details = {}
        if rule:
            details['rule'] = rule
        if context:
            details['context'] = context
            
        super().__init__(message, 'BUSINESS_LOGIC_ERROR', details if details else None)


class ResourceNotFoundError(HabitTrackerException):
    """Raised when a requested resource is not found"""
    
    def __init__(self, resource_type: str, resource_id: Any = None, message: str = None):
        """
        Initialize resource not found error
        
        Args:
            resource_type: Type of resource (e.g., 'habit', 'user')
            resource_id: ID of the resource (optional)
            message: Custom error message (optional)
        """
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        if not message:
            if resource_id:
                message = f"{resource_type.title()} with ID {resource_id} not found"
            else:
                message = f"{resource_type.title()} not found"
        
        details = {'resource_type': resource_type}
        if resource_id:
            details['resource_id'] = resource_id
            
        super().__init__(message, 'RESOURCE_NOT_FOUND', details)


class ConflictError(HabitTrackerException):
    """Raised when a resource conflict occurs"""
    
    def __init__(self, message: str, conflicting_resource: str = None):
        """
        Initialize conflict error
        
        Args:
            message: Error message
            conflicting_resource: Description of the conflicting resource (optional)
        """
        self.conflicting_resource = conflicting_resource
        
        details = {}
        if conflicting_resource:
            details['conflicting_resource'] = conflicting_resource
            
        super().__init__(message, 'CONFLICT_ERROR', details if details else None)


class RateLimitError(HabitTrackerException):
    """Raised when rate limits are exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        """
        Initialize rate limit error
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying (optional)
        """
        self.retry_after = retry_after
        
        details = {}
        if retry_after:
            details['retry_after'] = retry_after
            
        super().__init__(message, 'RATE_LIMIT_ERROR', details if details else None)


class ExternalServiceError(HabitTrackerException):
    """Raised when external service calls fail"""
    
    def __init__(self, service: str, message: str = None, status_code: int = None):
        """
        Initialize external service error
        
        Args:
            service: Name of the external service
            message: Error message (optional)
            status_code: HTTP status code from service (optional)
        """
        self.service = service
        self.status_code = status_code
        
        if not message:
            message = f"External service '{service}' error"
            
        details = {'service': service}
        if status_code:
            details['status_code'] = status_code
            
        super().__init__(message, 'EXTERNAL_SERVICE_ERROR', details)


class ConfigurationError(HabitTrackerException):
    """Raised when application configuration is invalid"""
    
    def __init__(self, setting: str, message: str = None):
        """
        Initialize configuration error
        
        Args:
            setting: Configuration setting that is invalid
            message: Error message (optional)
        """
        self.setting = setting
        
        if not message:
            message = f"Invalid configuration for setting '{setting}'"
            
        details = {'setting': setting}
        
        super().__init__(message, 'CONFIGURATION_ERROR', details)