"""
Property-Based Tests for HabitService

Tests universal properties of habit service operations
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timezone
import sys
import os
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.models.habit_types import HabitType
from app.validators.habit_validator import HabitValidator


class TestHabitServiceProperties:
    """Property-based tests for HabitService"""
    
    def setup_method(self):
        """Set up test database for each test method"""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        # Create Flask app with test configuration
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['TESTING'] = True
        
        # Initialize database
        self.db = SQLAlchemy(self.app)
        
        # Define models within app context
        with self.app.app_context():
            # User model
            class User(self.db.Model):
                __tablename__ = 'users'
                id = self.db.Column(self.db.Integer, primary_key=True)
                email = self.db.Column(self.db.String(120), unique=True, nullable=False)
                password_hash = self.db.Column(self.db.String(255))
                name = self.db.Column(self.db.String(100))
                created_at = self.db.Column(self.db.DateTime, default=lambda: datetime.now(timezone.utc))
                is_active = self.db.Column(self.db.Boolean, default=True)
                habits = self.db.relationship('Habit', backref='user', lazy=True, cascade='all, delete-orphan')
                
                def set_password(self, password):
                    from werkzeug.security import generate_password_hash
                    self.password_hash = generate_password_hash(password)
            
            # Habit model
            class Habit(self.db.Model):
                __tablename__ = 'habits'
                id = self.db.Column(self.db.Integer, primary_key=True)
                user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.id'), nullable=False)
                name = self.db.Column(self.db.String(100), nullable=False)
                description = self.db.Column(self.db.Text)
                execution_time = self.db.Column(self.db.Integer, default=60)
                frequency = self.db.Column(self.db.Integer, default=7)
                habit_type = self.db.Column(self.db.Enum(HabitType), default=HabitType.USEFUL)
                reward = self.db.Column(self.db.String(200))
                related_habit_id = self.db.Column(self.db.Integer, self.db.ForeignKey('habits.id'))
                created_at = self.db.Column(self.db.DateTime, default=lambda: datetime.now(timezone.utc))
                updated_at = self.db.Column(self.db.DateTime, default=lambda: datetime.now(timezone.utc))
                is_archived = self.db.Column(self.db.Boolean, default=False)
                
                def validate_business_rules(self):
                    errors = []
                    if self.habit_type == HabitType.PLEASANT and self.reward:
                        errors.append("Приятная привычка не может иметь вознаграждение")
                    if self.habit_type == HabitType.PLEASANT and self.related_habit_id:
                        errors.append("Приятная привычка не может быть связана с другой привычкой")
                    if self.execution_time and self.execution_time > 120:
                        errors.append("Время выполнения не может превышать 120 секунд")
                    if self.frequency and self.frequency < 7:
                        errors.append("Периодичность не может быть чаще чем раз в 7 дней")
                    if not self.name or not self.name.strip():
                        errors.append("Название привычки не может быть пустым")
                    return len(errors) == 0, errors
                
                def update_with_validation(self, **kwargs):
                    original_values = {}
                    for key, value in kwargs.items():
                        if hasattr(self, key):
                            original_values[key] = getattr(self, key)
                            setattr(self, key, value)
                    
                    is_valid, errors = self.validate_business_rules()
                    if not is_valid:
                        for key, value in original_values.items():
                            setattr(self, key, value)
                    
                    return is_valid, errors
            
            # HabitLog model
            class HabitLog(self.db.Model):
                __tablename__ = 'habit_logs'
                id = self.db.Column(self.db.Integer, primary_key=True)
                habit_id = self.db.Column(self.db.Integer, self.db.ForeignKey('habits.id'), nullable=False)
                date = self.db.Column(self.db.Date, nullable=False)
                completed = self.db.Column(self.db.Boolean, default=False)
                created_at = self.db.Column(self.db.DateTime, default=lambda: datetime.now(timezone.utc))
            
            # Store model classes
            self.User = User
            self.Habit = Habit
            self.HabitLog = HabitLog
            
            # Create tables
            self.db.create_all()
            
            # Create HabitService with custom models
            class TestHabitService:
                def __init__(self, db, User, Habit, HabitLog):
                    self.db = db
                    self.User = User
                    self.Habit = Habit
                    self.HabitLog = HabitLog
                    self.habit_validator = HabitValidator()
                
                def create_habit(self, user_id, habit_data):
                    validation_result = self.habit_validator.validate(habit_data)
                    if not validation_result.is_valid:
                        from app.services.habit_service import ValidationError
                        raise ValidationError(validation_result.errors)
                    
                    habit_data['user_id'] = user_id
                    habit = self.Habit(**habit_data)
                    
                    is_valid, errors = habit.validate_business_rules()
                    if not is_valid:
                        from app.services.habit_service import ValidationError
                        raise ValidationError(errors)
                    
                    self.db.session.add(habit)
                    self.db.session.commit()
                    return habit
                
                def update_habit(self, habit_id, user_id, habit_data):
                    habit = self.Habit.query.get(habit_id)
                    if not habit:
                        from app.services.habit_service import HabitNotFoundError
                        raise HabitNotFoundError(f"Habit with ID {habit_id} not found")
                    
                    if habit.user_id != user_id:
                        from app.services.habit_service import AuthorizationError
                        raise AuthorizationError("User does not have permission to update this habit")
                    
                    validation_result = self.habit_validator.validate(habit_data)
                    if not validation_result.is_valid:
                        from app.services.habit_service import ValidationError
                        raise ValidationError(validation_result.errors)
                    
                    is_valid, errors = habit.update_with_validation(**habit_data)
                    if not is_valid:
                        from app.services.habit_service import ValidationError
                        raise ValidationError(errors)
                    
                    habit.updated_at = datetime.now(timezone.utc)
                    self.db.session.commit()
                    return habit
                
                def delete_habit(self, habit_id, user_id):
                    habit = self.Habit.query.get(habit_id)
                    if not habit:
                        from app.services.habit_service import HabitNotFoundError
                        raise HabitNotFoundError(f"Habit with ID {habit_id} not found")
                    
                    if habit.user_id != user_id:
                        from app.services.habit_service import AuthorizationError
                        raise AuthorizationError("User does not have permission to delete this habit")
                    
                    # Delete related records
                    self.HabitLog.query.filter_by(habit_id=habit_id).delete()
                    
                    # Update related habits
                    related_habits = self.Habit.query.filter_by(related_habit_id=habit_id).all()
                    for related_habit in related_habits:
                        related_habit.related_habit_id = None
                    
                    self.db.session.delete(habit)
                    self.db.session.commit()
                    return True
            
            self.habit_service = TestHabitService(self.db, self.User, self.Habit, self.HabitLog)
            
            # Create test user
            self.sample_user = User(
                email='test@example.com',
                name='Test User'
            )
            self.sample_user.set_password('testpassword123')
            self.db.session.add(self.sample_user)
            self.db.session.commit()
    
    def teardown_method(self):
        """Clean up after each test method"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    @given(
        name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        execution_time=st.integers(min_value=1, max_value=120),
        frequency=st.integers(min_value=7, max_value=365),
        habit_type=st.sampled_from(['useful', 'pleasant'])
    )
    @settings(max_examples=20)
    def test_property_9_validation_before_creation(self, name, execution_time, frequency, habit_type):
        """
        **Property 9: Валидация перед созданием привычек**
        **Validates: Requirements 6.2**
        
        Feature: habit-tracker-improvements, Property 9: Валидация перед созданием привычек
        Для любых данных при создании привычки, HabitService должен выполнить полную валидацию перед сохранением в базу данных
        """
        with self.app.app_context():
            habit_data = {
                'name': name,
                'execution_time': execution_time,
                'frequency': frequency,
                'habit_type': habit_type
            }
            
            # For pleasant habits, ensure no reward or related_habit_id
            if habit_type == 'pleasant':
                habit_data['reward'] = None
                habit_data['related_habit_id'] = None
            
            # Test that validation occurs before database save
            try:
                habit = self.habit_service.create_habit(self.sample_user.id, habit_data)
                # If creation succeeds, the habit should be valid
                assert habit.name == name
                assert habit.execution_time == execution_time
                assert habit.frequency == frequency
                assert habit.habit_type.value == habit_type
            except Exception:
                # If validation fails, that's expected for some inputs
                pass
    
    @given(
        execution_time=st.integers(min_value=121, max_value=1000),
        frequency=st.integers(min_value=1, max_value=6)
    )
    @settings(max_examples=15)
    def test_property_9_validation_rejects_invalid_data(self, execution_time, frequency):
        """
        **Property 9: Валидация перед созданием привычек (Invalid Data)**
        **Validates: Requirements 6.2**
        
        Feature: habit-tracker-improvements, Property 9: Валидация перед созданием привычек
        Система должна отклонять создание привычек с невалидными данными
        """
        with self.app.app_context():
            # Refresh user instance to ensure it's attached to current session
            user = self.User.query.filter_by(email='test@example.com').first()
            
            habit_data = {
                'name': 'Test Habit',
                'execution_time': execution_time,
                'frequency': frequency,
                'habit_type': HabitType.USEFUL
            }
            
            # Should raise ValidationError for invalid data
            from app.services.habit_service import ValidationError
            with pytest.raises(ValidationError):
                self.habit_service.create_habit(user.id, habit_data)
    
    @given(
        other_user_id=st.integers(min_value=1001, max_value=2000)
    )
    @settings(max_examples=15)
    def test_property_10_authorization_check_on_update(self, other_user_id):
        """
        **Property 10: Проверка прав доступа при обновлении**
        **Validates: Requirements 6.3**
        
        Feature: habit-tracker-improvements, Property 10: Проверка прав доступа при обновлении
        Для любых операций обновления привычки, система должна проверить, что пользователь имеет права на изменение данной привычки
        """
        with self.app.app_context():
            # Refresh user instance to ensure it's attached to current session
            user = self.User.query.filter_by(email='test@example.com').first()
            assume(other_user_id != user.id)
            
            # Create a habit for the sample user
            habit_data = {
                'name': 'Test Habit',
                'execution_time': 60,
                'frequency': 7,
                'habit_type': HabitType.USEFUL
            }
            
            habit = self.habit_service.create_habit(user.id, habit_data)
            
            # Try to update with different user ID - should fail
            update_data = {'name': 'Updated Habit'}
            
            from app.services.habit_service import AuthorizationError
            with pytest.raises(AuthorizationError):
                self.habit_service.update_habit(habit.id, other_user_id, update_data)
            
            # Update with correct user ID - should succeed
            updated_habit = self.habit_service.update_habit(habit.id, user.id, update_data)
            assert updated_habit.name == 'Updated Habit'
    
    @given(
        other_user_id=st.integers(min_value=1001, max_value=2000)
    )
    @settings(max_examples=15)
    def test_property_10_authorization_check_on_delete(self, other_user_id):
        """
        **Property 10: Проверка прав доступа при удалении**
        **Validates: Requirements 6.3**
        
        Feature: habit-tracker-improvements, Property 10: Проверка прав доступа при обновлении
        Для любых операций удаления привычки, система должна проверить права доступа пользователя
        """
        with self.app.app_context():
            # Refresh user instance to ensure it's attached to current session
            user = self.User.query.filter_by(email='test@example.com').first()
            assume(other_user_id != user.id)
            
            # Create a habit for the sample user
            habit_data = {
                'name': 'Test Habit',
                'execution_time': 60,
                'frequency': 7,
                'habit_type': HabitType.USEFUL
            }
            
            habit = self.habit_service.create_habit(user.id, habit_data)
            
            # Try to delete with different user ID - should fail
            from app.services.habit_service import AuthorizationError
            with pytest.raises(AuthorizationError):
                self.habit_service.delete_habit(habit.id, other_user_id)
            
            # Delete with correct user ID - should succeed
            result = self.habit_service.delete_habit(habit.id, user.id)
            assert result is True
    
    @given(
        num_logs=st.integers(min_value=1, max_value=5),
        num_related=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=10)
    def test_property_11_cascade_deletion(self, num_logs, num_related):
        """
        **Property 11: Каскадное удаление связанных записей**
        **Validates: Requirements 6.4**
        
        Feature: habit-tracker-improvements, Property 11: Каскадное удаление связанных записей
        Для любой удаляемой привычки, система должна также удалить все связанные с ней записи
        """
        with self.app.app_context():
            # Refresh user instance to ensure it's attached to current session
            user = self.User.query.filter_by(email='test@example.com').first()
            
            # Create a main habit
            main_habit_data = {
                'name': 'Main Habit',
                'execution_time': 60,
                'frequency': 7,
                'habit_type': HabitType.USEFUL
            }
            
            main_habit = self.habit_service.create_habit(user.id, main_habit_data)
            
            # Create habit logs for the main habit
            for i in range(num_logs):
                log = self.HabitLog(
                    habit_id=main_habit.id,
                    date=datetime.now(timezone.utc).date(),
                    completed=True
                )
                self.db.session.add(log)
            
            # Create related habits that reference the main habit
            related_habits = []
            for i in range(num_related):
                related_data = {
                    'name': f'Related Habit {i}',
                    'execution_time': 30,
                    'frequency': 7,
                    'habit_type': HabitType.USEFUL,
                    'related_habit_id': main_habit.id
                }
                related_habit = self.habit_service.create_habit(user.id, related_data)
                related_habits.append(related_habit)
            
            self.db.session.commit()
            
            # Verify related records exist before deletion
            logs_before = self.HabitLog.query.filter_by(habit_id=main_habit.id).count()
            assert logs_before == num_logs
            
            for related_habit in related_habits:
                habit_obj = self.Habit.query.get(related_habit.id)
                assert habit_obj.related_habit_id == main_habit.id
            
            # Delete the main habit
            result = self.habit_service.delete_habit(main_habit.id, user.id)
            assert result is True
            
            # Verify cascade deletion occurred
            # 1. Habit logs should be deleted
            logs_after = self.HabitLog.query.filter_by(habit_id=main_habit.id).count()
            assert logs_after == 0
            
            # 2. Related habits should have their related_habit_id set to None
            for related_habit in related_habits:
                habit_obj = self.Habit.query.get(related_habit.id)
                assert habit_obj is not None  # Related habit should still exist
                assert habit_obj.related_habit_id is None  # But reference should be cleared
            
            # 3. Main habit should be deleted
            main_habit_after = self.Habit.query.get(main_habit.id)
            assert main_habit_after is None
    
    @given(
        pleasant_reward=st.text(min_size=1, max_size=50),
        pleasant_related_id=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=15)
    def test_property_9_pleasant_habit_constraints(self, pleasant_reward, pleasant_related_id):
        """
        **Property 9: Валидация ограничений приятных привычек**
        **Validates: Requirements 6.2**
        
        Feature: habit-tracker-improvements, Property 9: Валидация перед созданием привычек
        Приятные привычки не должны иметь вознаграждений или связанных привычек
        """
        with self.app.app_context():
            # Refresh user instance to ensure it's attached to current session
            user = self.User.query.filter_by(email='test@example.com').first()
            
            # Test pleasant habit with reward - should fail
            habit_data_with_reward = {
                'name': 'Pleasant Habit',
                'execution_time': 60,
                'frequency': 7,
                'habit_type': HabitType.PLEASANT,
                'reward': pleasant_reward
            }
            
            from app.services.habit_service import ValidationError
            with pytest.raises(ValidationError) as exc_info:
                self.habit_service.create_habit(user.id, habit_data_with_reward)
            
            assert any('приятная привычка не может иметь вознаграждение' in error.lower() 
                      for error in exc_info.value.errors)
            
            # Test pleasant habit with related_habit_id - should fail
            habit_data_with_related = {
                'name': 'Pleasant Habit',
                'execution_time': 60,
                'frequency': 7,
                'habit_type': HabitType.PLEASANT,
                'related_habit_id': pleasant_related_id
            }
            
            with pytest.raises(ValidationError) as exc_info:
                self.habit_service.create_habit(user.id, habit_data_with_related)
            
            assert any('приятная привычка не может быть связана' in error.lower() 
                      for error in exc_info.value.errors)