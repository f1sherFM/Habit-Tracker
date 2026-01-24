"""
Habit Validator

Validates habit data with comprehensive business rules
"""
from typing import List
from .base_validator import BaseValidator, ValidationResult
from .time_validator import TimeValidator
from .frequency_validator import FrequencyValidator
from ..models.habit_types import HabitType


class HabitValidator(BaseValidator):
    """Validates habit data with business rules"""
    
    def __init__(self, time_validator: TimeValidator = None, frequency_validator: FrequencyValidator = None):
        """
        Initialize HabitValidator with component validators
        
        Args:
            time_validator: Validator for time constraints
            frequency_validator: Validator for frequency constraints
        """
        self.time_validator = time_validator or TimeValidator()
        self.frequency_validator = frequency_validator or FrequencyValidator()
    
    def validate(self, data: dict) -> ValidationResult:
        """
        Validate habit data with comprehensive business rules
        
        Args:
            data: Dictionary containing habit data to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        
        # Validate basic required fields
        if not data.get('name'):
            errors.append("Название привычки обязательно для заполнения")
        elif len(data['name'].strip()) == 0:
            errors.append("Название привычки не может быть пустым")
        
        # Validate time constraints
        time_result = self.time_validator.validate(data)
        errors.extend(time_result.errors)
        
        # Validate frequency constraints
        frequency_result = self.frequency_validator.validate(data)
        errors.extend(frequency_result.errors)
        
        # Validate habit type specific constraints
        habit_type = data.get('habit_type')
        if habit_type:
            if isinstance(habit_type, str):
                # Convert string to enum if needed
                try:
                    habit_type_enum = HabitType(habit_type)
                except ValueError:
                    errors.append(f"Недопустимый тип привычки: {habit_type}")
                    habit_type_enum = None
            elif isinstance(habit_type, HabitType):
                habit_type_enum = habit_type
            else:
                errors.append("Тип привычки должен быть строкой или HabitType")
                habit_type_enum = None
            
            if habit_type_enum:
                if habit_type_enum == HabitType.PLEASANT:
                    pleasant_errors = self._validate_pleasant_habit_constraints(data)
                    errors.extend(pleasant_errors)
                elif habit_type_enum == HabitType.USEFUL:
                    useful_errors = self._validate_useful_habit_constraints(data)
                    errors.extend(useful_errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def _validate_pleasant_habit_constraints(self, data: dict) -> List[str]:
        """
        Validate constraints specific to pleasant habits
        
        Args:
            data: Habit data dictionary
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Pleasant habits cannot have rewards
        if data.get('reward'):
            errors.append("Приятная привычка не может иметь вознаграждение")
        
        # Pleasant habits cannot have related habits
        if data.get('related_habit_id'):
            errors.append("Приятная привычка не может быть связана с другой привычкой")
        
        return errors
    
    def _validate_useful_habit_constraints(self, data: dict) -> List[str]:
        """
        Validate constraints specific to useful habits
        
        Args:
            data: Habit data dictionary
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Useful habits can have either reward OR related habit, but not both
        has_reward = bool(data.get('reward'))
        has_related_habit = bool(data.get('related_habit_id'))
        
        if has_reward and has_related_habit:
            errors.append("Полезная привычка может иметь либо вознаграждение, либо связанную привычку, но не оба одновременно")
        
        # Validate reward length if present
        reward = data.get('reward')
        if reward and len(reward.strip()) > 200:
            errors.append("Описание вознаграждения не может превышать 200 символов")
        
        return errors