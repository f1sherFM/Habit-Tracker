"""
Property Tests for Validator Usage

Tests Property 2: Use of validators for data validation
**Validates: Requirements 1.4**
"""
import pytest
import os
from unittest.mock import patch
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from app import create_app, db
from app.models import get_models
from app.models.habit_types import HabitType
from app.services.habit_service import HabitService
from app.services.user_service import UserService
from app.validators.habit_validator import HabitValidator
from app.validators.time_validator import TimeValidator
from app.validators.frequency_validator import FrequencyValidator
from app.exceptions import ValidationError


class TestValidatorUsageProperties:
    """Property tests for validator usage across the system"""
    
    @pytest.fixture
    def app(self):
        """Create test application"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-for-property-tests-that-is-long-enough',
            'FLASK_ENV': 'testing',
            'DATABASE_URL': 'sqlite:///:memory:'
        }):
            app = create_app('testing')
            with app.app_context():
                db.create_all()
                yield app
                db.drop_all()
    
    @pytest.fixture
    def models(self, app):
        """Get model classes"""
        return get_models()
    
    @pytest.fixture
    def services(self, app, models):
        """Create service instances with validators"""
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
    
    @given(
        execution_time=st.integers(min_value=1, max_value=200),
        frequency=st.integers(min_value=1, max_value=30),
        habit_type=st.sampled_from([HabitType.USEFUL, HabitType.PLEASANT])
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_habit_service_always_uses_validators_for_creation(self, app, models, services, test_user, execution_time, frequency, habit_type):
        """
        Feature: habit-tracker-improvements, Property 2: Использование валидаторов для проверки данных
        
        For any habit creation data, the HabitService must use separate validator classes
        rather than inline validation logic
        """
        habit_service = services['habit_service']
        
        # Create habit data
        habit_data = {
            'name': 'Test Habit',
            'execution_time': execution_time,
            'frequency': frequency,
            'habit_type': habit_type
        }
        
        # Add reward only for useful habits to avoid validation conflicts
        if habit_type == HabitType.USEFUL:
            habit_data['reward'] = 'Test Reward'
        
        try:
            # Attempt to create habit
            habit = habit_service.create_habit(test_user.id, habit_data)
            
            # If creation succeeded, verify the habit was created with validated data
            assert habit is not None
            assert habit.name == 'Test Habit'
            assert habit.execution_time == execution_time
            assert habit.frequency == frequency
            assert habit.habit_type == habit_type
            
            # Verify that validation was applied (execution_time <= 120, frequency >= 7)
            if execution_time <= 120 and frequency >= 7:
                # Should succeed with valid data
                assert habit.execution_time <= 120
                assert habit.frequency >= 7
            else:
                # Should not reach here with invalid data
                pytest.fail("Invalid data should have been rejected by validators")
                
        except ValidationError as e:
            # If validation failed, verify it was due to validator rules
            assert isinstance(e.errors, list)
            assert len(e.errors) > 0
            
            # Check that validation errors match expected validator behavior
            if execution_time > 120:
                assert any("120 секунд" in error for error in e.errors)
            if frequency < 7:
                assert any("7 дней" in error for error in e.errors)
            if habit_type == HabitType.PLEASANT and 'reward' in habit_data:
                assert any("приятная привычка не может иметь вознаграждение" in error.lower() 
                          for error in e.errors)
    
    @given(
        execution_time=st.integers(min_value=1, max_value=200),
        frequency=st.integers(min_value=1, max_value=30)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_habit_service_always_uses_validators_for_updates(self, app, models, services, test_user, execution_time, frequency):
        """
        Feature: habit-tracker-improvements, Property 2: Использование валидаторов для проверки данных
        
        For any habit update data, the HabitService must use separate validator classes
        rather than inline validation logic
        """
        habit_service = services['habit_service']
        
        # First create a valid habit
        initial_habit_data = {
            'name': 'Initial Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL,
            'reward': 'Initial Reward'
        }
        
        habit = habit_service.create_habit(test_user.id, initial_habit_data)
        
        # Now try to update it
        update_data = {
            'name': 'Updated Habit',
            'execution_time': execution_time,
            'frequency': frequency,
            'habit_type': HabitType.USEFUL,
            'reward': 'Updated Reward'
        }
        
        try:
            # Attempt to update habit
            updated_habit = habit_service.update_habit(habit.id, test_user.id, update_data)
            
            # If update succeeded, verify the habit was updated with validated data
            assert updated_habit is not None
            assert updated_habit.name == 'Updated Habit'
            assert updated_habit.execution_time == execution_time
            assert updated_habit.frequency == frequency
            
            # Verify that validation was applied
            if execution_time <= 120 and frequency >= 7:
                # Should succeed with valid data
                assert updated_habit.execution_time <= 120
                assert updated_habit.frequency >= 7
            else:
                # Should not reach here with invalid data
                pytest.fail("Invalid data should have been rejected by validators")
                
        except ValidationError as e:
            # If validation failed, verify it was due to validator rules
            assert isinstance(e.errors, list)
            assert len(e.errors) > 0
            
            # Check that validation errors match expected validator behavior
            if execution_time > 120:
                assert any("120 секунд" in error for error in e.errors)
            if frequency < 7:
                assert any("7 дней" in error for error in e.errors)
    
    @given(
        name=st.text(min_size=0, max_size=100),
        execution_time=st.integers(min_value=-10, max_value=200),
        frequency=st.integers(min_value=-5, max_value=30)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_validators_are_used_for_all_validation_scenarios(self, app, models, services, test_user, name, execution_time, frequency):
        """
        Feature: habit-tracker-improvements, Property 2: Использование валидаторов для проверки данных
        
        For any validation scenario, the system must use dedicated validator classes
        rather than ad-hoc validation logic
        """
        # Skip empty or whitespace-only names to avoid unrelated validation issues
        assume(name.strip() != '')
        
        habit_service = services['habit_service']
        
        habit_data = {
            'name': name,
            'execution_time': execution_time,
            'frequency': frequency,
            'habit_type': HabitType.USEFUL,
            'reward': 'Test Reward'
        }
        
        try:
            habit = habit_service.create_habit(test_user.id, habit_data)
            
            # If creation succeeded, all validators must have passed
            assert habit.execution_time <= 120  # TimeValidator rule
            assert habit.execution_time > 0    # TimeValidator positive rule
            assert habit.frequency >= 7        # FrequencyValidator rule
            assert habit.frequency > 0         # FrequencyValidator positive rule
            assert habit.name.strip() != ''    # HabitValidator rule
            
        except ValidationError as e:
            # If validation failed, it must be due to validator rules
            assert isinstance(e.errors, list)
            assert len(e.errors) > 0
            
            # Verify that errors come from known validators
            # Time validator messages
            has_time_error = any("120 секунд" in error for error in e.errors)
            has_time_positive_error = any("положительным числом" in error and "Время" in error for error in e.errors)
            
            # Frequency validator messages  
            has_frequency_error = any("7 дней" in error for error in e.errors)
            has_frequency_positive_error = any("положительным числом" in error and "Периодичность" in error for error in e.errors)
            
            # Name validator messages
            has_name_error = any("название" in error.lower() for error in e.errors)
            
            # Check if we have expected validation violations
            expected_time_max_violation = execution_time > 120
            expected_time_positive_violation = execution_time <= 0
            expected_frequency_min_violation = frequency < 7 and frequency > 0
            expected_frequency_positive_violation = frequency <= 0
            expected_name_violation = not name.strip()
            
            # If we have violations, at least one validator should have triggered
            any_expected_violation = (expected_time_max_violation or expected_time_positive_violation or 
                                    expected_frequency_min_violation or expected_frequency_positive_violation or 
                                    expected_name_violation)
            
            if any_expected_violation:
                any_validator_triggered = (has_time_error or has_time_positive_error or 
                                         has_frequency_error or has_frequency_positive_error or 
                                         has_name_error)
                assert any_validator_triggered, f"Expected validation error for time={execution_time}, frequency={frequency}, name='{name}', but got errors: {e.errors}"
            
            # Verify specific errors match the input violations
            if expected_time_max_violation:
                assert has_time_error, f"Expected time max validation error for execution_time={execution_time}, but got errors: {e.errors}"
            if expected_time_positive_violation:
                assert has_time_positive_error, f"Expected time positive validation error for execution_time={execution_time}, but got errors: {e.errors}"
            if expected_frequency_min_violation:
                assert has_frequency_error, f"Expected frequency min validation error for frequency={frequency}, but got errors: {e.errors}"
            if expected_frequency_positive_violation:
                assert has_frequency_positive_error, f"Expected frequency positive validation error for frequency={frequency}, but got errors: {e.errors}"
    
    @given(
        habit_type=st.sampled_from([HabitType.USEFUL, HabitType.PLEASANT]),
        has_reward=st.booleans(),
        has_related_habit=st.booleans()
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_business_rule_validation_uses_validators(self, app, models, services, test_user, habit_type, has_reward, has_related_habit):
        """
        Feature: habit-tracker-improvements, Property 2: Использование валидаторов для проверки данных
        
        For any business rule validation (pleasant habit constraints, useful habit constraints),
        the system must use validator classes rather than inline business logic
        """
        habit_service = services['habit_service']
        
        # Create a base habit for related habit testing
        base_habit_data = {
            'name': 'Base Habit',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        base_habit = habit_service.create_habit(test_user.id, base_habit_data)
        
        # Create test habit data
        habit_data = {
            'name': 'Test Business Rules',
            'execution_time': 60,
            'frequency': 7,
            'habit_type': habit_type
        }
        
        if has_reward:
            habit_data['reward'] = 'Test Reward'
        
        if has_related_habit:
            habit_data['related_habit_id'] = base_habit.id
        
        try:
            habit = habit_service.create_habit(test_user.id, habit_data)
            
            # If creation succeeded, verify business rules were enforced by validators
            if habit_type == HabitType.PLEASANT:
                # Pleasant habits should not have rewards or related habits
                assert habit.reward is None
                assert habit.related_habit_id is None
            elif habit_type == HabitType.USEFUL:
                # Useful habits can have either reward OR related habit, but not both
                if has_reward and has_related_habit:
                    pytest.fail("Useful habit should not have both reward and related habit")
                
        except ValidationError as e:
            # If validation failed, verify it was due to business rule validators
            assert isinstance(e.errors, list)
            assert len(e.errors) > 0
            
            # Check for expected business rule validation errors
            if habit_type == HabitType.PLEASANT:
                if has_reward:
                    assert any("приятная привычка не может иметь вознаграждение" in error.lower() 
                              for error in e.errors)
                if has_related_habit:
                    assert any("приятная привычка не может быть связана" in error.lower() 
                              for error in e.errors)
            elif habit_type == HabitType.USEFUL and has_reward and has_related_habit:
                assert any("либо вознаграждение, либо связанную привычку" in error 
                          for error in e.errors)
    
    def test_validator_composition_in_habit_service(self, app, models, services, test_user):
        """
        Feature: habit-tracker-improvements, Property 2: Использование валидаторов для проверки данных
        
        The HabitService must compose multiple validators (TimeValidator, FrequencyValidator, HabitValidator)
        rather than implementing validation logic directly
        """
        habit_service = services['habit_service']
        
        # Verify that HabitService has a validator instance
        assert hasattr(habit_service, 'habit_validator')
        assert isinstance(habit_service.habit_validator, HabitValidator)
        
        # Verify that HabitValidator composes other validators
        habit_validator = habit_service.habit_validator
        assert hasattr(habit_validator, 'time_validator')
        assert hasattr(habit_validator, 'frequency_validator')
        assert isinstance(habit_validator.time_validator, TimeValidator)
        assert isinstance(habit_validator.frequency_validator, FrequencyValidator)
        
        # Test that validation goes through the validator chain
        invalid_data = {
            'name': 'Test Habit',
            'execution_time': 150,  # Invalid: > 120
            'frequency': 3,  # Invalid: < 7
            'habit_type': HabitType.PLEASANT,
            'reward': 'Invalid Reward'  # Invalid: pleasant habit with reward
        }
        
        with pytest.raises(ValidationError) as exc_info:
            habit_service.create_habit(test_user.id, invalid_data)
        
        # Should have errors from all validators
        errors = exc_info.value.errors
        assert any("120 секунд" in error for error in errors)  # TimeValidator
        assert any("7 дней" in error for error in errors)  # FrequencyValidator
        assert any("приятная привычка не может иметь вознаграждение" in error.lower() 
                  for error in errors)  # HabitValidator business rules
    
    @given(
        execution_time=st.integers(min_value=1, max_value=200)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_time_validator_is_used_consistently(self, app, models, services, test_user, execution_time):
        """
        Feature: habit-tracker-improvements, Property 2: Использование валидаторов для проверки данных
        
        For any time-related validation, the system must use TimeValidator consistently
        """
        habit_service = services['habit_service']
        time_validator = services['time_validator']
        
        # Test direct validator usage
        time_result = time_validator.validate({'execution_time': execution_time})
        
        # Test service usage (should use same validator)
        habit_data = {
            'name': 'Time Test Habit',
            'execution_time': execution_time,
            'frequency': 7,
            'habit_type': HabitType.USEFUL
        }
        
        try:
            habit = habit_service.create_habit(test_user.id, habit_data)
            # If service succeeded, direct validator should also succeed
            assert time_result.is_valid
            assert habit.execution_time == execution_time
            
        except ValidationError as service_error:
            # If service failed, direct validator should also fail
            if execution_time > 120:
                assert not time_result.is_valid
                assert any("120 секунд" in error for error in time_result.errors)
                assert any("120 секунд" in error for error in service_error.errors)
    
    @given(
        frequency=st.integers(min_value=1, max_value=30)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_frequency_validator_is_used_consistently(self, app, models, services, test_user, frequency):
        """
        Feature: habit-tracker-improvements, Property 2: Использование валидаторов для проверки данных
        
        For any frequency-related validation, the system must use FrequencyValidator consistently
        """
        habit_service = services['habit_service']
        frequency_validator = services['frequency_validator']
        
        # Test direct validator usage
        frequency_result = frequency_validator.validate({'frequency': frequency})
        
        # Test service usage (should use same validator)
        habit_data = {
            'name': 'Frequency Test Habit',
            'execution_time': 60,
            'frequency': frequency,
            'habit_type': HabitType.USEFUL
        }
        
        try:
            habit = habit_service.create_habit(test_user.id, habit_data)
            # If service succeeded, direct validator should also succeed
            assert frequency_result.is_valid
            assert habit.frequency == frequency
            
        except ValidationError as service_error:
            # If service failed, direct validator should also fail
            if frequency < 7:
                assert not frequency_result.is_valid
                assert any("7 дней" in error for error in frequency_result.errors)
                assert any("7 дней" in error for error in service_error.errors)