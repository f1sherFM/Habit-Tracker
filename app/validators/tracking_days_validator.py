"""
Валидатор Периода Отслеживания

Валидирует период отслеживания привычек (1-30 дней)
"""
from .base_validator import BaseValidator, ValidationResult


class TrackingDaysValidator(BaseValidator):
    """
    Валидатор для проверки периода отслеживания привычек
    """
    MIN_DAYS = 1
    MAX_DAYS = 30
    
    def validate(self, data: dict) -> ValidationResult:
        """
        Валидировать период отслеживания
        
        Args:
            data: Словарь с ключом 'tracking_days'
            
        Returns:
            ValidationResult с статусом валидации и ошибками
        """
        errors = []
        
        if 'tracking_days' not in data:
            errors.append("Период отслеживания не указан")
            return ValidationResult(is_valid=False, errors=errors)
        
        days = data['tracking_days']
        
        # Проверка типа
        if not isinstance(days, int):
            errors.append("Период должен быть целым числом")
        # Проверка минимума
        elif days < self.MIN_DAYS:
            errors.append(f"Период не может быть меньше {self.MIN_DAYS} дня")
        # Проверка максимума
        elif days > self.MAX_DAYS:
            errors.append(f"Период не может быть больше {self.MAX_DAYS} дней")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    @staticmethod
    def validate_days(days: int) -> ValidationResult:
        """
        Статический метод для валидации дней
        
        Args:
            days: Количество дней
            
        Returns:
            ValidationResult с статусом валидации и ошибками
        """
        validator = TrackingDaysValidator()
        return validator.validate({'tracking_days': days})
