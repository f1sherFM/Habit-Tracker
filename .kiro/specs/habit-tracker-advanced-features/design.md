# Дизайн-Документ: Продвинутые Функции Habit-Tracker

## Обзор

Данный документ описывает техническое решение для добавления продвинутых функций в Habit-Tracker: категории и теги, статистика и аналитика, комментарии к привычкам, и гибкий выбор периода отслеживания.

## Архитектура

### Новые Модели Данных

#### Модель Category

```python
class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#6366f1')  # Hex color
    icon = db.Column(db.String(50))  # Icon name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    habits = db.relationship('Habit', backref='category', lazy=True)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='unique_user_category'),
    )
```

#### Модель Tag

```python
class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Many-to-many relationship with habits
    habits = db.relationship('Habit', secondary='habit_tags', backref='tags')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='unique_user_tag'),
    )

# Association table for many-to-many relationship
habit_tags = db.Table('habit_tags',
    db.Column('habit_id', db.Integer, db.ForeignKey('habits.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)
```

#### Модель Comment

```python
class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False)
    habit_log_id = db.Column(db.Integer, db.ForeignKey('habit_logs.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    habit = db.relationship('Habit', backref='comments')
    habit_log = db.relationship('HabitLog', backref='comments')
    
    __table_args__ = (
        db.Index('idx_habit_log_comments', 'habit_log_id'),
    )
```

#### Обновленная Модель Habit

```python
class Habit(db.Model):
    # ... existing fields ...
    
    # Новые поля
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    tracking_days = db.Column(db.Integer, default=7)  # 1-30 дней
    
    # Relationships
    category = db.relationship('Category', backref='habits')
    tags = db.relationship('Tag', secondary='habit_tags', backref='habits')
    comments = db.relationship('Comment', backref='habit', cascade='all, delete-orphan')
```

#### Обновленная Модель User

```python
class User(UserMixin, db.Model):
    # ... existing fields ...
    
    # Новые поля
    default_tracking_days = db.Column(db.Integer, default=7)  # Период по умолчанию
    
    # Relationships
    categories = db.relationship('Category', backref='user', cascade='all, delete-orphan')
    tags = db.relationship('Tag', backref='user', cascade='all, delete-orphan')
```

## Система Валидации

### TrackingDaysValidator

```python
class TrackingDaysValidator(BaseValidator):
    MIN_DAYS = 1
    MAX_DAYS = 30
    
    @staticmethod
    def validate(days: int) -> ValidationResult:
        errors = []
        
        if not isinstance(days, int):
            errors.append("Период должен быть целым числом")
        elif days < TrackingDaysValidator.MIN_DAYS:
            errors.append(f"Период не может быть меньше {TrackingDaysValidator.MIN_DAYS} дня")
        elif days > TrackingDaysValidator.MAX_DAYS:
            errors.append(f"Период не может быть больше {TrackingDaysValidator.MAX_DAYS} дней")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

### CommentValidator

```python
class CommentValidator(BaseValidator):
    MIN_LENGTH = 1
    MAX_LENGTH = 500
    
    @staticmethod
    def validate(text: str) -> ValidationResult:
        errors = []
        
        if not text or not text.strip():
            errors.append("Комментарий не может быть пустым")
        elif len(text) > CommentValidator.MAX_LENGTH:
            errors.append(f"Комментарий не может быть длиннее {CommentValidator.MAX_LENGTH} символов")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

### TagValidator

```python
class TagValidator(BaseValidator):
    MIN_LENGTH = 1
    MAX_LENGTH = 20
    MAX_TAGS_PER_HABIT = 5
    
    @staticmethod
    def validate(tags: List[str]) -> ValidationResult:
        errors = []
        
        if len(tags) > TagValidator.MAX_TAGS_PER_HABIT:
            errors.append(f"Максимум {TagValidator.MAX_TAGS_PER_HABIT} тегов на привычку")
        
        for tag in tags:
            if not tag or not tag.strip():
                errors.append("Тег не может быть пустым")
            elif len(tag) > TagValidator.MAX_LENGTH:
                errors.append(f"Тег не может быть длиннее {TagValidator.MAX_LENGTH} символов")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

## Слой Сервисов

### CategoryService

```python
class CategoryService:
    def __init__(self):
        self.validator = CategoryValidator()
    
    def create_category(self, user_id: int, name: str, color: str = None) -> Result[Category, List[str]]:
        """Создает новую категорию"""
        
    def get_user_categories(self, user_id: int) -> List[Category]:
        """Получает все категории пользователя"""
        
    def delete_category(self, category_id: int, user_id: int) -> Result[bool, str]:
        """Удаляет категорию и переводит привычки в 'Без категории'"""
```

### TagService

```python
class TagService:
    def __init__(self):
        self.validator = TagValidator()
    
    def add_tags_to_habit(self, habit_id: int, user_id: int, tags: List[str]) -> Result[List[Tag], List[str]]:
        """Добавляет теги к привычке"""
        
    def get_habit_tags(self, habit_id: int) -> List[Tag]:
        """Получает все теги привычки"""
        
    def get_tag_suggestions(self, user_id: int, prefix: str) -> List[str]:
        """Получает предложения тегов по префиксу"""
```

### CommentService

```python
class CommentService:
    def __init__(self):
        self.validator = CommentValidator()
    
    def add_comment(self, habit_log_id: int, habit_id: int, text: str) -> Result[Comment, List[str]]:
        """Добавляет комментарий к выполнению привычки"""
        
    def update_comment(self, comment_id: int, text: str) -> Result[Comment, List[str]]:
        """Обновляет комментарий"""
        
    def delete_comment(self, comment_id: int) -> Result[bool, str]:
        """Удаляет комментарий"""
        
    def get_habit_comments(self, habit_id: int) -> List[Comment]:
        """Получает все комментарии привычки"""
```

### AnalyticsService

```python
class AnalyticsService:
    def get_habit_statistics(self, habit_id: int, days: int) -> HabitStatistics:
        """Получает статистику привычки за период"""
        
    def get_category_statistics(self, category_id: int, user_id: int, days: int) -> CategoryStatistics:
        """Получает статистику по категории"""
        
    def get_user_analytics(self, user_id: int, days: int) -> UserAnalytics:
        """Получает общую аналитику пользователя"""
        
    def calculate_streak(self, habit_id: int) -> int:
        """Рассчитывает текущий streak"""
        
    def calculate_best_streak(self, habit_id: int) -> int:
        """Рассчитывает лучший streak за все время"""
```

## API Эндпоинты

### Категории

```
GET /api/categories - Получить все категории
POST /api/categories - Создать категорию
PUT /api/categories/{id} - Обновить категорию
DELETE /api/categories/{id} - Удалить категорию
```

### Теги

```
GET /api/habits/{id}/tags - Получить теги привычки
POST /api/habits/{id}/tags - Добавить теги
DELETE /api/habits/{id}/tags/{tag_id} - Удалить тег
GET /api/tags/suggestions?prefix=... - Получить предложения тегов
```

### Комментарии

```
GET /api/habits/{id}/comments - Получить комментарии привычки
POST /api/habit-logs/{id}/comments - Добавить комментарий
PUT /api/comments/{id} - Обновить комментарий
DELETE /api/comments/{id} - Удалить комментарий
```

### Аналитика

```
GET /api/analytics/habits/{id}?days=7 - Статистика привычки
GET /api/analytics/categories/{id}?days=7 - Статистика категории
GET /api/analytics/overview?days=7 - Общая аналитика
GET /api/analytics/heatmap?days=30 - Тепловая карта
```

## Correctness Properties

### Свойство 1: Валидация Периода Отслеживания
*Для любого* периода отслеживания, система должна отклонять значения меньше 1 или больше 30 дней
**Validates: Requirements 10.1, 10.2, 10.3**

### Свойство 2: Валидация Комментариев
*Для любого* комментария, система должна отклонять пустые комментарии и комментарии длиннее 500 символов
**Validates: Requirements 11.1, 11.2**

### Свойство 3: Валидация Тегов
*Для любых* тегов, система должна отклонять пустые теги, теги длиннее 20 символов и более 5 тегов на привычку
**Validates: Requirements 12.1, 12.2, 12.3**

### Свойство 4: Расчет Streak
*Для любой* привычки, система должна корректно рассчитывать текущий streak как количество дней подряд выполнения
**Validates: Requirements 3.2**

### Свойство 5: Расчет Процента Выполнения
*Для любого* периода, система должна корректно рассчитывать процент выполнения как (выполнено / всего дней) * 100
**Validates: Requirements 3.1**

### Свойство 6: Фильтрация по Категориям
*Для любой* категории, система должна показывать только привычки, принадлежащие этой категории
**Validates: Requirements 7.1**

### Свойство 7: Фильтрация по Тегам
*Для любого* тега, система должна показывать только привычки с этим тегом
**Validates: Requirements 7.2**

### Свойство 8: Комбинированная Фильтрация
*Для любой* комбинации фильтров, система должна показывать привычки, соответствующие всем фильтрам (AND логика)
**Validates: Requirements 7.3**

### Свойство 9: Сохранение Комментариев
*Для любого* комментария, система должна сохранять текст, дату создания и дату редактирования
**Validates: Requirements 5.2, 5.3**

### Свойство 10: Статистика по Категориям
*Для любой* категории, система должна корректно рассчитывать среднее выполнение по всем привычкам в категории
**Validates: Requirements 8.1**

## Схема Базы Данных

### Диаграмма Сущностей

```
USERS
├── CATEGORIES (1:N)
├── TAGS (1:N)
└── HABITS (1:N)
    ├── CATEGORY (N:1)
    ├── TAGS (N:M через habit_tags)
    ├── HABIT_LOGS (1:N)
    │   └── COMMENTS (1:N)
    └── COMMENTS (1:N)
```

### Миграция Базы Данных

```python
# migrations/versions/003_add_categories_tags_comments.py
def upgrade():
    # Создание таблицы категорий
    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('color', sa.String(7), default='#6366f1'),
        sa.Column('icon', sa.String(50)),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('user_id', 'name', name='unique_user_category')
    )
    
    # Создание таблицы тегов
    op.create_table('tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('user_id', 'name', name='unique_user_tag')
    )
    
    # Создание таблицы связей привычек и тегов
    op.create_table('habit_tags',
        sa.Column('habit_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('habit_id', 'tag_id'),
        sa.ForeignKeyConstraint(['habit_id'], ['habits.id']),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'])
    )
    
    # Создание таблицы комментариев
    op.create_table('comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('habit_id', sa.Integer(), nullable=False),
        sa.Column('habit_log_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(500), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['habit_id'], ['habits.id']),
        sa.ForeignKeyConstraint(['habit_log_id'], ['habit_logs.id']),
        sa.Index('idx_habit_log_comments', 'habit_log_id')
    )
    
    # Добавление новых полей к таблице habits
    op.add_column('habits', sa.Column('category_id', sa.Integer()))
    op.add_column('habits', sa.Column('tracking_days', sa.Integer(), default=7))
    op.create_foreign_key('fk_habits_category', 'habits', 'categories', ['category_id'], ['id'])
    
    # Добавление нового поля к таблице users
    op.add_column('users', sa.Column('default_tracking_days', sa.Integer(), default=7))
```

## Стратегия Тестирования

### Property-Based Tests

```python
# tests/property/test_tracking_days_properties.py
@given(st.integers())
def test_tracking_days_validation_property(days):
    """Property 1: Валидация периода отслеживания"""
    result = TrackingDaysValidator.validate(days)
    
    if 1 <= days <= 30:
        assert result.is_valid
    else:
        assert not result.is_valid

# tests/property/test_comment_properties.py
@given(st.text(min_size=1, max_size=500))
def test_comment_validation_property(text):
    """Property 2: Валидация комментариев"""
    result = CommentValidator.validate(text)
    assert result.is_valid

@given(st.text(min_size=501))
def test_comment_too_long_property(text):
    """Property 2: Комментарий слишком длинный"""
    result = CommentValidator.validate(text)
    assert not result.is_valid

# tests/property/test_tag_properties.py
@given(st.lists(st.text(min_size=1, max_size=20), max_size=5))
def test_tag_validation_property(tags):
    """Property 3: Валидация тегов"""
    result = TagValidator.validate(tags)
    assert result.is_valid
```

### Unit Tests

```python
# tests/unit/test_analytics_service.py
class TestAnalyticsService:
    def test_calculate_streak_consecutive_days(self):
        """Тест расчета streak для последовательных дней"""
        
    def test_calculate_completion_percentage(self):
        """Тест расчета процента выполнения"""
        
    def test_category_statistics(self):
        """Тест статистики по категориям"""

# tests/unit/test_comment_service.py
class TestCommentService:
    def test_add_comment_to_habit_log(self):
        """Тест добавления комментария"""
        
    def test_update_comment(self):
        """Тест обновления комментария"""
        
    def test_delete_comment(self):
        """Тест удаления комментария"""

# tests/unit/test_tag_service.py
class TestTagService:
    def test_add_tags_to_habit(self):
        """Тест добавления тегов"""
        
    def test_tag_suggestions(self):
        """Тест предложений тегов"""
```

## Заключение

Данный дизайн-документ представляет комплексное решение для добавления продвинутых функций в Habit-Tracker, включая категории, теги, комментарии, аналитику и гибкий период отслеживания.
