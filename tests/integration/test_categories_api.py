"""
Интеграционные тесты для API категорий

Тестирование всех эндпоинтов категорий
"""
import pytest
import json
from datetime import datetime


class TestCategoriesAPI:
    """Тесты для API категорий"""
    
    def test_get_empty_categories(self, client, test_user):
        """Тест получения пустого списка категорий"""
        # Логин пользователя используя session
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        response = client.get('/api/categories')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'categories' in data
        assert data['total'] == 0
        assert data['categories'] == []
    
    def test_create_category(self, client, test_user):
        """Тест создания категории"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        category_data = {
            'name': 'Здоровье',
            'color': '#6366f1',
            'icon': 'heart'
        }
        
        response = client.post(
            '/api/categories',
            data=json.dumps(category_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'category' in data
        assert data['category']['name'] == 'Здоровье'
        assert data['category']['color'] == '#6366f1'
        assert data['category']['icon'] == 'heart'
        assert 'id' in data['category']
        assert 'created_at' in data['category']
    
    def test_create_category_without_name(self, client, test_user):
        """Тест создания категории без имени"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        category_data = {
            'color': '#6366f1'
        }
        
        response = client.post(
            '/api/categories',
            data=json.dumps(category_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'MISSING_REQUIRED_FIELDS'
    
    def test_create_duplicate_category(self, client, test_user):
        """Тест создания дублирующейся категории"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        category_data = {
            'name': 'Здоровье',
            'color': '#6366f1'
        }
        
        # Создать первую категорию
        response1 = client.post(
            '/api/categories',
            data=json.dumps(category_data),
            content_type='application/json'
        )
        assert response1.status_code == 201
        
        # Попытаться создать дублирующуюся категорию
        response2 = client.post(
            '/api/categories',
            data=json.dumps(category_data),
            content_type='application/json'
        )
        
        assert response2.status_code == 400
        data = json.loads(response2.data)
        assert 'error' in data
        assert 'уже существует' in data['error']['details'][0]
    
    def test_get_categories(self, client, test_user):
        """Тест получения списка категорий"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        # Создать несколько категорий
        categories_data = [
            {'name': 'Здоровье', 'color': '#6366f1'},
            {'name': 'Учеба', 'color': '#ec4899'},
            {'name': 'Работа', 'color': '#f59e0b'}
        ]
        
        for cat_data in categories_data:
            client.post(
                '/api/categories',
                data=json.dumps(cat_data),
                content_type='application/json'
            )
        
        # Получить все категории
        response = client.get('/api/categories')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] == 3
        assert len(data['categories']) == 3
        
        # Проверить, что все категории присутствуют
        names = [cat['name'] for cat in data['categories']]
        assert 'Здоровье' in names
        assert 'Учеба' in names
        assert 'Работа' in names
    
    def test_get_category_by_id(self, client, test_user):
        """Тест получения категории по ID"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        # Создать категорию
        category_data = {
            'name': 'Здоровье',
            'color': '#6366f1',
            'icon': 'heart'
        }
        
        create_response = client.post(
            '/api/categories',
            data=json.dumps(category_data),
            content_type='application/json'
        )
        
        category_id = json.loads(create_response.data)['category']['id']
        
        # Получить категорию по ID
        response = client.get(f'/api/categories/{category_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'category' in data
        assert data['category']['id'] == category_id
        assert data['category']['name'] == 'Здоровье'
    
    def test_get_nonexistent_category(self, client, test_user):
        """Тест получения несуществующей категории"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        response = client.get('/api/categories/999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'CATEGORY_NOT_FOUND'
    
    def test_update_category(self, client, test_user):
        """Тест обновления категории"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        # Создать категорию
        category_data = {
            'name': 'Здоровье',
            'color': '#6366f1'
        }
        
        create_response = client.post(
            '/api/categories',
            data=json.dumps(category_data),
            content_type='application/json'
        )
        
        category_id = json.loads(create_response.data)['category']['id']
        
        # Обновить категорию
        update_data = {
            'name': 'Фитнес',
            'color': '#ff0000',
            'icon': 'dumbbell'
        }
        
        response = client.put(
            f'/api/categories/{category_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['category']['name'] == 'Фитнес'
        assert data['category']['color'] == '#ff0000'
        assert data['category']['icon'] == 'dumbbell'
    
    def test_update_nonexistent_category(self, client, test_user):
        """Тест обновления несуществующей категории"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        update_data = {
            'name': 'Новое имя'
        }
        
        response = client.put(
            '/api/categories/999',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'CATEGORY_NOT_FOUND'
    
    def test_delete_category(self, client, test_user):
        """Тест удаления категории"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        # Создать категорию
        category_data = {
            'name': 'Здоровье',
            'color': '#6366f1'
        }
        
        create_response = client.post(
            '/api/categories',
            data=json.dumps(category_data),
            content_type='application/json'
        )
        
        category_id = json.loads(create_response.data)['category']['id']
        
        # Удалить категорию
        response = client.delete(f'/api/categories/{category_id}')
        
        assert response.status_code == 204
        
        # Проверить, что категория удалена
        get_response = client.get(f'/api/categories/{category_id}')
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_category(self, client, test_user):
        """Тест удаления несуществующей категории"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        response = client.delete('/api/categories/999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'CATEGORY_NOT_FOUND'
    
    def test_delete_category_with_habits(self, client, test_user, app):
        """Тест удаления категории с привычками (привычки должны переместиться в "Без категории")"""
        user_id = test_user.id
        
        # Создать привычку в категории перед логином
        with app.app_context():
            from app.models.category import Category
            from app.models.habit import Habit
            from app import db
            
            # Создать категорию
            category = Category(
                user_id=user_id,
                name='Здоровье',
                color='#6366f1'
            )
            db.session.add(category)
            db.session.commit()
            category_id = category.id
            
            # Создать привычку в этой категории
            habit = Habit(
                user_id=user_id,
                name='Бегать',
                description='Бегать каждый день',
                execution_time=30,
                frequency=1,
                category_id=category_id
            )
            db.session.add(habit)
            db.session.commit()
            habit_id = habit.id
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        # Удалить категорию
        response = client.delete(f'/api/categories/{category_id}')
        assert response.status_code == 204
        
        # Проверить, что привычка больше не связана с категорией
        with app.app_context():
            from app.models.habit import Habit
            habit = Habit.query.get(habit_id)
            assert habit.category_id is None
    
    def test_create_category_invalid_content_type(self, client, test_user):
        """Тест создания категории с неправильным типом контента"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        response = client.post(
            '/api/categories',
            data='name=Здоровье',
            content_type='application/x-www-form-urlencoded'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_CONTENT_TYPE'
    
    def test_update_category_empty_body(self, client, test_user):
        """Тест обновления категории с пустым телом запроса"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        # Создать категорию
        category_data = {
            'name': 'Здоровье',
            'color': '#6366f1'
        }
        
        create_response = client.post(
            '/api/categories',
            data=json.dumps(category_data),
            content_type='application/json'
        )
        
        category_id = json.loads(create_response.data)['category']['id']
        
        # Попытаться обновить с пустым телом
        response = client.put(
            f'/api/categories/{category_id}',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        # Должно быть 400, так как нет данных для обновления
        assert response.status_code == 400
    
    def test_unauthenticated_access(self, client):
        """Тест доступа без аутентификации"""
        response = client.get('/api/categories')
        
        # Должно быть перенаправление на логин или 401
        assert response.status_code in [401, 302]
