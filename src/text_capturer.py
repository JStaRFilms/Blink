"""
Text capture module for Blink.

Handles capturing selected text using Windows UI Automation API for non-destructive capture,
with clipboard fallback for compatibility.
"""

import uiautomation as auto
from typing import Optional, Tuple


class TextCapturer:
    """
    Captures selected text using Windows UI Automation API for non-destructive capture.

    Uses UI Automation as primary method, with clipboard fallback for maximum compatibility.
    """

    def __init__(self) -> None:
        """
        Initializes the TextCapturer.
        """
        # Initialize keyboard controller for fallback method
        from pynput.keyboard import Controller
        self.keyboard = Controller()

    def capture_selected_text(self) -> str:
        """
        Captures the currently selected text using Windows UI Automation.

        Returns:
            str: The captured text, or empty string if no text was selected.
        """
        text, _ = self.capture_selected_text_with_rect()
        return text

    def get_clipboard_content(self) -> str:
        """
        Gets the current content of the system clipboard.

        Returns:
            str: The clipboard content, or empty string if clipboard is empty or contains non-text data.
        """
        try:
            import pyperclip
            content = pyperclip.paste()
            return content if content else ""
        except Exception:
            # If pyperclip fails or clipboard contains non-text data
            return ""

    def capture_selected_text_with_rect(self) -> Tuple[str, Optional['QRect']]:
        """
        Captures the currently selected text using Windows UI Automation API.

        This method directly accesses the selected text without modifying the clipboard.
        Falls back to clipboard method if UI Automation fails for compatibility.

        Returns:
            Tuple[str, Optional[QRect]]: The captured text and None for rectangle.
        """
        # Try UI Automation first
        try:
            # First try the focused element
            focused_element = auto.GetFocusedElement()
            selected_text = self._get_selected_text_from_element(focused_element)
            if selected_text:
                return selected_text, None

            # If focused element doesn't have selection, try to find any text element with selection
            # Get the root element (desktop)
            root = auto.GetRootElement()
            # Find all elements that support text patterns
            text_elements = root.FindAll(auto.TreeScope_Subtree, auto.Condition(auto.PatternId.TextPattern))
            for elem in text_elements:
                selected_text = self._get_selected_text_from_element(elem)
                if selected_text:
                    return selected_text, None

        except Exception:
            # UI Automation failed, fall back to clipboard method
            pass

        # Fallback to clipboard method for compatibility
        return self._capture_with_clipboard()

    def _get_selected_text_from_element(self, element) -> str:
        """
        Gets selected text from a UI Automation element if it has a text selection.

        Args:
            element: UI Automation element

        Returns:
            str: Selected text or empty string
        """
        try:
            if element.GetPattern(auto.PatternId.TextPattern):
                text_pattern = element.GetPattern(auto.PatternId.TextPattern)
                text_range_array = text_pattern.GetSelection()
                if text_range_array:
                    selected_text = text_range_array[0].GetText(-1)
                    if selected_text.strip():
                        return selected_text
        except Exception:
            pass
        return ""

    def _capture_with_clipboard(self) -> Tuple[str, Optional['QRect']]:
        """
        Fallback method using clipboard for text capture.

        Returns:
            Tuple[str, Optional[QRect]]: The captured text and None for rectangle.
        """
        # Import here to avoid circular import issues
        import pyperclip
        from pynput.keyboard import Key
        import time

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
            return "", None

        return captured_text, None
