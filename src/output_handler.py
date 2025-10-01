"""
Output handler module for Blink.

Provides different methods for outputting AI responses, including direct text streaming.
"""

import threading
import time
from pynput.keyboard import Controller
from typing import Protocol


class OutputHandler(Protocol):
    """
    Protocol for output handlers.
    """

    def stream_token(self, token: str) -> None:
        """
        Streams a token to the output destination.

        Args:
            token (str): The token to stream.
        """
        ...


class DirectStreamHandler:
    """
    Handles direct text streaming by simulating keyboard input.

    This class accumulates streaming tokens and types them at natural break points
    (sentence endings, line breaks, or when buffer gets large enough) to avoid
    garbled output from partial words and tokens.
    """

    def __init__(self) -> None:
        """
        Initializes the DirectStreamHandler with a keyboard controller and buffer.
        """
        self.keyboard = Controller()
        self.buffer = ""
        self.lock = threading.Lock()

    def stream_token(self, token: str) -> None:
        """
        Accumulates tokens and types them at natural break points.

        Args:
            token (str): The token to add to the buffer.
        """
        with self.lock:
            self.buffer += token

            # Check if we should type the buffer now
            if self._should_type_buffer():
                self._type_buffer()

    def _should_type_buffer(self) -> bool:
        """
        Determines if the buffer should be typed based on content analysis.

        Returns:
            bool: True if buffer should be typed now.
        """
        if not self.buffer:
            return False

        # Type if buffer contains sentence endings
        if any(char in self.buffer for char in '.!?\n'):
            return True

        # Type if buffer gets too large (to prevent memory issues)
        if len(self.buffer) > 200:
            return True

        return False

    def _type_buffer(self) -> None:
        """
        Types the accumulated buffer content and clears it.
        """
        if self.buffer:
            self.keyboard.type(self.buffer)
            self.buffer = ""

    def finalize(self) -> None:
        """
        Forces typing of any remaining buffered content.
        Should be called when streaming is complete.
        """
        with self.lock:
            self._type_buffer()
