"""
Модель Категория

Модель для организации привычек по категориям
"""
from datetime import datetime, timezone

# Это будет инициализировано фабрикой приложения
db = None


def create_category_model(database):
    """Создать модель Category с экземпляром базы данных"""
    global db
    db = database
    
    class Category(db.Model):
        """
        Модель категории для организации привычек
        """
        __tablename__ = 'categories'
        
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
        name = db.Column(db.String(50), nullable=False)
        color = db.Column(db.String(7), default='#6366f1')  # Hex цвет
        icon = db.Column(db.String(50))  # Имя иконки
        created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
        
        # Связи
        habits = db.relationship('Habit', backref='category', lazy=True)
        user = db.relationship('User', backref='categories')
        
        # Индексы и ограничения
        __table_args__ = (
            db.UniqueConstraint('user_id', 'name', name='unique_user_category'),
            db.Index('idx_categories_user', 'user_id'),
        )
        
        def __repr__(self):
            return f'<Category {self.name}>'
        
        def to_dict(self):
            """
            Преобразовать категорию в словарь для API ответов
            
            Returns:
                dict: Данные категории в виде словаря
            """
            return {
                'id': self.id,
                'user_id': self.user_id,
                'name': self.name,
                'color': self.color,
                'icon': self.icon,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'habits_count': len(self.habits)
            }
    
    return Category


# Глобальный класс Category - будет установлен после инициализации
Category = None
