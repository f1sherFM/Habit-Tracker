"""
API Эндпоинты для Категорий

RESTful API для управления категориями привычек
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from ..services.category_service import CategoryService, CategoryNotFoundError, CategoryServiceError
import logging

# Создать blueprint
categories_bp = Blueprint('categories_api', __name__, url_prefix='/api/categories')

# Сервис будет инициализирован при необходимости
category_service = None

def get_category_service():
    """Получить или создать экземпляр CategoryService"""
    global category_service
    if category_service is None:
        category_service = CategoryService()
    return category_service

logger = logging.getLogger(__name__)


@categories_bp.route('', methods=['GET'])
@login_required
def get_categories():
    """
    Получить все категории пользователя
    
    Returns:
        JSON ответ со списком категорий
    """
    try:
        # Получить категории используя сервис
        category_service = get_category_service()
        categories = category_service.get_user_categories(current_user.id)
        
        # Преобразовать в JSON формат
        categories_data = []
        for category in categories:
            category_dict = {
                'id': category.id,
                'name': category.name,
                'color': category.color,
                'icon': category.icon,
                'created_at': category.created_at.isoformat() if category.created_at else None
            }
            categories_data.append(category_dict)
        
        return jsonify({
            'categories': categories_data,
            'total': len(categories_data)
        }), 200
        
    except CategoryServiceError as e:
        logger.error(f"Ошибка сервиса при получении категорий для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось получить категории',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении категорий для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@categories_bp.route('', methods=['POST'])
@login_required
def create_category():
    """
    Создать новую категорию
    
    Expected JSON payload:
    {
        "name": "Здоровье",
        "color": "#6366f1",
        "icon": "heart"
    }
    
    Returns:
        JSON ответ с созданной категорией
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
        
        category_data = request.get_json()
        
        # Валидировать обязательные поля
        if not category_data or not category_data.get('name'):
            return jsonify({
                'error': {
                    'code': 'MISSING_REQUIRED_FIELDS',
                    'message': 'Имя категории обязательно'
                }
            }), 400
        
        # Создать категорию используя сервис
        category_service = get_category_service()
        category, success, errors = category_service.create_category(
            current_user.id,
            category_data.get('name'),
            category_data.get('color'),
            category_data.get('icon')
        )
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Ошибка валидации данных категории',
                    'details': errors
                }
            }), 400
        
        # Вернуть созданную категорию
        return jsonify({
            'category': {
                'id': category.id,
                'name': category.name,
                'color': category.color,
                'icon': category.icon,
                'created_at': category.created_at.isoformat() if category.created_at else None
            }
        }), 201
        
    except CategoryServiceError as e:
        logger.error(f"Ошибка сервиса при создании категории для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось создать категорию',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании категории для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@categories_bp.route('/<int:category_id>', methods=['GET'])
@login_required
def get_category(category_id):
    """
    Получить конкретную категорию по ID
    
    Args:
        category_id: ID категории
        
    Returns:
        JSON ответ с данными категории
    """
    try:
        # Получить категорию используя сервис
        category_service = get_category_service()
        category = category_service.get_category(category_id, current_user.id)
        
        if not category:
            return jsonify({
                'error': {
                    'code': 'CATEGORY_NOT_FOUND',
                    'message': f'Категория с ID {category_id} не найдена'
                }
            }), 404
        
        return jsonify({
            'category': {
                'id': category.id,
                'name': category.name,
                'color': category.color,
                'icon': category.icon,
                'created_at': category.created_at.isoformat() if category.created_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении категории {category_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@categories_bp.route('/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    """
    Обновить категорию
    
    Args:
        category_id: ID категории
        
    Expected JSON payload:
    {
        "name": "Новое имя",
        "color": "#ff0000",
        "icon": "star"
    }
    
    Returns:
        JSON ответ с обновленной категорией
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
        
        category_data = request.get_json()
        
        if not category_data:
            return jsonify({
                'error': {
                    'code': 'EMPTY_REQUEST_BODY',
                    'message': 'Тело запроса не может быть пустым'
                }
            }), 400
        
        # Обновить категорию используя сервис
        category_service = get_category_service()
        category, success, errors = category_service.update_category(
            category_id,
            current_user.id,
            category_data.get('name'),
            category_data.get('color'),
            category_data.get('icon')
        )
        
        if not success:
            if "не найдена" in errors[0]:
                return jsonify({
                    'error': {
                        'code': 'CATEGORY_NOT_FOUND',
                        'message': f'Категория с ID {category_id} не найдена'
                    }
                }), 404
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Ошибка валидации данных категории',
                    'details': errors
                }
            }), 400
        
        # Вернуть обновленную категорию
        return jsonify({
            'category': {
                'id': category.id,
                'name': category.name,
                'color': category.color,
                'icon': category.icon,
                'created_at': category.created_at.isoformat() if category.created_at else None
            }
        }), 200
        
    except CategoryServiceError as e:
        logger.error(f"Ошибка сервиса при обновлении категории {category_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось обновить категорию',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обновлении категории {category_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@categories_bp.route('/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    """
    Удалить категорию (привычки переместятся в "Без категории")
    
    Args:
        category_id: ID категории
        
    Returns:
        Пустой ответ с кодом 204 при успехе
    """
    try:
        # Удалить категорию используя сервис
        category_service = get_category_service()
        success, errors = category_service.delete_category(category_id, current_user.id)
        
        if not success:
            if "не найдена" in errors[0]:
                return jsonify({
                    'error': {
                        'code': 'CATEGORY_NOT_FOUND',
                        'message': f'Категория с ID {category_id} не найдена'
                    }
                }), 404
            return jsonify({
                'error': {
                    'code': 'DELETE_ERROR',
                    'message': 'Не удалось удалить категорию',
                    'details': errors
                }
            }), 400
        
        # Вернуть пустой ответ с кодом 204 No Content
        return '', 204
        
    except CategoryServiceError as e:
        logger.error(f"Ошибка сервиса при удалении категории {category_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось удалить категорию',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при удалении категории {category_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


# Обработчики ошибок для blueprint
@categories_bp.errorhandler(404)
def handle_not_found(error):
    """Обработать ошибки 404 в API категорий"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Запрашиваемый ресурс не найден'
        }
    }), 404


@categories_bp.errorhandler(405)
def handle_method_not_allowed(error):
    """Обработать ошибки 405 в API категорий"""
    return jsonify({
        'error': {
            'code': 'METHOD_NOT_ALLOWED',
            'message': 'Запрашиваемый метод не разрешен для этого ресурса'
        }
    }), 405
