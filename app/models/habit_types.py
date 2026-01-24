"""
Habit Types Enumeration

Defines the types of habits supported by the system
"""
from enum import Enum


class HabitType(Enum):
    """Enumeration of habit types"""
    USEFUL = "useful"      # Полезная привычка
    PLEASANT = "pleasant"  # Приятная привычка