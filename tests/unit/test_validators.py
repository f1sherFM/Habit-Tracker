"""
Тесты для валидаторов

Тестирует функциональность всех валидаторов для продвинутых функций
"""
import pytest
from app.validators import (
    TrackingDaysValidator,
    CommentValidator,
    TagValidator,
    CategoryValidator,
    ValidationResult
)


class TestTrackingDaysValidator:
    """Тесты для валидатора периода отслеживания"""
    
    def test_valid_tracking_days(self):
        """Тест валидации корректного периода"""
        validator = TrackingDaysValidator()
        
        # Тест минимального значения
        result = validator.validate({'tracking_days': 1})
        assert result.is_valid
        assert len(result.errors) == 0
        
        # Тест максимального значения
        result = validator.validate({'tracking_days': 30})
        assert result.is_valid
        assert len(result.errors) == 0
        
        # Тест среднего значения
        result = validator.validate({'tracking_days': 7})
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_tracking_days_too_small(self):
        """Тест валидации периода меньше минимума"""
        validator = TrackingDaysValidator()
        result = validator.validate({'tracking_days': 0})
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "меньше" in result.errors[0].lower()
    
    def test_invalid_tracking_days_too_large(self):
        """Тест валидации периода больше максимума"""
        validator = TrackingDaysValidator()
        result = validator.validate({'tracking_days': 31})
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "больше" in result.errors[0].lower()
    
    def test_invalid_tracking_days_not_integer(self):
        """Тест валидации периода не целого числа"""
        validator = TrackingDaysValidator()
        result = validator.validate({'tracking_days': 7.5})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_invalid_tracking_days_string(self):
        """Тест валидации периода строки"""
        validator = TrackingDaysValidator()
        result = validator.validate({'tracking_days': "7"})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_missing_tracking_days(self):
        """Тест валидации отсутствия периода"""
        validator = TrackingDaysValidator()
        result = validator.validate({})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_static_validate_days(self):
        """Тест статического метода валидации"""
        result = TrackingDaysValidator.validate_days(14)
        assert result.is_valid
        
        result = TrackingDaysValidator.validate_days(50)
        assert not result.is_valid


class TestCommentValidator:
    """Тесты для валидатора комментариев"""
    
    def test_valid_comment(self):
        """Тест валидации корректного комментария"""
        validator = CommentValidator()
        
        # Тест минимальной длины
        result = validator.validate({'text': 'a'})
        assert result.is_valid
        assert len(result.errors) == 0
        
        # Тест нормальной длины
        result = validator.validate({'text': 'Это хороший комментарий'})
        assert result.is_valid
        assert len(result.errors) == 0
        
        # Тест максимальной длины
        result = validator.validate({'text': 'a' * 500})
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_comment_empty(self):
        """Тест валидации пустого комментария"""
        validator = CommentValidator()
        result = validator.validate({'text': ''})
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "пустым" in result.errors[0].lower()
    
    def test_invalid_comment_whitespace_only(self):
        """Тест валидации комментария только с пробелами"""
        validator = CommentValidator()
        result = validator.validate({'text': '   '})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_invalid_comment_too_long(self):
        """Тест валидации слишком длинного комментария"""
        validator = CommentValidator()
        result = validator.validate({'text': 'a' * 501})
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "длиннее" in result.errors[0].lower()
    
    def test_invalid_comment_not_string(self):
        """Тест валидации комментария не строки"""
        validator = CommentValidator()
        result = validator.validate({'text': 123})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_missing_comment_text(self):
        """Тест валидации отсутствия текста"""
        validator = CommentValidator()
        result = validator.validate({})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_sanitize_text(self):
        """Тест санитизации текста"""
        text = '<script>alert("xss")</script>'
        sanitized = CommentValidator.sanitize_text(text)
        
        assert '<script>' not in sanitized
        assert '&lt;script&gt;' in sanitized
    
    def test_static_validate_text(self):
        """Тест статического метода валидации"""
        result = CommentValidator.validate_text('Хороший комментарий')
        assert result.is_valid
        
        result = CommentValidator.validate_text('')
        assert not result.is_valid


class TestTagValidator:
    """Тесты для валидатора тегов"""
    
    def test_valid_tags(self):
        """Тест валидации корректных тегов"""
        validator = TagValidator()
        
        # Тест одного тега
        result = validator.validate({'tags': ['спорт']})
        assert result.is_valid
        assert len(result.errors) == 0
        
        # Тест нескольких тегов
        result = validator.validate({'tags': ['спорт', 'здоровье', 'утро']})
        assert result.is_valid
        assert len(result.errors) == 0
        
        # Тест максимального количества тегов
        result = validator.validate({'tags': ['тег1', 'тег2', 'тег3', 'тег4', 'тег5']})
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_tags_too_many(self):
        """Тест валидации слишком большого количества тегов"""
        validator = TagValidator()
        result = validator.validate({'tags': ['тег1', 'тег2', 'тег3', 'тег4', 'тег5', 'тег6']})
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "максимум" in result.errors[0].lower()
    
    def test_invalid_tags_empty_tag(self):
        """Тест валидации пустого тега"""
        validator = TagValidator()
        result = validator.validate({'tags': ['спорт', '', 'здоровье']})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_invalid_tags_tag_too_long(self):
        """Тест валидации слишком длинного тега"""
        validator = TagValidator()
        result = validator.validate({'tags': ['a' * 21]})
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "длиннее" in result.errors[0].lower()
    
    def test_invalid_tags_not_list(self):
        """Тест валидации тегов не списка"""
        validator = TagValidator()
        result = validator.validate({'tags': 'спорт'})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_invalid_tags_not_strings(self):
        """Тест валидации тегов не строк"""
        validator = TagValidator()
        result = validator.validate({'tags': [1, 2, 3]})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_missing_tags(self):
        """Тест валидации отсутствия тегов"""
        validator = TagValidator()
        result = validator.validate({})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_normalize_tags(self):
        """Тест нормализации тегов"""
        tags = ['Спорт', 'ЗДОРОВЬЕ', '  утро  ']
        normalized = TagValidator.normalize_tags(tags)
        
        assert normalized == ['спорт', 'здоровье', 'утро']
    
    def test_static_validate_tags(self):
        """Тест статического метода валидации"""
        result = TagValidator.validate_tags(['спорт', 'здоровье'])
        assert result.is_valid
        
        result = TagValidator.validate_tags(['тег1', 'тег2', 'тег3', 'тег4', 'тег5', 'тег6'])
        assert not result.is_valid


class TestCategoryValidator:
    """Тесты для валидатора категорий"""
    
    def test_valid_category(self):
        """Тест валидации корректной категории"""
        validator = CategoryValidator()
        
        # Тест с именем
        result = validator.validate({'name': 'Спорт'})
        assert result.is_valid
        assert len(result.errors) == 0
        
        # Тест с именем и цветом
        result = validator.validate({'name': 'Здоровье', 'color': '#FF0000'})
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_category_empty_name(self):
        """Тест валидации пустого имени категории"""
        validator = CategoryValidator()
        result = validator.validate({'name': ''})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_invalid_category_name_too_long(self):
        """Тест валидации слишком длинного имени категории"""
        validator = CategoryValidator()
        result = validator.validate({'name': 'a' * 51})
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "длиннее" in result.errors[0].lower()
    
    def test_invalid_category_invalid_color(self):
        """Тест валидации неправильного цвета"""
        validator = CategoryValidator()
        result = validator.validate({'name': 'Спорт', 'color': 'red'})
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "HEX" in result.errors[0]
    
    def test_invalid_category_invalid_hex_color(self):
        """Тест валидации неправильного HEX цвета"""
        validator = CategoryValidator()
        result = validator.validate({'name': 'Спорт', 'color': '#GGGGGG'})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_valid_hex_colors(self):
        """Тест валидации различных HEX цветов"""
        validator = CategoryValidator()
        
        valid_colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF', '#6366f1']
        for color in valid_colors:
            result = validator.validate({'name': 'Тест', 'color': color})
            assert result.is_valid, f"Цвет {color} должен быть валидным"
    
    def test_missing_category_name(self):
        """Тест валидации отсутствия имени"""
        validator = CategoryValidator()
        result = validator.validate({})
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_get_predefined_categories(self):
        """Тест получения предопределенных категорий"""
        categories = CategoryValidator.get_predefined_categories()
        
        assert isinstance(categories, list)
        assert len(categories) >= 10
        assert 'Здоровье' in categories
        assert 'Спорт' in categories
        assert 'Работа' in categories
    
    def test_static_validate_category(self):
        """Тест статического метода валидации"""
        result = CategoryValidator.validate_category('Спорт', '#FF0000')
        assert result.is_valid
        
        result = CategoryValidator.validate_category('', '#FF0000')
        assert not result.is_valid


class TestValidationResult:
    """Тесты для класса ValidationResult"""
    
    def test_validation_result_valid(self):
        """Тест создания валидного результата"""
        result = ValidationResult(is_valid=True, errors=[])
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validation_result_invalid(self):
        """Тест создания невалидного результата"""
        errors = ['Ошибка 1', 'Ошибка 2']
        result = ValidationResult(is_valid=False, errors=errors)
        
        assert not result.is_valid
        assert len(result.errors) == 2
        assert result.errors == errors
