"""
Property-Based Tests for Updated Habit Model

Tests universal properties of default value assignment in the updated habit model
"""
import pytest
from hypothesis import given, strategies as st, assume
import sys
import os
import tempfile
import sqlite3
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import the updated models from app.py by executing it
import importlib.util
import types

def load_app_module():
    """Load the app.py module dynamically"""
    app_path = os.path.join(os.path.dirname(__file__), '..', '..', 'app.py')
    spec = importlib.util.spec_from_file_location("app_module", app_path)
    app_module = importlib.util.module_from_spec(spec)
    
    # Set up required environment
    os.environ.setdefault('FLASK_ENV', 'testing')
    
    # Execute the module
    spec.loader.exec_module(app_module)
    return app_module

class TestUpdatedHabitProperties:
    """Property-based tests for updated Habit model with new fields"""
    
    def setup_method(self):
        """Set up test environment for each test method"""
        # Load the app module
        self.app_module = load_app_module()
        self.app = self.app_module.app
        self.db = self.app_module.db
        self.User = self.app_module.User
        self.Habit = self.app_module.Habit
        
        # Set up test database
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        
        with self.app.app_context():
            self.db.create_all()
            
            # Create a test user
            test_user = self.User(email='test@example.com', name='Test User')
            self.db.session.add(test_user)
            self.db.session.commit()
            self.test_user_id = test_user.id
    
    def teardown_method(self):
        """Clean up after each test method"""
        with self.app.app_context():
            self.db.session.remove()
            self.db.drop_all()
    
    @given(st.text(min_size=1, max_size=100))
    def test_default_execution_time_property(self, habit_name):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        assume(habit_name.strip())  # Ensure non-empty name
        
        with self.app.app_context():
            # Create habit without specifying execution_time
            habit = self.Habit(
                user_id=self.test_user_id,
                name=habit_name.strip()
            )
            self.db.session.add(habit)
            self.db.session.commit()
            
            # Property: execution_time should default to 60 seconds
            assert habit.execution_time == 60
            
            # Verify in database
            saved_habit = self.db.session.get(self.Habit, habit.id)
            assert saved_habit.execution_time == 60
    
    @given(st.text(min_size=1, max_size=100))
    def test_default_frequency_property(self, habit_name):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        assume(habit_name.strip())  # Ensure non-empty name
        
        with self.app.app_context():
            # Create habit without specifying frequency
            habit = self.Habit(
                user_id=self.test_user_id,
                name=habit_name.strip()
            )
            self.db.session.add(habit)
            self.db.session.commit()
            
            # Property: frequency should default to 1 (daily)
            assert habit.frequency == 1
            
            # Verify in database
            saved_habit = self.db.session.get(self.Habit, habit.id)
            assert saved_habit.frequency == 1
    
    @given(st.text(min_size=1, max_size=100))
    def test_default_habit_type_property(self, habit_name):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        assume(habit_name.strip())  # Ensure non-empty name
        
        with self.app.app_context():
            # Create habit without specifying habit_type
            habit = self.Habit(
                user_id=self.test_user_id,
                name=habit_name.strip()
            )
            self.db.session.add(habit)
            self.db.session.commit()
            
            # Property: habit_type should default to 'useful'
            assert habit.habit_type == 'useful'
            
            # Verify in database
            saved_habit = self.db.session.get(self.Habit, habit.id)
            assert saved_habit.habit_type == 'useful'
    
    @given(st.text(min_size=1, max_size=100))
    def test_business_rule_validation_property(self, habit_name):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        assume(habit_name.strip())  # Ensure non-empty name
        
        with self.app.app_context():
            # Create habit with pleasant type and reward (should be invalid)
            habit = self.Habit(
                user_id=self.test_user_id,
                name=habit_name.strip(),
                habit_type='pleasant',
                reward='Some reward'
            )
            
            # Property: Business rule validation should catch this error
            is_valid, errors = habit.validate_business_rules()
            assert not is_valid
            assert len(errors) > 0
            assert any('приятная привычка' in error.lower() for error in errors)
    
    @given(st.integers(min_value=121, max_value=1000))
    def test_execution_time_validation_property(self, execution_time):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        with self.app.app_context():
            # Create habit with execution time > 120 seconds
            habit = self.Habit(
                user_id=self.test_user_id,
                name='Test Habit',
                execution_time=execution_time
            )
            
            # Property: Should be invalid due to execution time limit
            is_valid, errors = habit.validate_business_rules()
            assert not is_valid
            assert len(errors) > 0
            assert any('120 секунд' in error for error in errors)
    
    @given(st.integers(min_value=1, max_value=6))
    def test_frequency_validation_property(self, frequency):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        with self.app.app_context():
            # Create habit with frequency < 7 days
            habit = self.Habit(
                user_id=self.test_user_id,
                name='Test Habit',
                frequency=frequency
            )
            
            # Property: Should be invalid due to frequency limit
            is_valid, errors = habit.validate_business_rules()
            assert not is_valid
            assert len(errors) > 0
            assert any('7 дней' in error for error in errors)
    
    @given(st.text(min_size=1, max_size=100))
    def test_new_methods_property(self, habit_name):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        assume(habit_name.strip())  # Ensure non-empty name
        
        with self.app.app_context():
            # Create habit with defaults
            habit = self.Habit(
                user_id=self.test_user_id,
                name=habit_name.strip()
            )
            self.db.session.add(habit)
            self.db.session.commit()
            
            # Property: New methods should work correctly with defaults
            assert habit.is_useful_habit() == True
            assert habit.is_pleasant_habit() == False
            assert habit.has_reward() == False
            assert habit.has_related_habit() == False
            assert habit.get_execution_time_minutes() == 1.0
            assert habit.get_frequency_description() == "Ежедневно"
            assert habit.can_be_completed_today() == True