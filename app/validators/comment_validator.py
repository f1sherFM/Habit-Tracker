"""
Валидатор Комментариев

Валидирует комментарии к привычкам
"""
import html
from .base_validator import BaseValidator, ValidationResult


class CommentValidator(BaseValidator):
    """
    Валидатор для проверки комментариев
    """
    MIN_LENGTH = 1
    MAX_LENGTH = 500
    
    def validate(self, data: dict) -> ValidationResult:
        """
        Валидировать комментарий
        
        Args:
            data: Словарь с ключом 'text'
            
        Returns:
            ValidationResult с статусом валидации и ошибками
        """
        errors = []
        
        if 'text' not in data:
            errors.append("Текст комментария не указан")
            return ValidationResult(is_valid=False, errors=errors)
        
        text = data['text']
        
        # Проверка типа
        if not isinstance(text, str):
            errors.append("Комментарий должен быть строкой")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Проверка пустоты
        if not text or not text.strip():
            errors.append("Комментарий не может быть пустым")
        # Проверка длины
        elif len(text) > self.MAX_LENGTH:
            errors.append(f"Комментарий не может быть длиннее {self.MAX_LENGTH} символов")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    @staticmethod
    def validate_text(text: str) -> ValidationResult:
        """
        Статический метод для валидации текста комментария
        
        Args:
            text: Текст комментария
            
        Returns:
            ValidationResult с статусом валидации и ошибками
        """
        validator = CommentValidator()
        return validator.validate({'text': text})
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Санитизировать текст комментария (удалить HTML теги)
        
        Args:
            text: Текст для санитизации
            
        Returns:
            str: Санитизированный текст
        """
        if not isinstance(text, str):
            return ""
        
        # Экранировать HTML теги
        return html.escape(text)
