"""
Base Validator Classes

Provides base classes and interfaces for validation system
"""
from typing import List
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[str]


class BaseValidator(ABC):
    """Base class for all validators"""
    
    @abstractmethod
    def validate(self, data: dict) -> ValidationResult:
        """
        Validate the provided data
        
        Args:
            data: Dictionary containing data to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        pass