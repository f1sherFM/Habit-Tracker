"""
Интеграционные тесты для API тегов

Тестирование всех эндпоинтов тегов
"""
import pytest
import json


class TestTagsAPI:
    """Тесты для API тегов"""
    
    def test_get_empty_habit_tags(self, client, test_user, app):
        """Тест получения пустого списка тегов привычки"""
        user_id = test_user.id
        
        # Создать привычку
        with app.app_context():
            from app.models.habit import Habit
            from app import db
            
            habit = Habit(
                user_id=user_id,
                name='Бегать',
                description='Бегать каждый день',
                execution_time=30,
                frequency=1
            )
            db.session.add(habit)
            db.session.commit()
            habit_id = habit.id
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = client.get(f'/api/habits/{habit_id}/tags')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tags' in data
        assert data['total'] == 0
        assert data['tags'] == []
    
    def test_add_tags_to_habit(self, client, test_user, app):
        """Тест добавления тегов к привычке"""
        user_id = test_user.id
        
        # Создать привычку
        with app.app_context():
            from app.models.habit import Habit
            from app import db
            
            habit = Habit(
                user_id=user_id,
                name='Бегать',
                description='Бегать каждый день',
                execution_time=30,
                frequency=1
            )
            db.session.add(habit)
            db.session.commit()
            habit_id = habit.id
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        tags_data = {
            'tags': ['спорт', 'здоровье', 'утро']
        }
        
        response = client.post(
            f'/api/habits/{habit_id}/tags',
            data=json.dumps(tags_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'tags' in data
        assert data['total'] == 3
        assert len(data['tags']) == 3
        
        # Проверить, что все теги присутствуют
        tag_names = [tag['name'] for tag in data['tags']]
        assert 'спорт' in tag_names
        assert 'здоровье' in tag_names
        assert 'утро' in tag_names
    
    def test_add_tags_without_tags_field(self, client, test_user, app):
        """Тест добавления тегов без поля tags"""
        user_id = test_user.id
        
        # Создать привычку
        with app.app_context():
            from app.models.habit import Habit
            from app import db
            
            habit = Habit(
                user_id=user_id,
                name='Бегать',
                description='Бегать каждый день',
                execution_time=30,
                frequency=1
            )
            db.session.add(habit)
            db.session.commit()
            habit_id = habit.id
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        tags_data = {}
        
        response = client.post(
            f'/api/habits/{habit_id}/tags',
            data=json.dumps(tags_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'MISSING_REQUIRED_FIELDS'
    
    def test_add_tags_to_nonexistent_habit(self, client, test_user):
        """Тест добавления тегов к несуществующей привычке"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        tags_data = {
            'tags': ['спорт', 'здоровье']
        }
        
        response = client.post(
            '/api/habits/999/tags',
            data=json.dumps(tags_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'HABIT_NOT_FOUND'
    
    def test_get_habit_tags(self, client, test_user, app):
        """Тест получения тегов привычки"""
        user_id = test_user.id
        
        # Создать привычку с тегами
        with app.app_context():
            from app.models.habit import Habit
            from app.models.tag import Tag
            from app import db
            
            habit = Habit(
                user_id=user_id,
                name='Бегать',
                description='Бегать каждый день',
                execution_time=30,
                frequency=1
            )
            db.session.add(habit)
            db.session.commit()
            habit_id = habit.id
            
            # Добавить теги
            tag1 = Tag(user_id=user_id, name='спорт')
            tag2 = Tag(user_id=user_id, name='здоровье')
            db.session.add(tag1)
            db.session.add(tag2)
            db.session.commit()
            
            habit.tags.append(tag1)
            habit.tags.append(tag2)
            db.session.commit()
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = client.get(f'/api/habits/{habit_id}/tags')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] == 2
        assert len(data['tags']) == 2
        
        tag_names = [tag['name'] for tag in data['tags']]
        assert 'спорт' in tag_names
        assert 'здоровье' in tag_names
    
    def test_remove_tag_from_habit(self, client, test_user, app):
        """Тест удаления тега из привычки"""
        user_id = test_user.id
        
        # Создать привычку с тегами
        with app.app_context():
            from app.models.habit import Habit
            from app.models.tag import Tag
            from app import db
            
            habit = Habit(
                user_id=user_id,
                name='Бегать',
                description='Бегать каждый день',
                execution_time=30,
                frequency=1
            )
            db.session.add(habit)
            db.session.commit()
            habit_id = habit.id
            
            # Добавить теги
            tag1 = Tag(user_id=user_id, name='спорт')
            tag2 = Tag(user_id=user_id, name='здоровье')
            db.session.add(tag1)
            db.session.add(tag2)
            db.session.commit()
            tag1_id = tag1.id
            
            habit.tags.append(tag1)
            habit.tags.append(tag2)
            db.session.commit()
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        # Удалить тег
        response = client.delete(f'/api/habits/{habit_id}/tags/{tag1_id}')
        
        assert response.status_code == 204
        
        # Проверить, что тег удален
        get_response = client.get(f'/api/habits/{habit_id}/tags')
        data = json.loads(get_response.data)
        assert data['total'] == 1
        assert data['tags'][0]['name'] == 'здоровье'
    
    def test_remove_nonexistent_tag(self, client, test_user, app):
        """Тест удаления несуществующего тега"""
        user_id = test_user.id
        
        # Создать привычку
        with app.app_context():
            from app.models.habit import Habit
            from app import db
            
            habit = Habit(
                user_id=user_id,
                name='Бегать',
                description='Бегать каждый день',
                execution_time=30,
                frequency=1
            )
            db.session.add(habit)
            db.session.commit()
            habit_id = habit.id
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = client.delete(f'/api/habits/{habit_id}/tags/999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error']['code'] == 'TAG_NOT_FOUND'
    
    def test_get_tag_suggestions_empty(self, client, test_user):
        """Тест получения пустого списка предложений тегов"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        response = client.get('/api/tags/suggestions?prefix=xyz')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'suggestions' in data
        assert data['total'] == 0
        assert data['suggestions'] == []
    
    def test_get_tag_suggestions(self, client, test_user, app):
        """Тест получения предложений тегов"""
        user_id = test_user.id
        
        # Создать теги
        with app.app_context():
            from app.models.tag import Tag
            from app import db
            
            tag1 = Tag(user_id=user_id, name='спорт')
            tag2 = Tag(user_id=user_id, name='спортзал')
            tag3 = Tag(user_id=user_id, name='здоровье')
            db.session.add(tag1)
            db.session.add(tag2)
            db.session.add(tag3)
            db.session.commit()
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = client.get('/api/tags/suggestions?prefix=спор')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] == 2
        assert 'спорт' in data['suggestions']
        assert 'спортзал' in data['suggestions']
    
    def test_get_tag_suggestions_without_prefix(self, client, test_user, app):
        """Тест получения всех предложений тегов без префикса"""
        user_id = test_user.id
        
        # Создать теги
        with app.app_context():
            from app.models.tag import Tag
            from app import db
            
            tag1 = Tag(user_id=user_id, name='спорт')
            tag2 = Tag(user_id=user_id, name='здоровье')
            db.session.add(tag1)
            db.session.add(tag2)
            db.session.commit()
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = client.get('/api/tags/suggestions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] == 2
        assert 'спорт' in data['suggestions']
        assert 'здоровье' in data['suggestions']
    
    def test_add_tags_invalid_content_type(self, client, test_user, app):
        """Тест добавления тегов с неправильным типом контента"""
        user_id = test_user.id
        
        # Создать привычку
        with app.app_context():
            from app.models.habit import Habit
            from app import db
            
            habit = Habit(
                user_id=user_id,
                name='Бегать',
                description='Бегать каждый день',
                execution_time=30,
                frequency=1
            )
            db.session.add(habit)
            db.session.commit()
            habit_id = habit.id
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = client.post(
            f'/api/habits/{habit_id}/tags',
            data='tags=спорт&tags=здоровье',
            content_type='application/x-www-form-urlencoded'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_CONTENT_TYPE'
    
    def test_unauthenticated_access(self, client):
        """Тест доступа без аутентификации"""
        response = client.get('/api/habits/1/tags')
        
        # Должно быть перенаправление на логин или 401
        assert response.status_code in [401, 302]
