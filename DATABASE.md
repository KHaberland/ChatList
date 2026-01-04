# Схема базы данных ChatList

База данных: **SQLite** (`chatlist.db`)

---

## Диаграмма связей

```
┌─────────────┐       ┌─────────────┐
│   prompts   │       │   models    │
├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │
│ text        │       │ name        │
│ author      │       │ api_url     │
│ created_at  │       │ api_id      │
└──────┬──────┘       │ is_active   │
       │              └──────┬──────┘
       │                     │
       │    ┌────────────────┘
       │    │
       ▼    ▼
┌─────────────────────┐
│       results       │
├─────────────────────┤
│ id (PK)             │
│ prompt_id (FK)      │
│ model_id (FK)       │
│ response_text       │
│ is_selected         │
│ created_at          │
└─────────────────────┘

┌─────────────┐
│  settings   │
├─────────────┤
│ key (PK)    │
│ value       │
└─────────────┘
```

---

## Таблицы

### 1. prompts (Промпты)

Хранит все введённые пользователем промпты.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор |
| `text` | TEXT | NOT NULL | Текст промпта |
| `author` | TEXT | DEFAULT 'user' | Автор промпта |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Дата и время создания |

```sql
CREATE TABLE prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    author TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### 2. models (Модели)

Список LLM-моделей для тестирования.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор |
| `name` | TEXT | NOT NULL UNIQUE | Название модели (отображаемое) |
| `api_url` | TEXT | NOT NULL | URL API endpoint |
| `api_id` | TEXT | NOT NULL | Идентификатор модели в API |
| `is_active` | INTEGER | DEFAULT 1 | Активна ли модель (0/1) |

```sql
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_url TEXT NOT NULL,
    api_id TEXT NOT NULL,
    is_active INTEGER DEFAULT 1
);
```

**Примечание:** API-ключи НЕ хранятся в базе данных. Они загружаются из файла `.env`.

---

### 3. results (Результаты)

Ответы моделей на промпты.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор |
| `prompt_id` | INTEGER | FOREIGN KEY → prompts.id | Ссылка на промпт |
| `model_id` | INTEGER | FOREIGN KEY → models.id | Ссылка на модель |
| `response_text` | TEXT | NOT NULL | Текст ответа модели |
| `is_selected` | INTEGER | DEFAULT 0 | Отмечен как избранный (0/1) |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Время получения ответа |

```sql
CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    response_text TEXT NOT NULL,
    is_selected INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
);
```

---

### 4. settings (Настройки)

Хранение настроек приложения в формате ключ-значение.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `key` | TEXT | PRIMARY KEY | Ключ настройки |
| `value` | TEXT | | Значение настройки |

```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

**Примеры настроек:**

| Ключ | Значение | Описание |
|------|----------|----------|
| `theme` | `dark` / `light` | Тема оформления |
| `default_author` | `user` | Автор по умолчанию |
| `request_timeout` | `30` | Таймаут запросов (сек) |

---

## Индексы

```sql
-- Ускорение поиска по тексту промпта
CREATE INDEX idx_prompts_text ON prompts(text);

-- Ускорение поиска по дате
CREATE INDEX idx_prompts_created ON prompts(created_at);

-- Ускорение фильтрации активных моделей
CREATE INDEX idx_models_active ON models(is_active);

-- Ускорение поиска результатов по промпту
CREATE INDEX idx_results_prompt ON results(prompt_id);

-- Ускорение поиска избранных результатов
CREATE INDEX idx_results_selected ON results(is_selected);
```

---

## Файл .env (шаблон)

```env
# API ключи для разных провайдеров
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=...
GROQ_API_KEY=...

# Общие настройки
DEFAULT_TIMEOUT=30
```

---

## Примеры SQL-запросов

### Получить все активные модели
```sql
SELECT * FROM models WHERE is_active = 1;
```

### Получить историю промптов с поиском
```sql
SELECT * FROM prompts 
WHERE text LIKE '%поисковый запрос%'
ORDER BY created_at DESC;
```

### Получить результаты для конкретного промпта
```sql
SELECT r.*, m.name as model_name 
FROM results r
JOIN models m ON r.model_id = m.id
WHERE r.prompt_id = ?
ORDER BY r.created_at;
```

### Сохранить избранные результаты
```sql
UPDATE results SET is_selected = 1 WHERE id IN (?, ?, ?);
```

### Получить все избранные ответы
```sql
SELECT r.*, p.text as prompt_text, m.name as model_name
FROM results r
JOIN prompts p ON r.prompt_id = p.id
JOIN models m ON r.model_id = m.id
WHERE r.is_selected = 1
ORDER BY r.created_at DESC;
```

