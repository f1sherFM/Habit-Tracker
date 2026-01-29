"""
Валидатор Тегов

Валидирует теги для привычек
"""
from typing import List
from .base_validator import BaseValidator, ValidationResult


class TagValidator(BaseValidator):
    """
    Валидатор для проверки тегов
    """
    MIN_LENGTH = 1
    MAX_LENGTH = 20
    MAX_TAGS_PER_HABIT = 5
    
    def validate(self, data: dict) -> ValidationResult:
        """
        Валидировать теги
        
        Args:
            data: Словарь с ключом 'tags' (список строк)
            
        Returns:
            ValidationResult с статусом валидации и ошибками
        """
        errors = []
        
        if 'tags' not in data:
            errors.append("Теги не указаны")
            return ValidationResult(is_valid=False, errors=errors)
        
        tags = data['tags']
        
        # Проверка типа
        if not isinstance(tags, list):
            errors.append("Теги должны быть списком")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Проверка количества тегов
        if len(tags) > self.MAX_TAGS_PER_HABIT:
            errors.append(f"Максимум {self.MAX_TAGS_PER_HABIT} тегов на привычку")
        
        # Проверка каждого тега
        for tag in tags:
            if not isinstance(tag, str):
                errors.append("Каждый тег должен быть строкой")
                continue
            
            if not tag or not tag.strip():
                errors.append("Тег не может быть пустым")
            elif len(tag) > self.MAX_LENGTH:
                errors.append(f"Тег не может быть длиннее {self.MAX_LENGTH} символов")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    @staticmethod
    def validate_tags(tags: List[str]) -> ValidationResult:
        """
        Статический метод для валидации списка тегов
        
        Args:
            tags: Список тегов
            
        Returns:
            ValidationResult с статусом валидации и ошибками
        """
        validator = TagValidator()
        return validator.validate({'tags': tags})
    
    @staticmethod
    def normalize_tags(tags: List[str]) -> List[str]:
        """
        Нормализовать теги (преобразовать в нижний регистр и удалить пробелы)
        
        Args:
            tags: Список тегов
            
        Returns:
            List[str]: Нормализованные теги
        """
        if not isinstance(tags, list):
            return []
        
        normalized = []
        for tag in tags:
            if isinstance(tag, str):
                normalized_tag = tag.strip().lower()
                if normalized_tag:
                    normalized.append(normalized_tag)
        
        return normalized
