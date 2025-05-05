from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class RemoteMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("<b>Remote PC Menu (Mock)</b>")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        layout.addStretch() 