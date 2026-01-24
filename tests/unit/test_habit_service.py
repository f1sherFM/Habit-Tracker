"""
Unit Tests for HabitService

Tests specific examples and edge cases for habit service operations
"""
import pytest
from datetime import datetime, timezone
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.habit_service import (
    HabitService,
    ValidationError,
    AuthorizationError,
    HabitNotFoundError,
    HabitServiceError
)
from app.models.habit_types import HabitType


class TestHabitService:
    """Unit tests for HabitService"""
    
    @pytest.fixture
    def habit_service(self, app):
        """Create HabitService instance for testing"""
        with app.app_context():
            return HabitService()
    
    @pytest.fixture
    def another_user(self, app):
        """Create another test user"""
        with app.app_context():
            from app.models import get_models
            User, _, _ = get_models()
            from app.models.user import db
            
            user = User(
                email='another@example.com',
                name='Another User'
            )
            user.set_password('SecureP@ssw0rd')
            db.session.add(user)
            db.session.commit()
            return user
    
    def test_create_habit_success(self, habit_service, sample_user):
        """Test successful habit creation"""
        habit_data = {
            'name': 'Morning Exercise',
            'description': 'Daily morning workout',
            'execution_time': 30,
            'frequency': 7,
            'habit_type': HabitType.USEFUL,
            'reward': 'Protein shake'
        }
        
        habit = habit_service.create_habit(sample_user, habit_data)
        
        assert habit.name == 'Morning Exercise'
        assert habit.description == 'Daily morning workout'
        assert habit.execution_time == 30
        assert habit.frequency == 7
        assert habit.habit_type == HabitType.USEFUL
        assert habit.reward == 'Protein shake'
        assert habit.user_id == sample_user
        assert not habit.is_archived
    
    def test_create_habit_validation_error(self, habit_service, sample_user):
        """Test habit creation with validation errors"""
        # Test with execution time too long
        habit_data = {
            'name': 'Long Exercise',
            'execution_time': 150,  # Too long
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(sample_user, habit_data)
        
        assert any('120 секунд' in error for error in exc_info.value.errors)
    
    def test_create_pleasant_habit_with_reward_fails(self, habit_service, sample_user):
        """Test that pleasant habits cannot have rewards"""
        habit_data = {
            'name': 'Watch TV',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.PLEASANT,
            'reward': 'Snacks'  # Should not be allowed
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(sample_user, habit_data)
        
        assert any('приятная привычка не может иметь вознаграждение' in error.lower() 
                  for error in exc_info.value.errors)
    
    def test_update_habit_success(self, habit_service, sample_user):
        """Test successful habit update"""
        # Create habit first
        habit_data = {
            'name': 'Original Name',
            'execution_time': 30,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit = habit_service.create_habit(sample_user, habit_data)
        
        # Update habit
        update_data = {
            'name': 'Updated Name',
            'execution_time': 45
        }
        
        updated_habit = habit_service.update_habit(habit.id, sample_user, update_data)
        
        assert updated_habit.name == 'Updated Name'
        assert updated_habit.execution_time == 45
        assert updated_habit.frequency == 7  # Unchanged
    
    def test_update_habit_authorization_error(self, habit_service, sample_user, another_user):
        """Test habit update with wrong user"""
        # sample_user and another_user are now IDs, not objects
        sample_user_id = sample_user
        another_user_id = another_user
        
        # Create habit with first user
        habit_data = {
            'name': 'User 1 Habit',
            'execution_time': 30,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit = habit_service.create_habit(sample_user_id, habit_data)
        
        # Try to update with second user
        update_data = {'name': 'Hacked Name'}
        
        with pytest.raises(AuthorizationError):
            habit_service.update_habit(habit.id, another_user_id, update_data)
    
    def test_update_nonexistent_habit(self, habit_service, sample_user):
        """Test updating a habit that doesn't exist"""
        update_data = {'name': 'New Name'}
        
        with pytest.raises(HabitNotFoundError):
            habit_service.update_habit(99999, sample_user, update_data)
    
    def test_delete_habit_success(self, habit_service, sample_user):
        """Test successful habit deletion"""
        # Create habit
        habit_data = {
            'name': 'To Delete',
            'execution_time': 30,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit = habit_service.create_habit(sample_user, habit_data)
        
        # Delete habit
        result = habit_service.delete_habit(habit.id, sample_user)
        
        assert result is True
        
        # Verify habit is deleted
        with pytest.raises(HabitNotFoundError):
            habit_service.get_habit_by_id(habit.id, sample_user)
    
    def test_delete_habit_authorization_error(self, habit_service, sample_user, another_user):
        """Test habit deletion with wrong user"""
        # Create habit with first user
        habit_data = {
            'name': 'User 1 Habit',
            'execution_time': 30,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit = habit_service.create_habit(sample_user, habit_data)
        
        # Try to delete with second user
        with pytest.raises(AuthorizationError):
            habit_service.delete_habit(habit.id, another_user)
    
    def test_delete_habit_cascade_logs(self, habit_service, sample_user):
        """Test that deleting habit also deletes related logs"""
        from app.models import get_models
        User, Habit, HabitLog = get_models()
        from app.models.habit import db
        
        # Create habit
        habit_data = {
            'name': 'Habit with Logs',
            'execution_time': 30,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit = habit_service.create_habit(sample_user, habit_data)
        
        # Create some logs with different dates
        from datetime import timedelta
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)
        
        log1 = HabitLog(habit_id=habit.id, date=today, completed=True)
        log2 = HabitLog(habit_id=habit.id, date=yesterday, completed=False)
        
        db.session.add(log1)
        db.session.add(log2)
        db.session.commit()
        
        # Verify logs exist
        logs_before = HabitLog.query.filter_by(habit_id=habit.id).count()
        assert logs_before == 2
        
        # Delete habit
        habit_service.delete_habit(habit.id, sample_user)
        
        # Verify logs are deleted
        logs_after = HabitLog.query.filter_by(habit_id=habit.id).count()
        assert logs_after == 0
    
    def test_get_user_habits(self, habit_service, sample_user):
        """Test getting user habits"""
        # Create multiple habits
        habit1_data = {
            'name': 'Habit 1',
            'execution_time': 30,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit2_data = {
            'name': 'Habit 2',
            'execution_time': 60,
            'frequency': 14,
            'habit_type': HabitType.PLEASANT
        }
        
        habit1 = habit_service.create_habit(sample_user, habit1_data)
        habit2 = habit_service.create_habit(sample_user, habit2_data)
        
        # Get user habits
        habits = habit_service.get_user_habits(sample_user)
        
        assert len(habits) == 2
        habit_names = [h.name for h in habits]
        assert 'Habit 1' in habit_names
        assert 'Habit 2' in habit_names
    
    def test_get_user_habits_excludes_archived(self, habit_service, sample_user):
        """Test that archived habits are excluded by default"""
        # Create habit
        habit_data = {
            'name': 'To Archive',
            'execution_time': 30,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit = habit_service.create_habit(sample_user, habit_data)
        
        # Archive it
        archived_habit = habit_service.archive_habit(habit.id, sample_user)
        assert archived_habit.is_archived
        
        # Get user habits (should exclude archived)
        habits = habit_service.get_user_habits(sample_user)
        assert len(habits) == 0
        
        # Get user habits including archived
        habits_with_archived = habit_service.get_user_habits(sample_user, include_archived=True)
        assert len(habits_with_archived) == 1
    
    def test_archive_and_restore_habit(self, habit_service, sample_user):
        """Test archiving and restoring habits"""
        # Create habit
        habit_data = {
            'name': 'To Archive',
            'execution_time': 30,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        habit = habit_service.create_habit(sample_user, habit_data)
        assert not habit.is_archived
        
        # Archive habit
        archived_habit = habit_service.archive_habit(habit.id, sample_user)
        assert archived_habit.is_archived
        
        # Restore habit
        restored_habit = habit_service.restore_habit(habit.id, sample_user)
        assert not restored_habit.is_archived
    
    def test_get_habits_by_type(self, habit_service, sample_user):
        """Test getting habits by type"""
        # Create habits of different types
        useful_data = {
            'name': 'Useful Habit',
            'execution_time': 30,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        pleasant_data = {
            'name': 'Pleasant Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.PLEASANT
        }
        
        habit_service.create_habit(sample_user, useful_data)
        habit_service.create_habit(sample_user, pleasant_data)
        
        # Get useful habits
        useful_habits = habit_service.get_habits_by_type(sample_user, 'useful')
        assert len(useful_habits) == 1
        assert useful_habits[0].name == 'Useful Habit'
        
        # Get pleasant habits
        pleasant_habits = habit_service.get_habits_by_type(sample_user, 'pleasant')
        assert len(pleasant_habits) == 1
        assert pleasant_habits[0].name == 'Pleasant Habit'
    
    def test_get_habits_by_invalid_type(self, habit_service, sample_user):
        """Test getting habits with invalid type"""
        with pytest.raises(HabitServiceError) as exc_info:
            habit_service.get_habits_by_type(sample_user, 'invalid_type')
        
        assert 'Invalid habit type' in str(exc_info.value)
    
    def test_create_habit_empty_name_fails(self, habit_service, sample_user):
        """Test that habits with empty names fail validation"""
        habit_data = {
            'name': '',  # Empty name
            'execution_time': 30,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(sample_user, habit_data)
        
        assert any('название' in error.lower() for error in exc_info.value.errors)
    
    def test_create_habit_frequency_too_low_fails(self, habit_service, sample_user):
        """Test that habits with frequency < 7 days fail validation"""
        habit_data = {
            'name': 'Daily Habit',
            'execution_time': 30,
            'frequency': 3,  # Too frequent
            'habit_type': HabitType.USEFUL
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(sample_user, habit_data)
        
        assert any('7 дней' in error for error in exc_info.value.errors)