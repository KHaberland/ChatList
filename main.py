"""
ChatList - приложение для сравнения ответов различных LLM моделей.
Главное окно приложения на PyQt6.
"""

import sys
import asyncio
from typing import List, Optional

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QScrollArea,
    QFrame,
    QSplitter,
    QLineEdit,
    QGroupBox,
    QMessageBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont

import db
from models import Prompt, Model, Result
from network import LLMClient, send_to_multiple_models, APIResponse


# =====================
# Стили приложения
# =====================

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

QGroupBox {
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #89b4fa;
}

QTextEdit, QLineEdit, QComboBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
}

QTextEdit:focus, QLineEdit:focus {
    border: 1px solid #89b4fa;
}

QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #b4befe;
}

QPushButton:pressed {
    background-color: #74c7ec;
}

QPushButton:disabled {
    background-color: #45475a;
    color: #6c7086;
}

QPushButton#secondary {
    background-color: #45475a;
    color: #cdd6f4;
}

QPushButton#secondary:hover {
    background-color: #585b70;
}

QCheckBox {
    spacing: 8px;
    color: #cdd6f4;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #45475a;
    background-color: #313244;
}

QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #313244;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}

QLabel#title {
    font-size: 24px;
    font-weight: bold;
    color: #89b4fa;
}

QLabel#subtitle {
    color: #6c7086;
    font-size: 12px;
}

QFrame#resultCard {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 10px;
    padding: 15px;
}

QFrame#resultCard[selected="true"] {
    border: 2px solid #a6e3a1;
}
"""


# =====================
# Рабочий поток для API запросов
# =====================

class APIWorker(QThread):
    """Фоновый поток для выполнения API запросов."""
    
    finished = pyqtSignal(dict)  # {model_id: APIResponse}
    error = pyqtSignal(str)
    progress = pyqtSignal(str)  # Сообщение о прогрессе
    
    def __init__(self, models: List[Model], prompt: str, timeout: int = 30):
        super().__init__()
        self.models = models
        self.prompt = prompt
        self.timeout = timeout
    
    def run(self):
        try:
            self.progress.emit("Отправка запросов...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                send_to_multiple_models(self.models, self.prompt, self.timeout)
            )
            loop.close()
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


# =====================
# Виджет карточки результата
# =====================

class ResultCard(QFrame):
    """Карточка с ответом модели."""
    
    selection_changed = pyqtSignal(int, bool)  # result_id, is_selected
    
    def __init__(self, result: Result, parent=None):
        super().__init__(parent)
        self.result = result
        self.setObjectName("resultCard")
        self.setMinimumWidth(350)
        self.setMaximumWidth(450)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Заголовок с названием модели
        header = QHBoxLayout()
        
        model_label = QLabel(self.result.model_name or f"Модель #{self.result.model_id}")
        model_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa;")
        header.addWidget(model_label)
        
        header.addStretch()
        
        # Чекбокс выбора
        self.select_checkbox = QCheckBox("Избранное")
        self.select_checkbox.setChecked(self.result.is_selected)
        self.select_checkbox.stateChanged.connect(self._on_selection_changed)
        header.addWidget(self.select_checkbox)
        
        layout.addLayout(header)
        
        # Текст ответа
        self.response_text = QTextEdit()
        self.response_text.setPlainText(self.result.response_text)
        self.response_text.setReadOnly(True)
        self.response_text.setMinimumHeight(200)
        layout.addWidget(self.response_text)
        
        # Обновляем стиль в зависимости от выбора
        self._update_style()
    
    def _on_selection_changed(self, state):
        is_selected = state == Qt.CheckState.Checked.value
        self.result.is_selected = is_selected
        self._update_style()
        if self.result.id:
            self.selection_changed.emit(self.result.id, is_selected)
    
    def _update_style(self):
        if self.result.is_selected:
            self.setStyleSheet("""
                QFrame#resultCard {
                    background-color: #313244;
                    border: 2px solid #a6e3a1;
                    border-radius: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#resultCard {
                    background-color: #313244;
                    border: 1px solid #45475a;
                    border-radius: 10px;
                }
            """)
    
    def set_response(self, text: str):
        """Установить текст ответа."""
        self.result.response_text = text
        self.response_text.setPlainText(text)
    
    def set_error(self, error: str):
        """Показать ошибку."""
        self.response_text.setPlainText(f"❌ Ошибка: {error}")
        self.response_text.setStyleSheet("color: #f38ba8;")


# =====================
# Главное окно
# =====================

class MainWindow(QMainWindow):
    """Главное окно приложения ChatList."""
    
    def __init__(self):
        super().__init__()
        
        self.current_prompt_id: Optional[int] = None
        self.result_cards: List[ResultCard] = []
        self.api_worker: Optional[APIWorker] = None
        
        self._setup_window()
        self._setup_ui()
        self._load_data()
    
    def _setup_window(self):
        """Настройка окна."""
        self.setWindowTitle("ChatList - Сравнение LLM моделей")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(DARK_STYLE)
    
    def _setup_ui(self):
        """Создание интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Основной контент
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель (ввод и модели)
        left_panel = self._create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Правая панель (результаты)
        right_panel = self._create_results_panel()
        content_splitter.addWidget(right_panel)
        
        content_splitter.setSizes([400, 800])
        main_layout.addWidget(content_splitter, 1)
        
        # Нижняя панель действий
        actions_panel = self._create_actions_panel()
        main_layout.addWidget(actions_panel)
    
    def _create_header(self) -> QWidget:
        """Создание заголовка."""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 10)
        
        # Логотип и название
        title_layout = QVBoxLayout()
        
        title = QLabel("🤖 ChatList")
        title.setObjectName("title")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Сравнивайте ответы разных LLM моделей на один промпт")
        subtitle.setObjectName("subtitle")
        title_layout.addWidget(subtitle)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        return header
    
    def _create_left_panel(self) -> QWidget:
        """Создание левой панели (ввод промпта и выбор моделей)."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Группа ввода промпта
        prompt_group = QGroupBox("📝 Промпт")
        prompt_layout = QVBoxLayout(prompt_group)
        
        # История промптов
        history_layout = QHBoxLayout()
        history_label = QLabel("История:")
        history_layout.addWidget(history_label)
        
        self.history_combo = QComboBox()
        self.history_combo.setMinimumWidth(200)
        self.history_combo.currentIndexChanged.connect(self._on_history_selected)
        history_layout.addWidget(self.history_combo, 1)
        
        prompt_layout.addLayout(history_layout)
        
        # Поле ввода промпта
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Введите ваш промпт здесь...")
        self.prompt_input.setMinimumHeight(150)
        prompt_layout.addWidget(self.prompt_input)
        
        # Кнопка отправки
        self.send_button = QPushButton("🚀 Отправить")
        self.send_button.clicked.connect(self._on_send_clicked)
        prompt_layout.addWidget(self.send_button)
        
        layout.addWidget(prompt_group)
        
        # Группа выбора моделей
        models_group = QGroupBox("🧠 Модели")
        models_layout = QVBoxLayout(models_group)
        
        # Контейнер для чекбоксов моделей
        self.models_container = QVBoxLayout()
        models_layout.addLayout(self.models_container)
        
        # Кнопки управления моделями
        models_buttons = QHBoxLayout()
        
        select_all_btn = QPushButton("Выбрать все")
        select_all_btn.setObjectName("secondary")
        select_all_btn.clicked.connect(self._select_all_models)
        models_buttons.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Снять все")
        deselect_all_btn.setObjectName("secondary")
        deselect_all_btn.clicked.connect(self._deselect_all_models)
        models_buttons.addWidget(deselect_all_btn)
        
        models_layout.addLayout(models_buttons)
        
        layout.addWidget(models_group)
        layout.addStretch()
        
        return panel
    
    def _create_results_panel(self) -> QWidget:
        """Создание панели результатов."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Заголовок
        header = QHBoxLayout()
        results_label = QLabel("📊 Результаты")
        results_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #89b4fa;")
        header.addWidget(results_label)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #6c7086;")
        header.addWidget(self.status_label)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Область прокрутки для карточек
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Контейнер для карточек
        self.results_container = QWidget()
        self.results_layout = QHBoxLayout(self.results_container)
        self.results_layout.setSpacing(15)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        scroll_area.setWidget(self.results_container)
        layout.addWidget(scroll_area, 1)
        
        return panel
    
    def _create_actions_panel(self) -> QWidget:
        """Создание панели действий."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Поиск
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по истории...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        layout.addStretch()
        
        # Кнопки действий
        save_selected_btn = QPushButton("💾 Сохранить избранные")
        save_selected_btn.clicked.connect(self._save_selected)
        layout.addWidget(save_selected_btn)
        
        return panel
    
    def _load_data(self):
        """Загрузка данных из БД."""
        self._load_models()
        self._load_history()
    
    def _load_models(self):
        """Загрузка списка моделей."""
        # Очищаем контейнер
        while self.models_container.count():
            item = self.models_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Загружаем модели из БД
        models = db.get_all_models()
        self.model_checkboxes = {}
        
        for model in models:
            checkbox = QCheckBox(model.name)
            checkbox.setChecked(model.is_active)
            checkbox.model_id = model.id
            self.model_checkboxes[model.id] = checkbox
            self.models_container.addWidget(checkbox)
    
    def _load_history(self, search: str = ""):
        """Загрузка истории промптов."""
        self.history_combo.clear()
        self.history_combo.addItem("-- Новый промпт --", None)
        
        prompts = db.get_all_prompts(search=search)
        for prompt in prompts:
            # Обрезаем длинный текст
            display_text = prompt.text[:50] + "..." if len(prompt.text) > 50 else prompt.text
            display_text = display_text.replace("\n", " ")
            self.history_combo.addItem(display_text, prompt.id)
    
    def _on_history_selected(self, index: int):
        """Обработчик выбора промпта из истории."""
        prompt_id = self.history_combo.currentData()
        if prompt_id:
            prompt = db.get_prompt(prompt_id)
            if prompt:
                self.prompt_input.setPlainText(prompt.text)
                self.current_prompt_id = prompt_id
                self._load_results_for_prompt(prompt_id)
        else:
            self.current_prompt_id = None
    
    def _load_results_for_prompt(self, prompt_id: int):
        """Загрузка результатов для промпта."""
        self._clear_results()
        
        results = db.get_results_for_prompt(prompt_id)
        for result in results:
            self._add_result_card(result)
    
    def _clear_results(self):
        """Очистка панели результатов."""
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.result_cards.clear()
    
    def _add_result_card(self, result: Result) -> ResultCard:
        """Добавить карточку результата."""
        card = ResultCard(result)
        card.selection_changed.connect(self._on_result_selection_changed)
        self.results_layout.addWidget(card)
        self.result_cards.append(card)
        return card
    
    def _on_result_selection_changed(self, result_id: int, is_selected: bool):
        """Обработчик изменения выбора результата."""
        db.update_result_selection(result_id, is_selected)
    
    def _get_selected_models(self) -> List[Model]:
        """Получить список выбранных моделей."""
        selected = []
        for model_id, checkbox in self.model_checkboxes.items():
            if checkbox.isChecked():
                model = db.get_model(model_id)
                if model:
                    selected.append(model)
        return selected
    
    def _select_all_models(self):
        """Выбрать все модели."""
        for checkbox in self.model_checkboxes.values():
            checkbox.setChecked(True)
    
    def _deselect_all_models(self):
        """Снять выбор со всех моделей."""
        for checkbox in self.model_checkboxes.values():
            checkbox.setChecked(False)
    
    def _on_send_clicked(self):
        """Обработчик нажатия кнопки отправки."""
        prompt_text = self.prompt_input.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Внимание", "Введите текст промпта")
            return
        
        selected_models = self._get_selected_models()
        if not selected_models:
            QMessageBox.warning(self, "Внимание", "Выберите хотя бы одну модель")
            return
        
        # Сохраняем промпт в БД
        prompt = Prompt(text=prompt_text)
        prompt_id = db.create_prompt(prompt)
        self.current_prompt_id = prompt_id
        
        # Очищаем результаты
        self._clear_results()
        
        # Создаём пустые карточки для каждой модели
        model_cards = {}
        for model in selected_models:
            result = Result(
                prompt_id=prompt_id,
                model_id=model.id,
                response_text="⏳ Загрузка...",
                model_name=model.name
            )
            card = self._add_result_card(result)
            model_cards[model.id] = card
        
        # Блокируем кнопку
        self.send_button.setEnabled(False)
        self.send_button.setText("⏳ Отправка...")
        self.status_label.setText("Отправка запросов...")
        
        # Запускаем фоновый поток
        settings = db.get_all_settings()
        self.api_worker = APIWorker(selected_models, prompt_text, settings.request_timeout)
        self.api_worker.finished.connect(
            lambda results: self._on_api_finished(results, model_cards, prompt_id)
        )
        self.api_worker.error.connect(self._on_api_error)
        self.api_worker.start()
        
        # Обновляем историю
        self._load_history()
    
    def _on_api_finished(self, results: dict, model_cards: dict, prompt_id: int):
        """Обработчик завершения API запросов."""
        for model_id, response in results.items():
            card = model_cards.get(model_id)
            if not card:
                continue
            
            if response.success:
                card.set_response(response.content)
                # Сохраняем в БД
                result = Result(
                    prompt_id=prompt_id,
                    model_id=model_id,
                    response_text=response.content
                )
                result_id = db.create_result(result)
                card.result.id = result_id
            else:
                card.set_error(response.error or "Неизвестная ошибка")
        
        self.send_button.setEnabled(True)
        self.send_button.setText("🚀 Отправить")
        self.status_label.setText(f"Получено {len(results)} ответов")
    
    def _on_api_error(self, error: str):
        """Обработчик ошибки API."""
        QMessageBox.critical(self, "Ошибка", f"Ошибка при выполнении запросов:\n{error}")
        self.send_button.setEnabled(True)
        self.send_button.setText("🚀 Отправить")
        self.status_label.setText("")
    
    def _on_search_changed(self, text: str):
        """Обработчик изменения поиска."""
        self._load_history(search=text)
    
    def _save_selected(self):
        """Сохранить избранные результаты."""
        selected_count = sum(1 for card in self.result_cards if card.result.is_selected)
        if selected_count == 0:
            QMessageBox.information(self, "Информация", "Нет избранных результатов для сохранения")
            return
        
        QMessageBox.information(
            self, 
            "Сохранено", 
            f"Сохранено {selected_count} избранных результатов"
        )


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
