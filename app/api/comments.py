"""
API Эндпоинты для Комментариев

RESTful API для управления комментариями к привычкам
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from ..services.comment_service import CommentService, CommentNotFoundError, CommentServiceError
import logging

# Создать blueprint
comments_bp = Blueprint('comments_api', __name__, url_prefix='/api')

# Сервис будет инициализирован при необходимости
comment_service = None

def get_comment_service():
    """Получить или создать экземпляр CommentService"""
    global comment_service
    if comment_service is None:
        comment_service = CommentService()
    return comment_service

logger = logging.getLogger(__name__)


@comments_bp.route('/habits/<int:habit_id>/comments', methods=['GET'])
@login_required
def get_habit_comments(habit_id):
    """
    Получить все комментарии привычки с опциональным поиском
    
    Args:
        habit_id: ID привычки
        
    Query parameters:
        search: Текст для поиска в комментариях (опционально)
        
    Returns:
        JSON ответ со списком комментариев
    """
    try:
        # Получить параметры запроса
        search = request.args.get('search', '').strip()
        
        # Получить комментарии используя сервис
        comment_service = get_comment_service()
        
        if search:
            comments = comment_service.search_comments(habit_id, current_user.id, search)
        else:
            comments = comment_service.get_habit_comments(habit_id, current_user.id)
        
        # Преобразовать в JSON формат
        comments_data = []
        for comment in comments:
            comment_dict = {
                'id': comment.id,
                'habit_id': comment.habit_id,
                'habit_log_id': comment.habit_log_id,
                'text': comment.text,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
                'updated_at': comment.updated_at.isoformat() if comment.updated_at else None,
                'is_edited': comment.created_at != comment.updated_at if comment.created_at and comment.updated_at else False
            }
            comments_data.append(comment_dict)
        
        return jsonify({
            'comments': comments_data,
            'total': len(comments_data),
            'search_query': search if search else None
        }), 200
        
    except CommentServiceError as e:
        logger.error(f"Ошибка сервиса при получении комментариев привычки {habit_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось получить комментарии',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении комментариев привычки {habit_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@comments_bp.route('/habit-logs/<int:habit_log_id>/comments', methods=['POST'])
@login_required
def add_comment(habit_log_id):
    """
    Добавить комментарий к выполнению привычки
    
    Expected JSON payload:
    {
        "habit_id": 1,
        "text": "Отличное выполнение!"
    }
    
    Returns:
        JSON ответ с добавленным комментарием
    """
    try:
        # Валидировать тип контента
        if not request.is_json:
            return jsonify({
                'error': {
                    'code': 'INVALID_CONTENT_TYPE',
                    'message': 'Content-Type должен быть application/json'
                }
            }), 400
        
        data = request.get_json()
        
        # Валидировать обязательные поля
        if not data or not data.get('habit_id') or not data.get('text'):
            return jsonify({
                'error': {
                    'code': 'MISSING_REQUIRED_FIELDS',
                    'message': 'Поля habit_id и text обязательны'
                }
            }), 400
        
        # Добавить комментарий используя сервис
        comment_service = get_comment_service()
        comment, success, errors = comment_service.add_comment(
            habit_log_id,
            data.get('habit_id'),
            current_user.id,
            data.get('text')
        )
        
        if not success:
            if "не найдена" in errors[0]:
                return jsonify({
                    'error': {
                        'code': 'HABIT_NOT_FOUND',
                        'message': 'Привычка не найдена'
                    }
                }), 404
            elif "не найдена" in errors[0] and "запись" in errors[0]:
                return jsonify({
                    'error': {
                        'code': 'HABIT_LOG_NOT_FOUND',
                        'message': 'Запись о выполнении привычки не найдена'
                    }
                }), 404
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Ошибка валидации данных комментария',
                    'details': errors
                }
            }), 400
        
        # Вернуть добавленный комментарий
        return jsonify({
            'comment': {
                'id': comment.id,
                'habit_id': comment.habit_id,
                'habit_log_id': comment.habit_log_id,
                'text': comment.text,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
                'updated_at': comment.updated_at.isoformat() if comment.updated_at else None,
                'is_edited': False
            }
        }), 201
        
    except CommentServiceError as e:
        logger.error(f"Ошибка сервиса при добавлении комментария для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось добавить комментарий',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при добавлении комментария для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@comments_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@login_required
def update_comment(comment_id):
    """
    Обновить комментарий
    
    Expected JSON payload:
    {
        "habit_id": 1,
        "text": "Обновленный текст комментария"
    }
    
    Returns:
        JSON ответ с обновленным комментарием
    """
    try:
        # Валидировать тип контента
        if not request.is_json:
            return jsonify({
                'error': {
                    'code': 'INVALID_CONTENT_TYPE',
                    'message': 'Content-Type должен быть application/json'
                }
            }), 400
        
        data = request.get_json()
        
        # Валидировать обязательные поля
        if not data or not data.get('habit_id') or not data.get('text'):
            return jsonify({
                'error': {
                    'code': 'MISSING_REQUIRED_FIELDS',
                    'message': 'Поля habit_id и text обязательны'
                }
            }), 400
        
        # Обновить комментарий используя сервис
        comment_service = get_comment_service()
        comment, success, errors = comment_service.update_comment(
            comment_id,
            data.get('habit_id'),
            current_user.id,
            data.get('text')
        )
        
        if not success:
            if "не найден" in errors[0]:
                return jsonify({
                    'error': {
                        'code': 'COMMENT_NOT_FOUND',
                        'message': f'Комментарий с ID {comment_id} не найден'
                    }
                }), 404
            elif "не найдена" in errors[0]:
                return jsonify({
                    'error': {
                        'code': 'HABIT_NOT_FOUND',
                        'message': 'Привычка не найдена'
                    }
                }), 404
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Ошибка валидации данных комментария',
                    'details': errors
                }
            }), 400
        
        # Вернуть обновленный комментарий
        return jsonify({
            'comment': {
                'id': comment.id,
                'habit_id': comment.habit_id,
                'habit_log_id': comment.habit_log_id,
                'text': comment.text,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
                'updated_at': comment.updated_at.isoformat() if comment.updated_at else None,
                'is_edited': comment.created_at != comment.updated_at if comment.created_at and comment.updated_at else False
            }
        }), 200
        
    except CommentServiceError as e:
        logger.error(f"Ошибка сервиса при обновлении комментария {comment_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось обновить комментарий',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обновлении комментария {comment_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@comments_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """
    Удалить комментарий
    
    Query parameters:
        habit_id: ID привычки (обязательно)
        
    Returns:
        Пустой ответ с кодом 204 при успехе
    """
    try:
        # Получить параметры запроса
        habit_id = request.args.get('habit_id', type=int)
        
        if not habit_id:
            return jsonify({
                'error': {
                    'code': 'MISSING_REQUIRED_FIELDS',
                    'message': 'Параметр habit_id обязателен'
                }
            }), 400
        
        # Удалить комментарий используя сервис
        comment_service = get_comment_service()
        success, errors = comment_service.delete_comment(comment_id, habit_id, current_user.id)
        
        if not success:
            if "не найден" in errors[0]:
                return jsonify({
                    'error': {
                        'code': 'COMMENT_NOT_FOUND',
                        'message': f'Комментарий с ID {comment_id} не найден'
                    }
                }), 404
            elif "не найдена" in errors[0]:
                return jsonify({
                    'error': {
                        'code': 'HABIT_NOT_FOUND',
                        'message': 'Привычка не найдена'
                    }
                }), 404
            return jsonify({
                'error': {
                    'code': 'DELETE_ERROR',
                    'message': 'Не удалось удалить комментарий',
                    'details': errors
                }
            }), 400
        
        # Вернуть пустой ответ с кодом 204 No Content
        return '', 204
        
    except CommentServiceError as e:
        logger.error(f"Ошибка сервиса при удалении комментария {comment_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось удалить комментарий',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при удалении комментария {comment_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


# Обработчики ошибок для blueprint
@comments_bp.errorhandler(404)
def handle_not_found(error):
    """Обработать ошибки 404 в API комментариев"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Запрашиваемый ресурс не найден'
        }
    }), 404


@comments_bp.errorhandler(405)
def handle_method_not_allowed(error):
    """Обработать ошибки 405 в API комментариев"""
    return jsonify({
        'error': {
            'code': 'METHOD_NOT_ALLOWED',
            'message': 'Запрашиваемый метод не разрешен для этого ресурса'
        }
    }), 405
