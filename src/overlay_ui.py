"""
Overlay UI module for Blink.

Manages the PyQt6 GUI overlay for displaying AI responses with status indicators.
"""

import pyperclip
import keyboard
from typing import Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                              QPushButton, QApplication, QLabel)
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt, pyqtSignal, QRect


class OverlayUI(QWidget):
    """
    A frameless GUI overlay that displays streaming AI responses.

    Appears at the mouse cursor position and provides copy/close functionality.
    Now includes status indicators for error feedback.
    """

    reset_signal = pyqtSignal()
    show_signal = pyqtSignal()
    append_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str, str)  # (status_type, message)

    def __init__(self) -> None:
        """
        Initializes the OverlayUI.
        """
        super().__init__()
        self.full_text = ""
        self.reset_signal.connect(self.reset)
        self.show_signal.connect(self.show_overlay)
        self.append_signal.connect(self.append_chunk)
        self.status_signal.connect(self.update_status)
        self.setup_ui()
        self.position_at_cursor()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components.
        """
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("Blink AI Response")
        self.resize(400, 300)

        layout = QVBoxLayout()

        # Status label (hidden by default)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            "padding: 5px; border-radius: 3px; font-weight: bold;"
        )
        self.status_label.hide()
        layout.addWidget(self.status_label)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)

        button_layout = QHBoxLayout()
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_and_close)
        button_layout.addWidget(self.copy_button)

        self.insert_button = QPushButton("Insert")
        self.insert_button.clicked.connect(self.insert_and_close)
        button_layout.addWidget(self.insert_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def update_status(self, status_type: str, message: str) -> None:
        """
        Updates the status indicator.

        Args:
            status_type (str): Type of status ('streaming', 'complete', 'error', 'warning')
            message (str): Status message to display
        """
        if status_type == "streaming":
            self.status_label.setText(f"⏳ {message}")
            self.status_label.setStyleSheet(
                "background-color: #3498db; color: white; "
                "padding: 5px; border-radius: 3px; font-weight: bold;"
            )
            self.status_label.show()
        elif status_type == "complete":
            self.status_label.setText(f"✓ {message}")
            self.status_label.setStyleSheet(
                "background-color: #2ecc71; color: white; "
                "padding: 5px; border-radius: 3px; font-weight: bold;"
            )
            self.status_label.show()
        elif status_type == "error":
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet(
                "background-color: #e74c3c; color: white; "
                "padding: 5px; border-radius: 3px; font-weight: bold;"
            )
            self.status_label.show()
        elif status_type == "warning":
            self.status_label.setText(f"⚠ {message}")
            self.status_label.setStyleSheet(
                "background-color: #f39c12; color: white; "
                "padding: 5px; border-radius: 3px; font-weight: bold;"
            )
            self.status_label.show()
        else:
            self.status_label.hide()

    def position_at_cursor(self) -> None:
        """
        Positions the overlay at the current mouse cursor location.
        """
        cursor_pos = QCursor.pos()
        x, y = cursor_pos.x(), cursor_pos.y()

        screen = QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()

            if x + self.width() > screen_rect.right():
                x = screen_rect.right() - self.width()
            if x < screen_rect.left():
                x = screen_rect.left()

            if y + self.height() > screen_rect.bottom():
                y = screen_rect.bottom() - self.height()
            if y < screen_rect.top():
                y = screen_rect.top()

        self.move(x, y)

    def position_near_selection(self, selection_rect: Optional['QRect'] = None) -> None:
        """
        Positions the overlay near the selected text area.

        Args:
            selection_rect: Rectangle of the selected text area, if available.
        """
        if selection_rect:
            screen = QApplication.primaryScreen()
            if screen:
                screen_rect = screen.availableGeometry()

                preferred_x = selection_rect.x() + selection_rect.width() // 2 - self.width() // 2
                preferred_y = selection_rect.y() + selection_rect.height() + 10

                if preferred_y + self.height() > screen_rect.bottom():
                    preferred_y = selection_rect.y() - self.height() - 10

                if preferred_x < screen_rect.left():
                    preferred_x = screen_rect.left()
                elif preferred_x + self.width() > screen_rect.right():
                    preferred_x = screen_rect.right() - self.width()

                if preferred_y < screen_rect.top():
                    preferred_y = screen_rect.top()
                elif preferred_y + self.height() > screen_rect.bottom():
                    preferred_y = screen_rect.bottom() - self.height()

                self.move(preferred_x, preferred_y)
            else:
                x = selection_rect.x() + selection_rect.width() // 2 - self.width() // 2
                y = selection_rect.y() + selection_rect.height() + 10
                self.move(x, y)
        else:
            self.position_at_cursor()

    def show_overlay(self) -> None:
        """
        Shows the overlay and ensures it has focus for key events.
        """
        self.show()
        self.setFocus()
        self.activateWindow()

    def reset(self) -> None:
        """
        Resets the overlay for a new response.
        """
        self.full_text = ""
        self.text_display.clear()
        self.status_label.hide()

    def append_chunk(self, chunk: str) -> None:
        """
        Appends a chunk of text to the display and accumulates the full text.

        Args:
            chunk (str): The text chunk to append.
        """
        self.full_text += chunk
        self.text_display.insertPlainText(chunk)
        scrollbar = self.text_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def copy_and_close(self) -> None:
        """
        Copies the full response text to clipboard and closes the overlay.
        """
        pyperclip.copy(self.full_text)
        self.close()

    def insert_and_close(self) -> None:
        """
        Inserts the full response text at the cursor position and closes the overlay.
        """
        self.close()

        import time
        time.sleep(0.1)

        original_clipboard = pyperclip.paste()
        pyperclip.copy(self.full_text)
        keyboard.press_and_release('ctrl+v')

        time.sleep(0.1)
        pyperclip.copy(original_clipboard)

    def keyPressEvent(self, event) -> None:
        """
        Handles key press events, specifically for closing with Escape.

        Args:
            event: The key event.
        """
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)