"""
Сервис Комментариев

Бизнес-логика для управления комментариями к привычкам
"""
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from ..validators.comment_validator import CommentValidator
from ..models import get_models
from ..exceptions import (
    ValidationError, AuthorizationError, ResourceNotFoundError,
    BusinessLogicError, HabitTrackerException
)


class CommentServiceError(HabitTrackerException):
    """Базовое исключение для ошибок CommentService"""
    pass


class CommentNotFoundError(ResourceNotFoundError):
    """Вызывается когда комментарий не найден"""
    def __init__(self, comment_id: int):
        super().__init__('comment', comment_id)


class CommentService:
    """
    Сервис для управления комментариями привычек с бизнес-логикой и валидацией
    """
    
    def __init__(self, comment_validator: CommentValidator = None):
        """
        Инициализировать CommentService
        
        Args:
            comment_validator: Валидатор для данных комментариев (опционально)
        """
        self.comment_validator = comment_validator or CommentValidator()
        # Получить модели после инициализации
        self.User, self.Habit, self.HabitLog, self.Category, self.Tag, self.Comment = get_models()
        
        # Импортировать db из моделей
        from ..models.comment import db
        self.db = db
    
    def add_comment(self, habit_log_id: int, habit_id: int, user_id: int, text: str) -> Tuple[Optional['Comment'], bool, List[str]]:
        """
        Добавить комментарий к выполнению привычки
        
        Args:
            habit_log_id: ID записи о выполнении привычки
            habit_id: ID привычки
            user_id: ID пользователя
            text: Текст комментария
            
        Returns:
            Tuple[Comment, bool, List[str]]: Комментарий, статус валидации, ошибки
        """
        # Валидировать текст
        result = self.comment_validator.validate({'text': text})
        if not result.is_valid:
            return None, False, result.errors
        
        # Санитизировать текст
        sanitized_text = CommentValidator.sanitize_text(text)
        
        try:
            # Проверить, существует ли привычка и принадлежит ли пользователю
            habit = self.Habit.query.filter_by(id=habit_id, user_id=user_id).first()
            if not habit:
                return None, False, ["Привычка не найдена"]
            
            # Проверить, существует ли запись о выполнении
            habit_log = self.HabitLog.query.filter_by(id=habit_log_id, habit_id=habit_id).first()
            if not habit_log:
                return None, False, ["Запись о выполнении привычки не найдена"]
            
            # Создать комментарий
            comment = self.Comment(
                habit_id=habit_id,
                habit_log_id=habit_log_id,
                text=sanitized_text
            )
            
            self.db.session.add(comment)
            self.db.session.commit()
            
            return comment, True, []
        except Exception as e:
            self.db.session.rollback()
            return None, False, [f"Ошибка при добавлении комментария: {str(e)}"]
    
    def update_comment(self, comment_id: int, habit_id: int, user_id: int, text: str) -> Tuple[Optional['Comment'], bool, List[str]]:
        """
        Обновить комментарий
        
        Args:
            comment_id: ID комментария
            habit_id: ID привычки
            user_id: ID пользователя
            text: Новый текст комментария
            
        Returns:
            Tuple[Comment, bool, List[str]]: Комментарий, статус валидации, ошибки
        """
        # Валидировать текст
        result = self.comment_validator.validate({'text': text})
        if not result.is_valid:
            return None, False, result.errors
        
        # Санитизировать текст
        sanitized_text = CommentValidator.sanitize_text(text)
        
        try:
            # Получить комментарий
            comment = self.Comment.query.filter_by(id=comment_id, habit_id=habit_id).first()
            if not comment:
                return None, False, ["Комментарий не найден"]
            
            # Проверить, принадлежит ли привычка пользователю
            habit = self.Habit.query.filter_by(id=habit_id, user_id=user_id).first()
            if not habit:
                return None, False, ["Привычка не найдена"]
            
            # Обновить комментарий
            comment.text = sanitized_text
            comment.updated_at = datetime.now(timezone.utc)
            
            self.db.session.commit()
            return comment, True, []
        except Exception as e:
            self.db.session.rollback()
            return None, False, [f"Ошибка при обновлении комментария: {str(e)}"]
    
    def delete_comment(self, comment_id: int, habit_id: int, user_id: int) -> Tuple[bool, List[str]]:
        """
        Удалить комментарий
        
        Args:
            comment_id: ID комментария
            habit_id: ID привычки
            user_id: ID пользователя
            
        Returns:
            Tuple[bool, List[str]]: Статус успеха, ошибки
        """
        try:
            # Получить комментарий
            comment = self.Comment.query.filter_by(id=comment_id, habit_id=habit_id).first()
            if not comment:
                return False, ["Комментарий не найден"]
            
            # Проверить, принадлежит ли привычка пользователю
            habit = self.Habit.query.filter_by(id=habit_id, user_id=user_id).first()
            if not habit:
                return False, ["Привычка не найдена"]
            
            # Удалить комментарий
            self.db.session.delete(comment)
            self.db.session.commit()
            
            return True, []
        except Exception as e:
            self.db.session.rollback()
            return False, [f"Ошибка при удалении комментария: {str(e)}"]
    
    def get_habit_comments(self, habit_id: int, user_id: int) -> List['Comment']:
        """
        Получить все комментарии привычки
        
        Args:
            habit_id: ID привычки
            user_id: ID пользователя
            
        Returns:
            List[Comment]: Список комментариев в хронологическом порядке
        """
        # Проверить, принадлежит ли привычка пользователю
        habit = self.Habit.query.filter_by(id=habit_id, user_id=user_id).first()
        if not habit:
            return []
        
        # Получить комментарии в хронологическом порядке
        comments = self.Comment.query.filter_by(habit_id=habit_id).order_by(
            self.Comment.created_at.asc()
        ).all()
        
        return comments
    
    def get_habit_log_comments(self, habit_log_id: int, habit_id: int, user_id: int) -> List['Comment']:
        """
        Получить все комментарии для конкретной записи о выполнении привычки
        
        Args:
            habit_log_id: ID записи о выполнении
            habit_id: ID привычки
            user_id: ID пользователя
            
        Returns:
            List[Comment]: Список комментариев
        """
        # Проверить, принадлежит ли привычка пользователю
        habit = self.Habit.query.filter_by(id=habit_id, user_id=user_id).first()
        if not habit:
            return []
        
        # Получить комментарии
        comments = self.Comment.query.filter_by(
            habit_log_id=habit_log_id,
            habit_id=habit_id
        ).order_by(self.Comment.created_at.asc()).all()
        
        return comments
    
    def search_comments(self, habit_id: int, user_id: int, search_text: str) -> List['Comment']:
        """
        Поиск комментариев по тексту
        
        Args:
            habit_id: ID привычки
            user_id: ID пользователя
            search_text: Текст для поиска
            
        Returns:
            List[Comment]: Список найденных комментариев
        """
        # Проверить, принадлежит ли привычка пользователю
        habit = self.Habit.query.filter_by(id=habit_id, user_id=user_id).first()
        if not habit:
            return []
        
        # Поиск по тексту (case-insensitive)
        search_pattern = f"%{search_text}%"
        comments = self.Comment.query.filter_by(habit_id=habit_id).filter(
            self.Comment.text.ilike(search_pattern)
        ).order_by(self.Comment.created_at.asc()).all()
        
        return comments
