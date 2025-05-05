from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame
from PySide6.QtCore import Qt

class AppMenu(QWidget):
    def __init__(self, add_app_callback, app_nav_container, app_nav_layout, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.add_app_button = QPushButton("+ Add App")
        self.add_app_button.setStyleSheet('''
            QPushButton {
                background-color: #23272e;
                color: #67c1f5;
                border: none;
                font-size: 13px;
                padding: 8px 0;
                border-radius: 0 8px 8px 0;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        ''')
        self.add_app_button.setFixedHeight(36)
        self.add_app_button.clicked.connect(add_app_callback)
        layout.addWidget(self.add_app_button)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet('color: #23272e; background: #23272e; margin: 8px 0;')
        layout.addWidget(sep)
        layout.addWidget(app_nav_container)
        layout.addStretch() 