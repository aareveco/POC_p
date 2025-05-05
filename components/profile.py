from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

class ProfileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profile Information")
        self.setFixedSize(250, 150)
        layout = QVBoxLayout(self)
        # Mock data
        layout.addWidget(QLabel("<b>Username:</b> johndoe"))
        layout.addWidget(QLabel("<b>Email:</b> johndoe@example.com"))
        layout.addWidget(QLabel("<b>Role:</b> Admin"))
        layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

def create_profile_button(parent, on_click):
    btn = QPushButton(parent)
    try:
        user_icon = QIcon("user.svg")
        if not user_icon.isNull():
            btn.setIcon(user_icon)
        else:
            btn.setIcon(QIcon.fromTheme('user-identity') or QIcon())
    except Exception:
        btn.setIcon(QIcon.fromTheme('user-identity') or QIcon())
    btn.setIconSize(QSize(28, 28))
    btn.setFixedSize(36, 36)
    btn.setStyleSheet('''
        QPushButton { background: transparent; border: none; }
        QPushButton:hover { background: #e0e0e0; }
    ''')
    btn.clicked.connect(on_click)
    return btn 