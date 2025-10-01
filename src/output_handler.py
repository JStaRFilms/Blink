"""
Output handler module for Blink.

Provides different methods for outputting AI responses, including direct text streaming
using a reliable clipboard-based approach.
"""

import threading
import queue
import time
import pyperclip
import pyautogui
from typing import Protocol, Optional


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
    Handles direct text streaming using clipboard-based paste operations.

    This approach is more reliable than character-by-character typing because:
    1. It uses the native paste mechanism that all Windows apps support
    2. It provides natural backpressure (can't paste faster than app can handle)
    3. It avoids input queue overflow and timing issues
    4. It's the industry-standard approach used by professional automation tools
    """

    def __init__(self) -> None:
        """
        Initializes the DirectStreamHandler with a queue for thread-safe communication.
        """
        self.token_queue = queue.Queue()
        self.consumer_thread = None
        self.is_streaming = False
        self.original_clipboard: Optional[str] = None
        
        # Tuning parameters
        self.buffer_size_limit = 80  # Max chars to buffer before pasting
        self.paste_delay = 0.05  # 50ms delay after each paste (adjust if needed)

    def stream_token(self, token: str) -> None:
        """
        Puts the token into the queue for the consumer thread to process.

        Args:
            token (str): The token to queue for typing. Pass None to signal completion.
        """
        self.token_queue.put(token)

    def start_streaming(self) -> None:
        """
        Starts the consumer thread that processes tokens from the queue.
        Uses non-daemon thread to prevent premature process exit.
        """
        if self.consumer_thread and self.consumer_thread.is_alive():
            return  # Already running

        # Save original clipboard content
        try:
            self.original_clipboard = pyperclip.paste()
        except Exception:
            self.original_clipboard = None

        self.is_streaming = True
        # Non-daemon thread prevents the main process from exiting while streaming
        self.consumer_thread = threading.Thread(target=self._consume_tokens, daemon=False)
        self.consumer_thread.start()

    def wait_for_completion(self) -> None:
        """
        Waits for the consumer thread to finish processing all tokens.
        Call this after the LLM stream completes and you've sent the None sentinel.
        """
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=10.0)  # Wait up to 10 seconds

        # Restore original clipboard content
        if self.original_clipboard is not None:
            try:
                pyperclip.copy(self.original_clipboard)
            except Exception:
                pass  # Fail silently if clipboard restoration fails

        self.is_streaming = False

    def stop_streaming(self) -> None:
        """
        DEPRECATED: Use stream_token(None) + wait_for_completion() instead.
        Kept for backward compatibility.
        """
        self.stream_token(None)  # Send sentinel
        self.wait_for_completion()

    def _consume_tokens(self) -> None:
        """
        Consumer thread that uses clipboard-based paste for reliable text insertion.
        
        Buffers tokens until reaching a word boundary or size limit, then pastes
        the accumulated text. This provides a good balance between streaming feel
        and reliability.
        """
        buffer = ""
        
        while True:  # Loop until we receive the sentinel (None)
            try:
                # Get token with timeout to allow for responsiveness
                token = self.token_queue.get(timeout=1.0)

                if token is None:  # Sentinel value - stream complete
                    # Paste any remaining buffer content
                    if buffer:
                        self._paste_text(buffer)
                    break

                # Add token to buffer
                buffer += token

                # Decide when to paste based on:
                # 1. Buffer size limit reached
                # 2. Word boundary detected (space, newline, punctuation)
                # 3. End of sentence/paragraph
                should_paste = False
                
                if len(buffer) >= self.buffer_size_limit:
                    should_paste = True
                elif token.endswith((' ', '\n', '\t', '.', ',', '!', '?', ';', ':')):
                    should_paste = True

                if should_paste:
                    self._paste_text(buffer)
                    buffer = ""

            except queue.Empty:
                # Queue empty, paste buffer if we have accumulated content
                if buffer:
                    self._paste_text(buffer)
                    buffer = ""
                continue
            except Exception as e:
                print(f"[Blink] Error in consumer thread: {e}")
                continue

    def _paste_text(self, text: str) -> None:
        """
        Pastes text using clipboard + Ctrl+V.

        Args:
            text (str): The text to paste.
        """
        if not text:
            return

        try:
            # Copy text to clipboard
            pyperclip.copy(text)
            
            # Small delay to ensure clipboard is updated
            time.sleep(0.01)
            
            # Simulate Ctrl+V
            pyautogui.hotkey('ctrl', 'v')
            
            # Delay to allow target application to process the paste
            # This provides natural backpressure
            time.sleep(self.paste_delay)
            
        except Exception as e:
            print(f"[Blink] Error pasting text: {e}")

    def finalize(self) -> None:
        """
        Legacy method for backward compatibility - calls stop_streaming.
        """
        self.stop_streaming()