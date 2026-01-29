"""
Тесты для фильтрации и поиска (Фаза 8)

Тестирует функциональность фильтрации привычек по категориям и тегам,
а также поиск по комментариям.
"""
import pytest
from datetime import datetime, timezone, timedelta
from flask import json


class TestHabitFiltering:
    """Тесты для фильтрации привычек"""
    
    def test_filter_habits_by_category(self, authenticated_client, test_user, db):
        """
        Тест фильтрации привычек по категориям
        
        **Validates: Requirements 7.1**
        """
        # Создать категорию
        category_response = authenticated_client.post(
            '/api/categories',
            json={'name': 'Здоровье', 'color': '#6366f1'}
        )
        assert category_response.status_code == 201
        category_id = category_response.json['category']['id']
        
        # Создать привычку с категорией
        habit_response = authenticated_client.post(
            '/api/habits',
            json={
                'name': 'Бегать',
                'description': 'Бегать каждый день',
                'execution_time': 60,
                'frequency': 1,
                'habit_type': 'useful',
                'category_id': category_id
            }
        )
        assert habit_response.status_code == 201
        habit_id = habit_response.json['habit']['id']
        
        # Получить привычки с фильтром по категории
        filter_response = authenticated_client.get(
            f'/api/habits?category_id={category_id}'
        )
        assert filter_response.status_code == 200
        habits = filter_response.json['habits']
        assert len(habits) >= 1
        assert any(h['id'] == habit_id for h in habits)
    
    def test_filter_habits_by_tags(self, authenticated_client, test_user, db):
        """
        Тест фильтрации привычек по тегам
        
        **Validates: Requirements 7.2**
        """
        # Создать привычку
        habit_response = authenticated_client.post(
            '/api/habits',
            json={
                'name': 'Медитация',
                'description': 'Медитировать 10 минут',
                'execution_time': 600,
                'frequency': 1,
                'habit_type': 'pleasant'
            }
        )
        assert habit_response.status_code == 201
        habit_id = habit_response.json['habit']['id']
        
        # Добавить теги к привычке
        tags_response = authenticated_client.post(
            f'/api/habits/{habit_id}/tags',
            json={'tags': ['медитация', 'спокойствие']}
        )
        assert tags_response.status_code == 201
        tags = tags_response.json['tags']
        tag_ids = [tag['id'] for tag in tags]
        
        # Получить привычки с фильтром по тегам
        filter_response = authenticated_client.get(
            f'/api/habits?tag_ids={tag_ids[0]}'
        )
        assert filter_response.status_code == 200
        habits = filter_response.json['habits']
        assert len(habits) >= 1
        assert any(h['id'] == habit_id for h in habits)
    
    def test_combined_filtering_and_logic(self, authenticated_client, test_user, db):
        """
        Тест комбинированной фильтрации с логикой AND
        
        **Validates: Requirements 7.3**
        """
        # Создать категорию
        category_response = authenticated_client.post(
            '/api/categories',
            json={'name': 'Спорт', 'color': '#ff0000'}
        )
        assert category_response.status_code == 201
        category_id = category_response.json['category']['id']
        
        # Создать привычку с категорией
        habit_response = authenticated_client.post(
            '/api/habits',
            json={
                'name': 'Плавание',
                'description': 'Плавать в бассейне',
                'execution_time': 3600,
                'frequency': 3,
                'habit_type': 'useful',
                'category_id': category_id
            }
        )
        assert habit_response.status_code == 201
        habit_id = habit_response.json['habit']['id']
        
        # Добавить теги
        tags_response = authenticated_client.post(
            f'/api/habits/{habit_id}/tags',
            json={'tags': ['спорт', 'вода']}
        )
        assert tags_response.status_code == 201
        tags = tags_response.json['tags']
        tag_ids = [tag['id'] for tag in tags]
        
        # Получить привычки с комбинированным фильтром
        filter_response = authenticated_client.get(
            f'/api/habits?category_id={category_id}&tag_ids={tag_ids[0]},{tag_ids[1]}'
        )
        assert filter_response.status_code == 200
        habits = filter_response.json['habits']
        assert len(habits) >= 1
        assert any(h['id'] == habit_id for h in habits)
    
    def test_filter_with_invalid_tracking_days(self, authenticated_client, test_user):
        """
        Тест фильтрации с невалидным tracking_days
        
        **Validates: Requirements 10.1, 10.2**
        """
        # Попытка получить привычки с tracking_days < 1
        response = authenticated_client.get(
            '/api/habits?tracking_days=0'
        )
        assert response.status_code == 400
        assert 'tracking_days must be between 1 and 30' in response.json['error']['message']
        
        # Попытка получить привычки с tracking_days > 30
        response = authenticated_client.get(
            '/api/habits?tracking_days=31'
        )
        assert response.status_code == 400
        assert 'tracking_days must be between 1 and 30' in response.json['error']['message']


class TestCommentSearch:
    """Тесты для поиска по комментариям"""
    
    def test_search_comments_by_text(self, authenticated_client, test_user, db):
        """
        Тест поиска комментариев по тексту
        
        **Validates: Requirements 9.4**
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
        
        # Получить комментарии без поиска
        response = authenticated_client.get(
            f'/api/habits/{habit_id}/comments'
        )
        assert response.status_code == 200
        assert 'comments' in response.json
        assert 'total' in response.json
    
    def test_get_all_comments_without_search(self, authenticated_client, test_user, db):
        """
        Тест получения всех комментариев без поиска
        
        **Validates: Requirements 9.1**
        """
        # Создать привычку
        habit_response = authenticated_client.post(
            '/api/habits',
            json={
                'name': 'Йога',
                'description': 'Йога 30 минут',
                'execution_time': 1800,
                'frequency': 1,
                'habit_type': 'pleasant'
            }
        )
        assert habit_response.status_code == 201
        habit_id = habit_response.json['habit']['id']
        
        # Получить комментарии без поиска
        response = authenticated_client.get(
            f'/api/habits/{habit_id}/comments'
        )
        assert response.status_code == 200
        assert 'comments' in response.json
        assert 'total' in response.json


class TestFilteringEdgeCases:
    """Тесты граничных случаев для фильтрации"""
    
    def test_filter_with_nonexistent_category(self, authenticated_client, test_user):
        """
        Тест фильтрации с несуществующей категорией
        """
        response = authenticated_client.get(
            '/api/habits?category_id=99999'
        )
        assert response.status_code == 200
        assert response.json['total'] == 0
    
    def test_filter_with_invalid_tag_ids(self, authenticated_client, test_user):
        """
        Тест фильтрации с невалидными ID тегов
        """
        response = authenticated_client.get(
            '/api/habits?tag_ids=invalid,ids'
        )
        assert response.status_code == 400
        assert 'tag_ids must be comma-separated integers' in response.json['error']['message']
    
    def test_filter_empty_results(self, authenticated_client, test_user, db):
        """
        Тест фильтрации с пустым результатом
        """
        # Создать категорию без привычек
        category_response = authenticated_client.post(
            '/api/categories',
            json={'name': 'Пустая категория', 'color': '#000000'}
        )
        assert category_response.status_code == 201
        category_id = category_response.json['category']['id']
        
        # Получить привычки с фильтром
        response = authenticated_client.get(
            f'/api/habits?category_id={category_id}'
        )
        assert response.status_code == 200
        assert response.json['total'] == 0
