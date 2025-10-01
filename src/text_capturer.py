"""
Text capture module for Blink.

Handles capturing selected text using the clipboard method.
"""

import time
import pyperclip
from pynput.keyboard import Key, Controller


class TextCapturer:
    """
    Captures selected text by simulating Ctrl+C and reading from clipboard.

    This implementation uses the "clipboard hack" method for MUS.
    """

    def __init__(self) -> None:
        """
        Initializes the TextCapturer.
        """
        self.keyboard = Controller()

    def capture_selected_text(self) -> str:
        """
        Captures the currently selected text.

        Simulates Ctrl+C to copy selected text to clipboard, then retrieves it.
        Restores the original clipboard content afterward.

        Returns:
            str: The captured text, or empty string if no text was selected.
        """
        # Save original clipboard content
        original_clipboard = pyperclip.paste()

        # Simulate Ctrl+C
        with self.keyboard.pressed(Key.ctrl):
            self.keyboard.press('c')
            self.keyboard.release('c')

        # Small delay to allow the copy operation to complete
        time.sleep(0.1)

        # Get the captured text
        captured_text = pyperclip.paste()

        # Restore original clipboard content
        pyperclip.copy(original_clipboard)

        # If captured text is the same as original, no selection was made
        if captured_text == original_clipboard:
            return ""

        return captured_text
