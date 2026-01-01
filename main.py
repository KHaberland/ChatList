"""
Минимальное приложение на PyQt6 с графическим интерфейсом.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
)
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()

        self.click_count = 0  # Счётчик нажатий

        self.setWindowTitle("Моё приложение")
        self.setMinimumSize(400, 300)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Компоновка
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Метка
        self.label = QLabel("Привет, мир!")
        self.label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # Кнопка
        self.button = QPushButton("Нажми меня")
        self.button.setFixedSize(150, 40)
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)

    def on_button_click(self):
        """Обработчик нажатия кнопки."""
        self.click_count += 1
        self.label.setText(f"Минимальная программа на Python\nНажатий: {self.click_count}")


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

