"""
Модели данных приложения ChatList.
Dataclass-ы для работы с промптами, моделями, результатами и настройками.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Prompt:
    """Промпт пользователя."""
    
    id: Optional[int] = None
    text: str = ""
    author: str = "user"
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Model:
    """LLM-модель для тестирования."""
    
    id: Optional[int] = None
    name: str = ""
    api_url: str = ""
    api_id: str = ""
    is_active: bool = True


@dataclass
class Result:
    """Результат тестирования - ответ модели на промпт."""
    
    id: Optional[int] = None
    prompt_id: int = 0
    model_id: int = 0
    response_text: str = ""
    is_selected: bool = False
    created_at: Optional[datetime] = None
    
    # Дополнительные поля для отображения (не хранятся в БД)
    model_name: Optional[str] = field(default=None, repr=False)
    prompt_text: Optional[str] = field(default=None, repr=False)
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Settings:
    """Настройки приложения."""
    
    theme: str = "dark"
    default_author: str = "user"
    request_timeout: int = 30

