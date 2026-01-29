"""
Сервис Тегов

Бизнес-логика для управления тегами привычек
"""
from typing import List, Optional, Tuple
from ..validators.tag_validator import TagValidator
from ..models import get_models
from ..exceptions import (
    ValidationError, AuthorizationError, ResourceNotFoundError,
    BusinessLogicError, HabitTrackerException
)


class TagServiceError(HabitTrackerException):
    """Базовое исключение для ошибок TagService"""
    pass


class TagNotFoundError(ResourceNotFoundError):
    """Вызывается когда тег не найден"""
    def __init__(self, tag_id: int):
        super().__init__('tag', tag_id)


class TagService:
    """
    Сервис для управления тегами привычек с бизнес-логикой и валидацией
    """
    
    def __init__(self, tag_validator: TagValidator = None):
        """
        Инициализировать TagService
        
        Args:
            tag_validator: Валидатор для данных тегов (опционально)
        """
        self.tag_validator = tag_validator or TagValidator()
        # Получить модели после инициализации
        self.User, self.Habit, self.HabitLog, self.Category, self.Tag, self.Comment = get_models()
        
        # Импортировать db из моделей
        from ..models.tag import db
        self.db = db
    
    def add_tags_to_habit(self, habit_id: int, user_id: int, tags: List[str]) -> Tuple[List['Tag'], bool, List[str]]:
        """
        Добавить теги к привычке
        
        Args:
            habit_id: ID привычки
            user_id: ID пользователя
            tags: Список тегов
            
        Returns:
            Tuple[List[Tag], bool, List[str]]: Теги, статус валидации, ошибки
        """
        # Валидировать теги
        result = self.tag_validator.validate({'tags': tags})
        if not result.is_valid:
            return [], False, result.errors
        
        # Нормализовать теги
        normalized_tags = TagValidator.normalize_tags(tags)
        
        try:
            # Получить привычку
            habit = self.Habit.query.filter_by(id=habit_id, user_id=user_id).first()
            if not habit:
                return [], False, ["Привычка не найдена"]
            
            # Получить или создать теги
            tag_objects = []
            for tag_name in normalized_tags:
                tag = self.Tag.query.filter_by(user_id=user_id, name=tag_name).first()
                if not tag:
                    tag = self.Tag(user_id=user_id, name=tag_name)
                    self.db.session.add(tag)
                
                tag_objects.append(tag)
            
            # Очистить старые теги и добавить новые
            habit.tags.clear()
            for tag in tag_objects:
                if tag not in habit.tags:
                    habit.tags.append(tag)
            
            self.db.session.commit()
            return tag_objects, True, []
        except Exception as e:
            self.db.session.rollback()
            return [], False, [f"Ошибка при добавлении тегов: {str(e)}"]
    
    def get_habit_tags(self, habit_id: int, user_id: int) -> List['Tag']:
        """
        Получить все теги привычки
        
        Args:
            habit_id: ID привычки
            user_id: ID пользователя
            
        Returns:
            List[Tag]: Список тегов
        """
        habit = self.Habit.query.filter_by(id=habit_id, user_id=user_id).first()
        if not habit:
            return []
        
        return habit.tags
    
    def remove_tag_from_habit(self, habit_id: int, tag_id: int, user_id: int) -> Tuple[bool, List[str]]:
        """
        Удалить тег из привычки
        
        Args:
            habit_id: ID привычки
            tag_id: ID тега
            user_id: ID пользователя
            
        Returns:
            Tuple[bool, List[str]]: Статус успеха, ошибки
        """
        try:
            habit = self.Habit.query.filter_by(id=habit_id, user_id=user_id).first()
            if not habit:
                return False, ["Привычка не найдена"]
            
            tag = self.Tag.query.filter_by(id=tag_id, user_id=user_id).first()
            if not tag:
                return False, ["Тег не найден"]
            
            if tag in habit.tags:
                habit.tags.remove(tag)
                
                # Если тег больше не используется, удалить его
                if len(tag.habits) == 0:
                    self.db.session.delete(tag)
            
            self.db.session.commit()
            return True, []
        except Exception as e:
            self.db.session.rollback()
            return False, [f"Ошибка при удалении тега: {str(e)}"]
    
    def get_tag_suggestions(self, user_id: int, prefix: str = "") -> List[str]:
        """
        Получить предложения тегов по префиксу
        
        Args:
            user_id: ID пользователя
            prefix: Префикс для поиска
            
        Returns:
            List[str]: Список предложенных тегов
        """
        prefix_lower = prefix.lower()
        
        tags = self.Tag.query.filter_by(user_id=user_id).all()
        suggestions = []
        
        for tag in tags:
            if tag.name.lower().startswith(prefix_lower):
                suggestions.append(tag.name)
        
        # Сортировать по релевантности (длина совпадения)
        suggestions.sort(key=lambda x: len(x))
        
        return suggestions[:10]  # Вернуть максимум 10 предложений
    
    def get_user_tags(self, user_id: int) -> List['Tag']:
        """
        Получить все теги пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Tag]: Список тегов
        """
        return self.Tag.query.filter_by(user_id=user_id).all()
    
    def cleanup_unused_tags(self, user_id: int) -> Tuple[int, List[str]]:
        """
        Удалить неиспользуемые теги пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Tuple[int, List[str]]: Количество удаленных тегов, ошибки
        """
        try:
            tags = self.Tag.query.filter_by(user_id=user_id).all()
            deleted_count = 0
            
            for tag in tags:
                if len(tag.habits) == 0:
                    self.db.session.delete(tag)
                    deleted_count += 1
            
            self.db.session.commit()
            return deleted_count, []
        except Exception as e:
            self.db.session.rollback()
            return 0, [f"Ошибка при удалении неиспользуемых тегов: {str(e)}"]
