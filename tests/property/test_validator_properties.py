"""
Property-Based Tests для валидаторов

Тестирует универсальные свойства валидаторов используя Hypothesis
"""
import pytest
from hypothesis import given, strategies as st, assume
from app.validators import (
    TrackingDaysValidator,
    CommentValidator,
    TagValidator,
    CategoryValidator
)


class TestTrackingDaysValidatorProperties:
    """Property-based тесты для валидатора периода отслеживания"""
    
    @given(st.integers())
    def test_tracking_days_validation_property(self, days):
        """
        Property 1: Валидация периода отслеживания
        
        Для любого периода отслеживания, система должна отклонять значения 
        меньше 1 или больше 30 дней
        
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        result = TrackingDaysValidator.validate_days(days)
        
        if 1 <= days <= 30:
            assert result.is_valid, f"Период {days} должен быть валидным"
        else:
            assert not result.is_valid, f"Период {days} должен быть невалидным"
    
    @given(st.integers(min_value=1, max_value=30))
    def test_valid_tracking_days_always_pass(self, days):
        """Тест что валидные периоды всегда проходят валидацию"""
        result = TrackingDaysValidator.validate_days(days)
        assert result.is_valid
        assert len(result.errors) == 0
    
    @given(st.integers(max_value=0) | st.integers(min_value=31))
    def test_invalid_tracking_days_always_fail(self, days):
        """Тест что невалидные периоды всегда не проходят валидацию"""
        result = TrackingDaysValidator.validate_days(days)
        assert not result.is_valid
        assert len(result.errors) > 0


class TestCommentValidatorProperties:
    """Property-based тесты для валидатора комментариев"""
    
    @given(st.text(min_size=1, max_size=500).filter(lambda x: x.strip()))
    def test_comment_validation_property(self, text):
        """
        Property 2: Валидация комментариев
        
        Для любого комментария от 1 до 500 символов (не только пробелы), система должна 
        принимать его как валидный
        
        **Validates: Requirements 11.1, 11.2**
        """
        result = CommentValidator.validate_text(text)
        assert result.is_valid, f"Комментарий '{text[:50]}...' должен быть валидным"
    
    @given(st.text(min_size=501))
    def test_comment_too_long_property(self, text):
        """Тест что комментарии длиннее 500 символов не проходят валидацию"""
        result = CommentValidator.validate_text(text)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    @given(st.just('') | st.text(max_size=0))
    def test_empty_comment_property(self, text):
        """Тест что пустые комментарии не проходят валидацию"""
        result = CommentValidator.validate_text(text)
        assert not result.is_valid
    
    @given(st.text(min_size=1, max_size=500))
    def test_comment_sanitization_property(self, text):
        """Тест что санитизация не удаляет валидный текст"""
        sanitized = CommentValidator.sanitize_text(text)
        
        # Санитизированный текст должен быть строкой
        assert isinstance(sanitized, str)
        # Санитизированный текст не должен быть пустым если исходный не пустой
        if text.strip():
            assert len(sanitized) > 0


class TestTagValidatorProperties:
    """Property-based тесты для валидатора тегов"""
    
    @given(st.lists(st.text(min_size=1, max_size=20), max_size=5, unique=True))
    def test_tag_validation_property(self, tags):
        """
        Property 3: Валидация тегов
        
        Для любых тегов (максимум 5, каждый до 20 символов), система должна 
        принимать их как валидные
        
        **Validates: Requirements 12.1, 12.2, 12.3**
        """
        # Фильтровать пустые теги
        tags = [t for t in tags if t.strip()]
        
        if len(tags) <= 5:
            result = TagValidator.validate_tags(tags)
            assert result.is_valid, f"Теги {tags} должны быть валидными"
    
    @given(st.lists(st.text(min_size=1, max_size=20), min_size=6))
    def test_too_many_tags_property(self, tags):
        """Тест что более 5 тегов не проходят валидацию"""
        assume(len(tags) > 5)
        result = TagValidator.validate_tags(tags)
        assert not result.is_valid
    
    @given(st.lists(st.text(min_size=21), max_size=5))
    def test_tag_too_long_property(self, tags):
        """Тест что теги длиннее 20 символов не проходят валидацию"""
        assume(len(tags) > 0)
        result = TagValidator.validate_tags(tags)
        assert not result.is_valid
    
    @given(st.lists(st.text(min_size=1, max_size=20), max_size=5, unique=True))
    def test_tag_normalization_property(self, tags):
        """Тест что нормализация сохраняет валидные теги"""
        tags = [t for t in tags if t.strip()]
        normalized = TagValidator.normalize_tags(tags)
        
        # Все нормализованные теги должны быть в нижнем регистре
        for tag in normalized:
            assert tag == tag.lower()
        
        # Количество тегов не должно увеличиться
        assert len(normalized) <= len(tags)


class TestCategoryValidatorProperties:
    """Property-based тесты для валидатора категорий"""
    
    @given(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
    def test_category_name_validation_property(self, name):
        """Тест что имена категорий от 1 до 50 символов валидны"""
        result = CategoryValidator.validate_category(name)
        assert result.is_valid, f"Имя категории '{name}' должно быть валидным"
    
    @given(st.text(min_size=51))
    def test_category_name_too_long_property(self, name):
        """Тест что имена категорий длиннее 50 символов не валидны"""
        result = CategoryValidator.validate_category(name)
        assert not result.is_valid
    
    @given(st.sampled_from(['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF', '#6366f1']))
    def test_valid_hex_color_property(self, color):
        """Тест что валидные HEX цвета проходят валидацию"""
        result = CategoryValidator.validate_category('Тест', color)
        assert result.is_valid
    
    @given(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
    def test_category_with_valid_color_property(self, name):
        """Тест что категория с валидным цветом проходит валидацию"""
        result = CategoryValidator.validate_category(name, '#FF0000')
        assert result.is_valid


class TestValidatorConsistency:
    """Тесты на консистентность валидаторов"""
    
    @given(st.integers(min_value=1, max_value=30))
    def test_tracking_days_consistency(self, days):
        """Тест что валидация периода консистентна"""
        result1 = TrackingDaysValidator.validate_days(days)
        result2 = TrackingDaysValidator.validate_days(days)
        
        assert result1.is_valid == result2.is_valid
        assert result1.errors == result2.errors
    
    @given(st.text(min_size=1, max_size=500))
    def test_comment_consistency(self, text):
        """Тест что валидация комментариев консистентна"""
        result1 = CommentValidator.validate_text(text)
        result2 = CommentValidator.validate_text(text)
        
        assert result1.is_valid == result2.is_valid
        assert result1.errors == result2.errors
    
    @given(st.lists(st.text(min_size=1, max_size=20), max_size=5, unique=True))
    def test_tags_consistency(self, tags):
        """Тест что валидация тегов консистентна"""
        tags = [t for t in tags if t.strip()]
        
        result1 = TagValidator.validate_tags(tags)
        result2 = TagValidator.validate_tags(tags)
        
        assert result1.is_valid == result2.is_valid
        assert result1.errors == result2.errors
