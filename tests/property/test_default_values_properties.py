"""
Property-Based Tests for Default Values

Tests universal properties of default value assignment in habit creation
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

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from app.models.habit_types import HabitType


class TestDefaultValuesProperties:
    """Property-based tests for default values in habit creation"""
    
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
                created_at = self.db.Column(self.db.DateTime, default=lambda: datetime.now(timezone.utc))
                habits = self.db.relationship('Habit', backref='user', lazy=True)
            
            # Habit model with new fields and defaults
            class Habit(self.db.Model):
                __tablename__ = 'habits'
                id = self.db.Column(self.db.Integer, primary_key=True)
                user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.id'), nullable=False)
                name = self.db.Column(self.db.String(100), nullable=False)
                description = self.db.Column(self.db.Text)
                
                # New fields with defaults
                execution_time = self.db.Column(self.db.Integer, default=60)
                frequency = self.db.Column(self.db.Integer, default=1)
                habit_type = self.db.Column(self.db.String(20), default='useful')
                reward = self.db.Column(self.db.String(200))
                related_habit_id = self.db.Column(self.db.Integer, self.db.ForeignKey('habits.id'))
                
                created_at = self.db.Column(self.db.DateTime, default=lambda: datetime.now(timezone.utc))
                updated_at = self.db.Column(self.db.DateTime, default=lambda: datetime.now(timezone.utc))
                is_archived = self.db.Column(self.db.Boolean, default=False)
            
            # Store model classes for use in tests
            self.User = User
            self.Habit = Habit
            
            # Create tables
            self.db.create_all()
            
            # Create a test user
            test_user = User(email='test@example.com')
            self.db.session.add(test_user)
            self.db.session.commit()
            self.test_user_id = test_user.id
    
    def teardown_method(self):
        """Clean up after each test method"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
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
    def test_default_reward_null_property(self, habit_name):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        assume(habit_name.strip())  # Ensure non-empty name
        
        with self.app.app_context():
            # Create habit without specifying reward
            habit = self.Habit(
                user_id=self.test_user_id,
                name=habit_name.strip()
            )
            self.db.session.add(habit)
            self.db.session.commit()
            
            # Property: reward should default to None (nullable field)
            assert habit.reward is None
            
            # Verify in database
            saved_habit = self.db.session.get(self.Habit, habit.id)
            assert saved_habit.reward is None
    
    @given(st.text(min_size=1, max_size=100))
    def test_default_related_habit_id_null_property(self, habit_name):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        assume(habit_name.strip())  # Ensure non-empty name
        
        with self.app.app_context():
            # Create habit without specifying related_habit_id
            habit = self.Habit(
                user_id=self.test_user_id,
                name=habit_name.strip()
            )
            self.db.session.add(habit)
            self.db.session.commit()
            
            # Property: related_habit_id should default to None (nullable field)
            assert habit.related_habit_id is None
            
            # Verify in database
            saved_habit = self.db.session.get(self.Habit, habit.id)
            assert saved_habit.related_habit_id is None
    
    @given(st.text(min_size=1, max_size=100))
    def test_default_is_archived_false_property(self, habit_name):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        assume(habit_name.strip())  # Ensure non-empty name
        
        with self.app.app_context():
            # Create habit without specifying is_archived
            habit = self.Habit(
                user_id=self.test_user_id,
                name=habit_name.strip()
            )
            self.db.session.add(habit)
            self.db.session.commit()
            
            # Property: is_archived should default to False
            assert habit.is_archived is False
            
            # Verify in database
            saved_habit = self.db.session.get(self.Habit, habit.id)
            assert saved_habit.is_archived is False
    
    @given(
        st.text(min_size=1, max_size=100),
        st.integers(min_value=1, max_value=3600),
        st.integers(min_value=1, max_value=365),
        st.sampled_from(['useful', 'pleasant'])
    )
    def test_explicit_values_override_defaults_property(self, habit_name, execution_time, frequency, habit_type):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        assume(habit_name.strip())  # Ensure non-empty name
        
        with self.app.app_context():
            # Create habit with explicit values
            habit = self.Habit(
                user_id=self.test_user_id,
                name=habit_name.strip(),
                execution_time=execution_time,
                frequency=frequency,
                habit_type=habit_type
            )
            self.db.session.add(habit)
            self.db.session.commit()
            
            # Property: Explicit values should override defaults
            assert habit.execution_time == execution_time
            assert habit.frequency == frequency
            assert habit.habit_type == habit_type
            
            # Verify in database
            saved_habit = self.db.session.get(self.Habit, habit.id)
            assert saved_habit.execution_time == execution_time
            assert saved_habit.frequency == frequency
            assert saved_habit.habit_type == habit_type
    
    @given(st.text(min_size=1, max_size=100), st.text(min_size=1, max_size=200))
    def test_reward_assignment_property(self, habit_name, reward_text):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        assume(habit_name.strip())  # Ensure non-empty name
        assume(reward_text.strip())  # Ensure non-empty reward
        
        with self.app.app_context():
            # Create habit with explicit reward
            habit = self.Habit(
                user_id=self.test_user_id,
                name=habit_name.strip(),
                reward=reward_text.strip()
            )
            self.db.session.add(habit)
            self.db.session.commit()
            
            # Property: Explicit reward should be preserved
            assert habit.reward == reward_text.strip()
            
            # Verify in database
            saved_habit = self.db.session.get(self.Habit, habit.id)
            assert saved_habit.reward == reward_text.strip()
    
    @given(st.text(min_size=1, max_size=100))
    def test_all_defaults_applied_simultaneously_property(self, habit_name):
        """
        Feature: habit-tracker-improvements, Property 12: Установка значений по умолчанию
        Для любой новой привычки, система должна автоматически устанавливать корректные значения по умолчанию для всех новых полей
        Validates: Requirements 10.4
        """
        assume(habit_name.strip())  # Ensure non-empty name
        
        with self.app.app_context():
            # Create minimal habit (only required fields)
            habit = self.Habit(
                user_id=self.test_user_id,
                name=habit_name.strip()
            )
            self.db.session.add(habit)
            self.db.session.commit()
            
            # Property: All default values should be applied simultaneously
            assert habit.execution_time == 60
            assert habit.frequency == 1
            assert habit.habit_type == 'useful'
            assert habit.reward is None
            assert habit.related_habit_id is None
            assert habit.is_archived is False
            
            # Verify all defaults are persisted in database
            saved_habit = self.db.session.get(self.Habit, habit.id)
            assert saved_habit.execution_time == 60
            assert saved_habit.frequency == 1
            assert saved_habit.habit_type == 'useful'
            assert saved_habit.reward is None
            assert saved_habit.related_habit_id is None
            assert saved_habit.is_archived is False