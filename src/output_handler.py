"""
Output handler module for Blink.

Provides different methods for outputting AI responses, including direct text streaming.
"""

import threading
import queue
import pyautogui
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

    Uses a thread-safe queue to decouple LLM streaming from keyboard typing,
    and pyautogui.write() with interval for reliable character-by-character typing.
    """

    def __init__(self) -> None:
        """
        Initializes the DirectStreamHandler with a queue for thread-safe communication.
        """
        self.token_queue = queue.Queue()
        self.consumer_thread = None
        self.is_streaming = False

    def stream_token(self, token: str) -> None:
        """
        Puts the token into the queue for the consumer thread to process.

        Args:
            token (str): The token to queue for typing.
        """
        if not token:
            return

        self.token_queue.put(token)

    def start_streaming(self) -> None:
        """
        Starts the consumer thread that processes tokens from the queue.
        """
        if self.consumer_thread and self.consumer_thread.is_alive():
            return  # Already running

        self.is_streaming = True
        self.consumer_thread = threading.Thread(target=self._consume_tokens, daemon=True)
        self.consumer_thread.start()

    def stop_streaming(self) -> None:
        """
        Stops the streaming by sending a sentinel value and waiting for completion.
        """
        if not self.is_streaming:
            return

        # Send sentinel to stop the consumer
        self.token_queue.put(None)
        self.is_streaming = False

        # Wait for consumer to finish processing remaining tokens
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=2.0)

        # Clear any remaining tokens in the queue
        self._clear_queue()

    def _consume_tokens(self) -> None:
        """
        Consumer thread that processes tokens from the queue using pyautogui.
        """
        while self.is_streaming:
            try:
                # Get token with timeout to allow for clean shutdown
                token = self.token_queue.get(timeout=1.0)

                if token is None:  # Sentinel value
                    break

                # Use pyautogui.write with interval for reliable character-by-character typing
                # interval=0.01 (10ms) provides smooth typing without overwhelming target apps
                pyautogui.write(token, interval=0.01)

            except queue.Empty:
                continue  # Timeout, check if still streaming

    def _clear_queue(self) -> None:
        """
        Clears any remaining tokens from the queue during shutdown.
        """
        while not self.token_queue.empty():
            try:
                self.token_queue.get_nowait()
            except queue.Empty:
                break

    def finalize(self) -> None:
        """
        Legacy method for backward compatibility - calls stop_streaming.
        """
        self.stop_streaming()
