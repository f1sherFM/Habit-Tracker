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

from .category_service import (
    CategoryService,
    CategoryServiceError,
    CategoryNotFoundError
)

from .tag_service import (
    TagService,
    TagServiceError,
    TagNotFoundError
)

from .comment_service import (
    CommentService,
    CommentServiceError,
    CommentNotFoundError
)

from .analytics_service import (
    AnalyticsService,
    AnalyticsServiceError
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
    'UserAlreadyExistsError',
    'CategoryService',
    'CategoryServiceError',
    'CategoryNotFoundError',
    'TagService',
    'TagServiceError',
    'TagNotFoundError',
    'CommentService',
    'CommentServiceError',
    'CommentNotFoundError',
    'AnalyticsService',
    'AnalyticsServiceError'
]