import sys
import os
import shutil
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QPushButton, QLabel, QDialog, QComboBox, QLineEdit, 
                              QFormLayout, QMessageBox, QHBoxLayout, QFrame,
                              QScrollArea, QSizePolicy, QGridLayout, QFileDialog,
                              QStackedWidget)
from PySide6.QtCore import Qt, QPoint, QSize, Signal, QEvent
from PySide6.QtGui import QColor, QPalette, QShortcut, QKeySequence, QIcon, QAction, QPixmap
from app_manager import AppManager
import threading
from pynput import keyboard
import objc
from AppKit import NSApplication, NSApp, NSRunningApplication, NSApplicationActivateIgnoringOtherApps
try:
    from Quartz import AXIsProcessTrusted
except ImportError:
    AXIsProcessTrusted = None
from components.sidebar import Sidebar
from components.app_nav_button import AppNavButton

class AppWindow(QFrame):
    closeRequested = Signal(str)
    launchRequested = Signal(str)
    
    def __init__(self, app_name: str, app_type: str, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.app_type = app_type
        self.initUI()
        
    def initUI(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin: 2px;
                padding: 5px;
            }
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 3px;
                border-radius: 3px;
                min-height: 20px;
                max-height: 20px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton#closeButton {
                background-color: #e74c3c;
                min-width: 16px;
                max-width: 16px;
                min-height: 16px;
                max-height: 16px;
                border-radius: 8px;
                font-size: 12px;
            }
            QPushButton#closeButton:hover {
                background-color: #c0392b;
            }
            QLabel {
                font-size: 11px;
            }
        """)
        
        # Set size policy to make the widget expandable
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Header with title and close button
        header = QHBoxLayout()
        header.setSpacing(3)
        title = QLabel(self.app_name)
        title.setStyleSheet("font-weight: bold;")
        close_btn = QPushButton("×")
        close_btn.setObjectName("closeButton")
        close_btn.clicked.connect(self.close_app)
        header.addWidget(title)
        header.addWidget(close_btn)
        
        # Content area
        content = QLabel(f"Type: {self.app_type}")
        content.setStyleSheet("color: #666;")
        
        # Add launch button
        launch_btn = QPushButton("Launch")
        launch_btn.setFixedHeight(20)
        launch_btn.clicked.connect(self.launch_app)
        
        layout.addLayout(header)
        layout.addWidget(content)
        layout.addWidget(launch_btn)
        self.setLayout(layout)
        
    def close_app(self):
        self.closeRequested.emit(self.app_name)
        
    def launch_app(self):
        self.launchRequested.emit(self.app_name)

class AppContainer(QWidget):
    def __init__(self, app_manager, parent=None):
        super().__init__(parent)
        self.app_manager = app_manager
        self.app_windows = {}
        self.initUI()
        
    def initUI(self):
        # Use QGridLayout for responsive app windows
        self.layout = QGridLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
    def add_app_window(self, app_name: str, app_type: str):
        if app_name not in self.app_windows:
            app_window = AppWindow(app_name, app_type, self)
            app_window.closeRequested.connect(self.remove_app)
            app_window.launchRequested.connect(self.launch_app)
            self.app_windows[app_name] = app_window
            
            # Calculate position in grid
            count = len(self.app_windows) - 1
            row = count // 2  # 2 columns
            col = count % 2
            
            self.layout.addWidget(app_window, row, col)
            
    def remove_app(self, app_name: str):
        if app_name in self.app_windows:
            app_window = self.app_windows[app_name]
            self.layout.removeWidget(app_window)
            app_window.deleteLater()
            del self.app_windows[app_name]
            self.app_manager.remove_app(app_name)
            
            # Rearrange remaining windows
            self.rearrange_windows()
            
    def rearrange_windows(self):
        # Remove all widgets from layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Add widgets back in order
        for i, (app_name, window) in enumerate(self.app_windows.items()):
            row = i // 2
            col = i % 2
            self.layout.addWidget(window, row, col)
            
    def launch_app(self, app_name: str):
        app_data = self.app_manager.apps.get(app_name)
        if not app_data:
            return
            
        try:
            if app_data['type'] == 'TeamViewer':
                teamviewer_path = self.find_teamviewer_path()
                if not teamviewer_path:
                    QMessageBox.warning(self, "Error", "TeamViewer is not installed or not found.")
                    return
                subprocess.Popen([teamviewer_path, '--id', app_data['config']['connection_id']])
            elif app_data['type'] == 'OBS Studio':
                obs_path = self.find_obs_path()
                if not obs_path:
                    QMessageBox.warning(self, "Error", "OBS Studio is not installed or not found.")
                    return
                self.app_manager.launch_obs(app_data['config'].get('stream_key', ''))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to launch {app_data['type']}: {str(e)}")
            
    def find_teamviewer_path(self):
        if sys.platform == 'darwin':  # macOS
            paths = [
                '/Applications/TeamViewer.app/Contents/MacOS/TeamViewer',
                os.path.expanduser('~/Applications/TeamViewer.app/Contents/MacOS/TeamViewer')
            ]
        elif sys.platform == 'win32':  # Windows
            paths = [
                'C:\\Program Files\\TeamViewer\\TeamViewer.exe',
                'C:\\Program Files (x86)\\TeamViewer\\TeamViewer.exe'
            ]
        else:  # Linux
            paths = [
                '/usr/bin/teamviewer',
                '/opt/teamviewer/teamviewer'
            ]
            
        for path in paths:
            if os.path.exists(path):
                return path
        return None
        
    def find_obs_path(self):
        if sys.platform == 'darwin':  # macOS
            paths = [
                '/Applications/OBS.app/Contents/MacOS/obs',
                os.path.expanduser('~/Applications/OBS.app/Contents/MacOS/obs')
            ]
        elif sys.platform == 'win32':  # Windows
            paths = [
                'C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe',
                'C:\\Program Files (x86)\\obs-studio\\bin\\32bit\\obs32.exe'
            ]
        else:  # Linux
            paths = [
                '/usr/bin/obs',
                '/usr/local/bin/obs'
            ]
            
        for path in paths:
            if os.path.exists(path):
                return path
        return None

class AddAppDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Application")
        layout = QFormLayout(self)
        self.app_type = QComboBox()
        self.app_type.addItems(["TeamViewer", "OBS Studio", "Image Editor"])
        layout.addRow("Application Type:", self.app_type)
        self.connection_id = QLineEdit()
        layout.addRow("Connection ID:", self.connection_id)
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow("", button_layout)
    def get_app_data(self):
        return {
            'type': self.app_type.currentText(),
            'connection_id': self.connection_id.text()
        }

class NavButton(QPushButton):
    def __init__(self, text, icon=None, parent=None):
        super().__init__(parent)
        self.setText(text)
        if icon:
            self.setIcon(icon)
        self.setCheckable(True)
        self.setStyleSheet('''
            QPushButton {
                background-color: transparent;
                color: #d6d6d6;
                border: none;
                text-align: left;
                padding: 8px 12px;
                font-size: 13px;
                border-radius: 4px;
            }
            QPushButton:checked, QPushButton:hover {
                background-color: #23272e;
                color: #fff;
            }
        ''')
        self.setMinimumHeight(32)
        self.setIconSize(QSize(18, 18))

class AppNavButton(QWidget):
    def __init__(self, app_name, icon, delete_callback, select_callback, launch_callback, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.delete_callback = delete_callback
        self.select_callback = select_callback
        self.launch_callback = launch_callback
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.button = NavButton(app_name, icon)
        self.button.clicked.connect(self.on_select)
        self.button.installEventFilter(self)
        layout.addWidget(self.button)
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon.fromTheme('edit-delete') or QIcon())
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setStyleSheet('''
            QPushButton { background: transparent; border: none; color: #e74c3c; }
            QPushButton:hover { background: #2c3e50; }
        ''')
        self.delete_btn.clicked.connect(self.on_delete)
        layout.addWidget(self.delete_btn)
        self.setLayout(layout)
    def on_delete(self):
        self.delete_callback(self.app_name)
    def on_select(self):
        self.select_callback(self.button, self.app_name)
    def setChecked(self, checked):
        self.button.setChecked(checked)
    def eventFilter(self, obj, event):
        if obj == self.button and event.type() == QEvent.MouseButtonDblClick:
            self.launch_callback(self.app_name)
            return True
        return super().eventFilter(obj, event)

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

class ImageEditorMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("<b>Image Editor Menu (Mock)</b>")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        layout.addStretch()

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_manager = AppManager()
        self.selected_nav_name = None
        self.nav_buttons = {}
        self._drag_pos = None
        self.initUI()
        self.setup_shortcuts()
        self.start_global_hotkey_listener()
        
    def initUI(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
        )
        # Sidebar as main window
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 10, 0, 0)
        sidebar_layout.setSpacing(0)

        # --- Profile icon row ---
        profile_row = QHBoxLayout()
        profile_row.addStretch()
        self.profile_btn = QPushButton()
        try:
            user_icon = QIcon("user.svg")
            if not user_icon.isNull():
                self.profile_btn.setIcon(user_icon)
            else:
                self.profile_btn.setIcon(QIcon.fromTheme('user-identity') or QIcon())
        except Exception:
            self.profile_btn.setIcon(QIcon.fromTheme('user-identity') or QIcon())
        self.profile_btn.setIconSize(QSize(28, 28))
        self.profile_btn.setFixedSize(36, 36)
        self.profile_btn.setStyleSheet('''
            QPushButton { background: transparent; border: none; }
            QPushButton:hover { background: #e0e0e0; }
        ''')
        self.profile_btn.clicked.connect(self.show_profile_dialog)
        profile_row.addWidget(self.profile_btn)
        sidebar_layout.addLayout(profile_row)

        # --- Menu toggle buttons ---
        toggle_row = QHBoxLayout()
        self.menu1_btn = QPushButton("My PC")
        self.menu2_btn = QPushButton("Remote PC")
        for btn in (self.menu1_btn, self.menu2_btn):
            btn.setCheckable(True)
            btn.setStyleSheet('''
                QPushButton { background: #23272e; color: #67c1f5; border: none; font-size: 13px; padding: 8px 0; border-radius: 8px; }
                QPushButton:checked { background: #67c1f5; color: #23272e; }
                QPushButton:hover { background: #2c3e50; }
            ''')
            btn.setFixedHeight(32)
        self.menu1_btn.setChecked(True)
        self.menu1_btn.clicked.connect(lambda: self.switch_menu(0))
        self.menu2_btn.clicked.connect(lambda: self.switch_menu(1))
        toggle_row.addWidget(self.menu1_btn)
        toggle_row.addWidget(self.menu2_btn)
        sidebar_layout.addLayout(toggle_row)

        # --- Stacked menus ---
        self.stacked = QStackedWidget()
        # Menu 1: App management
        menu1 = QWidget()
        menu1_layout = QVBoxLayout(menu1)
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
        self.add_app_button.clicked.connect(self.add_app)
        menu1_layout.addWidget(self.add_app_button)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet('color: #23272e; background: #23272e; margin: 8px 0;')
        menu1_layout.addWidget(sep)
        self.app_nav_container = QWidget()
        self.app_nav_layout = QVBoxLayout(self.app_nav_container)
        self.app_nav_layout.setContentsMargins(0, 0, 0, 0)
        self.app_nav_layout.setSpacing(0)
        menu1_layout.addWidget(self.app_nav_container)
        menu1_layout.addStretch()
        self.stacked.addWidget(menu1)
        # Menu 2: Image editor menu (mock)
        self.stacked.addWidget(ImageEditorMenu())
        sidebar_layout.addWidget(self.stacked)
        sidebar_layout.addStretch()
        self.setCentralWidget(sidebar_widget)
        self.setGeometry(100, 100, 220, 600)
        self.refresh_navbar()

    def setup_shortcuts(self):
        # Minimize/Maximize shortcut (Cmd+Shift+Space)
        shortcut = QShortcut(QKeySequence('Meta+Shift+Space'), self)
        shortcut.activated.connect(self.toggle_minimize)
        
    def toggle_minimize(self):
        if self.isMinimized() or not self.isActiveWindow():
            self.showNormal()
            self.raise_()
            self.activateWindow()
        else:
            self.showMinimized()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

    def refresh_navbar(self):
        for i in reversed(range(self.app_nav_layout.count())):
            widget = self.app_nav_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.nav_buttons.clear()
        for app_name, app_data in self.app_manager.apps.items():
            icon = QIcon()  # Placeholder, can use real icons per app type
            btn = AppNavButton(
                app_name, icon,
                delete_callback=self.delete_app,
                select_callback=self.select_nav,
                launch_callback=self.launch_app
            )
            self.app_nav_layout.addWidget(btn)
            self.nav_buttons[app_name] = btn
        # Restore selection if possible
        if self.selected_nav_name in self.nav_buttons:
            self.nav_buttons[self.selected_nav_name].setChecked(True)
        else:
            self.selected_nav_name = None

    def select_nav(self, btn, app_name):
        # Uncheck previous selection
        if self.selected_nav_name and self.selected_nav_name in self.nav_buttons:
            self.nav_buttons[self.selected_nav_name].setChecked(False)
        btn.setChecked(True)
        self.selected_nav_name = app_name

    def delete_app(self, app_name):
        if app_name in self.app_manager.apps:
            self.app_manager.remove_app(app_name)
            self.refresh_navbar()

    def launch_app(self, app_name):
        app_data = self.app_manager.apps.get(app_name)
        if not app_data:
            return
        try:
            if app_data['type'] == 'TeamViewer':
                teamviewer_path = self.find_teamviewer_path()
                if not teamviewer_path:
                    QMessageBox.warning(self, "Error", "TeamViewer is not installed or not found.")
                    return
                subprocess.Popen([teamviewer_path, '--id', app_data['config']['connection_id']])
            elif app_data['type'] == 'OBS Studio':
                obs_path = self.find_obs_path()
                if not obs_path:
                    QMessageBox.warning(self, "Error", "OBS Studio is not installed or not found.")
                    return
                self.app_manager.launch_obs(app_data['config'].get('stream_key', ''))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to launch {app_data['type']}: {str(e)}")

    def find_teamviewer_path(self):
        if sys.platform == 'darwin':  # macOS
            paths = [
                '/Applications/TeamViewer.app/Contents/MacOS/TeamViewer',
                os.path.expanduser('~/Applications/TeamViewer.app/Contents/MacOS/TeamViewer')
            ]
        elif sys.platform == 'win32':  # Windows
            paths = [
                'C:\\Program Files\\TeamViewer\\TeamViewer.exe',
                'C:\\Program Files (x86)\\TeamViewer\\TeamViewer.exe'
            ]
        else:  # Linux
            paths = [
                '/usr/bin/teamviewer',
                '/opt/teamviewer/teamviewer'
            ]
        for path in paths:
            if os.path.exists(path):
                return path
        return None
        
    def find_obs_path(self):
        if sys.platform == 'darwin':  # macOS
            paths = [
                '/Applications/OBS.app/Contents/MacOS/obs',
                os.path.expanduser('~/Applications/OBS.app/Contents/MacOS/obs')
            ]
        elif sys.platform == 'win32':  # Windows
            paths = [
                'C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe',
                'C:\\Program Files (x86)\\obs-studio\\bin\\32bit\\obs32.exe'
            ]
        else:  # Linux
            paths = [
                '/usr/bin/obs',
                '/usr/local/bin/obs'
            ]
            
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def add_app(self):
        dialog = AddAppDialog(self)
        if dialog.exec():
            app_data = dialog.get_app_data()
            app_name = f"{app_data['type']}_{app_data['connection_id']}"
            print(f"Attempting to add app: {app_name}")
            if app_name not in self.app_manager.apps:
                # Placeholder icon
                icon = QIcon()
                def launch_app(name):
                    data = self.app_manager.apps.get(name)
                    if not data:
                        return
                    try:
                        if data['type'] == 'TeamViewer':
                            teamviewer_path = self.find_teamviewer_path()
                            if not teamviewer_path:
                                QMessageBox.warning(self, "Error", "TeamViewer is not installed or not found.")
                                return
                            subprocess.Popen([teamviewer_path, '--id', data['connection_id']])
                        elif data['type'] == 'OBS Studio':
                            obs_path = self.find_obs_path()
                            if not obs_path:
                                QMessageBox.warning(self, "Error", "OBS Studio is not installed or not found.")
                                return
                            # Add OBS launch logic here
                            QMessageBox.information(self, "OBS", "OBS Studio launch (mock)")
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to launch {data['type']}: {str(e)}")
                def delete_app(name):
                    if name in self.app_manager.apps:
                        app_btn.setParent(None)
                        self.app_manager.remove_app(name)
                        self.refresh_navbar()
                        print(f"Deleted app: {name}")
                def select_app(name):
                    print(f"Selected app: {name}")
                app_btn = AppNavButton(app_name, icon, delete_app, select_app, launch_app)
                # Remove any existing stretch at the end
                count = self.app_nav_layout.count()
                if count > 0 and self.app_nav_layout.itemAt(count-1).spacerItem():
                    self.app_nav_layout.takeAt(count-1)
                self.app_nav_layout.addWidget(app_btn)
                self.app_nav_layout.addStretch()
                self.app_nav_layout.update()
                self.app_nav_layout.repaint()
                print(f"Added app widget: {app_name}")
                self.app_manager.add_app(
                    app_name=app_name,
                    app_type=data['type'],
                    config={'connection_id': data['connection_id']}
                )
                QMessageBox.information(self, "Success", "Application added successfully!")
            else:
                print(f"App already exists: {app_name}")
                QMessageBox.warning(self, "Error", "App already exists!")

    def start_global_hotkey_listener(self):
        def on_press(key):
            try:
                if (
                    key == keyboard.Key.space and
                    self._hotkey_mods['cmd'] and
                    self._hotkey_mods['shift']
                ):
                    self.toggle_minimize()
            except Exception:
                pass
        def on_release(key):
            if key == keyboard.Key.cmd:
                self._hotkey_mods['cmd'] = False
            if key == keyboard.Key.shift:
                self._hotkey_mods['shift'] = False
        def on_mod(key, pressed):
            if key == keyboard.Key.cmd:
                self._hotkey_mods['cmd'] = pressed
            if key == keyboard.Key.shift:
                self._hotkey_mods['shift'] = pressed
        self._hotkey_mods = {'cmd': False, 'shift': False}
        def listener_thread():
            with keyboard.Listener(
                on_press=lambda key: (on_mod(key, True), on_press(key)),
                on_release=lambda key: (on_mod(key, False), on_release(key))
            ) as listener:
                listener.join()
        t = threading.Thread(target=listener_thread, daemon=True)
        t.start()

    def bring_to_front(self):
        # Use pyobjc to bring the app to the front
        app = NSRunningApplication.runningApplicationWithProcessIdentifier_(os.getpid())
        app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def show_profile_dialog(self):
        dlg = ProfileDialog(self)
        dlg.exec()

    def switch_menu(self, idx):
        self.stacked.setCurrentIndex(idx)
        self.menu1_btn.setChecked(idx == 0)
        self.menu2_btn.setChecked(idx == 1)

class SignInDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign In")
        self.setFixedSize(300, 180)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Sign in to your account</b>"))
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        layout.addWidget(self.user_input)
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pass_input)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        layout.addWidget(self.error_label)
        btn = QPushButton("Sign In")
        btn.clicked.connect(self.try_login)
        layout.addWidget(btn)
        self.success = False
    def try_login(self):
        if self.user_input.text() == "admin" and self.pass_input.text() == "admin":
            self.success = True
            self.accept()
        else:
            self.error_label.setText("Invalid username or password.")

def main():
    app = QApplication(sys.argv)
    # Show sign-in dialog first
    signin = SignInDialog()
    if not signin.exec():
        sys.exit(0)
    # If login successful, show main app
    main_window = QMainWindow()
    main_window.setWindowTitle("Overlay App")
    # App navigation container for Sidebar
    app_nav_container = QWidget()
    app_nav_layout = QVBoxLayout(app_nav_container)
    app_nav_layout.setContentsMargins(0, 0, 0, 0)
    app_nav_layout.setSpacing(0)
    sidebar = Sidebar(app_nav_container, app_nav_layout)

    # App management state
    apps = {}
    def handle_add_app():
        dialog = AddAppDialog(main_window)
        if dialog.exec():
            app_data = dialog.get_app_data()
            app_name = f"{app_data['type']}_{app_data['connection_id']}"
            print(f"Attempting to add app: {app_name}")
            if app_name not in apps:
                # Placeholder icon
                icon = QIcon()
                def launch_app(name):
                    data = apps.get(name)
                    if not data:
                        return
                    try:
                        if data['type'] == 'TeamViewer':
                            teamviewer_path = find_teamviewer_path()
                            if not teamviewer_path:
                                QMessageBox.warning(main_window, "Error", "TeamViewer is not installed or not found.")
                                return
                            subprocess.Popen([teamviewer_path, '--id', data['connection_id']])
                        elif data['type'] == 'OBS Studio':
                            obs_path = find_obs_path()
                            if not obs_path:
                                QMessageBox.warning(main_window, "Error", "OBS Studio is not installed or not found.")
                                return
                            # Add OBS launch logic here
                            QMessageBox.information(main_window, "OBS", "OBS Studio launch (mock)")
                    except Exception as e:
                        QMessageBox.warning(main_window, "Error", f"Failed to launch {data['type']}: {str(e)}")
                def delete_app(name):
                    if name in apps:
                        app_btn.setParent(None)
                        del apps[name]
                        app_nav_container.adjustSize()
                        app_nav_container.update()
                        app_nav_container.repaint()
                        print(f"Deleted app: {name}")
                def select_app(name):
                    print(f"Selected app: {name}")
                app_btn = AppNavButton(app_name, icon, delete_app, select_app, launch_app)
                # Remove any existing stretch at the end
                count = app_nav_layout.count()
                if count > 0 and app_nav_layout.itemAt(count-1).spacerItem():
                    app_nav_layout.takeAt(count-1)
                app_nav_layout.addWidget(app_btn)
                app_nav_layout.addStretch()
                app_nav_container.adjustSize()
                app_nav_container.update()
                app_nav_container.repaint()
                print(f"Added app widget: {app_name}")
                apps[app_name] = app_data
                QMessageBox.information(main_window, "Success", "Application added successfully!")
            else:
                print(f"App already exists: {app_name}")
                QMessageBox.warning(main_window, "Error", "App already exists!")
    sidebar.add_app_requested.connect(handle_add_app)

    def find_teamviewer_path():
        if sys.platform == 'darwin':  # macOS
            paths = [
                '/Applications/TeamViewer.app/Contents/MacOS/TeamViewer',
                os.path.expanduser('~/Applications/TeamViewer.app/Contents/MacOS/TeamViewer')
            ]
        elif sys.platform == 'win32':  # Windows
            paths = [
                'C:\\Program Files\\TeamViewer\\TeamViewer.exe',
                'C:\\Program Files (x86)\\TeamViewer\\TeamViewer.exe'
            ]
        else:  # Linux
            paths = [
                '/usr/bin/teamviewer',
                '/opt/teamviewer/teamviewer'
            ]
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def find_obs_path():
        if sys.platform == 'darwin':  # macOS
            paths = [
                '/Applications/OBS.app/Contents/MacOS/obs',
                os.path.expanduser('~/Applications/OBS.app/Contents/MacOS/obs')
            ]
        elif sys.platform == 'win32':  # Windows
            paths = [
                'C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe',
                'C:\\Program Files (x86)\\obs-studio\\bin\\32bit\\obs32.exe'
            ]
        else:  # Linux
            paths = [
                '/usr/bin/obs',
                '/usr/local/bin/obs'
            ]
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    main_window.setCentralWidget(sidebar)
    main_window.setGeometry(100, 100, 220, 600)
    main_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 