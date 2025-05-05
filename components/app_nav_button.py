from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QIcon

class AppNavButton(QWidget):
    launchRequested = Signal(str)
    deleteRequested = Signal(str)

    def __init__(self, app_name, icon=None, delete_callback=None, select_callback=None, launch_callback=None, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.delete_callback = delete_callback
        self.select_callback = select_callback
        self.launch_callback = launch_callback
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.label = QLabel()
        if icon and isinstance(icon, QIcon):
            self.label.setPixmap(icon.pixmap(18, 18))
            self.label.setText(f' {app_name}')
        else:
            self.label.setText(app_name)
        self.label.setStyleSheet('font-size: 13px; padding: 6px;')
        layout.addWidget(self.label)
        self.delete_btn = QPushButton('✕')
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setStyleSheet('''
            QPushButton { background: transparent; border: none; color: #e74c3c; }
            QPushButton:hover { background: #2c3e50; }
        ''')
        self.delete_btn.clicked.connect(self.on_delete)
        layout.addWidget(self.delete_btn)
        self.setLayout(layout)
        self.setAttribute(Qt.WA_Hover)
        self.installEventFilter(self)
    def on_delete(self):
        if self.delete_callback:
            self.delete_callback(self.app_name)
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonDblClick:
            if self.launch_callback:
                self.launch_callback(self.app_name)
            return True
        if event.type() == QEvent.MouseButtonPress:
            if self.select_callback:
                self.select_callback(self.app_name)
        return super().eventFilter(obj, event) 