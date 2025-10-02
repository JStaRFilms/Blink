"""
Output handler module for Blink.

Provides different methods for outputting AI responses, including direct text streaming
with comprehensive error handling and status tracking.
"""

import threading
import queue
import time
import pyperclip
import pyautogui
from typing import Protocol, Optional, Callable
from enum import Enum
from .error_logger import logger


class StreamStatus(Enum):
    """Enumeration of possible streaming states."""
    IDLE = "idle"
    STREAMING = "streaming"
    COMPLETE = "complete"
    ERROR = "error"
    TIMEOUT = "timeout"


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

    Features:
    - Clipboard-based paste for reliability
    - Error detection and recovery
    - Status tracking and logging
    - Timeout detection
    """

    def __init__(self, timeout: int = 120, on_error: Optional[Callable[[str, str], None]] = None) -> None:
        """
        Initializes the DirectStreamHandler with error handling.

        Args:
            timeout (int): Maximum seconds to wait for stream completion.
            on_error (Callable): Optional callback for error notifications (error_type, message).
        """
        self.token_queue = queue.Queue()
        self.consumer_thread = None
        self.is_streaming = False
        self.original_clipboard: Optional[str] = None
        self.timeout = timeout
        self.on_error = on_error
        
        # Status tracking
        self.status = StreamStatus.IDLE
        self.error_message: Optional[str] = None
        self.token_count = 0
        self.start_time: Optional[float] = None
        
        # Tuning parameters
        self.buffer_size_limit = 150
        self.paste_delay = 0.1

    def stream_token(self, token: str) -> None:
        """
        Puts the token into the queue for the consumer thread to process.

        Args:
            token (str): The token to queue for typing. Pass None to signal completion.
        """
        if token is not None:
            self.token_count += 1
        self.token_queue.put(token)

    def start_streaming(self) -> None:
        """
        Starts the consumer thread that processes tokens from the queue.
        """
        if self.consumer_thread and self.consumer_thread.is_alive():
            logger.warning("Streaming already in progress")
            return

        # Save original clipboard content
        try:
            self.original_clipboard = pyperclip.paste()
        except Exception as e:
            logger.warning(f"Could not save clipboard: {e}")
            self.original_clipboard = None

        # Reset state
        self.status = StreamStatus.STREAMING
        self.error_message = None
        self.token_count = 0
        self.start_time = time.time()
        self.is_streaming = True
        
        logger.info("Direct stream handler started")

        # Start consumer thread
        self.consumer_thread = threading.Thread(target=self._consume_tokens, daemon=False)
        self.consumer_thread.start()

    def wait_for_completion(self) -> StreamStatus:
        """
        Waits for the consumer thread to finish processing all tokens.
        
        Returns:
            StreamStatus: Final status of the stream.
        """
        if not self.consumer_thread:
            return StreamStatus.IDLE

        try:
            # Wait with timeout
            self.consumer_thread.join(timeout=self.timeout)
            
            if self.consumer_thread.is_alive():
                # Timeout occurred
                self.status = StreamStatus.TIMEOUT
                self.error_message = f"Stream timeout after {self.timeout}s"
                logger.streaming_timeout(self.timeout)
                
                if self.on_error:
                    self.on_error("timeout", self.error_message)
                
                # Force stop
                self.is_streaming = False
                self.consumer_thread.join(timeout=2.0)
            
            elif self.status == StreamStatus.STREAMING:
                # Completed successfully
                duration = time.time() - self.start_time if self.start_time else 0
                self.status = StreamStatus.COMPLETE
                logger.streaming_complete(self.token_count, duration)

        except Exception as e:
            self.status = StreamStatus.ERROR
            self.error_message = str(e)
            logger.streaming_error("wait_error", str(e))
            
            if self.on_error:
                self.on_error("wait_error", str(e))

        finally:
            # Restore original clipboard
            self._restore_clipboard()
            self.is_streaming = False

        return self.status

    def stop_streaming(self) -> None:
        """
        DEPRECATED: Use stream_token(None) + wait_for_completion() instead.
        """
        self.stream_token(None)
        self.wait_for_completion()

    def _consume_tokens(self) -> None:
        """
        Consumer thread that uses clipboard-based paste for reliable text insertion.
        """
        buffer = ""
        
        try:
            while True:
                try:
                    # Get token with timeout
                    token = self.token_queue.get(timeout=1.0)

                    if token is None:  # Sentinel - stream complete
                        if buffer:
                            self._paste_text(buffer)
                        break

                    # Add token to buffer
                    buffer += token

                    # Decide when to paste
                    should_paste = False
                    
                    if len(buffer) >= self.buffer_size_limit:
                        should_paste = True
                    elif token.endswith((' ', '\n', '\t', '.', ',', '!', '?', ';', ':')):
                        should_paste = True

                    if should_paste:
                        self._paste_text(buffer)
                        buffer = ""

                except queue.Empty:
                    # Queue empty, paste accumulated buffer
                    if buffer:
                        self._paste_text(buffer)
                        buffer = ""
                    continue

        except Exception as e:
            # Critical error in consumer thread
            self.status = StreamStatus.ERROR
            self.error_message = f"Consumer thread error: {e}"
            logger.streaming_error("consumer_error", str(e))
            
            if self.on_error:
                self.on_error("consumer_error", str(e))
            
            # Try to paste any remaining buffer
            if buffer:
                try:
                    self._paste_text(buffer)
                except Exception:
                    pass

    def _paste_text(self, text: str) -> None:
        """
        Pastes text using clipboard + Ctrl+V with error handling.

        Args:
            text (str): The text to paste.
        """
        if not text:
            return

        try:
            # Copy to clipboard
            pyperclip.copy(text)
            time.sleep(0.01)

            # Simulate Ctrl+V
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(self.paste_delay)

            # Explicitly release keys to prevent sticking
            pyautogui.keyUp('ctrl')
            pyautogui.keyUp('v')
            pyautogui.keyUp('c')
            
        except pyperclip.PyperclipException as e:
            error_msg = f"Clipboard error: {e}"
            logger.error(error_msg)
            self.status = StreamStatus.ERROR
            self.error_message = error_msg
            
            if self.on_error:
                self.on_error("clipboard_error", error_msg)
                
        except pyautogui.PyAutoGUIException as e:
            error_msg = f"Keyboard simulation error: {e}"
            logger.error(error_msg)
            self.status = StreamStatus.ERROR
            self.error_message = error_msg
            
            if self.on_error:
                self.on_error("keyboard_error", error_msg)

    def _restore_clipboard(self) -> None:
        """Restores original clipboard content."""
        if self.original_clipboard is not None:
            try:
                pyperclip.copy(self.original_clipboard)
            except Exception as e:
                logger.warning(f"Could not restore clipboard: {e}")

    def finalize(self) -> None:
        """Legacy method for backward compatibility."""
        self.stop_streaming()

    def get_status(self) -> StreamStatus:
        """Returns current streaming status."""
        return self.status

    def get_error_message(self) -> Optional[str]:
        """Returns error message if status is ERROR or TIMEOUT."""
        return self.error_message
