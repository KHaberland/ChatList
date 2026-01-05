"""
ChatList - приложение для сравнения ответов различных LLM моделей.
Главное окно приложения на PyQt6.
"""

import sys
import asyncio
import json
from datetime import datetime, date
from typing import List, Optional

import markdown

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QTextBrowser,
    QComboBox,
    QCheckBox,
    QScrollArea,
    QFrame,
    QSplitter,
    QLineEdit,
    QGroupBox,
    QMessageBox,
    QSizePolicy,
    QDialog,
    QDateEdit,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QTabWidget,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt6.QtGui import QFont

import db
from models import Prompt, Model, Result, Settings
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

QTextEdit, QLineEdit, QComboBox, QDateEdit, QSpinBox {
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

QPushButton#icon {
    background-color: transparent;
    padding: 5px 10px;
    font-size: 18px;
}

QPushButton#icon:hover {
    background-color: #45475a;
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

QTableWidget {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    gridline-color: #45475a;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}

QHeaderView::section {
    background-color: #45475a;
    color: #cdd6f4;
    padding: 8px;
    border: none;
    font-weight: bold;
}

QTabWidget::pane {
    border: 1px solid #45475a;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #313244;
    color: #cdd6f4;
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}
"""

LIGHT_STYLE = """
QMainWindow, QWidget {
    background-color: #eff1f5;
    color: #4c4f69;
}

QGroupBox {
    border: 1px solid #ccd0da;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #1e66f5;
}

QTextEdit, QLineEdit, QComboBox, QDateEdit, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 8px;
    color: #4c4f69;
    selection-background-color: #1e66f5;
}

QTextEdit:focus, QLineEdit:focus {
    border: 1px solid #1e66f5;
}

QPushButton {
    background-color: #1e66f5;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #7287fd;
}

QPushButton:pressed {
    background-color: #04a5e5;
}

QPushButton:disabled {
    background-color: #ccd0da;
    color: #9ca0b0;
}

QPushButton#secondary {
    background-color: #ccd0da;
    color: #4c4f69;
}

QPushButton#secondary:hover {
    background-color: #bcc0cc;
}

QPushButton#icon {
    background-color: transparent;
    padding: 5px 10px;
    font-size: 18px;
}

QPushButton#icon:hover {
    background-color: #ccd0da;
}

QCheckBox {
    spacing: 8px;
    color: #4c4f69;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #ccd0da;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #1e66f5;
    border-color: #1e66f5;
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
    background-color: #e6e9ef;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #ccd0da;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #bcc0cc;
}

QLabel#title {
    font-size: 24px;
    font-weight: bold;
    color: #1e66f5;
}

QLabel#subtitle {
    color: #9ca0b0;
    font-size: 12px;
}

QFrame#resultCard {
    background-color: #ffffff;
    border: 1px solid #ccd0da;
    border-radius: 10px;
    padding: 15px;
}

QFrame#resultCard[selected="true"] {
    border: 2px solid #40a02b;
}

QTableWidget {
    background-color: #ffffff;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    gridline-color: #ccd0da;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #1e66f5;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #ccd0da;
    color: #4c4f69;
    padding: 8px;
    border: none;
    font-weight: bold;
}

QTabWidget::pane {
    border: 1px solid #ccd0da;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #e6e9ef;
    color: #4c4f69;
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #1e66f5;
    color: #ffffff;
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
# Диалог просмотра Markdown
# =====================

MARKDOWN_VIEWER_STYLE = """
QDialog {
    background-color: #1e1e2e;
}

QTextBrowser {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 20px;
    font-size: 14px;
    line-height: 1.6;
}

QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 10px 30px;
    font-weight: bold;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #b4befe;
}

QLabel#dialogTitle {
    font-size: 20px;
    font-weight: bold;
    color: #89b4fa;
}
"""

MARKDOWN_HTML_STYLE = """
<style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.7;
        color: #cdd6f4;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #89b4fa;
        margin-top: 1.2em;
        margin-bottom: 0.6em;
        font-weight: 600;
    }
    h1 { font-size: 1.8em; border-bottom: 2px solid #45475a; padding-bottom: 0.3em; }
    h2 { font-size: 1.5em; border-bottom: 1px solid #45475a; padding-bottom: 0.3em; }
    h3 { font-size: 1.3em; }
    h4 { font-size: 1.1em; }
    p { margin: 0.8em 0; }
    code {
        background-color: #45475a;
        color: #a6e3a1;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 0.9em;
    }
    pre {
        background-color: #1e1e2e;
        border: 1px solid #45475a;
        border-radius: 6px;
        padding: 12px;
        overflow-x: auto;
        margin: 1em 0;
    }
    pre code {
        background-color: transparent;
        padding: 0;
        color: #cdd6f4;
    }
    blockquote {
        border-left: 4px solid #89b4fa;
        margin: 1em 0;
        padding: 0.5em 1em;
        background-color: #1e1e2e;
        color: #a6adc8;
    }
    ul, ol {
        margin: 0.8em 0;
        padding-left: 2em;
    }
    li { margin: 0.4em 0; }
    a { color: #89b4fa; text-decoration: none; }
    a:hover { text-decoration: underline; }
    hr {
        border: none;
        border-top: 1px solid #45475a;
        margin: 1.5em 0;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
    }
    th, td {
        border: 1px solid #45475a;
        padding: 8px 12px;
        text-align: left;
    }
    th {
        background-color: #45475a;
        color: #89b4fa;
    }
    strong { color: #f9e2af; }
    em { color: #cba6f7; }
</style>
"""


class MarkdownViewerDialog(QDialog):
    """Диалог для просмотра форматированного Markdown."""
    
    def __init__(self, title: str, markdown_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Просмотр ответа")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        self.setStyleSheet(MARKDOWN_VIEWER_STYLE)
        
        self._setup_ui(title, markdown_text)
    
    def _setup_ui(self, title: str, markdown_text: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel(f"📄 {title}")
        title_label.setObjectName("dialogTitle")
        layout.addWidget(title_label)
        
        # Конвертируем markdown в HTML
        md = markdown.Markdown(extensions=['fenced_code', 'tables', 'nl2br'])
        html_content = md.convert(markdown_text)
        full_html = f"{MARKDOWN_HTML_STYLE}<body>{html_content}</body>"
        
        # Браузер для отображения HTML
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setHtml(full_html)
        layout.addWidget(self.text_browser, 1)
        
        # Кнопка закрытия
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)


# =====================
# Диалог настроек
# =====================

class SettingsDialog(QDialog):
    """Диалог настроек приложения."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Настройки")
        self.setMinimumSize(800, 600)
        self.resize(900, 650)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Вкладки
        self.tabs = QTabWidget()
        
        # Вкладка "Общие"
        general_tab = self._create_general_tab()
        self.tabs.addTab(general_tab, "🎨 Общие")
        
        # Вкладка "Модели"
        models_tab = self._create_models_tab()
        self.tabs.addTab(models_tab, "🧠 Модели")
        
        layout.addWidget(self.tabs)
        
        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_general_tab(self) -> QWidget:
        """Создание вкладки общих настроек."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Тема
        theme_group = QGroupBox("🎨 Тема оформления")
        theme_layout = QHBoxLayout(theme_group)
        
        theme_label = QLabel("Тема:")
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("🌙 Тёмная", "dark")
        self.theme_combo.addItem("☀️ Светлая", "light")
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        layout.addWidget(theme_group)
        
        # Таймаут
        timeout_group = QGroupBox("⏱️ Сеть")
        timeout_layout = QHBoxLayout(timeout_group)
        
        timeout_label = QLabel("Таймаут запроса (сек):")
        timeout_layout.addWidget(timeout_label)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(30)
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        
        layout.addWidget(timeout_group)
        layout.addStretch()
        
        return widget
    
    def _create_models_tab(self) -> QWidget:
        """Создание вкладки управления моделями."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Таблица моделей
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(5)
        self.models_table.setHorizontalHeaderLabels(["Активна", "Название", "API URL", "Model ID", ""])
        self.models_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.models_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.models_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.models_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.models_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.models_table.setColumnWidth(0, 70)
        self.models_table.setColumnWidth(4, 80)
        layout.addWidget(self.models_table)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Добавить модель")
        add_btn.clicked.connect(self._add_model_row)
        btn_layout.addWidget(add_btn)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def _load_data(self):
        """Загрузка данных настроек."""
        settings = db.get_all_settings()
        
        # Тема
        index = self.theme_combo.findData(settings.theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        # Таймаут
        self.timeout_spin.setValue(settings.request_timeout)
        
        # Модели
        self._load_models()
    
    def _load_models(self):
        """Загрузка списка моделей в таблицу."""
        models = db.get_all_models()
        self.models_table.setRowCount(len(models))
        
        for row, model in enumerate(models):
            # Чекбокс активности
            active_checkbox = QCheckBox()
            active_checkbox.setChecked(model.is_active)
            active_widget = QWidget()
            active_layout = QHBoxLayout(active_widget)
            active_layout.addWidget(active_checkbox)
            active_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            active_layout.setContentsMargins(0, 0, 0, 0)
            self.models_table.setCellWidget(row, 0, active_widget)
            
            # Название
            name_item = QTableWidgetItem(model.name)
            name_item.setData(Qt.ItemDataRole.UserRole, model.id)
            self.models_table.setItem(row, 1, name_item)
            
            # API URL
            self.models_table.setItem(row, 2, QTableWidgetItem(model.api_url))
            
            # Model ID
            self.models_table.setItem(row, 3, QTableWidgetItem(model.api_id))
            
            # Кнопка удаления
            delete_btn = QPushButton("🗑️")
            delete_btn.setObjectName("secondary")
            delete_btn.setFixedWidth(60)
            delete_btn.clicked.connect(lambda checked, r=row: self._delete_model_row(r))
            self.models_table.setCellWidget(row, 4, delete_btn)
    
    def _add_model_row(self):
        """Добавить новую строку модели."""
        row = self.models_table.rowCount()
        self.models_table.insertRow(row)
        
        # Чекбокс активности
        active_checkbox = QCheckBox()
        active_checkbox.setChecked(True)
        active_widget = QWidget()
        active_layout = QHBoxLayout(active_widget)
        active_layout.addWidget(active_checkbox)
        active_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        active_layout.setContentsMargins(0, 0, 0, 0)
        self.models_table.setCellWidget(row, 0, active_widget)
        
        # Пустые ячейки
        name_item = QTableWidgetItem("")
        name_item.setData(Qt.ItemDataRole.UserRole, None)  # Новая модель
        self.models_table.setItem(row, 1, name_item)
        self.models_table.setItem(row, 2, QTableWidgetItem("https://openrouter.ai/api/v1/chat/completions"))
        self.models_table.setItem(row, 3, QTableWidgetItem(""))
        
        # Кнопка удаления
        delete_btn = QPushButton("🗑️")
        delete_btn.setObjectName("secondary")
        delete_btn.setFixedWidth(60)
        delete_btn.clicked.connect(lambda checked, r=row: self._delete_model_row(r))
        self.models_table.setCellWidget(row, 4, delete_btn)
    
    def _delete_model_row(self, row: int):
        """Удалить строку модели."""
        name_item = self.models_table.item(row, 1)
        if name_item:
            model_id = name_item.data(Qt.ItemDataRole.UserRole)
            if model_id:
                reply = QMessageBox.question(
                    self, "Подтверждение",
                    "Удалить эту модель? Это действие нельзя отменить.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    db.delete_model(model_id)
        self.models_table.removeRow(row)
    
    def _save_settings(self):
        """Сохранить настройки."""
        # Сохраняем общие настройки
        settings = Settings(
            theme=self.theme_combo.currentData(),
            request_timeout=self.timeout_spin.value()
        )
        db.save_settings(settings)
        
        # Сохраняем модели
        for row in range(self.models_table.rowCount()):
            name_item = self.models_table.item(row, 1)
            api_url_item = self.models_table.item(row, 2)
            api_id_item = self.models_table.item(row, 3)
            
            if not name_item or not name_item.text().strip():
                continue
            
            # Получаем чекбокс активности
            active_widget = self.models_table.cellWidget(row, 0)
            is_active = False
            if active_widget:
                checkbox = active_widget.findChild(QCheckBox)
                if checkbox:
                    is_active = checkbox.isChecked()
            
            model_id = name_item.data(Qt.ItemDataRole.UserRole)
            model = Model(
                id=model_id,
                name=name_item.text().strip(),
                api_url=api_url_item.text().strip() if api_url_item else "",
                api_id=api_id_item.text().strip() if api_id_item else "",
                is_active=is_active
            )
            
            if model_id:
                db.update_model(model)
            else:
                db.create_model(model)
        
        self.settings_changed.emit()
        self.accept()


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
        
        # Кнопка открытия в markdown
        self.open_btn = QPushButton("📖 Открыть")
        self.open_btn.setObjectName("secondary")
        self.open_btn.setFixedWidth(100)
        self.open_btn.clicked.connect(self._on_open_clicked)
        header.addWidget(self.open_btn)
        
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
        self.response_text.setMinimumHeight(400)
        layout.addWidget(self.response_text)
        
        # Обновляем стиль в зависимости от выбора
        self._update_style()
    
    def _on_open_clicked(self):
        """Открыть ответ в диалоге с форматированным markdown."""
        title = self.result.model_name or f"Модель #{self.result.model_id}"
        dialog = MarkdownViewerDialog(title, self.result.response_text, self)
        dialog.exec()
    
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
        self.current_theme: str = "dark"
        
        self._setup_window()
        self._setup_ui()
        self._load_data()
        self._apply_theme()
    
    def _setup_window(self):
        """Настройка окна."""
        self.setWindowTitle("ChatList - Сравнение LLM моделей")
        self.setMinimumSize(1200, 800)
    
    def _apply_theme(self):
        """Применить тему."""
        settings = db.get_all_settings()
        self.current_theme = settings.theme
        if self.current_theme == "light":
            self.setStyleSheet(LIGHT_STYLE)
        else:
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
        
        # Кнопка переключения темы
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setObjectName("icon")
        self.theme_btn.setToolTip("Переключить тему")
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)
        
        # Кнопка настроек
        settings_btn = QPushButton("⚙️")
        settings_btn.setObjectName("icon")
        settings_btn.setToolTip("Настройки")
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)
        
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
        
        # Фильтры по дате
        date_layout = QHBoxLayout()
        
        date_label = QLabel("Дата:")
        date_layout.addWidget(date_label)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        self.date_from.dateChanged.connect(self._on_filter_changed)
        date_layout.addWidget(self.date_from)
        
        date_layout.addWidget(QLabel("—"))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        self.date_to.dateChanged.connect(self._on_filter_changed)
        date_layout.addWidget(self.date_to)
        
        self.date_filter_enabled = QCheckBox("Фильтр")
        self.date_filter_enabled.stateChanged.connect(self._on_filter_changed)
        date_layout.addWidget(self.date_filter_enabled)
        
        prompt_layout.addLayout(date_layout)
        
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
        
        # Контейнер для чекбоксов моделей в скролле
        models_scroll = QScrollArea()
        models_scroll.setWidgetResizable(True)
        models_scroll.setMaximumHeight(200)
        
        models_widget = QWidget()
        self.models_container = QVBoxLayout(models_widget)
        models_scroll.setWidget(models_widget)
        models_layout.addWidget(models_scroll)
        
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
        
        # Кнопка настройки моделей
        settings_models_btn = QPushButton("⚙️ Настроить модели")
        settings_models_btn.setObjectName("secondary")
        settings_models_btn.clicked.connect(self._open_settings)
        models_layout.addWidget(settings_models_btn)
        
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
        
        # Кнопки экспорта
        export_md_btn = QPushButton("📄 Экспорт MD")
        export_md_btn.setObjectName("secondary")
        export_md_btn.clicked.connect(self._export_markdown)
        layout.addWidget(export_md_btn)
        
        export_json_btn = QPushButton("📋 Экспорт JSON")
        export_json_btn.setObjectName("secondary")
        export_json_btn.clicked.connect(self._export_json)
        layout.addWidget(export_json_btn)
        
        # Кнопка сохранения избранных
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
    
    def _load_history(self, search: str = "", date_from: str = "", date_to: str = ""):
        """Загрузка истории промптов."""
        self.history_combo.blockSignals(True)
        self.history_combo.clear()
        self.history_combo.addItem("-- Новый промпт --", None)
        
        prompts = db.get_all_prompts(search=search, date_from=date_from, date_to=date_to)
        for prompt in prompts:
            # Обрезаем длинный текст
            display_text = prompt.text[:50] + "..." if len(prompt.text) > 50 else prompt.text
            display_text = display_text.replace("\n", " ")
            # Добавляем дату
            if prompt.created_at:
                try:
                    dt = datetime.fromisoformat(str(prompt.created_at).replace(" ", "T"))
                    display_text = f"[{dt.strftime('%d.%m')}] {display_text}"
                except:
                    pass
            self.history_combo.addItem(display_text, prompt.id)
        
        self.history_combo.blockSignals(False)
    
    def _on_filter_changed(self):
        """Обработчик изменения фильтров."""
        self._update_history_filter()
    
    def _update_history_filter(self):
        """Обновить историю с учётом фильтров."""
        search = self.search_input.text()
        date_from = ""
        date_to = ""
        
        if self.date_filter_enabled.isChecked():
            date_from = self.date_from.date().toString("yyyy-MM-dd")
            date_to = self.date_to.date().toString("yyyy-MM-dd")
        
        self._load_history(search=search, date_from=date_from, date_to=date_to)
    
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
            self.prompt_input.clear()
            self._clear_results()
    
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
    
    def _toggle_theme(self):
        """Переключить тему."""
        if self.current_theme == "dark":
            self.current_theme = "light"
            self.setStyleSheet(LIGHT_STYLE)
            self.theme_btn.setText("☀️")
        else:
            self.current_theme = "dark"
            self.setStyleSheet(DARK_STYLE)
            self.theme_btn.setText("🌙")
        
        # Сохраняем в настройки
        db.set_setting("theme", self.current_theme)
    
    def _open_settings(self):
        """Открыть диалог настроек."""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()
    
    def _on_settings_changed(self):
        """Обработчик изменения настроек."""
        self._load_models()
        self._apply_theme()
        # Обновляем иконку темы
        if self.current_theme == "light":
            self.theme_btn.setText("☀️")
        else:
            self.theme_btn.setText("🌙")
    
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
        self._update_history_filter()
    
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
        self._update_history_filter()
    
    def _export_markdown(self):
        """Экспорт результатов в Markdown."""
        if not self.result_cards:
            QMessageBox.information(self, "Информация", "Нет результатов для экспорта")
            return
        
        # Получаем текущий промпт
        prompt_text = self.prompt_input.toPlainText().strip()
        
        # Формируем Markdown
        md_content = f"# Сравнение ответов LLM\n\n"
        md_content += f"**Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        md_content += f"## Промпт\n\n```\n{prompt_text}\n```\n\n"
        md_content += f"## Ответы моделей\n\n"
        
        for card in self.result_cards:
            model_name = card.result.model_name or f"Модель #{card.result.model_id}"
            selected = "⭐ " if card.result.is_selected else ""
            md_content += f"### {selected}{model_name}\n\n"
            md_content += f"{card.result.response_text}\n\n"
            md_content += "---\n\n"
        
        # Сохраняем файл
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить Markdown", 
            f"chatlist_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            "Markdown Files (*.md)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            QMessageBox.information(self, "Успех", f"Файл сохранён:\n{file_path}")
    
    def _export_json(self):
        """Экспорт результатов в JSON."""
        if not self.result_cards:
            QMessageBox.information(self, "Информация", "Нет результатов для экспорта")
            return
        
        # Получаем текущий промпт
        prompt_text = self.prompt_input.toPlainText().strip()
        
        # Формируем JSON
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt_text,
            "results": []
        }
        
        for card in self.result_cards:
            export_data["results"].append({
                "model_name": card.result.model_name or f"Model #{card.result.model_id}",
                "model_id": card.result.model_id,
                "response": card.result.response_text,
                "is_selected": card.result.is_selected
            })
        
        # Сохраняем файл
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить JSON",
            f"chatlist_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Успех", f"Файл сохранён:\n{file_path}")
    
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
