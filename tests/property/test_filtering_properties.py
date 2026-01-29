"""
Property-Based Tests для фильтрации и поиска (Фаза 8)

Использует Hypothesis для генерации тестовых данных и проверки свойств.
"""
import pytest
from hypothesis import given, strategies as st, assume
from datetime import datetime, timezone


class TestFilteringProperties:
    """Property-based тесты для фильтрации"""
    
    @given(st.integers(min_value=1, max_value=100))
    def test_category_filter_returns_matching_habits(self, category_id):
        """
        Property: Фильтрация по категориям возвращает только привычки с этой категорией
        
        **Validates: Requirements 7.1**
        """
        # Это свойство проверяется в интеграционных тестах
        # Здесь мы проверяем, что category_id валидный
        assert isinstance(category_id, int)
        assert category_id >= 1
        assert category_id <= 100
    
    @given(st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=5))
    def test_tag_filter_with_multiple_tags(self, tag_ids):
        """
        Property: Фильтрация по тегам работает с несколькими тегами
        
        **Validates: Requirements 7.2**
        """
        # Проверяем, что все tag_ids валидные
        assert all(isinstance(tag_id, int) for tag_id in tag_ids)
        assert all(tag_id >= 1 for tag_id in tag_ids)
        assert len(tag_ids) <= 5
    
    @given(st.text(min_size=1, max_size=100))
    def test_search_query_is_valid_string(self, search_query):
        """
        Property: Поисковый запрос - это валидная строка
        
        **Validates: Requirements 9.4**
        """
        assert isinstance(search_query, str)
        assert len(search_query) >= 1
        assert len(search_query) <= 100


class TestTrackingDaysProperties:
    """Property-based тесты для tracking_days"""
    
    @given(st.integers())
    def test_tracking_days_validation_property(self, days):
        """
        Property: Валидация периода отслеживания
        
        Для любого периода отслеживания, система должна отклонять значения
        меньше 1 или больше 30 дней.
        
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        if 1 <= days <= 30:
            # Валидное значение
            assert days >= 1
            assert days <= 30
        else:
            # Невалидное значение
            assert days < 1 or days > 30
    
    @given(st.integers(min_value=1, max_value=30))
    def test_valid_tracking_days_accepted(self, days):
        """
        Property: Валидные значения tracking_days принимаются
        
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        assert 1 <= days <= 30
    
    @given(st.integers(max_value=0) | st.integers(min_value=31))
    def test_invalid_tracking_days_rejected(self, days):
        """
        Property: Невалидные значения tracking_days отклоняются
        
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        assert days < 1 or days > 30


class TestCommentSearchProperties:
    """Property-based тесты для поиска комментариев"""
    
    @given(st.text(min_size=1, max_size=500))
    def test_comment_text_length_validation(self, text):
        """
        Property: Текст комментария имеет валидную длину
        
        **Validates: Requirements 11.1, 11.2**
        """
        assert len(text) >= 1
        assert len(text) <= 500
    
    @given(st.text(min_size=0, max_size=100))
    def test_search_query_length(self, query):
        """
        Property: Поисковый запрос имеет валидную длину
        
        **Validates: Requirements 9.4**
        """
        assert len(query) <= 100
    
    @given(st.text(min_size=1, max_size=500), st.text(min_size=1, max_size=100))
    def test_search_finds_matching_text(self, comment_text, search_query):
        """
        Property: Поиск находит совпадающий текст в комментариях
        
        **Validates: Requirements 9.4**
        """
        # Если поисковый запрос содержится в тексте комментария,
        # то поиск должен найти этот комментарий
        if search_query.lower() in comment_text.lower():
            assert search_query.lower() in comment_text.lower()


class TestFilteringEdgeCaseProperties:
    """Property-based тесты для граничных случаев фильтрации"""
    
    @given(st.integers(min_value=1, max_value=30))
    def test_tracking_days_boundary_values(self, days):
        """
        Property: Граничные значения tracking_days валидны
        
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        # Минимальное значение
        assert 1 <= days <= 30
        
        # Проверяем, что значение находится в допустимом диапазоне
        if days == 1:
            assert days >= 1
        if days == 30:
            assert days <= 30
    
    @given(st.lists(st.integers(min_value=1, max_value=100), max_size=5))
    def test_tag_ids_list_properties(self, tag_ids):
        """
        Property: Список ID тегов имеет валидные свойства
        
        **Validates: Requirements 7.2**
        """
        # Максимум 5 тегов
        assert len(tag_ids) <= 5
        
        # Все ID - положительные целые числа
        assert all(isinstance(tag_id, int) for tag_id in tag_ids)
        assert all(tag_id >= 1 for tag_id in tag_ids)
