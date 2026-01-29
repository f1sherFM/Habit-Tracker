"""
Сервис Категорий

Бизнес-логика для управления категориями привычек
"""
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from ..validators.category_validator import CategoryValidator
from ..models import get_models
from ..exceptions import (
    ValidationError, AuthorizationError, ResourceNotFoundError,
    BusinessLogicError, HabitTrackerException
)


class CategoryServiceError(HabitTrackerException):
    """Базовое исключение для ошибок CategoryService"""
    pass


class CategoryNotFoundError(ResourceNotFoundError):
    """Вызывается когда категория не найдена"""
    def __init__(self, category_id: int):
        super().__init__('category', category_id)


class CategoryService:
    """
    Сервис для управления категориями привычек с бизнес-логикой и валидацией
    """
    
    def __init__(self, category_validator: CategoryValidator = None):
        """
        Инициализировать CategoryService
        
        Args:
            category_validator: Валидатор для данных категории (опционально)
        """
        self.category_validator = category_validator or CategoryValidator()
        # Получить модели после инициализации
        self.User, self.Habit, self.HabitLog, self.Category, self.Tag, self.Comment = get_models()
        
        # Импортировать db из моделей
        from ..models.category import db
        self.db = db
    
    def create_category(self, user_id: int, name: str, color: str = None, icon: str = None) -> Tuple['Category', bool, List[str]]:
        """
        Создать новую категорию
        
        Args:
            user_id: ID пользователя
            name: Имя категории
            color: Опциональный HEX цвет
            icon: Опциональное имя иконки
            
        Returns:
            Tuple[Category, bool, List[str]]: Категория, статус валидации, ошибки
        """
        # Валидировать данные
        validation_data = {'name': name}
        if color:
            validation_data['color'] = color
        
        result = self.category_validator.validate(validation_data)
        if not result.is_valid:
            return None, False, result.errors
        
        try:
            # Проверить, существует ли уже категория с таким именем для пользователя
            existing = self.Category.query.filter_by(
                user_id=user_id,
                name=name
            ).first()
            
            if existing:
                return None, False, ["Категория с таким именем уже существует"]
            
            # Создать новую категорию
            category = self.Category(
                user_id=user_id,
                name=name,
                color=color or '#6366f1',
                icon=icon
            )
            
            self.db.session.add(category)
            self.db.session.commit()
            
            return category, True, []
        except Exception as e:
            self.db.session.rollback()
            return None, False, [f"Ошибка при создании категории: {str(e)}"]
    
    def get_user_categories(self, user_id: int) -> List['Category']:
        """
        Получить все категории пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Category]: Список категорий
        """
        return self.Category.query.filter_by(user_id=user_id).all()
    
    def get_category(self, category_id: int, user_id: int) -> Optional['Category']:
        """
        Получить категорию по ID с проверкой прав доступа
        
        Args:
            category_id: ID категории
            user_id: ID пользователя
            
        Returns:
            Optional[Category]: Категория или None
        """
        category = self.Category.query.filter_by(
            id=category_id,
            user_id=user_id
        ).first()
        
        return category
    
    def update_category(self, category_id: int, user_id: int, name: str = None, 
                       color: str = None, icon: str = None) -> Tuple[Optional['Category'], bool, List[str]]:
        """
        Обновить категорию
        
        Args:
            category_id: ID категории
            user_id: ID пользователя
            name: Новое имя (опционально)
            color: Новый цвет (опционально)
            icon: Новая иконка (опционально)
            
        Returns:
            Tuple[Category, bool, List[str]]: Категория, статус, ошибки
        """
        category = self.get_category(category_id, user_id)
        if not category:
            return None, False, ["Категория не найдена"]
        
        # Валидировать новые данные
        validation_data = {}
        if name:
            validation_data['name'] = name
        if color:
            validation_data['color'] = color
        
        if validation_data:
            result = self.category_validator.validate(validation_data)
            if not result.is_valid:
                return None, False, result.errors
        
        try:
            if name:
                # Проверить, не существует ли уже категория с таким именем
                existing = self.Category.query.filter_by(
                    user_id=user_id,
                    name=name
                ).filter(self.Category.id != category_id).first()
                
                if existing:
                    return None, False, ["Категория с таким именем уже существует"]
                
                category.name = name
            
            if color:
                category.color = color
            
            if icon:
                category.icon = icon
            
            self.db.session.commit()
            return category, True, []
        except Exception as e:
            self.db.session.rollback()
            return None, False, [f"Ошибка при обновлении категории: {str(e)}"]
    
    def delete_category(self, category_id: int, user_id: int) -> Tuple[bool, List[str]]:
        """
        Удалить категорию и переместить привычки в "Без категории"
        
        Args:
            category_id: ID категории
            user_id: ID пользователя
            
        Returns:
            Tuple[bool, List[str]]: Статус успеха, ошибки
        """
        category = self.get_category(category_id, user_id)
        if not category:
            return False, ["Категория не найдена"]
        
        try:
            # Переместить все привычки в эту категорию в "Без категории"
            habits = self.Habit.query.filter_by(category_id=category_id).all()
            for habit in habits:
                habit.category_id = None
            
            # Удалить категорию
            self.db.session.delete(category)
            self.db.session.commit()
            
            return True, []
        except Exception as e:
            self.db.session.rollback()
            return False, [f"Ошибка при удалении категории: {str(e)}"]
    
    def get_predefined_categories(self) -> List[str]:
        """
        Получить список предопределенных категорий
        
        Returns:
            List[str]: Список предопределенных категорий
        """
        return CategoryValidator.get_predefined_categories()
