"""
User Service

Business logic layer for user management with authentication and authorization
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from werkzeug.security import check_password_hash
from ..models import get_models
from ..exceptions import (
    AuthenticationError, ResourceNotFoundError, ConflictError,
    HabitTrackerException
)


class UserServiceError(HabitTrackerException):
    """Base exception for UserService errors"""
    pass


class UserNotFoundError(ResourceNotFoundError):
    """Raised when user is not found"""
    def __init__(self, user_id: int = None, email: str = None):
        if user_id:
            super().__init__('user', user_id)
        elif email:
            super().__init__('user', email, f"User with email {email} not found")
        else:
            super().__init__('user')


class UserAlreadyExistsError(ConflictError):
    """Raised when trying to create a user that already exists"""
    def __init__(self, email: str):
        super().__init__(f"User with email {email} already exists", f"email: {email}")


class UserService:
    """
    Service layer for user management with authentication and authorization
    """
    
    def __init__(self):
        """Initialize UserService"""
        # Get models after initialization
        self.User, self.Habit, self.HabitLog = get_models()
        
        # Import db from models
        from ..models.user import db
        self.db = db
    
    def create_user(self, email: str, password: str, name: str = None) -> 'User':
        """
        Create a new user with validation
        
        Args:
            email: User's email address
            password: User's password (plain text, will be hashed)
            name: User's display name (optional)
            
        Returns:
            User: Created user instance
            
        Raises:
            UserAlreadyExistsError: If user with email already exists
            UserServiceError: If creation fails
        """
        # Check if user already exists
        existing_user = self.User.query.filter_by(email=email.lower().strip()).first()
        if existing_user:
            raise UserAlreadyExistsError(email)
        
        try:
            # Create user instance
            user = self.User(
                email=email.lower().strip(),
                name=name.strip() if name else None
            )
            
            # Set password (will be hashed automatically)
            user.set_password(password)
            
            # Save to database
            self.db.session.add(user)
            self.db.session.commit()
            
            return user
            
        except Exception as e:
            self.db.session.rollback()
            if isinstance(e, UserServiceError):
                raise
            raise UserServiceError(f"Failed to create user: {str(e)}")
    
    def authenticate_user(self, email: str, password: str) -> Optional['User']:
        """
        Authenticate user with email and password
        
        Args:
            email: User's email address
            password: User's password (plain text)
            
        Returns:
            User: Authenticated user instance or None if authentication fails
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Find user by email
            user = self.User.query.filter_by(email=email.lower().strip()).first()
            
            if not user:
                raise AuthenticationError("Invalid email or password")
            
            # Check if user is active
            if not user.is_active:
                raise AuthenticationError("User account is deactivated")
            
            # Verify password
            if not user.check_password(password):
                raise AuthenticationError("Invalid email or password")
            
            # Update last login timestamp if available
            if hasattr(user, 'last_login'):
                user.last_login = datetime.now(timezone.utc)
                self.db.session.commit()
            
            return user
            
        except Exception as e:
            if isinstance(e, AuthenticationError):
                raise
            raise UserServiceError(f"Authentication failed: {str(e)}")
    
    def get_user_by_id(self, user_id: int) -> 'User':
        """
        Get user by ID
        
        Args:
            user_id: User's ID
            
        Returns:
            User: User instance
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = self.User.query.get(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        return user
    
    def get_user_by_email(self, email: str) -> 'User':
        """
        Get user by email
        
        Args:
            email: User's email address
            
        Returns:
            User: User instance
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = self.User.query.filter_by(email=email.lower().strip()).first()
        if not user:
            raise UserNotFoundError(email=email)
        
        return user
    
    def update_user(self, user_id: int, user_data: dict) -> 'User':
        """
        Update user information
        
        Args:
            user_id: ID of the user to update
            user_data: Dictionary containing updated user data
            
        Returns:
            User: Updated user instance
            
        Raises:
            UserNotFoundError: If user doesn't exist
            UserServiceError: If update fails
        """
        user = self.get_user_by_id(user_id)
        
        try:
            # Update allowed fields
            allowed_fields = ['name', 'avatar_url']
            for field in allowed_fields:
                if field in user_data:
                    setattr(user, field, user_data[field])
            
            # Update timestamp
            user.updated_at = datetime.now(timezone.utc)
            
            # Save to database
            self.db.session.commit()
            
            return user
            
        except Exception as e:
            self.db.session.rollback()
            if isinstance(e, UserServiceError):
                raise
            raise UserServiceError(f"Failed to update user: {str(e)}")
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            user_id: ID of the user
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            bool: True if password was changed successfully
            
        Raises:
            UserNotFoundError: If user doesn't exist
            AuthenticationError: If current password is incorrect
            UserServiceError: If password change fails
        """
        user = self.get_user_by_id(user_id)
        
        # Verify current password
        if not user.check_password(current_password):
            raise AuthenticationError("Current password is incorrect")
        
        try:
            # Set new password
            user.set_password(new_password)
            user.updated_at = datetime.now(timezone.utc)
            
            # Save to database
            self.db.session.commit()
            
            return True
            
        except Exception as e:
            self.db.session.rollback()
            if isinstance(e, UserServiceError):
                raise
            raise UserServiceError(f"Failed to change password: {str(e)}")
    
    def deactivate_user(self, user_id: int) -> 'User':
        """
        Deactivate user account
        
        Args:
            user_id: ID of the user to deactivate
            
        Returns:
            User: Deactivated user instance
            
        Raises:
            UserNotFoundError: If user doesn't exist
            UserServiceError: If deactivation fails
        """
        user = self.get_user_by_id(user_id)
        
        try:
            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)
            
            # Save to database
            self.db.session.commit()
            
            return user
            
        except Exception as e:
            self.db.session.rollback()
            raise UserServiceError(f"Failed to deactivate user: {str(e)}")
    
    def activate_user(self, user_id: int) -> 'User':
        """
        Activate user account
        
        Args:
            user_id: ID of the user to activate
            
        Returns:
            User: Activated user instance
            
        Raises:
            UserNotFoundError: If user doesn't exist
            UserServiceError: If activation fails
        """
        user = self.get_user_by_id(user_id)
        
        try:
            user.is_active = True
            user.updated_at = datetime.now(timezone.utc)
            
            # Save to database
            self.db.session.commit()
            
            return user
            
        except Exception as e:
            self.db.session.rollback()
            raise UserServiceError(f"Failed to activate user: {str(e)}")
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get user statistics including habit completion data
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict: User statistics
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = self.get_user_by_id(user_id)
        
        try:
            # Get basic user stats
            stats = user.get_completion_stats()
            
            # Add additional statistics
            total_habits = len(user.get_active_habits())
            useful_habits = len(user.get_habits_by_type('useful'))
            pleasant_habits = len(user.get_habits_by_type('pleasant'))
            
            stats.update({
                'total_active_habits': total_habits,
                'useful_habits_count': useful_habits,
                'pleasant_habits_count': pleasant_habits,
                'account_created': user.created_at.isoformat() if user.created_at else None
            })
            
            return stats
            
        except Exception as e:
            raise UserServiceError(f"Failed to get user statistics: {str(e)}")
    
    def authorize_user_action(self, user_id: int, resource_user_id: int) -> bool:
        """
        Check if user is authorized to perform action on resource
        
        Args:
            user_id: ID of the user performing the action
            resource_user_id: ID of the user who owns the resource
            
        Returns:
            bool: True if authorized
        """
        return user_id == resource_user_id
    
    def get_or_create_oauth_user(self, provider: str, provider_data: dict) -> 'User':
        """
        Get or create user from OAuth provider data
        
        Args:
            provider: OAuth provider name ('google', 'github')
            provider_data: User data from OAuth provider
            
        Returns:
            User: User instance
            
        Raises:
            UserServiceError: If OAuth user creation/retrieval fails
        """
        try:
            if provider == 'google':
                return self.User.get_or_create_from_google(provider_data)
            elif provider == 'github':
                return self.User.get_or_create_from_github(provider_data)
            else:
                raise UserServiceError(f"Unsupported OAuth provider: {provider}")
                
        except Exception as e:
            if isinstance(e, UserServiceError):
                raise
            raise UserServiceError(f"Failed to handle OAuth user: {str(e)}")