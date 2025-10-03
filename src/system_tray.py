"""
System tray module for Blink.

Manages the system tray icon and menu for application control.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle, QSpinBox, QWidgetAction, QLabel, QFileDialog
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject
from typing import Optional
import os
from .utils import get_asset_path


class SystemTrayManager(QObject):
    """
    Manages the system tray icon and associated menu.

    Provides access to settings and quit functionality.
    """

    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    restart_requested = pyqtSignal()

    def __init__(self, app: QApplication, config_manager=None) -> None:
        """
        Initializes the SystemTrayManager.

        Args:
            app (QApplication): The main Qt application instance.
            config_manager: Configuration manager for memory settings.
        """
        super().__init__()
        self.app = app
        self.config_manager = config_manager
        self.tray_icon = QSystemTrayIcon(self.app)

        # Try to load icon from assets
        icon_path = get_asset_path("icon.ico")
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

        # Memory submenu
        if self.config_manager:
            self.setup_memory_menu()

        # Separator
        self.menu.addSeparator()

        # Restart action
        restart_action = QAction("Restart", self.app)
        restart_action.triggered.connect(lambda: self.restart_requested.emit())
        self.menu.addAction(restart_action)

        # Quit action
        quit_action = QAction("Quit", self.app)
        quit_action.triggered.connect(lambda: self.quit_requested.emit())
        self.menu.addAction(quit_action)

    def setup_memory_menu(self) -> None:
        """
        Sets up the memory submenu.
        """
        # Memory submenu
        memory_menu = self.menu.addMenu("Memory")

        # Enable/Disable memory
        memory_enabled = self.config_manager.get("memory_enabled", True)
        enable_action = QAction("Enable Memory", self.app)
        enable_action.setCheckable(True)
        enable_action.setChecked(memory_enabled)
        enable_action.triggered.connect(self.toggle_memory)
        memory_menu.addAction(enable_action)

        memory_menu.addSeparator()

        # Max messages setting
        max_messages_label = QLabel("Max Messages:")
        max_messages_action = QWidgetAction(self.app)
        max_messages_action.setDefaultWidget(max_messages_label)
        memory_menu.addAction(max_messages_action)

        # Spin box for max messages
        current_max = self.config_manager.get("memory_max_messages", 50)
        spin_box = QSpinBox()
        spin_box.setRange(5, 200)  # Reasonable range
        spin_box.setValue(current_max)
        spin_box.setSuffix(" messages")
        spin_box.valueChanged.connect(self.update_max_messages)

        spin_action = QWidgetAction(self.app)
        spin_action.setDefaultWidget(spin_box)
        memory_menu.addAction(spin_action)

        memory_menu.addSeparator()

        # Clear history action
        clear_action = QAction("Clear History", self.app)
        clear_action.triggered.connect(self.clear_history)
        memory_menu.addAction(clear_action)

        # Export history action
        export_action = QAction("Export Conversation...", self.app)
        export_action.triggered.connect(self.export_history)
        memory_menu.addAction(export_action)

    def toggle_memory(self) -> None:
        """Toggles memory on/off."""
        if self.config_manager:
            current = self.config_manager.get("memory_enabled", True)
            self.config_manager.set("memory_enabled", not current)

    def update_max_messages(self, value: int) -> None:
        """Updates the maximum number of messages."""
        if self.config_manager:
            self.config_manager.set("memory_max_messages", value)
            # Update the history manager if it exists
            try:
                from .history_manager import get_conversation_history
                history = get_conversation_history(self.config_manager)
                history.update_maxlen()
            except ImportError:
                pass

    def clear_history(self) -> None:
        """Clears the conversation history."""
        try:
            from .history_manager import get_conversation_history
            history = get_conversation_history(self.config_manager)
            history.clear()
            self.show_message("Memory", "Conversation history cleared", QSystemTrayIcon.MessageIcon.Information)
        except ImportError:
            pass

    def export_history(self) -> None:
        """Exports the conversation history to a file."""
        try:
            from .history_manager import get_conversation_history
            history = get_conversation_history(self.config_manager)

            # Open file dialog for save location
            file_path, _ = QFileDialog.getSaveFileName(
                None,  # parent widget
                "Export Conversation",  # dialog title
                "conversation.txt",  # default filename
                "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)"  # file filters
            )

            if file_path:  # User didn't cancel
                success = history.export_history(file_path)
                if success:
                    self.show_message("Export", "Conversation exported successfully", QSystemTrayIcon.MessageIcon.Information)
                else:
                    self.show_message("Export", "Failed to export conversation", QSystemTrayIcon.MessageIcon.Warning)
        except ImportError:
            self.show_message("Export", "Export feature not available", QSystemTrayIcon.MessageIcon.Warning)
        except Exception as e:
            self.show_message("Export", f"Export failed: {str(e)}", QSystemTrayIcon.MessageIcon.Warning)

    def show_message(self, title: str, message: str, icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information) -> None:
        """
        Shows a notification message from the tray icon.

        Args:
            title (str): Message title.
            message (str): Message content.
            icon: Message icon type.
        """
        self.tray_icon.showMessage(title, message, icon)

    def show_notification(self, title: str, message: str, icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information) -> None:
        """
        Shows a notification message from the tray icon, respecting user settings.

        Non-error notifications are only shown if enable_notifications is True.
        Error notifications are always shown.

        Args:
            title (str): Message title.
            message (str): Message content.
            icon: Message icon type.
        """
        # Always show error notifications
        if icon == QSystemTrayIcon.MessageIcon.Critical or icon == QSystemTrayIcon.MessageIcon.Warning:
            self.show_message(title, message, icon)
            return

        # For non-error notifications, check user setting
        if self.config_manager and self.config_manager.get("enable_notifications", True):
            self.show_message(title, message, icon)

    def hide(self) -> None:
        """
        Hides the tray icon.
        """
        self.tray_icon.hide()
