"""
Тесты для ChatList.
Проверка CRUD-операций и сетевых функций.
"""

import unittest
import os
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from models import Prompt, Model, Result, Settings
import db


class TestPromptsCRUD(unittest.TestCase):
    """Тесты CRUD-операций для промптов."""
    
    def test_create_prompt(self):
        """Тест создания промпта."""
        prompt = Prompt(text="Тестовый промпт для юнит-теста")
        prompt_id = db.create_prompt(prompt)
        
        self.assertIsNotNone(prompt_id)
        self.assertIsInstance(prompt_id, int)
        self.assertGreater(prompt_id, 0)
        
        # Удаляем тестовые данные
        db.delete_prompt(prompt_id)
    
    def test_get_prompt(self):
        """Тест получения промпта по ID."""
        # Создаём промпт
        prompt = Prompt(text="Тест получения промпта")
        prompt_id = db.create_prompt(prompt)
        
        # Получаем промпт
        retrieved = db.get_prompt(prompt_id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.text, "Тест получения промпта")
        self.assertEqual(retrieved.id, prompt_id)
        
        # Удаляем тестовые данные
        db.delete_prompt(prompt_id)
    
    def test_get_nonexistent_prompt(self):
        """Тест получения несуществующего промпта."""
        result = db.get_prompt(999999)
        self.assertIsNone(result)
    
    def test_get_all_prompts(self):
        """Тест получения списка промптов."""
        # Создаём несколько промптов
        ids = []
        for i in range(3):
            prompt = Prompt(text=f"Тестовый промпт {i}")
            ids.append(db.create_prompt(prompt))
        
        # Получаем список
        prompts = db.get_all_prompts(limit=100)
        
        self.assertIsInstance(prompts, list)
        self.assertGreaterEqual(len(prompts), 3)
        
        # Удаляем тестовые данные
        for pid in ids:
            db.delete_prompt(pid)
    
    def test_search_prompts(self):
        """Тест поиска промптов по тексту."""
        # Создаём промпт с уникальным текстом
        unique_text = "УНИКАЛЬНЫЙ_ТЕКСТ_ДЛЯ_ПОИСКА_12345"
        prompt = Prompt(text=unique_text)
        prompt_id = db.create_prompt(prompt)
        
        # Ищем
        results = db.get_all_prompts(search="УНИКАЛЬНЫЙ_ТЕКСТ")
        
        self.assertGreaterEqual(len(results), 1)
        found = any(p.text == unique_text for p in results)
        self.assertTrue(found)
        
        # Удаляем тестовые данные
        db.delete_prompt(prompt_id)
    
    def test_delete_prompt(self):
        """Тест удаления промпта."""
        prompt = Prompt(text="Промпт для удаления")
        prompt_id = db.create_prompt(prompt)
        
        # Удаляем
        result = db.delete_prompt(prompt_id)
        self.assertTrue(result)
        
        # Проверяем, что удалён
        retrieved = db.get_prompt(prompt_id)
        self.assertIsNone(retrieved)


class TestModelsCRUD(unittest.TestCase):
    """Тесты CRUD-операций для моделей."""
    
    def test_create_model(self):
        """Тест создания модели."""
        model = Model(
            name="Test Model Unit",
            api_url="https://test.api/v1/chat",
            api_id="test-model-id",
            is_active=True
        )
        model_id = db.create_model(model)
        
        self.assertIsNotNone(model_id)
        self.assertGreater(model_id, 0)
        
        # Удаляем тестовые данные
        db.delete_model(model_id)
    
    def test_get_model(self):
        """Тест получения модели по ID."""
        model = Model(
            name="Test Get Model",
            api_url="https://test.api/v1/chat",
            api_id="test-get-model",
            is_active=False
        )
        model_id = db.create_model(model)
        
        retrieved = db.get_model(model_id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Get Model")
        self.assertEqual(retrieved.api_id, "test-get-model")
        self.assertFalse(retrieved.is_active)
        
        db.delete_model(model_id)
    
    def test_get_all_models(self):
        """Тест получения списка моделей."""
        models = db.get_all_models()
        
        self.assertIsInstance(models, list)
        # Должны быть предустановленные модели из seed_db
        self.assertGreater(len(models), 0)
    
    def test_get_active_models(self):
        """Тест получения только активных моделей."""
        models = db.get_all_models(active_only=True)
        
        self.assertIsInstance(models, list)
        for model in models:
            self.assertTrue(model.is_active)
    
    def test_update_model(self):
        """Тест обновления модели."""
        model = Model(
            name="Model to Update",
            api_url="https://old.api/v1",
            api_id="old-id",
            is_active=True
        )
        model_id = db.create_model(model)
        
        # Обновляем
        model.id = model_id
        model.name = "Updated Model Name"
        model.api_url = "https://new.api/v1"
        result = db.update_model(model)
        
        self.assertTrue(result)
        
        # Проверяем
        updated = db.get_model(model_id)
        self.assertEqual(updated.name, "Updated Model Name")
        self.assertEqual(updated.api_url, "https://new.api/v1")
        
        db.delete_model(model_id)
    
    def test_delete_model(self):
        """Тест удаления модели."""
        model = Model(
            name="Model to Delete",
            api_url="https://delete.api/v1",
            api_id="delete-id"
        )
        model_id = db.create_model(model)
        
        result = db.delete_model(model_id)
        self.assertTrue(result)
        
        retrieved = db.get_model(model_id)
        self.assertIsNone(retrieved)


class TestResultsCRUD(unittest.TestCase):
    """Тесты CRUD-операций для результатов."""
    
    @classmethod
    def setUpClass(cls):
        """Создание тестовых данных."""
        # Создаём промпт для тестов
        cls.test_prompt = Prompt(text="Промпт для тестов результатов")
        cls.prompt_id = db.create_prompt(cls.test_prompt)
        
        # Получаем первую модель
        models = db.get_all_models()
        cls.model_id = models[0].id if models else None
    
    @classmethod
    def tearDownClass(cls):
        """Удаление тестовых данных."""
        if cls.prompt_id:
            db.delete_prompt(cls.prompt_id)
    
    def test_create_result(self):
        """Тест создания результата."""
        if not self.model_id:
            self.skipTest("Нет моделей в БД")
        
        result = Result(
            prompt_id=self.prompt_id,
            model_id=self.model_id,
            response_text="Тестовый ответ модели",
            is_selected=False
        )
        result_id = db.create_result(result)
        
        self.assertIsNotNone(result_id)
        self.assertGreater(result_id, 0)
        
        db.delete_result(result_id)
    
    def test_get_results_for_prompt(self):
        """Тест получения результатов для промпта."""
        if not self.model_id:
            self.skipTest("Нет моделей в БД")
        
        # Создаём результат
        result = Result(
            prompt_id=self.prompt_id,
            model_id=self.model_id,
            response_text="Ответ для теста получения"
        )
        result_id = db.create_result(result)
        
        # Получаем результаты
        results = db.get_results_for_prompt(self.prompt_id)
        
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)
        
        db.delete_result(result_id)
    
    def test_update_result_selection(self):
        """Тест обновления статуса избранного."""
        if not self.model_id:
            self.skipTest("Нет моделей в БД")
        
        result = Result(
            prompt_id=self.prompt_id,
            model_id=self.model_id,
            response_text="Ответ для теста избранного",
            is_selected=False
        )
        result_id = db.create_result(result)
        
        # Обновляем статус
        success = db.update_result_selection(result_id, True)
        self.assertTrue(success)
        
        # Проверяем через get_selected_results
        selected = db.get_selected_results()
        found = any(r.id == result_id for r in selected)
        self.assertTrue(found)
        
        db.delete_result(result_id)


class TestSettingsCRUD(unittest.TestCase):
    """Тесты функций настроек."""
    
    def test_get_setting(self):
        """Тест получения настройки."""
        # Настройка theme должна существовать из seed_db
        theme = db.get_setting("theme")
        self.assertIn(theme, ["dark", "light"])
    
    def test_get_setting_default(self):
        """Тест значения по умолчанию для несуществующей настройки."""
        value = db.get_setting("nonexistent_key", "default_value")
        self.assertEqual(value, "default_value")
    
    def test_set_setting(self):
        """Тест установки настройки."""
        db.set_setting("test_key", "test_value")
        
        value = db.get_setting("test_key")
        self.assertEqual(value, "test_value")
        
        # Очистка - устанавливаем пустое значение
        db.set_setting("test_key", "")
    
    def test_get_all_settings(self):
        """Тест получения всех настроек."""
        settings = db.get_all_settings()
        
        self.assertIsInstance(settings, Settings)
        self.assertIn(settings.theme, ["dark", "light"])
        self.assertIsInstance(settings.request_timeout, int)
    
    def test_save_settings(self):
        """Тест сохранения настроек."""
        # Сохраняем текущие настройки
        original = db.get_all_settings()
        
        # Меняем
        new_settings = Settings(
            theme="light",
            default_author="test_author",
            request_timeout=60
        )
        db.save_settings(new_settings)
        
        # Проверяем
        loaded = db.get_all_settings()
        self.assertEqual(loaded.theme, "light")
        self.assertEqual(loaded.request_timeout, 60)
        
        # Восстанавливаем оригинальные настройки
        db.save_settings(original)


class TestDateFilter(unittest.TestCase):
    """Тесты фильтрации по дате."""
    
    def test_filter_by_date_range(self):
        """Тест фильтрации промптов по диапазону дат."""
        # Создаём промпт (он будет с текущей датой)
        prompt = Prompt(text="Промпт для теста фильтра по дате")
        prompt_id = db.create_prompt(prompt)
        
        from datetime import date, timedelta
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # Фильтруем с датой, включающей сегодня
        results = db.get_all_prompts(
            date_from=yesterday.isoformat(),
            date_to=tomorrow.isoformat()
        )
        
        found = any(p.id == prompt_id for p in results)
        self.assertTrue(found)
        
        # Фильтруем с датой в прошлом (не должен найти)
        old_date = today - timedelta(days=30)
        older_date = today - timedelta(days=31)
        results_old = db.get_all_prompts(
            date_from=older_date.isoformat(),
            date_to=old_date.isoformat()
        )
        
        found_old = any(p.id == prompt_id for p in results_old)
        self.assertFalse(found_old)
        
        db.delete_prompt(prompt_id)


class TestModelsDataclass(unittest.TestCase):
    """Тесты dataclass моделей."""
    
    def test_prompt_defaults(self):
        """Тест значений по умолчанию Prompt."""
        prompt = Prompt(text="Test")
        
        self.assertIsNone(prompt.id)
        self.assertEqual(prompt.text, "Test")
        self.assertEqual(prompt.author, "user")
        self.assertIsNotNone(prompt.created_at)
    
    def test_model_defaults(self):
        """Тест значений по умолчанию Model."""
        model = Model()
        
        self.assertIsNone(model.id)
        self.assertEqual(model.name, "")
        self.assertEqual(model.api_url, "")
        self.assertEqual(model.api_id, "")
        self.assertTrue(model.is_active)
    
    def test_result_defaults(self):
        """Тест значений по умолчанию Result."""
        result = Result(prompt_id=1, model_id=1)
        
        self.assertIsNone(result.id)
        self.assertEqual(result.prompt_id, 1)
        self.assertEqual(result.model_id, 1)
        self.assertEqual(result.response_text, "")
        self.assertFalse(result.is_selected)
        self.assertIsNotNone(result.created_at)
    
    def test_settings_defaults(self):
        """Тест значений по умолчанию Settings."""
        settings = Settings()
        
        self.assertEqual(settings.theme, "dark")
        self.assertEqual(settings.default_author, "user")
        self.assertEqual(settings.request_timeout, 30)


def run_tests():
    """Запуск всех тестов."""
    # Создаём загрузчик тестов
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestPromptsCRUD))
    suite.addTests(loader.loadTestsFromTestCase(TestModelsCRUD))
    suite.addTests(loader.loadTestsFromTestCase(TestResultsCRUD))
    suite.addTests(loader.loadTestsFromTestCase(TestSettingsCRUD))
    suite.addTests(loader.loadTestsFromTestCase(TestDateFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestModelsDataclass))
    
    # Запускаем с подробным выводом
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)






