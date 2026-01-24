"""
Integration Tests for Habit Tracker System

Tests the integration between all components: models, services, validators, and API layers.
"""
import pytest
from datetime import datetime, timezone
from app import create_app, db
from app.models import init_db, get_models
from app.models.habit_types import HabitType
from app.services.habit_service import HabitService
from app.services.user_service import UserService
from app.validators.habit_validator import HabitValidator
from app.validators.time_validator import TimeValidator
from app.validators.frequency_validator import FrequencyValidator
from app.exceptions import ValidationError, AuthorizationError


class TestSystemIntegration:
    """Integration tests for the complete system"""
    
    @pytest.fixture
    def app(self):
        """Create test application"""
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
            'habit_validator': habit_validator
        }
    
    @pytest.fixture
    def test_user(self, app, models, services):
        """Create a test user"""
        User, Habit, HabitLog = models
        user_service = services['user_service']
        
        user = user_service.create_user(
            email='test@example.com',
            password='T3stP@ssw0rd!',
            name='Test User'
        )
        db.session.commit()
        return user
    
    def test_complete_habit_workflow(self, app, models, services, test_user):
        """Test complete workflow: create user, create habit, validate, update, delete"""
        User, Habit, HabitLog = models
        habit_service = services['habit_service']
        
        # 1. Create a valid useful habit
        habit_data = {
            'name': 'Morning Exercise',
            'description': 'Daily morning workout',
            'execution_time': 60,  # 1 minute
            'frequency': 7,  # Weekly
            'habit_type': HabitType.USEFUL,
            'reward': 'Healthy breakfast'
        }
        
        habit = habit_service.create_habit(test_user.id, habit_data)
        assert habit is not None
        assert habit.name == 'Morning Exercise'
        assert habit.habit_type == HabitType.USEFUL
        assert habit.reward == 'Healthy breakfast'
        
        # 2. Verify habit was saved to database
        saved_habit = Habit.query.filter_by(id=habit.id).first()
        assert saved_habit is not None
        assert saved_habit.user_id == test_user.id
        
        # 3. Update the habit
        update_data = {
            'execution_time': 90,  # 1.5 minutes
            'description': 'Updated morning workout routine'
        }
        
        updated_habit = habit_service.update_habit(habit.id, test_user.id, update_data)
        assert updated_habit.execution_time == 90
        assert updated_habit.description == 'Updated morning workout routine'
        
        # 4. Get user habits
        user_habits = habit_service.get_user_habits(test_user.id)
        assert len(user_habits) == 1
        assert user_habits[0].id == habit.id
        
        # 5. Delete the habit
        result = habit_service.delete_habit(habit.id, test_user.id)
        assert result is True
        
        # 6. Verify habit is deleted
        deleted_habit = Habit.query.filter_by(id=habit.id).first()
        assert deleted_habit is None
    
    def test_validation_integration(self, app, models, services, test_user):
        """Test that validation works properly across the system"""
        habit_service = services['habit_service']
        
        # Test execution time validation (should fail > 120 seconds)
        invalid_habit_data = {
            'name': 'Long Exercise',
            'execution_time': 150,  # Invalid: > 120 seconds
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(test_user.id, invalid_habit_data)
        
        assert "120 секунд" in str(exc_info.value)
        
        # Test frequency validation (should fail < 7 days)
        invalid_habit_data = {
            'name': 'Daily Exercise',
            'execution_time': 60,
            'frequency': 3,  # Invalid: < 7 days
            'habit_type': HabitType.USEFUL
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(test_user.id, invalid_habit_data)
        
        assert "7 дней" in str(exc_info.value)
        
        # Test pleasant habit constraints (should fail with reward)
        invalid_habit_data = {
            'name': 'Watch TV',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.PLEASANT,
            'reward': 'Snack'  # Invalid: pleasant habits can't have rewards
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(test_user.id, invalid_habit_data)
        
        assert "Приятная привычка не может иметь вознаграждение" in str(exc_info.value)
    
    def test_authorization_integration(self, app, models, services, test_user):
        """Test that authorization works properly across the system"""
        User, Habit, HabitLog = models
        habit_service = services['habit_service']
        user_service = services['user_service']
        
        # Create another user
        other_user_data = {
            'email': 'other@example.com',
            'password': 'OtherPassword123!',
            'name': 'Other User'
        }
        other_user = user_service.create_user(other_user_data)
        db.session.commit()
        
        # Create a habit for the first user
        habit_data = {
            'name': 'Test Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit = habit_service.create_habit(test_user.id, habit_data)
        
        # Try to update the habit as the other user (should fail)
        update_data = {'name': 'Hacked Habit'}
        
        with pytest.raises(AuthorizationError):
            habit_service.update_habit(habit.id, other_user.id, update_data)
        
        # Try to delete the habit as the other user (should fail)
        with pytest.raises(AuthorizationError):
            habit_service.delete_habit(habit.id, other_user.id)
        
        # Verify the habit is unchanged
        unchanged_habit = Habit.query.filter_by(id=habit.id).first()
        assert unchanged_habit.name == 'Test Habit'
    
    def test_business_rules_integration(self, app, models, services, test_user):
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
        
        assert "либо вознаграждение, либо связанную привычку" in str(exc_info.value)
        
        # Test that pleasant habits cannot be related to other habits
        invalid_pleasant_data = {
            'name': 'Invalid Pleasant',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.PLEASANT,
            'related_habit_id': base_habit.id
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(test_user.id, invalid_pleasant_data)
        
        assert "Приятная привычка не может быть связана" in str(exc_info.value)
    
    def test_model_relationships_integration(self, app, models, services, test_user):
        """Test that model relationships work properly"""
        User, Habit, HabitLog = models
        habit_service = services['habit_service']
        
        # Create multiple habits for the user
        habit1_data = {
            'name': 'Habit 1',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit2_data = {
            'name': 'Habit 2',
            'execution_time': 90,
            'frequency': 7,
            'habit_type': HabitType.PLEASANT
        }
        
        habit1 = habit_service.create_habit(test_user.id, habit1_data)
        habit2 = habit_service.create_habit(test_user.id, habit2_data)
        
        # Test user -> habits relationship
        user_habits = test_user.habits
        assert len(user_habits) == 2
        habit_names = [h.name for h in user_habits]
        assert 'Habit 1' in habit_names
        assert 'Habit 2' in habit_names
        
        # Test habit -> user relationship
        assert habit1.user.id == test_user.id
        assert habit2.user.id == test_user.id
        
        # Create a habit log
        today = datetime.now(timezone.utc).date()
        log = HabitLog(habit_id=habit1.id, date=today, completed=True)
        db.session.add(log)
        db.session.commit()
        
        # Test habit -> logs relationship
        habit1_logs = habit1.logs
        assert len(habit1_logs) == 1
        assert habit1_logs[0].completed is True
        
        # Test log -> habit relationship
        assert log.habit.id == habit1.id
    
    def test_cascade_deletion_integration(self, app, models, services, test_user):
        """Test that cascade deletion works properly"""
        User, Habit, HabitLog = models
        habit_service = services['habit_service']
        
        # Create a habit
        habit_data = {
            'name': 'Test Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit = habit_service.create_habit(test_user.id, habit_data)
        
        # Create some logs for the habit
        today = datetime.now(timezone.utc).date()
        log1 = HabitLog(habit_id=habit.id, date=today, completed=True)
        log2 = HabitLog(habit_id=habit.id, date=today, completed=False)
        
        db.session.add_all([log1, log2])
        db.session.commit()
        
        # Verify logs exist
        logs_before = HabitLog.query.filter_by(habit_id=habit.id).all()
        assert len(logs_before) == 2
        
        # Delete the habit
        habit_service.delete_habit(habit.id, test_user.id)
        
        # Verify logs are also deleted (cascade)
        logs_after = HabitLog.query.filter_by(habit_id=habit.id).all()
        assert len(logs_after) == 0
    
    def test_default_values_integration(self, app, models, services, test_user):
        """Test that default values are properly set"""
        habit_service = services['habit_service']
        
        # Create a minimal habit (should get default values)
        minimal_habit_data = {
            'name': 'Minimal Habit'
        }
        
        habit = habit_service.create_habit(test_user.id, minimal_habit_data)
        
        # Verify default values are set
        assert habit.execution_time == 60  # Default 60 seconds
        assert habit.frequency == 1  # Default daily (but will be adjusted by validator to 7)
        assert habit.habit_type == HabitType.USEFUL  # Default useful
        assert habit.is_archived is False  # Default not archived
        assert habit.created_at is not None
        assert habit.updated_at is not None
    
    def test_error_handling_integration(self, app, models, services, test_user):
        """Test that errors are properly handled and propagated"""
        habit_service = services['habit_service']
        
        # Test handling of non-existent habit update
        with pytest.raises(Exception):  # Should raise some kind of error
            habit_service.update_habit(99999, test_user.id, {'name': 'Updated'})
        
        # Test handling of non-existent habit deletion
        with pytest.raises(Exception):  # Should raise some kind of error
            habit_service.delete_habit(99999, test_user.id)
        
        # Test handling of empty habit name
        invalid_data = {
            'name': '',  # Empty name should fail
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(test_user.id, invalid_data)
        
        assert "пустым" in str(exc_info.value)