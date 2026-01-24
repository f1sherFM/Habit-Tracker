"""
Services Package

Business logic layer with service classes for habit and user management
"""

from .habit_service import (
    HabitService,
    HabitServiceError,
    ValidationError,
    AuthorizationError,
    HabitNotFoundError
)

from .user_service import (
    UserService,
    UserServiceError,
    AuthenticationError,
    UserNotFoundError,
    UserAlreadyExistsError
)

__all__ = [
    'HabitService',
    'HabitServiceError',
    'ValidationError',
    'AuthorizationError',
    'HabitNotFoundError',
    'UserService',
    'UserServiceError',
    'AuthenticationError',
    'UserNotFoundError',
    'UserAlreadyExistsError'
]