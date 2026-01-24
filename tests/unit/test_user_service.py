"""
Unit Tests for UserService

Tests specific examples and edge cases for user service operations
"""
import pytest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.user_service import (
    UserService,
    UserServiceError,
    AuthenticationError,
    UserNotFoundError,
    UserAlreadyExistsError
)


class TestUserService:
    """Unit tests for UserService"""
    
    @pytest.fixture
    def user_service(self, app):
        """Create UserService instance for testing"""
        with app.app_context():
            return UserService()
    
    def test_create_user_success(self, user_service):
        """Test successful user creation"""
        user = user_service.create_user(
            email='test@example.com',
            password='SecureP@ssw0rd',
            name='Test User'
        )
        
        assert user.email == 'test@example.com'
        assert user.name == 'Test User'
        assert user.is_active is True
        assert user.password_hash is not None
        assert user.password_hash != 'SecureP@ssw0rd'  # Should be hashed
    
    def test_create_user_duplicate_email_fails(self, user_service):
        """Test that creating user with duplicate email fails"""
        # Create first user
        user_service.create_user(
            email='test@example.com',
            password='SecureP@ssw0rd',
            name='First User'
        )
        
        # Try to create second user with same email
        with pytest.raises(UserAlreadyExistsError):
            user_service.create_user(
                email='test@example.com',
                password='An0therP@ssw0rd',
                name='Second User'
            )
    
    def test_create_user_email_case_insensitive(self, user_service):
        """Test that email comparison is case insensitive"""
        # Create user with lowercase email
        user_service.create_user(
            email='test@example.com',
            password='SecureP@ssw0rd',
            name='First User'
        )
        
        # Try to create user with uppercase email
        with pytest.raises(UserAlreadyExistsError):
            user_service.create_user(
                email='TEST@EXAMPLE.COM',
                password='An0therP@ssw0rd',
                name='Second User'
            )
    
    def test_authenticate_user_success(self, user_service):
        """Test successful user authentication"""
        # Create user
        created_user = user_service.create_user(
            email='test@example.com',
            password='testSecureP@ssw0rd',
            name='Test User'
        )
        
        # Authenticate user
        authenticated_user = user_service.authenticate_user(
            email='test@example.com',
            password='testSecureP@ssw0rd'
        )
        
        assert authenticated_user.id == created_user.id
        assert authenticated_user.email == created_user.email
    
    def test_authenticate_user_wrong_password(self, user_service):
        """Test authentication with wrong password"""
        # Create user
        user_service.create_user(
            email='test@example.com',
            password='C0rrectP@ssw0rd',
            name='Test User'
        )
        
        # Try to authenticate with wrong password
        with pytest.raises(AuthenticationError):
            user_service.authenticate_user(
                email='test@example.com',
                password='Wr0ngP@ssw0rd'
            )
    
    def test_authenticate_user_nonexistent_email(self, user_service):
        """Test authentication with nonexistent email"""
        with pytest.raises(AuthenticationError):
            user_service.authenticate_user(
                email='nonexistent@example.com',
                password='anypassword'
            )
    
    def test_authenticate_inactive_user(self, user_service):
        """Test authentication of inactive user"""
        # Create user
        user = user_service.create_user(
            email='test@example.com',
            password='testSecureP@ssw0rd',
            name='Test User'
        )
        
        # Deactivate user
        user_service.deactivate_user(user.id)
        
        # Try to authenticate inactive user
        with pytest.raises(AuthenticationError):
            user_service.authenticate_user(
                email='test@example.com',
                password='testSecureP@ssw0rd'
            )
    
    def test_get_user_by_id_success(self, user_service):
        """Test getting user by ID"""
        # Create user
        created_user = user_service.create_user(
            email='test@example.com',
            password='testSecureP@ssw0rd',
            name='Test User'
        )
        
        # Get user by ID
        retrieved_user = user_service.get_user_by_id(created_user.id)
        
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email
        assert retrieved_user.name == created_user.name
    
    def test_get_user_by_id_not_found(self, user_service):
        """Test getting user by nonexistent ID"""
        with pytest.raises(UserNotFoundError):
            user_service.get_user_by_id(99999)
    
    def test_get_user_by_email_success(self, user_service):
        """Test getting user by email"""
        # Create user
        created_user = user_service.create_user(
            email='test@example.com',
            password='testSecureP@ssw0rd',
            name='Test User'
        )
        
        # Get user by email
        retrieved_user = user_service.get_user_by_email('test@example.com')
        
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email
    
    def test_get_user_by_email_not_found(self, user_service):
        """Test getting user by nonexistent email"""
        with pytest.raises(UserNotFoundError):
            user_service.get_user_by_email('nonexistent@example.com')
    
    def test_update_user_success(self, user_service):
        """Test successful user update"""
        # Create user
        user = user_service.create_user(
            email='test@example.com',
            password='testSecureP@ssw0rd',
            name='Original Name'
        )
        
        # Update user
        update_data = {
            'name': 'Updated Name',
            'avatar_url': 'https://example.com/avatar.jpg'
        }
        
        updated_user = user_service.update_user(user.id, update_data)
        
        assert updated_user.name == 'Updated Name'
        assert updated_user.avatar_url == 'https://example.com/avatar.jpg'
        assert updated_user.email == 'test@example.com'  # Should not change
    
    def test_update_user_not_found(self, user_service):
        """Test updating nonexistent user"""
        update_data = {'name': 'New Name'}
        
        with pytest.raises(UserNotFoundError):
            user_service.update_user(99999, update_data)
    
    def test_change_password_success(self, user_service):
        """Test successful password change"""
        # Create user
        user = user_service.create_user(
            email='test@example.com',
            password='0ldP@ssw0rd',
            name='Test User'
        )
        
        # Change password
        result = user_service.change_password(
            user.id,
            current_password='0ldP@ssw0rd',
            new_password='newSecureP@ssw0rd'
        )
        
        assert result is True
        
        # Verify new password works
        authenticated_user = user_service.authenticate_user(
            email='test@example.com',
            password='newSecureP@ssw0rd'
        )
        assert authenticated_user.id == user.id
        
        # Verify old password doesn't work
        with pytest.raises(AuthenticationError):
            user_service.authenticate_user(
                email='test@example.com',
                password='0ldP@ssw0rd'
            )
    
    def test_change_password_wrong_current_password(self, user_service):
        """Test password change with wrong current password"""
        # Create user
        user = user_service.create_user(
            email='test@example.com',
            password='C0rrectP@ssw0rd',
            name='Test User'
        )
        
        # Try to change password with wrong current password
        with pytest.raises(AuthenticationError):
            user_service.change_password(
                user.id,
                current_password='Wr0ngP@ssw0rd',
                new_password='newSecureP@ssw0rd'
            )
    
    def test_deactivate_and_activate_user(self, user_service):
        """Test user deactivation and activation"""
        # Create user
        user = user_service.create_user(
            email='test@example.com',
            password='testSecureP@ssw0rd',
            name='Test User'
        )
        
        assert user.is_active is True
        
        # Deactivate user
        deactivated_user = user_service.deactivate_user(user.id)
        assert deactivated_user.is_active is False
        
        # Activate user
        activated_user = user_service.activate_user(user.id)
        assert activated_user.is_active is True
    
    def test_get_user_statistics(self, user_service):
        """Test getting user statistics"""
        # Create user
        user = user_service.create_user(
            email='test@example.com',
            password='testSecureP@ssw0rd',
            name='Test User'
        )
        
        # Get statistics
        stats = user_service.get_user_statistics(user.id)
        
        assert isinstance(stats, dict)
        assert 'total_active_habits' in stats
        assert 'useful_habits_count' in stats
        assert 'pleasant_habits_count' in stats
        assert 'account_created' in stats
        
        # For new user, should have no habits
        assert stats['total_active_habits'] == 0
        assert stats['useful_habits_count'] == 0
        assert stats['pleasant_habits_count'] == 0
    
    def test_authorize_user_action(self, user_service):
        """Test user action authorization"""
        # Same user should be authorized
        assert user_service.authorize_user_action(1, 1) is True
        
        # Different users should not be authorized
        assert user_service.authorize_user_action(1, 2) is False
    
    def test_create_user_without_name(self, user_service):
        """Test creating user without name"""
        user = user_service.create_user(
            email='test@example.com',
            password='testSecureP@ssw0rd'
        )
        
        assert user.email == 'test@example.com'
        assert user.name is None
        assert user.is_active is True
    
    def test_email_normalization(self, user_service):
        """Test that emails are normalized (lowercase, trimmed)"""
        user = user_service.create_user(
            email='  TEST@EXAMPLE.COM  ',
            password='testSecureP@ssw0rd',
            name='Test User'
        )
        
        assert user.email == 'test@example.com'
        
        # Should be able to authenticate with original format
        authenticated_user = user_service.authenticate_user(
            email='  TEST@EXAMPLE.COM  ',
            password='testSecureP@ssw0rd'
        )
        assert authenticated_user.id == user.id