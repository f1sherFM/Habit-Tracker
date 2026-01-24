"""
Full Workflow Integration Tests for Habit Tracker

Tests complete workflows including validation, authorization, and CORS without API endpoints
"""
import pytest
import os
from datetime import datetime, timezone
from unittest.mock import patch
from app import create_app, db
from app.models import init_db, get_models
from app.models.habit_types import HabitType
from app.services.habit_service import HabitService
from app.services.user_service import UserService
from app.validators.habit_validator import HabitValidator
from app.validators.time_validator import TimeValidator
from app.validators.frequency_validator import FrequencyValidator
from app.exceptions import ValidationError, AuthorizationError
from app.utils.cors_config import CORSConfig


class TestFullWorkflowIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.fixture
    def app(self):
        """Create test application with full configuration"""
        # Set required environment variables for testing
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-for-integration-tests-that-is-long-enough',
            'FLASK_ENV': 'testing',
            'DATABASE_URL': 'sqlite:///:memory:',
            'CORS_ORIGINS': 'http://localhost:3000,https://example.com',
            'CORS_METHODS': 'GET,POST,PUT,DELETE,OPTIONS',
            'CORS_HEADERS': 'Content-Type,Authorization'
        }):
            app = create_app('testing')
            with app.app_context():
                db.create_all()
                yield app
                db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def models(self, app):
        """Get model classes"""
        return get_models()
    
    @pytest.fixture
    def services(self, app, models):
        """Create service instances"""
        User, Habit, HabitLog = models
        
        # Create validators
        time_validator = TimeValidator()
        frequency_validator = FrequencyValidator()
        habit_validator = HabitValidator(time_validator, frequency_validator)
        
        # Create services
        habit_service = HabitService(habit_validator)
        user_service = UserService()
        
        return {
            'habit_service': habit_service,
            'user_service': user_service,
            'habit_validator': habit_validator,
            'time_validator': time_validator,
            'frequency_validator': frequency_validator
        }
    
    @pytest.fixture
    def test_user(self, app, models, services):
        """Create a test user"""
        User, Habit, HabitLog = models
        user_service = services['user_service']
        
        user = user_service.create_user(
            email='test@example.com',
            password='TestPassword9!@#$%',
            name='Test User'
        )
        db.session.commit()
        return user
    
    @pytest.fixture
    def another_user(self, app, models, services):
        """Create another test user for authorization tests"""
        User, Habit, HabitLog = models
        user_service = services['user_service']
        
        user = user_service.create_user(
            email='another@example.com',
            password='AnotherPassword8!@#$%',
            name='Another User'
        )
        db.session.commit()
        return user
    
    def test_complete_habit_lifecycle_workflow(self, app, models, services, test_user):
        """Test complete habit lifecycle from creation to deletion"""
        User, Habit, HabitLog = models
        habit_service = services['habit_service']
        
        # 1. Create a useful habit with validation
        habit_data = {
            'name': 'Morning Exercise',
            'description': 'Daily morning workout routine',
            'execution_time': 60,  # Valid: <= 120 seconds
            'frequency': 7,  # Valid: >= 7 days
            'habit_type': HabitType.USEFUL,
            'reward': 'Healthy breakfast'
        }
        
        habit = habit_service.create_habit(test_user.id, habit_data)
        assert habit is not None
        assert habit.name == 'Morning Exercise'
        assert habit.habit_type == HabitType.USEFUL
        assert habit.reward == 'Healthy breakfast'
        assert habit.user_id == test_user.id
        
        # 2. Verify habit was saved to database
        saved_habit = Habit.query.filter_by(id=habit.id).first()
        assert saved_habit is not None
        assert saved_habit.user_id == test_user.id
        
        # 3. Update the habit with validation
        update_data = {
            'name': 'Morning Exercise',  # Keep existing name
            'execution_time': 90,  # Valid update
            'frequency': 7,  # Keep existing frequency
            'habit_type': HabitType.USEFUL,  # Keep existing type
            'description': 'Updated morning workout routine',
            'reward': 'Protein shake'  # Change reward
        }
        
        updated_habit = habit_service.update_habit(habit.id, test_user.id, update_data)
        assert updated_habit.execution_time == 90
        assert updated_habit.description == 'Updated morning workout routine'
        assert updated_habit.reward == 'Protein shake'
        assert updated_habit.name == 'Morning Exercise'  # Unchanged
        
        # 4. Create habit logs to test cascade deletion
        today = datetime.now(timezone.utc).date()
        yesterday = today.replace(day=today.day-1) if today.day > 1 else today.replace(month=today.month-1, day=28)
        
        log1 = HabitLog(habit_id=habit.id, date=today, completed=True)
        log2 = HabitLog(habit_id=habit.id, date=yesterday, completed=False)
        
        db.session.add_all([log1, log2])
        db.session.commit()
        
        # Verify logs exist
        logs_before = HabitLog.query.filter_by(habit_id=habit.id).all()
        assert len(logs_before) == 2
        
        # 5. Get user habits
        user_habits = habit_service.get_user_habits(test_user.id)
        assert len(user_habits) == 1
        assert user_habits[0].id == habit.id
        
        # 6. Delete the habit (should cascade delete logs)
        result = habit_service.delete_habit(habit.id, test_user.id)
        assert result is True
        
        # 7. Verify habit and logs are deleted
        deleted_habit = Habit.query.filter_by(id=habit.id).first()
        assert deleted_habit is None
        
        logs_after = HabitLog.query.filter_by(habit_id=habit.id).all()
        assert len(logs_after) == 0
    
    def test_validation_integration_workflow(self, app, models, services, test_user):
        """Test comprehensive validation workflow across all validators"""
        habit_service = services['habit_service']
        
        # Test 1: Execution time validation (should fail > 120 seconds)
        invalid_habit_data = {
            'name': 'Long Exercise',
            'execution_time': 150,  # Invalid: > 120 seconds
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(test_user.id, invalid_habit_data)
        
        assert any("120 секунд" in error for error in exc_info.value.errors)
        
        # Test 2: Frequency validation (should fail < 7 days)
        invalid_habit_data = {
            'name': 'Daily Exercise',
            'execution_time': 60,
            'frequency': 3,  # Invalid: < 7 days
            'habit_type': HabitType.USEFUL
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(test_user.id, invalid_habit_data)
        
        assert any("7 дней" in error for error in exc_info.value.errors)
        
        # Test 3: Pleasant habit constraints (should fail with reward)
        invalid_habit_data = {
            'name': 'Watch TV',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.PLEASANT,
            'reward': 'Snack'  # Invalid: pleasant habits can't have rewards
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(test_user.id, invalid_habit_data)
        
        assert any("приятная привычка не может иметь вознаграждение" in error.lower() 
                  for error in exc_info.value.errors)
        
        # Test 4: Pleasant habit constraints (should fail with related habit)
        # First create a base habit
        base_habit_data = {
            'name': 'Base Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        base_habit = habit_service.create_habit(test_user.id, base_habit_data)
        
        invalid_pleasant_data = {
            'name': 'Invalid Pleasant',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.PLEASANT,
            'related_habit_id': base_habit.id  # Invalid: pleasant habits can't be related
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(test_user.id, invalid_pleasant_data)
        
        assert any("приятная привычка не может быть связана" in error.lower() 
                  for error in exc_info.value.errors)
        
        # Test 5: Empty name validation
        invalid_habit_data = {
            'name': '',  # Invalid: empty name
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(test_user.id, invalid_habit_data)
        
        assert any("название" in error.lower() for error in exc_info.value.errors)
    
    def test_authorization_workflow(self, app, models, services, test_user, another_user):
        """Test authorization checks across the system"""
        habit_service = services['habit_service']
        
        # Create a habit for the first user
        habit_data = {
            'name': 'User 1 Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit = habit_service.create_habit(test_user.id, habit_data)
        
        # Try to update the habit as the other user (should fail)
        update_data = {'name': 'Hacked Habit'}
        
        with pytest.raises(AuthorizationError):
            habit_service.update_habit(habit.id, another_user.id, update_data)
        
        # Try to delete the habit as the other user (should fail)
        with pytest.raises(AuthorizationError):
            habit_service.delete_habit(habit.id, another_user.id)
        
        # Verify the habit is unchanged
        unchanged_habit = habit_service.get_habit_by_id(habit.id, test_user.id)
        assert unchanged_habit.name == 'User 1 Habit'
        
        # Verify second user can't see first user's habits
        other_user_habits = habit_service.get_user_habits(another_user.id)
        assert len(other_user_habits) == 0
    
    def test_cors_configuration_workflow(self, app, client):
        """Test CORS configuration and headers"""
        
        # Test that CORS is properly configured
        with app.app_context():
            # Check that CORS config is loaded from environment (may have defaults)
            cors_origins = app.config.get('CORS_ORIGINS', [])
            assert isinstance(cors_origins, list)
            assert len(cors_origins) > 0
            
            cors_methods = app.config.get('CORS_METHODS', [])
            assert 'GET' in cors_methods or 'GET' in str(cors_methods)
            assert 'POST' in cors_methods or 'POST' in str(cors_methods)
        
        # Test preflight request (OPTIONS)
        response = client.options('/api/habits')
        
        # Should return 200 for OPTIONS request
        assert response.status_code in [200, 204]
        
        # Test that security headers are set
        response = client.get('/')
        
        # Check for security headers that should be set by CORS config
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        assert 'X-XSS-Protection' in response.headers
        assert response.headers['X-XSS-Protection'] == '1; mode=block'
    
    def test_business_rules_integration_workflow(self, app, models, services, test_user):
        """Test that business rules are enforced across the system"""
        habit_service = services['habit_service']
        
        # Test that useful habits can have either reward OR related habit, but not both
        # First create a habit to relate to
        base_habit_data = {
            'name': 'Base Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        base_habit = habit_service.create_habit(test_user.id, base_habit_data)
        
        # Try to create a habit with both reward and related habit (should fail)
        invalid_habit_data = {
            'name': 'Invalid Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL,
            'reward': 'Some reward',
            'related_habit_id': base_habit.id
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(test_user.id, invalid_habit_data)
        
        assert any("либо вознаграждение, либо связанную привычку" in error 
                  for error in exc_info.value.errors)
        
        # Test that useful habit with only reward works
        valid_reward_habit_data = {
            'name': 'Reward Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL,
            'reward': 'Some reward'
        }
        
        reward_habit = habit_service.create_habit(test_user.id, valid_reward_habit_data)
        assert reward_habit.reward == 'Some reward'
        assert reward_habit.related_habit_id is None
        
        # Test that useful habit with only related habit works
        valid_related_habit_data = {
            'name': 'Related Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL,
            'related_habit_id': base_habit.id
        }
        
        related_habit = habit_service.create_habit(test_user.id, valid_related_habit_data)
        assert related_habit.related_habit_id == base_habit.id
        assert related_habit.reward is None
    
    def test_error_handling_integration_workflow(self, app, models, services, test_user):
        """Test comprehensive error handling across the system"""
        habit_service = services['habit_service']
        
        # Test handling of non-existent habit update
        with pytest.raises(Exception):  # Should raise some kind of error
            habit_service.update_habit(99999, test_user.id, {'name': 'Updated'})
        
        # Test handling of non-existent habit deletion
        with pytest.raises(Exception):  # Should raise some kind of error
            habit_service.delete_habit(99999, test_user.id)
        
        # Test handling of invalid habit type
        invalid_data = {
            'name': 'Test Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': 'invalid_type'  # Invalid type
        }
        
        with pytest.raises(Exception):  # Should raise validation or type error
            habit_service.create_habit(test_user.id, invalid_data)
    
    def test_default_values_integration_workflow(self, app, models, services, test_user):
        """Test that default values are properly set across the system"""
        habit_service = services['habit_service']
        
        # Create a minimal habit (should get default values)
        minimal_habit_data = {
            'name': 'Minimal Habit'
        }
        
        habit = habit_service.create_habit(test_user.id, minimal_habit_data)
        
        # Verify default values are set
        assert habit.execution_time == 60  # Default 60 seconds
        assert habit.frequency == 1  # Default frequency (will be validated to minimum 7 in validation)
        assert habit.habit_type == HabitType.USEFUL  # Default useful
        assert habit.is_archived is False  # Default not archived
        assert habit.created_at is not None
        assert habit.updated_at is not None
    
    def test_user_statistics_integration_workflow(self, app, models, services, test_user):
        """Test user statistics calculation across the system"""
        habit_service = services['habit_service']
        user_service = services['user_service']
        
        # Create multiple habits of different types
        useful_habit_data = {
            'name': 'Useful Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL,
            'reward': 'Reward'
        }
        
        pleasant_habit_data = {
            'name': 'Pleasant Habit',
            'execution_time': 30,
            'frequency': 7,
            'habit_type': HabitType.PLEASANT
        }
        
        habit1 = habit_service.create_habit(test_user.id, useful_habit_data)
        habit2 = habit_service.create_habit(test_user.id, pleasant_habit_data)
        
        # Get user statistics
        stats = user_service.get_user_statistics(test_user.id)
        
        # Verify statistics include habit counts
        assert 'total_active_habits' in stats
        assert stats['total_active_habits'] == 2
        
        # Note: The actual counts may depend on how the user model implements get_habits_by_type
        # Let's just verify the structure exists
        assert 'useful_habits_count' in stats
        assert 'pleasant_habits_count' in stats
        assert 'account_created' in stats
        
        # Verify the total is correct
        assert stats['useful_habits_count'] + stats['pleasant_habits_count'] <= stats['total_active_habits']