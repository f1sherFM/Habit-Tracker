"""
Интеграционные тесты для API комментариев

Тестирование всех эндпоинтов комментариев
"""
import pytest
import json


class TestCommentsAPI:
    """Тесты для API комментариев"""
    
    def test_get_empty_habit_comments(self, client, test_user, app):
        """Тест получения пустого списка комментариев привычки"""
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
        
        response = client.get(f'/api/habits/{habit_id}/comments')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'comments' in data
        assert data['total'] == 0
        assert data['comments'] == []
    
    def test_add_comment(self, client, test_user, app):
        """Тест добавления комментария"""
        user_id = test_user.id
        
        # Создать привычку и запись о выполнении
        with app.app_context():
            from app.models.habit import Habit
            from app.models.habit_log import HabitLog
            from app import db
            from datetime import datetime
            
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
            
            habit_log = HabitLog(
                habit_id=habit_id,
                date=datetime.now().date(),
                completed=True
            )
            db.session.add(habit_log)
            db.session.commit()
            habit_log_id = habit_log.id
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        comment_data = {
            'habit_id': habit_id,
            'text': 'Отличное выполнение!'
        }
        
        response = client.post(
            f'/api/habit-logs/{habit_log_id}/comments',
            data=json.dumps(comment_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'comment' in data
        assert data['comment']['text'] == 'Отличное выполнение!'
        assert data['comment']['habit_id'] == habit_id
        assert data['comment']['habit_log_id'] == habit_log_id
        assert data['comment']['is_edited'] == False
    
    def test_add_comment_without_text(self, client, test_user, app):
        """Тест добавления комментария без текста"""
        user_id = test_user.id
        
        # Создать привычку и запись о выполнении
        with app.app_context():
            from app.models.habit import Habit
            from app.models.habit_log import HabitLog
            from app import db
            from datetime import datetime
            
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
            
            habit_log = HabitLog(
                habit_id=habit_id,
                date=datetime.now().date(),
                completed=True
            )
            db.session.add(habit_log)
            db.session.commit()
            habit_log_id = habit_log.id
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        comment_data = {
            'habit_id': habit_id
        }
        
        response = client.post(
            f'/api/habit-logs/{habit_log_id}/comments',
            data=json.dumps(comment_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'MISSING_REQUIRED_FIELDS'
    
    def test_get_habit_comments(self, client, test_user, app):
        """Тест получения комментариев привычки"""
        user_id = test_user.id
        
        # Создать привычку, запись о выполнении и комментарии
        with app.app_context():
            from app.models.habit import Habit
            from app.models.habit_log import HabitLog
            from app.models.comment import Comment
            from app import db
            from datetime import datetime
            
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
            
            habit_log = HabitLog(
                habit_id=habit_id,
                date=datetime.now().date(),
                completed=True
            )
            db.session.add(habit_log)
            db.session.commit()
            habit_log_id = habit_log.id
            
            comment1 = Comment(
                habit_id=habit_id,
                habit_log_id=habit_log_id,
                text='Первый комментарий'
            )
            comment2 = Comment(
                habit_id=habit_id,
                habit_log_id=habit_log_id,
                text='Второй комментарий'
            )
            db.session.add(comment1)
            db.session.add(comment2)
            db.session.commit()
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = client.get(f'/api/habits/{habit_id}/comments')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] == 2
        assert len(data['comments']) == 2
        assert data['comments'][0]['text'] == 'Первый комментарий'
        assert data['comments'][1]['text'] == 'Второй комментарий'
    
    def test_update_comment(self, client, test_user, app):
        """Тест обновления комментария"""
        user_id = test_user.id
        
        # Создать привычку, запись о выполнении и комментарий
        with app.app_context():
            from app.models.habit import Habit
            from app.models.habit_log import HabitLog
            from app.models.comment import Comment
            from app import db
            from datetime import datetime
            
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
            
            habit_log = HabitLog(
                habit_id=habit_id,
                date=datetime.now().date(),
                completed=True
            )
            db.session.add(habit_log)
            db.session.commit()
            
            comment = Comment(
                habit_id=habit_id,
                habit_log_id=habit_log.id,
                text='Исходный текст'
            )
            db.session.add(comment)
            db.session.commit()
            comment_id = comment.id
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        update_data = {
            'habit_id': habit_id,
            'text': 'Обновленный текст'
        }
        
        response = client.put(
            f'/api/comments/{comment_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['comment']['text'] == 'Обновленный текст'
        assert data['comment']['is_edited'] == True
    
    def test_delete_comment(self, client, test_user, app):
        """Тест удаления комментария"""
        user_id = test_user.id
        
        # Создать привычку, запись о выполнении и комментарий
        with app.app_context():
            from app.models.habit import Habit
            from app.models.habit_log import HabitLog
            from app.models.comment import Comment
            from app import db
            from datetime import datetime
            
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
            
            habit_log = HabitLog(
                habit_id=habit_id,
                date=datetime.now().date(),
                completed=True
            )
            db.session.add(habit_log)
            db.session.commit()
            
            comment = Comment(
                habit_id=habit_id,
                habit_log_id=habit_log.id,
                text='Комментарий для удаления'
            )
            db.session.add(comment)
            db.session.commit()
            comment_id = comment.id
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = client.delete(f'/api/comments/{comment_id}?habit_id={habit_id}')
        
        assert response.status_code == 204
        
        # Проверить, что комментарий удален
        get_response = client.get(f'/api/habits/{habit_id}/comments')
        data = json.loads(get_response.data)
        assert data['total'] == 0
    
    def test_search_comments(self, client, test_user, app):
        """Тест поиска комментариев"""
        user_id = test_user.id
        
        # Создать привычку, запись о выполнении и комментарии
        with app.app_context():
            from app.models.habit import Habit
            from app.models.habit_log import HabitLog
            from app.models.comment import Comment
            from app import db
            from datetime import datetime
            
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
            
            habit_log = HabitLog(
                habit_id=habit_id,
                date=datetime.now().date(),
                completed=True
            )
            db.session.add(habit_log)
            db.session.commit()
            
            comment1 = Comment(
                habit_id=habit_id,
                habit_log_id=habit_log.id,
                text='Отличное выполнение'
            )
            comment2 = Comment(
                habit_id=habit_id,
                habit_log_id=habit_log.id,
                text='Плохое выполнение'
            )
            db.session.add(comment1)
            db.session.add(comment2)
            db.session.commit()
        
        # Логин пользователя
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = client.get(f'/api/habits/{habit_id}/comments?search=Отличное')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] == 1
        assert 'Отличное' in data['comments'][0]['text']
    
    def test_unauthenticated_access(self, client):
        """Тест доступа без аутентификации"""
        response = client.get('/api/habits/1/comments')
        
        # Должно быть перенаправление на логин или 401
        assert response.status_code in [401, 302]
