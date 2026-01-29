"""
Сервис Аналитики

Бизнес-логика для расчета статистики и аналитики привычек
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timezone, timedelta
from ..validators.tracking_days_validator import TrackingDaysValidator
from ..models import get_models
from ..exceptions import (
    ValidationError, ResourceNotFoundError, HabitTrackerException
)


class AnalyticsServiceError(HabitTrackerException):
    """Базовое исключение для ошибок AnalyticsService"""
    pass


class AnalyticsService:
    """
    Сервис для расчета статистики и аналитики привычек
    """
    
    def __init__(self, tracking_days_validator: TrackingDaysValidator = None):
        """
        Инициализировать AnalyticsService
        
        Args:
            tracking_days_validator: Валидатор для периода отслеживания (опционально)
        """
        self.tracking_days_validator = tracking_days_validator or TrackingDaysValidator()
        # Получить модели после инициализации
        self.User, self.Habit, self.HabitLog, self.Category, self.Tag, self.Comment = get_models()
        
        # Импортировать db из моделей
        from ..models.habit_log import db
        self.db = db
    
    def get_habit_statistics(self, habit_id: int, user_id: int, days: int = 7) -> Tuple[Optional[Dict], bool, List[str]]:
        """
        Получить статистику привычки за период
        
        Args:
            habit_id: ID привычки
            user_id: ID пользователя
            days: Количество дней для анализа (1-30)
            
        Returns:
            Tuple[Dict, bool, List[str]]: Статистика, статус валидации, ошибки
        """
        # Валидировать период
        result = self.tracking_days_validator.validate({'tracking_days': days})
        if not result.is_valid:
            return None, False, result.errors
        
        try:
            # Получить привычку
            habit = self.Habit.query.filter_by(id=habit_id, user_id=user_id).first()
            if not habit:
                return None, False, ["Привычка не найдена"]
            
            # Получить логи за период
            today = datetime.now(timezone.utc).date()
            start_date = today - timedelta(days=days - 1)
            
            logs = self.HabitLog.query.filter(
                self.HabitLog.habit_id == habit_id,
                self.HabitLog.date >= start_date,
                self.HabitLog.date <= today
            ).all()
            
            # Рассчитать статистику
            completed_count = sum(1 for log in logs if log.completed)
            completion_percentage = int((completed_count / days) * 100) if days > 0 else 0
            
            # Рассчитать текущий streak
            current_streak = self._calculate_current_streak(habit_id)
            
            # Рассчитать лучший streak
            best_streak = self._calculate_best_streak(habit_id)
            
            # Получить общее количество выполнений
            total_completions = self.HabitLog.query.filter_by(
                habit_id=habit_id,
                completed=True
            ).count()
            
            # Получить последний день выполнения
            last_completion = self.HabitLog.query.filter_by(
                habit_id=habit_id,
                completed=True
            ).order_by(self.HabitLog.date.desc()).first()
            
            last_completion_date = last_completion.date.isoformat() if last_completion else None
            
            return {
                'habit_id': habit_id,
                'habit_name': habit.name,
                'period_days': days,
                'completed_count': completed_count,
                'completion_percentage': completion_percentage,
                'current_streak': current_streak,
                'best_streak': best_streak,
                'total_completions': total_completions,
                'last_completion_date': last_completion_date,
                'start_date': start_date.isoformat(),
                'end_date': today.isoformat()
            }, True, []
        except Exception as e:
            return None, False, [f"Ошибка при расчете статистики: {str(e)}"]
    
    def get_category_statistics(self, category_id: int, user_id: int, days: int = 7) -> Tuple[Optional[Dict], bool, List[str]]:
        """
        Получить статистику по категории
        
        Args:
            category_id: ID категории
            user_id: ID пользователя
            days: Количество дней для анализа (1-30)
            
        Returns:
            Tuple[Dict, bool, List[str]]: Статистика, статус валидации, ошибки
        """
        # Валидировать период
        result = self.tracking_days_validator.validate({'tracking_days': days})
        if not result.is_valid:
            return None, False, result.errors
        
        try:
            # Получить категорию
            category = self.Category.query.filter_by(id=category_id, user_id=user_id).first()
            if not category:
                return None, False, ["Категория не найдена"]
            
            # Получить все привычки в категории
            habits = self.Habit.query.filter_by(category_id=category_id).all()
            
            if not habits:
                return {
                    'category_id': category_id,
                    'category_name': category.name,
                    'habits_count': 0,
                    'average_completion_percentage': 0,
                    'total_completions': 0,
                    'period_days': days
                }, True, []
            
            # Рассчитать статистику для каждой привычки
            total_completion_percentage = 0
            total_completions = 0
            
            for habit in habits:
                stats, is_valid, errors = self.get_habit_statistics(habit.id, user_id, days)
                if is_valid and stats:
                    total_completion_percentage += stats['completion_percentage']
                    total_completions += stats['total_completions']
            
            average_completion_percentage = int(total_completion_percentage / len(habits)) if habits else 0
            
            return {
                'category_id': category_id,
                'category_name': category.name,
                'habits_count': len(habits),
                'average_completion_percentage': average_completion_percentage,
                'total_completions': total_completions,
                'period_days': days
            }, True, []
        except Exception as e:
            return None, False, [f"Ошибка при расчете статистики категории: {str(e)}"]
    
    def get_user_analytics(self, user_id: int, days: int = 7) -> Tuple[Optional[Dict], bool, List[str]]:
        """
        Получить общую аналитику пользователя
        
        Args:
            user_id: ID пользователя
            days: Количество дней для анализа (1-30)
            
        Returns:
            Tuple[Dict, bool, List[str]]: Аналитика, статус валидации, ошибки
        """
        # Валидировать период
        result = self.tracking_days_validator.validate({'tracking_days': days})
        if not result.is_valid:
            return None, False, result.errors
        
        try:
            # Получить все привычки пользователя
            habits = self.Habit.query.filter_by(user_id=user_id).all()
            
            if not habits:
                return {
                    'user_id': user_id,
                    'total_habits': 0,
                    'average_completion_percentage': 0,
                    'total_completions': 0,
                    'period_days': days,
                    'categories': []
                }, True, []
            
            # Рассчитать общую статистику
            total_completion_percentage = 0
            total_completions = 0
            
            for habit in habits:
                stats, is_valid, errors = self.get_habit_statistics(habit.id, user_id, days)
                if is_valid and stats:
                    total_completion_percentage += stats['completion_percentage']
                    total_completions += stats['total_completions']
            
            average_completion_percentage = int(total_completion_percentage / len(habits)) if habits else 0
            
            # Получить статистику по категориям
            categories = self.Category.query.filter_by(user_id=user_id).all()
            category_stats = []
            
            for category in categories:
                cat_stats, is_valid, errors = self.get_category_statistics(category.id, user_id, days)
                if is_valid and cat_stats:
                    category_stats.append(cat_stats)
            
            return {
                'user_id': user_id,
                'total_habits': len(habits),
                'average_completion_percentage': average_completion_percentage,
                'total_completions': total_completions,
                'period_days': days,
                'categories': category_stats
            }, True, []
        except Exception as e:
            return None, False, [f"Ошибка при расчете аналитики: {str(e)}"]
    
    def _calculate_current_streak(self, habit_id: int) -> int:
        """
        Рассчитать текущий streak (количество дней подряд выполнения)
        
        Args:
            habit_id: ID привычки
            
        Returns:
            int: Текущий streak
        """
        today = datetime.now(timezone.utc).date()
        streak = 0
        
        for i in range(365):  # Проверить до 365 дней назад
            check_date = today - timedelta(days=i)
            log = self.HabitLog.query.filter_by(
                habit_id=habit_id,
                date=check_date,
                completed=True
            ).first()
            
            if log:
                streak += 1
            else:
                break
        
        return streak
    
    def _calculate_best_streak(self, habit_id: int) -> int:
        """
        Рассчитать лучший streak за все время
        
        Args:
            habit_id: ID привычки
            
        Returns:
            int: Лучший streak
        """
        logs = self.HabitLog.query.filter_by(habit_id=habit_id, completed=True).order_by(
            self.HabitLog.date.asc()
        ).all()
        
        if not logs:
            return 0
        
        best_streak = 1
        current_streak = 1
        
        for i in range(1, len(logs)):
            # Проверить, является ли дата следующей после предыдущей
            if (logs[i].date - logs[i-1].date).days == 1:
                current_streak += 1
                best_streak = max(best_streak, current_streak)
            else:
                current_streak = 1
        
        return best_streak
    
    def get_heatmap_data(self, user_id: int, days: int = 30) -> Tuple[Optional[Dict], bool, List[str]]:
        """
        Получить данные для тепловой карты (как GitHub contributions)
        
        Args:
            user_id: ID пользователя
            days: Количество дней для анализа (1-30)
            
        Returns:
            Tuple[Dict, bool, List[str]]: Данные тепловой карты, статус валидации, ошибки
        """
        # Валидировать период
        result = self.tracking_days_validator.validate({'tracking_days': days})
        if not result.is_valid:
            return None, False, result.errors
        
        try:
            today = datetime.now(timezone.utc).date()
            start_date = today - timedelta(days=days - 1)
            
            # Получить все логи за период
            logs = self.HabitLog.query.filter(
                self.HabitLog.habit_id.in_(
                    self.db.session.query(self.Habit.id).filter_by(user_id=user_id)
                ),
                self.HabitLog.date >= start_date,
                self.HabitLog.date <= today
            ).all()
            
            # Построить словарь дата -> количество выполнений
            heatmap = {}
            for i in range(days):
                date = start_date + timedelta(days=i)
                heatmap[date.isoformat()] = 0
            
            for log in logs:
                if log.completed:
                    date_key = log.date.isoformat()
                    if date_key in heatmap:
                        heatmap[date_key] += 1
            
            return {
                'user_id': user_id,
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': today.isoformat(),
                'heatmap': heatmap
            }, True, []
        except Exception as e:
            return None, False, [f"Ошибка при расчете тепловой карты: {str(e)}"]
