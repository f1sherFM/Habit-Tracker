"""
Property-Based Tests for Validators

Tests universal properties of validation system
"""
import pytest
from hypothesis import given, strategies as st
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.validators import TimeValidator, FrequencyValidator


class TestValidatorProperties:
    """Property-based tests for validator system"""
    
    @given(st.integers(min_value=121, max_value=10000))
    def test_time_validation_rejects_over_120_seconds(self, execution_time):
        """
        Feature: habit-tracker-improvements, Property 3: Комплексная валидация привычек
        Для любого времени выполнения больше 120 секунд система должна отклонить валидацию
        Validates: Requirements 2.1
        """
        validator = TimeValidator()
        result = validator.validate_execution_time(execution_time)
        
        # Property: Any execution time > 120 seconds should be invalid
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("120 секунд" in error for error in result.errors)
    
    @given(st.integers(min_value=1, max_value=120))
    def test_time_validation_accepts_valid_times(self, execution_time):
        """
        Feature: habit-tracker-improvements, Property 3: Комплексная валидация привычек
        Для любого времени выполнения от 1 до 120 секунд система должна принять валидацию
        Validates: Requirements 2.1
        """
        validator = TimeValidator()
        result = validator.validate_execution_time(execution_time)
        
        # Property: Any execution time 1-120 seconds should be valid
        assert result.is_valid
        assert len(result.errors) == 0
    
    @given(st.integers(min_value=1, max_value=6))
    def test_frequency_validation_rejects_under_7_days(self, frequency):
        """
        Feature: habit-tracker-improvements, Property 3: Комплексная валидация привычек
        Для любой периодичности чаще раза в 7 дней система должна отклонить валидацию
        Validates: Requirements 2.2
        """
        validator = FrequencyValidator()
        result = validator.validate_frequency(frequency)
        
        # Property: Any frequency < 7 days should be invalid
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("7 дней" in error for error in result.errors)
    
    @given(st.integers(min_value=7, max_value=365))
    def test_frequency_validation_accepts_valid_frequencies(self, frequency):
        """
        Feature: habit-tracker-improvements, Property 3: Комплексная валидация привычек
        Для любой периодичности от 7 дней и больше система должна принять валидацию
        Validates: Requirements 2.2
        """
        validator = FrequencyValidator()
        result = validator.validate_frequency(frequency)
        
        # Property: Any frequency >= 7 days should be valid
        assert result.is_valid
        assert len(result.errors) == 0
    
    @given(st.integers(max_value=0))
    def test_time_validation_rejects_non_positive_values(self, execution_time):
        """
        Feature: habit-tracker-improvements, Property 3: Комплексная валидация привычек
        Для любого неположительного времени выполнения система должна отклонить валидацию
        Validates: Requirements 2.1
        """
        validator = TimeValidator()
        result = validator.validate_execution_time(execution_time)
        
        # Property: Any non-positive execution time should be invalid
        assert not result.is_valid
        assert len(result.errors) > 0
    
    @given(st.integers(max_value=0))
    def test_frequency_validation_rejects_non_positive_values(self, frequency):
        """
        Feature: habit-tracker-improvements, Property 3: Комплексная валидация привычек
        Для любой неположительной периодичности система должна отклонить валидацию
        Validates: Requirements 2.2
        """
        validator = FrequencyValidator()
        result = validator.validate_frequency(frequency)
        
        # Property: Any non-positive frequency should be invalid
        assert not result.is_valid
        assert len(result.errors) > 0