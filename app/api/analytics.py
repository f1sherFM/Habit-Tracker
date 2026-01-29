"""
API Эндпоинты для Аналитики

RESTful API для получения статистики и аналитики привычек
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from ..services.analytics_service import AnalyticsService, AnalyticsServiceError
import logging

# Создать blueprint
analytics_bp = Blueprint('analytics_api', __name__, url_prefix='/api/analytics')

# Сервис будет инициализирован при необходимости
analytics_service = None

def get_analytics_service():
    """Получить или создать экземпляр AnalyticsService"""
    global analytics_service
    if analytics_service is None:
        analytics_service = AnalyticsService()
    return analytics_service

logger = logging.getLogger(__name__)


@analytics_bp.route('/habits/<int:habit_id>', methods=['GET'])
@login_required
def get_habit_analytics(habit_id):
    """
    Получить статистику привычки
    
    Query parameters:
        days: Количество дней для анализа (1-30, по умолчанию 7)
        tracking_days: Альтернативное имя параметра для количества дней
        
    Returns:
        JSON ответ со статистикой привычки
    """
    try:
        # Получить параметры запроса (поддерживаем оба имена параметров)
        days = int(request.args.get('days') or request.args.get('tracking_days', 7))
        
        # Валидировать диапазон дней
        if days < 1 or days > 30:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Количество дней должно быть между 1 и 30'
                }
            }), 400
        
        # Получить статистику используя сервис
        analytics_service = get_analytics_service()
        stats, success, errors = analytics_service.get_habit_statistics(habit_id, current_user.id, days)
        
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
                    'message': 'Ошибка валидации параметров',
                    'details': errors
                }
            }), 400
        
        return jsonify({
            'statistics': stats,
            'tracking_days': days
        }), 200
        
    except AnalyticsServiceError as e:
        logger.error(f"Ошибка сервиса при получении статистики привычки {habit_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось получить статистику',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении статистики привычки {habit_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@analytics_bp.route('/categories/<int:category_id>', methods=['GET'])
@login_required
def get_category_analytics(category_id):
    """
    Получить статистику по категории
    
    Query parameters:
        days: Количество дней для анализа (1-30, по умолчанию 7)
        tracking_days: Альтернативное имя параметра для количества дней
        
    Returns:
        JSON ответ со статистикой категории
    """
    try:
        # Получить параметры запроса (поддерживаем оба имена параметров)
        days = int(request.args.get('days') or request.args.get('tracking_days', 7))
        
        # Валидировать диапазон дней
        if days < 1 or days > 30:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Количество дней должно быть между 1 и 30'
                }
            }), 400
        
        # Получить статистику используя сервис
        analytics_service = get_analytics_service()
        stats, success, errors = analytics_service.get_category_statistics(category_id, current_user.id, days)
        
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
                    'message': 'Ошибка валидации параметров',
                    'details': errors
                }
            }), 400
        
        return jsonify({
            'statistics': stats,
            'tracking_days': days
        }), 200
        
    except AnalyticsServiceError as e:
        logger.error(f"Ошибка сервиса при получении статистики категории {category_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось получить статистику',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении статистики категории {category_id} для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@analytics_bp.route('/overview', methods=['GET'])
@login_required
def get_user_analytics():
    """
    Получить общую аналитику пользователя
    
    Query parameters:
        days: Количество дней для анализа (1-30, по умолчанию 7)
        tracking_days: Альтернативное имя параметра для количества дней
        
    Returns:
        JSON ответ с общей аналитикой
    """
    try:
        # Получить параметры запроса (поддерживаем оба имена параметров)
        days = int(request.args.get('days') or request.args.get('tracking_days', 7))
        
        # Валидировать диапазон дней
        if days < 1 or days > 30:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Количество дней должно быть между 1 и 30'
                }
            }), 400
        
        # Получить аналитику используя сервис
        analytics_service = get_analytics_service()
        analytics, success, errors = analytics_service.get_user_analytics(current_user.id, days)
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Ошибка валидации параметров',
                    'details': errors
                }
            }), 400
        
        return jsonify({
            'analytics': analytics,
            'tracking_days': days
        }), 200
        
    except AnalyticsServiceError as e:
        logger.error(f"Ошибка сервиса при получении аналитики для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось получить аналитику',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении аналитики для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


@analytics_bp.route('/heatmap', methods=['GET'])
@login_required
def get_heatmap():
    """
    Получить данные для тепловой карты (как GitHub contributions)
    
    Query parameters:
        days: Количество дней для анализа (1-30, по умолчанию 30)
        tracking_days: Альтернативное имя параметра для количества дней
        
    Returns:
        JSON ответ с данными тепловой карты
    """
    try:
        # Получить параметры запроса (поддерживаем оба имена параметров)
        days = int(request.args.get('days') or request.args.get('tracking_days', 30))
        
        # Валидировать диапазон дней
        if days < 1 or days > 30:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Количество дней должно быть между 1 и 30'
                }
            }), 400
        
        # Получить данные используя сервис
        analytics_service = get_analytics_service()
        heatmap, success, errors = analytics_service.get_heatmap_data(current_user.id, days)
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Ошибка валидации параметров',
                    'details': errors
                }
            }), 400
        
        return jsonify({
            'heatmap': heatmap,
            'tracking_days': days
        }), 200
        
    except AnalyticsServiceError as e:
        logger.error(f"Ошибка сервиса при получении тепловой карты для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'SERVICE_ERROR',
                'message': 'Не удалось получить тепловую карту',
                'details': str(e)
            }
        }), 500
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении тепловой карты для пользователя {current_user.id}: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Произошла неожиданная ошибка'
            }
        }), 500


# Обработчики ошибок для blueprint
@analytics_bp.errorhandler(404)
def handle_not_found(error):
    """Обработать ошибки 404 в API аналитики"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Запрашиваемый ресурс не найден'
        }
    }), 404


@analytics_bp.errorhandler(405)
def handle_method_not_allowed(error):
    """Обработать ошибки 405 в API аналитики"""
    return jsonify({
        'error': {
            'code': 'METHOD_NOT_ALLOWED',
            'message': 'Запрашиваемый метод не разрешен для этого ресурса'
        }
    }), 405
