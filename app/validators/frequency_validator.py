"""
Frequency Validator

Validates frequency constraints for habits
"""
from typing import List
from .base_validator import BaseValidator, ValidationResult


class FrequencyValidator(BaseValidator):
    """Validates frequency constraints for habits"""
    
    MIN_FREQUENCY_DAYS = 7  # Minimum frequency in days (once per week)
    
    def validate(self, data: dict) -> ValidationResult:
        """
        Validate frequency-related data
        
        Args:
            data: Dictionary containing frequency data to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        
        # Validate frequency if present
        if 'frequency' in data:
            frequency = data['frequency']
            
            # Check if frequency is a valid integer
            if not isinstance(frequency, int):
                errors.append("Периодичность должна быть целым числом")
            elif frequency <= 0:
                errors.append("Периодичность должна быть положительным числом")
            elif frequency < self.MIN_FREQUENCY_DAYS:
                errors.append(f"Периодичность не может быть чаще чем раз в {self.MIN_FREQUENCY_DAYS} дней")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def validate_frequency(self, frequency: int) -> ValidationResult:
        """
        Validate frequency specifically
        
        Args:
            frequency: Frequency in days
            
        Returns:
            ValidationResult with validation status and any errors
        """
        return self.validate({'frequency': frequency})