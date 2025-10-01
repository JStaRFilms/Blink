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

    This class types tokens immediately for real-time response.
    """

    def __init__(self) -> None:
        """
        Initializes the DirectStreamHandler with a keyboard controller.
        """
        self.keyboard = Controller()

    def stream_token(self, token: str) -> None:
        """
        Types the token immediately using the keyboard controller.

        Args:
            token (str): The token to type.
        """
        if token:
            self.keyboard.type(token)

    def finalize(self) -> None:
        """
        No-op for immediate typing implementation.
        """
        pass
