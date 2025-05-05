from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton
from PySide6.QtCore import Qt, Signal
from components.profile import create_profile_button, ProfileDialog
from components.app_menu import AppMenu
from components.remote_menu import RemoteMenu

class Sidebar(QWidget):
    add_app_requested = Signal()

    def __init__(self, app_nav_container, app_nav_layout, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(0)

        # Profile button
        profile_row = QHBoxLayout()
        profile_row.addStretch()
        self.profile_btn = create_profile_button(self, self.show_profile_dialog)
        profile_row.addWidget(self.profile_btn)
        layout.addLayout(profile_row)

        # Toggle buttons
        toggle_row = QHBoxLayout()
        self.menu1_btn = self._make_toggle_btn("My PC")
        self.menu2_btn = self._make_toggle_btn("Remote PC")
        self.menu1_btn.setChecked(True)
        self.menu1_btn.clicked.connect(lambda: self.switch_menu(0))
        self.menu2_btn.clicked.connect(lambda: self.switch_menu(1))
        toggle_row.addWidget(self.menu1_btn)
        toggle_row.addWidget(self.menu2_btn)
        layout.addLayout(toggle_row)

        # Stacked menus
        self.stacked = QStackedWidget()
        self.app_menu = AppMenu(self.add_app_requested.emit, app_nav_container, app_nav_layout)
        self.remote_menu = RemoteMenu()
        self.stacked.addWidget(self.app_menu)
        self.stacked.addWidget(self.remote_menu)
        layout.addWidget(self.stacked)
        layout.addStretch()

    def _make_toggle_btn(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setStyleSheet('''
            QPushButton { background: #23272e; color: #67c1f5; border: none; font-size: 13px; padding: 8px 0; border-radius: 8px; }
            QPushButton:checked { background: #67c1f5; color: #23272e; }
            QPushButton:hover { background: #2c3e50; }
        ''')
        btn.setFixedHeight(32)
        return btn

    def switch_menu(self, idx):
        self.stacked.setCurrentIndex(idx)
        self.menu1_btn.setChecked(idx == 0)
        self.menu2_btn.setChecked(idx == 1)

    def show_profile_dialog(self):
        dlg = ProfileDialog(self)
        dlg.exec() 