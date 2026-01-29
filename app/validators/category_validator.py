"""
Валидатор Категорий

Валидирует категории привычек
"""
import re
from .base_validator import BaseValidator, ValidationResult


class CategoryValidator(BaseValidator):
    """
    Валидатор для проверки категорий
    """
    MIN_NAME_LENGTH = 1
    MAX_NAME_LENGTH = 50
    
    # Предопределенные категории
    PREDEFINED_CATEGORIES = [
        'Здоровье',
        'Учеба',
        'Работа',
        'Спорт',
        'Хобби',
        'Финансы',
        'Отношения',
        'Развитие',
        'Быт',
        'Другое'
    ]
    
    def validate(self, data: dict) -> ValidationResult:
        """
        Валидировать категорию
        
        Args:
            data: Словарь с ключами 'name' и опционально 'color'
            
        Returns:
            ValidationResult с статусом валидации и ошибками
        """
        errors = []
        
        if 'name' not in data:
            errors.append("Имя категории не указано")
            return ValidationResult(is_valid=False, errors=errors)
        
        name = data['name']
        
        # Проверка типа имени
        if not isinstance(name, str):
            errors.append("Имя категории должно быть строкой")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Проверка пустоты
        if not name or not name.strip():
            errors.append("Имя категории не может быть пустым")
        # Проверка длины
        elif len(name) > self.MAX_NAME_LENGTH:
            errors.append(f"Имя категории не может быть длиннее {self.MAX_NAME_LENGTH} символов")
        
        # Проверка цвета, если указан
        if 'color' in data:
            color = data['color']
            if not self._is_valid_hex_color(color):
                errors.append("Цвет должен быть в формате HEX (#RRGGBB)")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    @staticmethod
    def validate_category(name: str, color: str = None) -> ValidationResult:
        """
        Статический метод для валидации категории
        
        Args:
            name: Имя категории
            color: Опциональный HEX цвет
            
        Returns:
            ValidationResult с статусом валидации и ошибками
        """
        validator = CategoryValidator()
        data = {'name': name}
        if color:
            data['color'] = color
        return validator.validate(data)
    
    @staticmethod
    def _is_valid_hex_color(color: str) -> bool:
        """
        Проверить, является ли строка валидным HEX цветом
        
        Args:
            color: Строка для проверки
            
        Returns:
            bool: True если валидный HEX цвет
        """
        if not isinstance(color, str):
            return False
        
        # Проверить формат #RRGGBB
        hex_pattern = r'^#[0-9a-fA-F]{6}$'
        return bool(re.match(hex_pattern, color))
    
    @staticmethod
    def get_predefined_categories():
        """
        Получить список предопределенных категорий
        
        Returns:
            List[str]: Список предопределенных категорий
        """
        return CategoryValidator.PREDEFINED_CATEGORIES.copy()
