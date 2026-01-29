"""
API Эндпоинты для Тегов

RESTful API для управления тегами привычек
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from ..services.tag_service import TagService, TagNotFoundError, TagServiceError
import logging

# Создать blueprint
tags_bp = Blueprint('tags_api', __name__, url_prefix='/api')

# Сервис будет инициализирован при необходимости
tag_service = None

def get_tag_service():
    """Получить или создать экземпляр TagService"""
    global tag_service
    if tag_service is None:
        tag_service = TagService()
    return tag_service

logger = logging.getLogger(__name__)


@tags_bp.route('/habits/<int:habit_id>/tags', methods=['GET'])
@login_required
def get_habit_tags(habit_id):
    """
    Получить все теги привычки
    
    Args:
        habit_id: ID привычки
        
    Returns:
        JSON ответ со списком тегов
    """
    try:
        # Получить теги используя сервис
        tag_service = get_tag_service()
        tags = tag_service.get_habit_tags(habit_id, current_user.id)
        
        # Преобразовать в JSON формат
        tags_data = []
        for tag in tags:
            tag_dict = {
                'id': tag.id,
                'name': tag.name,
                'created_at': tag.created_at.isoformat() if tag.created_at else None
            }
            tags_data.append(tag_dict)
        
        return jsonify({
            'tags': tags_data,
            'total': len(tags_data)
        }), 200
        
    except TagServiceError as e:
        logger.error(f"Ошибка сервиса при получении тегов привычки {habit_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось получить теги',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении тегов привычки {habit_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@tags_bp.route('/habits/<int:habit_id>/tags', methods=['POST'])
@login_required
def add_tags_to_habit(habit_id):
    """
    Добавить теги к привычке
    
    Expected JSON payload:
    {
        "tags": ["спорт", "здоровье", "утро"]
    }
    
    Returns:
        JSON ответ с добавленными тегами
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
        if not data or not data.get('tags'):
            return jsonify({
                'error': {
                    'code': 'MISSING_REQUIRED_FIELDS',
                    'message': 'Список тегов обязателен'
                }
            }), 400
        
        # Добавить теги используя сервис
        tag_service = get_tag_service()
        tags, success, errors = tag_service.add_tags_to_habit(
            habit_id,
            current_user.id,
            data.get('tags')
        )
        
        if not success:
            if "не найдена" in errors[0]:
                return jsonify({
                    'error': {
                        'code': 'HABIT_NOT_FOUND',
                        'message': f'Привычка с ID {habit_id} не найдена'
                    }
                }), 404
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Ошибка валидации данных тегов',
                    'details': errors
                }
            }), 400
        
        # Вернуть добавленные теги
        tags_data = []
        for tag in tags:
            tag_dict = {
                'id': tag.id,
                'name': tag.name,
                'created_at': tag.created_at.isoformat() if tag.created_at else None
            }
            tags_data.append(tag_dict)
        
        return jsonify({
            'tags': tags_data,
            'total': len(tags_data)
        }), 201
        
    except TagServiceError as e:
        logger.error(f"Ошибка сервиса при добавлении тегов к привычке {habit_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось добавить теги',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при добавлении тегов к привычке {habit_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@tags_bp.route('/habits/<int:habit_id>/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def remove_tag_from_habit(habit_id, tag_id):
    """
    Удалить тег из привычки
    
    Args:
        habit_id: ID привычки
        tag_id: ID тега
        
    Returns:
        Пустой ответ с кодом 204 при успехе
    """
    try:
        # Удалить тег используя сервис
        tag_service = get_tag_service()
        success, errors = tag_service.remove_tag_from_habit(habit_id, tag_id, current_user.id)
        
        if not success:
            if "не найдена" in errors[0]:
                return jsonify({
                    'error': {
                        'code': 'HABIT_NOT_FOUND',
                        'message': f'Привычка с ID {habit_id} не найдена'
                    }
                }), 404
            elif "не найден" in errors[0]:
                return jsonify({
                    'error': {
                        'code': 'TAG_NOT_FOUND',
                        'message': f'Тег с ID {tag_id} не найден'
                    }
                }), 404
            return jsonify({
                'error': {
                    'code': 'DELETE_ERROR',
                    'message': 'Не удалось удалить тег',
                    'details': errors
                }
            }), 400
        
        # Вернуть пустой ответ с кодом 204 No Content
        return '', 204
        
    except TagServiceError as e:
        logger.error(f"Ошибка сервиса при удалении тега {tag_id} из привычки {habit_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось удалить тег',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при удалении тега {tag_id} из привычки {habit_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@tags_bp.route('/tags/suggestions', methods=['GET'])
@login_required
def get_tag_suggestions():
    """
    Получить предложения тегов по префиксу
    
    Query parameters:
        prefix: Префикс для поиска (опционально)
        
    Returns:
        JSON ответ со списком предложенных тегов
    """
    try:
        # Получить параметры запроса
        prefix = request.args.get('prefix', '')
        
        # Получить предложения используя сервис
        tag_service = get_tag_service()
        suggestions = tag_service.get_tag_suggestions(current_user.id, prefix)
        
        return jsonify({
            'suggestions': suggestions,
            'total': len(suggestions)
        }), 200
        
    except TagServiceError as e:
        logger.error(f"Ошибка сервиса при получении предложений тегов для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось получить предложения тегов',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении предложений тегов для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


# Обработчики ошибок для blueprint
@tags_bp.errorhandler(404)
def handle_not_found(error):
    """Обработать ошибки 404 в API тегов"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Запрашиваемый ресурс не найден'
        }
    }), 404


@tags_bp.errorhandler(405)
def handle_method_not_allowed(error):
    """Обработать ошибки 405 в API тегов"""
    return jsonify({
        'error': {
            'code': 'METHOD_NOT_ALLOWED',
            'message': 'Запрашиваемый метод не разрешен для этого ресурса'
        }
    }), 405
