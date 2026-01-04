"""
Модуль работы с базой данных SQLite.
CRUD-операции для таблиц prompts, models, results, settings.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager

from models import Prompt, Model, Result, Settings


# Путь к файлу базы данных
DB_PATH = Path(__file__).parent / "chatlist.db"


@contextmanager
def get_connection():
    """Контекстный менеджер для подключения к БД."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Инициализация базы данных и создание таблиц."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Таблица промптов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                author TEXT DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица моделей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                api_url TEXT NOT NULL,
                api_id TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Таблица результатов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER NOT NULL,
                model_id INTEGER NOT NULL,
                response_text TEXT NOT NULL,
                is_selected INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
            )
        """)
        
        # Таблица настроек
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Создание индексов
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prompts_text ON prompts(text)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prompts_created ON prompts(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_prompt ON results(prompt_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_selected ON results(is_selected)")


def seed_db():
    """Добавление тестовых данных при первом запуске."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Модели для добавления (OpenRouter использует OpenAI-совместимый формат)
        openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        all_models = [
            # OpenRouter модели (рекомендуемые)
            ("GPT-4o (OpenRouter)", openrouter_url, "openai/gpt-4o"),
            ("GPT-4o-mini (OpenRouter)", openrouter_url, "openai/gpt-4o-mini"),
            ("Claude 3.5 Sonnet (OpenRouter)", openrouter_url, "anthropic/claude-3.5-sonnet"),
            ("Claude 3 Opus (OpenRouter)", openrouter_url, "anthropic/claude-3-opus"),
            ("Gemini Pro 1.5 (OpenRouter)", openrouter_url, "google/gemini-pro-1.5"),
            ("DeepSeek V3 (OpenRouter)", openrouter_url, "deepseek/deepseek-chat"),
            ("Llama 3.3 70B (OpenRouter)", openrouter_url, "meta-llama/llama-3.3-70b-instruct"),
            ("Mixtral 8x7B (OpenRouter)", openrouter_url, "mistralai/mixtral-8x7b-instruct"),
            # Прямые API (опционально, требуют отдельных ключей)
            ("GPT-4o (Direct)", "https://api.openai.com/v1/chat/completions", "gpt-4o"),
            ("DeepSeek V3 (Direct)", "https://api.deepseek.com/v1/chat/completions", "deepseek-chat"),
            ("Claude 3.5 Sonnet (Direct)", "https://api.anthropic.com/v1/messages", "claude-3-5-sonnet-20241022"),
        ]
        
        # Добавляем только те модели, которых ещё нет
        for name, api_url, api_id in all_models:
            cursor.execute(
                "INSERT OR IGNORE INTO models (name, api_url, api_id) VALUES (?, ?, ?)",
                (name, api_url, api_id)
            )
        
        # Добавляем настройки по умолчанию
        default_settings = [
            ("theme", "dark"),
            ("default_author", "user"),
            ("request_timeout", "30"),
        ]
        for key, value in default_settings:
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )


# =====================
# CRUD для Prompts
# =====================

def create_prompt(prompt: Prompt) -> int:
    """Создать новый промпт. Возвращает ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO prompts (text, author) VALUES (?, ?)",
            (prompt.text, prompt.author)
        )
        return cursor.lastrowid


def get_prompt(prompt_id: int) -> Optional[Prompt]:
    """Получить промпт по ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
        row = cursor.fetchone()
        if row:
            return Prompt(
                id=row["id"],
                text=row["text"],
                author=row["author"],
                created_at=row["created_at"]
            )
        return None


def get_all_prompts(search: str = "", limit: int = 100) -> List[Prompt]:
    """Получить список промптов с возможностью поиска."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if search:
            cursor.execute(
                """SELECT * FROM prompts 
                   WHERE text LIKE ? 
                   ORDER BY created_at DESC LIMIT ?""",
                (f"%{search}%", limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM prompts ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        return [
            Prompt(
                id=row["id"],
                text=row["text"],
                author=row["author"],
                created_at=row["created_at"]
            )
            for row in cursor.fetchall()
        ]


def delete_prompt(prompt_id: int) -> bool:
    """Удалить промпт по ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        return cursor.rowcount > 0


# =====================
# CRUD для Models
# =====================

def create_model(model: Model) -> int:
    """Создать новую модель. Возвращает ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO models (name, api_url, api_id, is_active) VALUES (?, ?, ?, ?)",
            (model.name, model.api_url, model.api_id, int(model.is_active))
        )
        return cursor.lastrowid


def get_model(model_id: int) -> Optional[Model]:
    """Получить модель по ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
        row = cursor.fetchone()
        if row:
            return Model(
                id=row["id"],
                name=row["name"],
                api_url=row["api_url"],
                api_id=row["api_id"],
                is_active=bool(row["is_active"])
            )
        return None


def get_all_models(active_only: bool = False) -> List[Model]:
    """Получить список моделей."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if active_only:
            cursor.execute("SELECT * FROM models WHERE is_active = 1 ORDER BY name")
        else:
            cursor.execute("SELECT * FROM models ORDER BY name")
        return [
            Model(
                id=row["id"],
                name=row["name"],
                api_url=row["api_url"],
                api_id=row["api_id"],
                is_active=bool(row["is_active"])
            )
            for row in cursor.fetchall()
        ]


def update_model(model: Model) -> bool:
    """Обновить модель."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE models 
               SET name = ?, api_url = ?, api_id = ?, is_active = ? 
               WHERE id = ?""",
            (model.name, model.api_url, model.api_id, int(model.is_active), model.id)
        )
        return cursor.rowcount > 0


def delete_model(model_id: int) -> bool:
    """Удалить модель по ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
        return cursor.rowcount > 0


# =====================
# CRUD для Results
# =====================

def create_result(result: Result) -> int:
    """Создать новый результат. Возвращает ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO results (prompt_id, model_id, response_text, is_selected) 
               VALUES (?, ?, ?, ?)""",
            (result.prompt_id, result.model_id, result.response_text, int(result.is_selected))
        )
        return cursor.lastrowid


def get_results_for_prompt(prompt_id: int) -> List[Result]:
    """Получить все результаты для промпта."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT r.*, m.name as model_name 
               FROM results r
               JOIN models m ON r.model_id = m.id
               WHERE r.prompt_id = ?
               ORDER BY r.created_at""",
            (prompt_id,)
        )
        return [
            Result(
                id=row["id"],
                prompt_id=row["prompt_id"],
                model_id=row["model_id"],
                response_text=row["response_text"],
                is_selected=bool(row["is_selected"]),
                created_at=row["created_at"],
                model_name=row["model_name"]
            )
            for row in cursor.fetchall()
        ]


def get_selected_results() -> List[Result]:
    """Получить все избранные результаты."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT r.*, p.text as prompt_text, m.name as model_name
               FROM results r
               JOIN prompts p ON r.prompt_id = p.id
               JOIN models m ON r.model_id = m.id
               WHERE r.is_selected = 1
               ORDER BY r.created_at DESC"""
        )
        return [
            Result(
                id=row["id"],
                prompt_id=row["prompt_id"],
                model_id=row["model_id"],
                response_text=row["response_text"],
                is_selected=True,
                created_at=row["created_at"],
                model_name=row["model_name"],
                prompt_text=row["prompt_text"]
            )
            for row in cursor.fetchall()
        ]


def update_result_selection(result_id: int, is_selected: bool) -> bool:
    """Обновить статус избранного для результата."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE results SET is_selected = ? WHERE id = ?",
            (int(is_selected), result_id)
        )
        return cursor.rowcount > 0


def update_results_selection(result_ids: List[int], is_selected: bool) -> int:
    """Обновить статус избранного для нескольких результатов."""
    with get_connection() as conn:
        cursor = conn.cursor()
        placeholders = ",".join("?" * len(result_ids))
        cursor.execute(
            f"UPDATE results SET is_selected = ? WHERE id IN ({placeholders})",
            [int(is_selected)] + result_ids
        )
        return cursor.rowcount


def delete_result(result_id: int) -> bool:
    """Удалить результат по ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM results WHERE id = ?", (result_id,))
        return cursor.rowcount > 0


# =====================
# Функции для Settings
# =====================

def get_setting(key: str, default: str = "") -> str:
    """Получить значение настройки."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str):
    """Установить значение настройки."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )


def get_all_settings() -> Settings:
    """Получить все настройки как объект Settings."""
    return Settings(
        theme=get_setting("theme", "dark"),
        default_author=get_setting("default_author", "user"),
        request_timeout=int(get_setting("request_timeout", "30"))
    )


def save_settings(settings: Settings):
    """Сохранить все настройки."""
    set_setting("theme", settings.theme)
    set_setting("default_author", settings.default_author)
    set_setting("request_timeout", str(settings.request_timeout))


# Инициализация БД при импорте модуля
init_db()
seed_db()

