"""
Time Validator

Validates time-related constraints for habits
"""
from typing import List
from .base_validator import BaseValidator, ValidationResult


class TimeValidator(BaseValidator):
    """Validates time constraints for habits"""
    
    MAX_EXECUTION_TIME = 120  # Maximum execution time in seconds
    
    def validate(self, data: dict) -> ValidationResult:
        """
        Validate time-related data
        
        Args:
            data: Dictionary containing time data to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        
        # Validate execution_time if present
        if 'execution_time' in data:
            execution_time = data['execution_time']
            
            # Check if execution_time is a valid integer
            if not isinstance(execution_time, int):
                errors.append("Время выполнения должно быть целым числом")
            elif execution_time <= 0:
                errors.append("Время выполнения должно быть положительным числом")
            elif execution_time > self.MAX_EXECUTION_TIME:
                errors.append(f"Время выполнения не может превышать {self.MAX_EXECUTION_TIME} секунд")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def validate_execution_time(self, execution_time: int) -> ValidationResult:
        """
        Validate execution time specifically
        
        Args:
            execution_time: Time in seconds
            
        Returns:
            ValidationResult with validation status and any errors
        """
        return self.validate({'execution_time': execution_time})