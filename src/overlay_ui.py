"""
Overlay UI module for Blink.

Manages the PyQt6 GUI overlay for displaying AI responses.
"""

import pyperclip
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt, pyqtSignal


class OverlayUI(QWidget):
    """
    A frameless GUI overlay that displays streaming AI responses.

    Appears at the mouse cursor position and provides copy/close functionality.
    """

    reset_signal = pyqtSignal()
    show_signal = pyqtSignal()
    append_signal = pyqtSignal(str)

    def __init__(self) -> None:
        """
        Initializes the OverlayUI.
        """
        super().__init__()
        self.full_text = ""
        self.reset_signal.connect(self.reset)
        self.show_signal.connect(self.show)
        self.append_signal.connect(self.append_chunk)
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

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)

        button_layout = QHBoxLayout()
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_and_close)
        button_layout.addWidget(self.copy_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def position_at_cursor(self) -> None:
        """
        Positions the overlay at the current mouse cursor location.
        """
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x(), cursor_pos.y())

    def reset(self) -> None:
        """
        Resets the overlay for a new response.
        """
        self.full_text = ""
        self.text_display.clear()

    def append_chunk(self, chunk: str) -> None:
        """
        Appends a chunk of text to the display and accumulates the full text.

        Args:
            chunk (str): The text chunk to append.
        """
        self.full_text += chunk
        self.text_display.insertPlainText(chunk)
        # Scroll to the bottom to show latest content
        scrollbar = self.text_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def copy_and_close(self) -> None:
        """
        Copies the full response text to clipboard and closes the overlay.
        """
        pyperclip.copy(self.full_text)
        self.close()

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
