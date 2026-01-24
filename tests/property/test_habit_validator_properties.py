"""
Property-Based Tests for HabitValidator

Tests universal properties of habit validation system
"""
import pytest
from hypothesis import given, strategies as st
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.validators import HabitValidator
from app.models import HabitType


class TestHabitValidatorProperties:
    """Property-based tests for HabitValidator"""
    
    @given(st.text(min_size=1, max_size=100))
    def test_validation_result_format_consistency(self, habit_name):
        """
        Feature: habit-tracker-improvements, Property 5: Стандартный формат результатов валидации
        Для любого валидатора в системе, результат проверки должен возвращаться в формате (is_valid: bool, errors: List[str])
        Validates: Requirements 3.4
        """
        validator = HabitValidator()
        data = {
            'name': habit_name,
            'execution_time': 60,
            'frequency': 7,
            'habit_type': 'useful'
        }
        
        result = validator.validate(data)
        
        # Property: Result must always have is_valid (bool) and errors (List[str])
        assert hasattr(result, 'is_valid')
        assert isinstance(result.is_valid, bool)
        assert hasattr(result, 'errors')
        assert isinstance(result.errors, list)
        assert all(isinstance(error, str) for error in result.errors)
    
    @given(st.text(min_size=1, max_size=200))
    def test_pleasant_habit_reward_rejection(self, reward_text):
        """
        Feature: habit-tracker-improvements, Property 4: Описательные сообщения об ошибках валидации
        Для любых невалидных данных, система должна возвращать конкретные и понятные описания обнаруженных проблем
        Validates: Requirements 2.5
        """
        validator = HabitValidator()
        data = {
            'name': 'Pleasant Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': 'pleasant',
            'reward': reward_text
        }
        
        result = validator.validate(data)
        
        # Property: Pleasant habits with rewards should always be invalid with descriptive error
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("приятная привычка" in error.lower() and "вознаграждение" in error.lower() 
                  for error in result.errors)
    
    @given(st.integers(min_value=1, max_value=1000))
    def test_pleasant_habit_related_habit_rejection(self, related_habit_id):
        """
        Feature: habit-tracker-improvements, Property 4: Описательные сообщения об ошибках валидации
        Для любых невалидных данных, система должна возвращать конкретные и понятные описания обнаруженных проблем
        Validates: Requirements 2.5
        """
        validator = HabitValidator()
        data = {
            'name': 'Pleasant Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': 'pleasant',
            'related_habit_id': related_habit_id
        }
        
        result = validator.validate(data)
        
        # Property: Pleasant habits with related habits should always be invalid with descriptive error
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("приятная привычка" in error.lower() and "связана" in error.lower() 
                  for error in result.errors)
    
    @given(st.text(min_size=1, max_size=200), st.integers(min_value=1, max_value=1000))
    def test_useful_habit_reward_and_related_habit_conflict(self, reward_text, related_habit_id):
        """
        Feature: habit-tracker-improvements, Property 6: Конкретные описания ошибок валидации
        Для любых ошибок валидации, система должна включать конкретное описание проблемы, а не общие сообщения
        Validates: Requirements 3.5
        """
        validator = HabitValidator()
        data = {
            'name': 'Useful Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': 'useful',
            'reward': reward_text,
            'related_habit_id': related_habit_id
        }
        
        result = validator.validate(data)
        
        # Property: Useful habits with both reward and related habit should be invalid with specific error
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("либо вознаграждение, либо связанную привычку" in error.lower() 
                  for error in result.errors)
    
    @given(st.text(min_size=201, max_size=500))
    def test_reward_length_validation_with_descriptive_error(self, long_reward):
        """
        Feature: habit-tracker-improvements, Property 4: Описательные сообщения об ошибках валидации
        Для любых невалидных данных, система должна возвращать конкретные и понятные описания обнаруженных проблем
        Validates: Requirements 2.5
        """
        validator = HabitValidator()
        data = {
            'name': 'Useful Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': 'useful',
            'reward': long_reward
        }
        
        result = validator.validate(data)
        
        # Property: Long rewards should be invalid with descriptive error about length
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("200 символов" in error for error in result.errors)
    
    @given(st.sampled_from(['', '   ', '\t\n']))
    def test_empty_name_validation_with_descriptive_error(self, empty_name):
        """
        Feature: habit-tracker-improvements, Property 4: Описательные сообщения об ошибках валидации
        Для любых невалидных данных, система должна возвращать конкретные и понятные описания обнаруженных проблем
        Validates: Requirements 2.5
        """
        validator = HabitValidator()
        data = {
            'name': empty_name,
            'execution_time': 60,
            'frequency': 7,
            'habit_type': 'useful'
        }
        
        result = validator.validate(data)
        
        # Property: Empty names should be invalid with descriptive error
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("название" in error.lower() for error in result.errors)
    
    @given(st.sampled_from(['invalid_type', 'wrong', 123, None]))
    def test_invalid_habit_type_with_descriptive_error(self, invalid_type):
        """
        Feature: habit-tracker-improvements, Property 4: Описательные сообщения об ошибках валидации
        Для любых невалидных данных, система должна возвращать конкретные и понятные описания обнаруженных проблем
        Validates: Requirements 2.5
        """
        validator = HabitValidator()
        data = {
            'name': 'Test Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': invalid_type
        }
        
        result = validator.validate(data)
        
        # Property: Invalid habit types should be invalid with descriptive error
        if invalid_type is not None:
            assert not result.is_valid
            assert len(result.errors) > 0
            assert any("тип привычки" in error.lower() for error in result.errors)