"""
Миграция: Добавить таблицы категорий, тегов и комментариев

Revision ID: 002
Revises: 001
Create Date: 2024-01-25

Добавляет новые таблицы для поддержки продвинутых функций:
- categories: Категории привычек
- tags: Теги для привычек
- habit_tags: Связь многие-ко-многим между привычками и тегами
- comments: Комментарии к выполнению привычек

Также добавляет новые поля к существующим таблицам:
- habits: category_id, tracking_days
- users: default_tracking_days
"""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

# Метаданные миграции
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade(engine):
    """
    Добавить новые таблицы и поля.
    
    Args:
        engine: Экземпляр SQLAlchemy engine
    """
    try:
        logger.info("Начало миграции 002: Добавление таблиц категорий, тегов и комментариев")
        
        with engine.connect() as connection:
            # Начать транзакцию
            trans = connection.begin()
            
            try:
                # Проверить, используется ли PostgreSQL или SQLite
                is_postgresql = 'postgresql' in str(engine.url)
                
                if is_postgresql:
                    logger.info("Применение миграции PostgreSQL")
                    
                    # Создать таблицу категорий
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS categories (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES users(id),
                            name VARCHAR(50) NOT NULL,
                            color VARCHAR(7) DEFAULT '#6366f1',
                            icon VARCHAR(50),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(user_id, name)
                        )
                    """))
                    
                    # Создать индекс для категорий
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_categories_user ON categories(user_id)
                    """))
                    
                    # Создать таблицу тегов
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS tags (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES users(id),
                            name VARCHAR(20) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(user_id, name)
                        )
                    """))
                    
                    # Создать индекс для тегов
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_tags_user ON tags(user_id)
                    """))
                    
                    # Создать таблицу связей привычек и тегов
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS habit_tags (
                            habit_id INTEGER NOT NULL REFERENCES habits(id),
                            tag_id INTEGER NOT NULL REFERENCES tags(id),
                            PRIMARY KEY (habit_id, tag_id)
                        )
                    """))
                    
                    # Создать таблицу комментариев
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS comments (
                            id SERIAL PRIMARY KEY,
                            habit_id INTEGER NOT NULL REFERENCES habits(id),
                            habit_log_id INTEGER NOT NULL REFERENCES habit_logs(id),
                            text VARCHAR(500) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    
                    # Создать индексы для комментариев
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_habit_log_comments ON comments(habit_log_id)
                    """))
                    
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_habit_comments ON comments(habit_id)
                    """))
                    
                    # Добавить новые поля к таблице habits
                    connection.execute(text("""
                        ALTER TABLE habits 
                        ADD COLUMN IF NOT EXISTS category_id INTEGER REFERENCES categories(id)
                    """))
                    
                    connection.execute(text("""
                        ALTER TABLE habits 
                        ADD COLUMN IF NOT EXISTS tracking_days INTEGER DEFAULT 7
                    """))
                    
                    # Создать индекс для category_id
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_habits_category ON habits(category_id)
                    """))
                    
                    # Добавить новое поле к таблице users
                    connection.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS default_tracking_days INTEGER DEFAULT 7
                    """))
                    
                else:
                    logger.info("Применение миграции SQLite")
                    
                    # Проверить, существуют ли таблицы
                    result = connection.execute(text("""
                        SELECT name FROM sqlite_master WHERE type='table' AND name='categories'
                    """))
                    
                    if not result.fetchone():
                        # Создать таблицу категорий
                        connection.execute(text("""
                            CREATE TABLE categories (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL REFERENCES users(id),
                                name VARCHAR(50) NOT NULL,
                                color VARCHAR(7) DEFAULT '#6366f1',
                                icon VARCHAR(50),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE(user_id, name)
                            )
                        """))
                        
                        # Создать индекс для категорий
                        connection.execute(text("""
                            CREATE INDEX idx_categories_user ON categories(user_id)
                        """))
                    
                    # Проверить, существует ли таблица тегов
                    result = connection.execute(text("""
                        SELECT name FROM sqlite_master WHERE type='table' AND name='tags'
                    """))
                    
                    if not result.fetchone():
                        # Создать таблицу тегов
                        connection.execute(text("""
                            CREATE TABLE tags (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL REFERENCES users(id),
                                name VARCHAR(20) NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE(user_id, name)
                            )
                        """))
                        
                        # Создать индекс для тегов
                        connection.execute(text("""
                            CREATE INDEX idx_tags_user ON tags(user_id)
                        """))
                    
                    # Проверить, существует ли таблица связей
                    result = connection.execute(text("""
                        SELECT name FROM sqlite_master WHERE type='table' AND name='habit_tags'
                    """))
                    
                    if not result.fetchone():
                        # Создать таблицу связей привычек и тегов
                        connection.execute(text("""
                            CREATE TABLE habit_tags (
                                habit_id INTEGER NOT NULL REFERENCES habits(id),
                                tag_id INTEGER NOT NULL REFERENCES tags(id),
                                PRIMARY KEY (habit_id, tag_id)
                            )
                        """))
                    
                    # Проверить, существует ли таблица комментариев
                    result = connection.execute(text("""
                        SELECT name FROM sqlite_master WHERE type='table' AND name='comments'
                    """))
                    
                    if not result.fetchone():
                        # Создать таблицу комментариев
                        connection.execute(text("""
                            CREATE TABLE comments (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                habit_id INTEGER NOT NULL REFERENCES habits(id),
                                habit_log_id INTEGER NOT NULL REFERENCES habit_logs(id),
                                text VARCHAR(500) NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """))
                        
                        # Создать индексы для комментариев
                        connection.execute(text("""
                            CREATE INDEX idx_habit_log_comments ON comments(habit_log_id)
                        """))
                        
                        connection.execute(text("""
                            CREATE INDEX idx_habit_comments ON comments(habit_id)
                        """))
                    
                    # Проверить, существуют ли новые поля в таблице habits
                    result = connection.execute(text("PRAGMA table_info(habits)"))
                    existing_columns = {row[1] for row in result.fetchall()}
                    
                    if 'category_id' not in existing_columns:
                        connection.execute(text("""
                            ALTER TABLE habits ADD COLUMN category_id INTEGER REFERENCES categories(id)
                        """))
                    
                    if 'tracking_days' not in existing_columns:
                        connection.execute(text("""
                            ALTER TABLE habits ADD COLUMN tracking_days INTEGER DEFAULT 7
                        """))
                    
                    # Создать индекс для category_id
                    try:
                        connection.execute(text("""
                            CREATE INDEX idx_habits_category ON habits(category_id)
                        """))
                    except SQLAlchemyError:
                        pass
                    
                    # Проверить, существует ли новое поле в таблице users
                    result = connection.execute(text("PRAGMA table_info(users)"))
                    existing_columns = {row[1] for row in result.fetchall()}
                    
                    if 'default_tracking_days' not in existing_columns:
                        connection.execute(text("""
                            ALTER TABLE users ADD COLUMN default_tracking_days INTEGER DEFAULT 7
                        """))
                
                # Зафиксировать транзакцию
                trans.commit()
                logger.info("Миграция 002 успешно завершена")
                
            except Exception as e:
                # Откатить при ошибке
                trans.rollback()
                logger.error(f"Миграция 002 не удалась: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Ошибка миграции 002: {str(e)}")
        raise


def downgrade(engine):
    """
    Удалить новые таблицы и поля.
    
    Args:
        engine: Экземпляр SQLAlchemy engine
    """
    try:
        logger.info("Начало отката миграции 002: Удаление таблиц категорий, тегов и комментариев")
        
        with engine.connect() as connection:
            # Начать транзакцию
            trans = connection.begin()
            
            try:
                # Проверить, используется ли PostgreSQL или SQLite
                is_postgresql = 'postgresql' in str(engine.url)
                
                if is_postgresql:
                    logger.info("Применение отката PostgreSQL")
                    
                    # Удалить внешние ключи и столбцы из таблицы habits
                    connection.execute(text("""
                        ALTER TABLE habits DROP COLUMN IF EXISTS category_id
                    """))
                    
                    connection.execute(text("""
                        ALTER TABLE habits DROP COLUMN IF EXISTS tracking_days
                    """))
                    
                    # Удалить столбец из таблицы users
                    connection.execute(text("""
                        ALTER TABLE users DROP COLUMN IF EXISTS default_tracking_days
                    """))
                    
                    # Удалить таблицы в правильном порядке (из-за внешних ключей)
                    connection.execute(text("DROP TABLE IF EXISTS comments"))
                    connection.execute(text("DROP TABLE IF EXISTS habit_tags"))
                    connection.execute(text("DROP TABLE IF EXISTS tags"))
                    connection.execute(text("DROP TABLE IF EXISTS categories"))
                    
                else:
                    logger.info("Применение отката SQLite")
                    
                    # SQLite имеет ограниченную поддержку ALTER TABLE
                    # Мы можем только удалить таблицы
                    connection.execute(text("DROP TABLE IF EXISTS comments"))
                    connection.execute(text("DROP TABLE IF EXISTS habit_tags"))
                    connection.execute(text("DROP TABLE IF EXISTS tags"))
                    connection.execute(text("DROP TABLE IF EXISTS categories"))
                    
                    logger.warning("SQLite откат: столбцы в таблицах habits и users остаются, но не используются")
                
                # Зафиксировать транзакцию
                trans.commit()
                logger.info("Откат миграции 002 успешно завершен")
                
            except Exception as e:
                # Откатить при ошибке
                trans.rollback()
                logger.error(f"Откат миграции 002 не удалась: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Ошибка отката миграции 002: {str(e)}")
        raise


def get_migration_info():
    """
    Получить информацию об этой миграции.
    
    Returns:
        dict: Метаданные миграции
    """
    return {
        'revision': revision,
        'down_revision': down_revision,
        'branch_labels': branch_labels,
        'depends_on': depends_on,
        'description': 'Добавить таблицы категорий, тегов и комментариев для продвинутых функций',
        'tables_added': [
            'categories',
            'tags',
            'habit_tags',
            'comments'
        ],
        'tables_modified': [
            'habits',
            'users'
        ],
        'columns_added': {
            'habits': ['category_id', 'tracking_days'],
            'users': ['default_tracking_days']
        },
        'indexes_added': [
            'idx_categories_user',
            'idx_tags_user',
            'idx_habit_log_comments',
            'idx_habit_comments',
            'idx_habits_category'
        ]
    }
