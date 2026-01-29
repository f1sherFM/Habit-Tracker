"""
Тесты для гибкого периода отслеживания (Фаза 9)

Тестирует функциональность поддержки переменного периода отслеживания
от 1 до 30 дней.
"""
import pytest
from datetime import datetime, timezone, timedelta
from flask import json


class TestTrackingDaysParameter:
    """Тесты для параметра tracking_days"""
    
    def test_get_habits_with_tracking_days(self, authenticated_client, test_user, db):
        """
        Тест получения привычек с параметром tracking_days
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Создать привычку
        habit_response = authenticated_client.post(
            '/api/habits',
            json={
                'name': 'Упражнения',
                'description': 'Физические упражнения',
                'execution_time': 1800,
                'frequency': 1,
                'habit_type': 'useful'
            }
        )
        assert habit_response.status_code == 201
        
        # Получить привычки с tracking_days=14
        response = authenticated_client.get(
            '/api/habits?tracking_days=14'
        )
        assert response.status_code == 200
        assert response.json['tracking_days'] == 14
        assert len(response.json['habits']) > 0
    
    def test_analytics_with_tracking_days(self, authenticated_client, test_user, db):
        """
        Тест получения аналитики с параметром tracking_days
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Создать привычку
        habit_response = authenticated_client.post(
            '/api/habits',
            json={
                'name': 'Медитация',
                'description': 'Медитировать',
                'execution_time': 600,
                'frequency': 1,
                'habit_type': 'pleasant'
            }
        )
        assert habit_response.status_code == 201
        habit_id = habit_response.json['habit']['id']
        
        # Получить аналитику с tracking_days=7
        response = authenticated_client.get(
            f'/api/analytics/habits/{habit_id}?tracking_days=7'
        )
        assert response.status_code == 200
        assert response.json['tracking_days'] == 7
    
    def test_analytics_overview_with_tracking_days(self, authenticated_client, test_user):
        """
        Тест получения общей аналитики с параметром tracking_days
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Получить общую аналитику с tracking_days=30
        response = authenticated_client.get(
            '/api/analytics/overview?tracking_days=30'
        )
        assert response.status_code == 200
        assert response.json['tracking_days'] == 30
    
    def test_heatmap_with_tracking_days(self, authenticated_client, test_user):
        """
        Тест получения тепловой карты с параметром tracking_days
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Получить тепловую карту с tracking_days=14
        response = authenticated_client.get(
            '/api/analytics/heatmap?tracking_days=14'
        )
        assert response.status_code == 200
        assert response.json['tracking_days'] == 14


class TestDefaultTrackingDays:
    """Тесты для default_tracking_days в профиле пользователя"""
    
    def test_get_user_default_tracking_days(self, authenticated_client, test_user):
        """
        Тест получения default_tracking_days из профиля пользователя
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        response = authenticated_client.get(
            '/api/users/me'
        )
        assert response.status_code == 200
        assert 'default_tracking_days' in response.json['user']
        assert response.json['user']['default_tracking_days'] == 7  # Default value
    
    def test_update_user_default_tracking_days(self, authenticated_client, test_user):
        """
        Тест обновления default_tracking_days в профиле пользователя
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Обновить default_tracking_days
        response = authenticated_client.put(
            '/api/users/me',
            json={'default_tracking_days': 14}
        )
        assert response.status_code == 200
        assert response.json['user']['default_tracking_days'] == 14
        
        # Проверить, что значение сохранилось
        get_response = authenticated_client.get(
            '/api/users/me'
        )
        assert get_response.status_code == 200
        assert get_response.json['user']['default_tracking_days'] == 14
    
    def test_update_user_with_invalid_tracking_days(self, authenticated_client, test_user):
        """
        Тест обновления default_tracking_days с невалидным значением
        
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        # Попытка установить tracking_days < 1
        response = authenticated_client.put(
            '/api/users/me',
            json={'default_tracking_days': 0}
        )
        assert response.status_code == 400
        assert 'must be an integer between 1 and 30' in response.json['error']['message']
        
        # Попытка установить tracking_days > 30
        response = authenticated_client.put(
            '/api/users/me',
            json={'default_tracking_days': 31}
        )
        assert response.status_code == 400
        assert 'must be an integer between 1 and 30' in response.json['error']['message']
        
        # Попытка установить tracking_days как строку
        response = authenticated_client.put(
            '/api/users/me',
            json={'default_tracking_days': 'invalid'}
        )
        assert response.status_code == 400
        assert 'must be an integer between 1 and 30' in response.json['error']['message']


class TestTrackingDaysValidation:
    """Тесты для валидации tracking_days"""
    
    def test_tracking_days_boundary_values(self, authenticated_client, test_user):
        """
        Тест граничных значений tracking_days
        
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        # Минимальное значение (1)
        response = authenticated_client.get(
            '/api/habits?tracking_days=1'
        )
        assert response.status_code == 200
        assert response.json['tracking_days'] == 1
        
        # Максимальное значение (30)
        response = authenticated_client.get(
            '/api/habits?tracking_days=30'
        )
        assert response.status_code == 200
        assert response.json['tracking_days'] == 30
    
    def test_tracking_days_invalid_values(self, authenticated_client, test_user):
        """
        Тест невалидных значений tracking_days
        
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        # Значение меньше 1
        response = authenticated_client.get(
            '/api/habits?tracking_days=0'
        )
        assert response.status_code == 400
        
        # Значение больше 30
        response = authenticated_client.get(
            '/api/habits?tracking_days=31'
        )
        assert response.status_code == 400
        
        # Отрицательное значение
        response = authenticated_client.get(
            '/api/habits?tracking_days=-5'
        )
        assert response.status_code == 400
    
    def test_tracking_days_default_value(self, authenticated_client, test_user):
        """
        Тест значения по умолчанию для tracking_days
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Получить привычки без указания tracking_days
        response = authenticated_client.get(
            '/api/habits'
        )
        assert response.status_code == 200
        assert response.json['tracking_days'] == 7  # Default value


class TestTrackingDaysIntegration:
    """Интеграционные тесты для tracking_days"""
    
    def test_tracking_days_affects_analytics(self, authenticated_client, test_user, db):
        """
        Тест того, что tracking_days влияет на расчеты аналитики
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Создать привычку
        habit_response = authenticated_client.post(
            '/api/habits',
            json={
                'name': 'Чтение',
                'description': 'Читать книгу',
                'execution_time': 1800,
                'frequency': 1,
                'habit_type': 'pleasant'
            }
        )
        assert habit_response.status_code == 201
        habit_id = habit_response.json['habit']['id']
        
        # Получить аналитику с разными tracking_days
        response_7 = authenticated_client.get(
            f'/api/analytics/habits/{habit_id}?tracking_days=7'
        )
        assert response_7.status_code == 200
        
        response_14 = authenticated_client.get(
            f'/api/analytics/habits/{habit_id}?tracking_days=14'
        )
        assert response_14.status_code == 200
        
        # Оба ответа должны содержать tracking_days
        assert response_7.json['tracking_days'] == 7
        assert response_14.json['tracking_days'] == 14
    
    def test_tracking_days_with_category_analytics(self, authenticated_client, test_user, db):
        """
        Тест tracking_days с аналитикой по категориям
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Создать категорию
        category_response = authenticated_client.post(
            '/api/categories',
            json={'name': 'Здоровье', 'color': '#6366f1'}
        )
        assert category_response.status_code == 201
        category_id = category_response.json['category']['id']
        
        # Получить аналитику категории с tracking_days
        response = authenticated_client.get(
            f'/api/analytics/categories/{category_id}?tracking_days=21'
        )
        assert response.status_code == 200
        assert response.json['tracking_days'] == 21


class TestTrackingDaysAlternativeParameter:
    """Тесты для альтернативного имени параметра tracking_days"""
    
    def test_days_parameter_still_works(self, authenticated_client, test_user):
        """
        Тест того, что старый параметр 'days' все еще работает
        """
        response = authenticated_client.get(
            '/api/analytics/overview?days=14'
        )
        assert response.status_code == 200
        assert response.json['tracking_days'] == 14
    
    def test_tracking_days_parameter_preferred(self, authenticated_client, test_user):
        """
        Тест того, что параметр tracking_days имеет приоритет над days
        """
        response = authenticated_client.get(
            '/api/analytics/overview?days=7&tracking_days=14'
        )
        assert response.status_code == 200
        # tracking_days должен иметь приоритет
        assert response.json['tracking_days'] == 14
