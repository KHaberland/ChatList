"""
Тестовая программа для просмотра и редактирования базы данных SQLite.
Поддерживает пагинацию и CRUD операции.
"""

import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QFileDialog,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSpinBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QSplitter,
    QFrame,
)
from PyQt6.QtCore import Qt


DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

QLabel {
    color: #cdd6f4;
    font-size: 14px;
}

QListWidget {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px;
    color: #cdd6f4;
    font-size: 14px;
}

QListWidget::item {
    padding: 6px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}

QListWidget::item:hover {
    background-color: #45475a;
}

QTableWidget {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    color: #cdd6f4;
    gridline-color: #45475a;
    font-size: 13px;
}

QTableWidget::item {
    padding: 5px;
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

QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 14px;
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

QPushButton#deleteBtn {
    background-color: #f38ba8;
}

QPushButton#deleteBtn:hover {
    background-color: #eba0ac;
}

QPushButton#createBtn {
    background-color: #a6e3a1;
}

QPushButton#createBtn:hover {
    background-color: #94e2d5;
}

QPushButton#updateBtn {
    background-color: #fab387;
}

QPushButton#updateBtn:hover {
    background-color: #f9e2af;
}

QSpinBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 5px;
    color: #cdd6f4;
    font-size: 14px;
}

QLineEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px;
    color: #cdd6f4;
    font-size: 14px;
}

QLineEdit:focus {
    border: 1px solid #89b4fa;
}

QDialog {
    background-color: #1e1e2e;
}

QFrame#separator {
    background-color: #45475a;
}

QSplitter::handle {
    background-color: #45475a;
}
"""


class RecordDialog(QDialog):
    """Диалог для создания/редактирования записи."""
    
    def __init__(self, columns, values=None, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.values = values or {}
        self.inputs = {}
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса диалога."""
        title = "Редактировать запись" if self.values else "Создать запись"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        for col in self.columns:
            line_edit = QLineEdit()
            if col in self.values:
                line_edit.setText(str(self.values[col]) if self.values[col] is not None else "")
            self.inputs[col] = line_edit
            form_layout.addRow(f"{col}:", line_edit)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_values(self):
        """Получить значения из полей ввода."""
        return {col: self.inputs[col].text() for col in self.columns}


class DatabaseViewerWindow(QMainWindow):
    """Главное окно для просмотра базы данных SQLite."""
    
    def __init__(self):
        super().__init__()
        self.db_path = None
        self.current_table = None
        self.columns = []
        self.page = 0
        self.page_size = 20
        self.total_rows = 0
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle("SQLite Database Viewer")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Верхняя панель с кнопкой открытия файла
        top_panel = QHBoxLayout()
        
        self.open_file_btn = QPushButton("📂 Открыть файл БД")
        self.open_file_btn.clicked.connect(self.open_database)
        top_panel.addWidget(self.open_file_btn)
        
        self.file_label = QLabel("Файл не выбран")
        self.file_label.setStyleSheet("color: #6c7086; font-style: italic;")
        top_panel.addWidget(self.file_label, 1)
        
        main_layout.addLayout(top_panel)
        
        # Разделитель
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Сплиттер для списка таблиц и данных
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель - список таблиц
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)
        
        tables_label = QLabel("📋 Таблицы:")
        tables_label.setStyleSheet("font-weight: bold; color: #89b4fa;")
        left_layout.addWidget(tables_label)
        
        self.tables_list = QListWidget()
        self.tables_list.setMinimumWidth(200)
        self.tables_list.itemDoubleClicked.connect(self.on_table_double_click)
        left_layout.addWidget(self.tables_list)
        
        self.open_table_btn = QPushButton("Открыть")
        self.open_table_btn.clicked.connect(self.open_selected_table)
        self.open_table_btn.setEnabled(False)
        left_layout.addWidget(self.open_table_btn)
        
        self.tables_list.itemSelectionChanged.connect(self.on_table_selection_changed)
        
        splitter.addWidget(left_panel)
        
        # Правая панель - данные таблицы
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        # Заголовок таблицы
        self.table_title = QLabel("Выберите таблицу")
        self.table_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #f9e2af;")
        right_layout.addWidget(self.table_title)
        
        # CRUD кнопки
        crud_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("➕ Создать")
        self.create_btn.setObjectName("createBtn")
        self.create_btn.clicked.connect(self.create_record)
        self.create_btn.setEnabled(False)
        crud_layout.addWidget(self.create_btn)
        
        self.update_btn = QPushButton("✏️ Изменить")
        self.update_btn.setObjectName("updateBtn")
        self.update_btn.clicked.connect(self.update_record)
        self.update_btn.setEnabled(False)
        crud_layout.addWidget(self.update_btn)
        
        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.clicked.connect(self.delete_record)
        self.delete_btn.setEnabled(False)
        crud_layout.addWidget(self.delete_btn)
        
        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setEnabled(False)
        crud_layout.addWidget(self.refresh_btn)
        
        crud_layout.addStretch()
        right_layout.addLayout(crud_layout)
        
        # Таблица данных
        self.data_table = QTableWidget()
        self.data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.data_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.data_table.itemSelectionChanged.connect(self.on_row_selection_changed)
        right_layout.addWidget(self.data_table)
        
        # Пагинация
        pagination_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("◀ Назад")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        pagination_layout.addWidget(self.prev_btn)
        
        self.page_label = QLabel("Страница: 0 / 0")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pagination_layout.addWidget(self.page_label)
        
        self.next_btn = QPushButton("Вперёд ▶")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        pagination_layout.addWidget(self.next_btn)
        
        pagination_layout.addSpacing(30)
        
        pagination_layout.addWidget(QLabel("Записей на странице:"))
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(5, 100)
        self.page_size_spin.setValue(20)
        self.page_size_spin.valueChanged.connect(self.on_page_size_changed)
        pagination_layout.addWidget(self.page_size_spin)
        
        pagination_layout.addStretch()
        
        self.total_label = QLabel("Всего записей: 0")
        self.total_label.setStyleSheet("color: #a6adc8;")
        pagination_layout.addWidget(self.total_label)
        
        right_layout.addLayout(pagination_layout)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 750])
        
        main_layout.addWidget(splitter)
    
    def open_database(self):
        """Открыть файл базы данных SQLite."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл базы данных SQLite",
            "",
            "SQLite Database (*.db *.sqlite *.sqlite3);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        self.db_path = file_path
        self.file_label.setText(file_path)
        self.file_label.setStyleSheet("color: #a6e3a1;")
        
        self.load_tables()
        self.clear_data_view()
    
    def load_tables(self):
        """Загрузить список таблиц из базы данных."""
        self.tables_list.clear()
        
        if not self.db_path:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = cursor.fetchall()
            
            for table in tables:
                self.tables_list.addItem(table[0])
            
            conn.close()
            
        except sqlite3.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось открыть базу данных:\n{str(e)}"
            )
    
    def on_table_selection_changed(self):
        """Обработчик изменения выбора таблицы."""
        self.open_table_btn.setEnabled(bool(self.tables_list.currentItem()))
    
    def on_table_double_click(self, item):
        """Обработчик двойного клика по таблице."""
        self.open_selected_table()
    
    def open_selected_table(self):
        """Открыть выбранную таблицу."""
        item = self.tables_list.currentItem()
        if not item:
            return
        
        self.current_table = item.text()
        self.page = 0
        self.table_title.setText(f"📊 Таблица: {self.current_table}")
        
        self.load_columns()
        self.load_data()
        
        self.create_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
    
    def load_columns(self):
        """Загрузить информацию о колонках таблицы."""
        if not self.db_path or not self.current_table:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns_info = cursor.fetchall()
            self.columns = [col[1] for col in columns_info]
            
            conn.close()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки колонок:\n{str(e)}")
    
    def load_data(self):
        """Загрузить данные таблицы с пагинацией."""
        if not self.db_path or not self.current_table:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем общее количество записей
            cursor.execute(f"SELECT COUNT(*) FROM {self.current_table}")
            self.total_rows = cursor.fetchone()[0]
            
            # Получаем данные с пагинацией
            offset = self.page * self.page_size
            cursor.execute(
                f"SELECT * FROM {self.current_table} LIMIT ? OFFSET ?",
                (self.page_size, offset)
            )
            rows = cursor.fetchall()
            
            conn.close()
            
            # Заполняем таблицу
            self.data_table.clear()
            self.data_table.setColumnCount(len(self.columns))
            self.data_table.setRowCount(len(rows))
            self.data_table.setHorizontalHeaderLabels(self.columns)
            
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.data_table.setItem(row_idx, col_idx, item)
            
            # Обновляем пагинацию
            total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
            self.page_label.setText(f"Страница: {self.page + 1} / {total_pages}")
            self.total_label.setText(f"Всего записей: {self.total_rows}")
            
            self.prev_btn.setEnabled(self.page > 0)
            self.next_btn.setEnabled((self.page + 1) * self.page_size < self.total_rows)
            
            self.update_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных:\n{str(e)}")
    
    def clear_data_view(self):
        """Очистить представление данных."""
        self.current_table = None
        self.columns = []
        self.data_table.clear()
        self.data_table.setRowCount(0)
        self.data_table.setColumnCount(0)
        self.table_title.setText("Выберите таблицу")
        self.page_label.setText("Страница: 0 / 0")
        self.total_label.setText("Всего записей: 0")
        self.create_btn.setEnabled(False)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
    
    def on_row_selection_changed(self):
        """Обработчик изменения выбора строки."""
        has_selection = bool(self.data_table.selectedItems())
        self.update_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def prev_page(self):
        """Перейти на предыдущую страницу."""
        if self.page > 0:
            self.page -= 1
            self.load_data()
    
    def next_page(self):
        """Перейти на следующую страницу."""
        if (self.page + 1) * self.page_size < self.total_rows:
            self.page += 1
            self.load_data()
    
    def on_page_size_changed(self, value):
        """Обработчик изменения размера страницы."""
        self.page_size = value
        self.page = 0
        if self.current_table:
            self.load_data()
    
    def refresh_data(self):
        """Обновить данные таблицы."""
        if self.current_table:
            self.load_data()
    
    def get_selected_row_data(self):
        """Получить данные выбранной строки."""
        selected_rows = self.data_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        
        row_idx = selected_rows[0].row()
        data = {}
        for col_idx, col_name in enumerate(self.columns):
            item = self.data_table.item(row_idx, col_idx)
            data[col_name] = item.text() if item else ""
        return data
    
    def create_record(self):
        """Создать новую запись."""
        if not self.current_table or not self.columns:
            return
        
        dialog = RecordDialog(self.columns, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()
            
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cols = ", ".join(self.columns)
                placeholders = ", ".join(["?" for _ in self.columns])
                vals = [values[col] if values[col] else None for col in self.columns]
                
                cursor.execute(
                    f"INSERT INTO {self.current_table} ({cols}) VALUES ({placeholders})",
                    vals
                )
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Успех", "Запись успешно создана!")
                self.load_data()
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка создания записи:\n{str(e)}")
    
    def update_record(self):
        """Обновить выбранную запись."""
        row_data = self.get_selected_row_data()
        if not row_data:
            return
        
        dialog = RecordDialog(self.columns, row_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_values = dialog.get_values()
            
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Используем первую колонку как идентификатор (обычно id)
                id_col = self.columns[0]
                id_val = row_data[id_col]
                
                set_clause = ", ".join([f"{col} = ?" for col in self.columns])
                vals = [new_values[col] if new_values[col] else None for col in self.columns]
                vals.append(id_val)
                
                cursor.execute(
                    f"UPDATE {self.current_table} SET {set_clause} WHERE {id_col} = ?",
                    vals
                )
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Успех", "Запись успешно обновлена!")
                self.load_data()
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка обновления записи:\n{str(e)}")
    
    def delete_record(self):
        """Удалить выбранную запись."""
        row_data = self.get_selected_row_data()
        if not row_data:
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить эту запись?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Используем первую колонку как идентификатор
                id_col = self.columns[0]
                id_val = row_data[id_col]
                
                cursor.execute(
                    f"DELETE FROM {self.current_table} WHERE {id_col} = ?",
                    (id_val,)
                )
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Успех", "Запись успешно удалена!")
                self.load_data()
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка удаления записи:\n{str(e)}")


def main():
    """Запуск приложения."""
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    
    window = DatabaseViewerWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
