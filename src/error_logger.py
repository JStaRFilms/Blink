"""
Error logging module for Blink.

Provides centralized error logging with console and file output options.
"""

import logging
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path


class BlinkLogger:
    """
    Centralized logger for Blink application with configurable output.
    """

    _instance: Optional['BlinkLogger'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the logger (only once)."""
        if not BlinkLogger._initialized:
            self.logger = logging.getLogger("Blink")
            self.logger.setLevel(logging.DEBUG)
            
            # Console handler (always enabled)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
            
            # File handler (configured later if enabled)
            self.file_handler: Optional[logging.FileHandler] = None
            
            BlinkLogger._initialized = True

    def configure_file_logging(self, log_file_path: str) -> None:
        """
        Enable file logging to specified path.

        Args:
            log_file_path (str): Path to log file.
        """
        if self.file_handler:
            return  # Already configured
        
        try:
            # Ensure log directory exists
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            self.file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(funcName)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            self.file_handler.setFormatter(file_format)
            self.logger.addHandler(self.file_handler)
            
            self.info(f"File logging enabled: {log_file_path}")
        except Exception as e:
            self.error(f"Failed to enable file logging: {e}")

    def info(self, message: str) -> None:
        """Log info level message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning level message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error level message."""
        self.logger.error(message)

    def debug(self, message: str) -> None:
        """Log debug level message."""
        self.logger.debug(message)

    def streaming_started(self, prompt_preview: str) -> None:
        """Log streaming start."""
        preview = prompt_preview[:50] + "..." if len(prompt_preview) > 50 else prompt_preview
        self.info(f"Streaming started for prompt: '{preview}'")

    def streaming_complete(self, token_count: int, duration: float) -> None:
        """Log successful streaming completion."""
        self.info(f"Streaming complete: {token_count} tokens in {duration:.2f}s")

    def streaming_error(self, error_type: str, error_message: str) -> None:
        """Log streaming error."""
        self.error(f"Streaming error [{error_type}]: {error_message}")

    def streaming_timeout(self, timeout_duration: int) -> None:
        """Log streaming timeout."""
        self.warning(f"Streaming timeout after {timeout_duration}s")

    def retry_attempt(self, attempt: int, max_attempts: int) -> None:
        """Log retry attempt."""
        self.warning(f"Retry attempt {attempt}/{max_attempts}")


# Global logger instance
logger = BlinkLogger()