"""
System tray module for Blink.

Manages the system tray icon and menu for application control.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject
from typing import Optional
import os


class SystemTrayManager(QObject):
    """
    Manages the system tray icon and associated menu.

    Provides access to settings and quit functionality.
    """

    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, app: QApplication) -> None:
        """
        Initializes the SystemTrayManager.

        Args:
            app (QApplication): The main Qt application instance.
        """
        super().__init__()
        self.app = app
        self.tray_icon = QSystemTrayIcon(self.app)

        # Try to load icon from assets
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Fallback to default icon
            self.tray_icon.setIcon(self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

        self.tray_icon.setToolTip("Blink AI Assistant")

        # Create menu
        self.menu = QMenu()
        self.setup_menu()

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()

    def setup_menu(self) -> None:
        """
        Sets up the context menu for the tray icon.
        """
        # Settings action
        settings_action = QAction("Settings", self.app)
        settings_action.triggered.connect(lambda: self.settings_requested.emit())
        self.menu.addAction(settings_action)

        # Separator
        self.menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", self.app)
        quit_action.triggered.connect(lambda: self.quit_requested.emit())
        self.menu.addAction(quit_action)

    def show_message(self, title: str, message: str, icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information) -> None:
        """
        Shows a notification message from the tray icon.

        Args:
            title (str): Message title.
            message (str): Message content.
            icon: Message icon type.
        """
        self.tray_icon.showMessage(title, message, icon)

    def hide(self) -> None:
        """
        Hides the tray icon.
        """
        self.tray_icon.hide()
