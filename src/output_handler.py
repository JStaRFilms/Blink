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

    This class accumulates streaming tokens and types them in timed chunks
    to allow complete words and phrases to form before typing.
    """

    def __init__(self) -> None:
        """
        Initializes the DirectStreamHandler with a keyboard controller and buffer.
        """
        self.keyboard = Controller()
        self.buffer = ""
        self.timer: threading.Timer | None = None
        self.lock = threading.Lock()
        self.last_type_time = time.time()

    def stream_token(self, token: str) -> None:
        """
        Accumulates tokens and schedules typing after a delay.

        Args:
            token (str): The token to add to the buffer.
        """
        with self.lock:
            self.buffer += token

            # Cancel any existing timer
            if self.timer and self.timer.is_alive():
                self.timer.cancel()

            # Schedule typing after a delay to allow more tokens to accumulate
            self.timer = threading.Timer(0.8, self._type_buffer)
            self.timer.start()

    def _type_buffer(self) -> None:
        """
        Types the accumulated buffer content and clears it.
        """
        with self.lock:
            if self.buffer:
                self.keyboard.type(self.buffer)
                self.buffer = ""
                self.last_type_time = time.time()

    def finalize(self) -> None:
        """
        Forces typing of any remaining buffered content.
        Should be called when streaming is complete.
        """
        with self.lock:
            if self.timer and self.timer.is_alive():
                self.timer.cancel()
            self._type_buffer()
