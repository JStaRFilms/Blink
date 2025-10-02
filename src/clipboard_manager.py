"""
Clipboard manager module for Blink.

Handles detecting and extracting different types of clipboard content including text, files, and images.
"""

import enum
from typing import Optional, List
import win32clipboard
import pyperclip
import time


class ClipboardContentType(enum.Enum):
    """Enumeration of supported clipboard content types."""
    TEXT = "text"
    FILE = "file"
    IMAGE = "image"
    UNKNOWN = "unknown"


class ClipboardManager:
    """
    Manages clipboard content detection and extraction for different data types.
    """

    def __init__(self) -> None:
        """Initialize the clipboard manager."""
        pass

    def _open_clipboard_with_retries(self, retries: int = 4, delay: float = 0.05) -> bool:
        """
        Tries to open the clipboard with retries to mitigate transient access errors.

        Args:
            retries (int): Number of additional attempts after the first try.
            delay (float): Delay between attempts in seconds.

        Returns:
            bool: True if the clipboard was opened, False otherwise.
        """
        attempt = 0
        while True:
            try:
                win32clipboard.OpenClipboard()
                return True
            except Exception:
                if attempt >= retries:
                    return False
                time.sleep(delay)
                attempt += 1

    def get_clipboard_content_type(self) -> ClipboardContentType:
        """
        Determines the type of content currently on the clipboard.

        Returns:
            ClipboardContentType: The detected content type.
        """
        # Prefer Win32 clipboard inspection to detect files/images reliably
        if self._open_clipboard_with_retries():
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                    return ClipboardContentType.FILE
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_BITMAP):
                    return ClipboardContentType.IMAGE
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    return ClipboardContentType.TEXT
                return ClipboardContentType.UNKNOWN
            finally:
                try:
                    win32clipboard.CloseClipboard()
                except Exception:
                    pass

        # Fall back to pyperclip if Win32 access failed
        try:
            content = pyperclip.paste()
            if content and content.strip():
                return ClipboardContentType.TEXT
        except Exception:
            pass

        return ClipboardContentType.UNKNOWN

    def get_text_from_clipboard(self) -> str:
        """
        Gets text content from the clipboard.

        Returns:
            str: The text content, or empty string if no text found.
        """
        # Try Win32 first for consistency
        if self._open_clipboard_with_retries():
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    try:
                        data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                        return data or ""
                    except Exception:
                        pass
                # No UNICODETEXT, fall back to generic text requests
            finally:
                try:
                    win32clipboard.CloseClipboard()
                except Exception:
                    pass

        # Fallback to pyperclip if Win32 approach fails
        try:
            return pyperclip.paste() or ""
        except Exception:
            return ""

    def get_file_path_from_clipboard(self) -> Optional[str]:
        """
        Gets the file path from the clipboard if it contains file data.

        Returns:
            Optional[str]: The file path, or None if no file found.
        """
        if self._open_clipboard_with_retries():
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                    try:
                        files = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                        # pywin32 returns a list/tuple of file paths
                        if files:
                            return files[0]
                    except Exception:
                        pass
                return None
            finally:
                try:
                    win32clipboard.CloseClipboard()
                except Exception:
                    pass

    def get_image_from_clipboard(self):
        """
        Gets an image object from the clipboard if present.

        Returns:
            PIL.Image.Image | None: The image, or None if not available.
        """
        try:
            # Import lazily to avoid hard dependency at import time
            from PIL import ImageGrab, Image
        except Exception:
            return None

        try:
            # ImageGrab.grabclipboard() returns an Image, or a list of file paths, or None
            data = ImageGrab.grabclipboard()
            # If it's already an Image, return it
            if hasattr(data, 'size') and hasattr(data, 'mode'):
                return data
            # If it's a list of files and first is an image, try open it
            if isinstance(data, (list, tuple)) and data:
                first = data[0]
                try:
                    from PIL import Image
                    return Image.open(first)
                except Exception:
                    return None
            return None
        except Exception:
            return None
        return None

    def get_clipboard_content(self) -> str:
        """
        Gets clipboard content as text, regardless of type.
        For files, returns the file path as text.

        Returns:
            str: The clipboard content as text.
        """
        content_type = self.get_clipboard_content_type()

        if content_type == ClipboardContentType.FILE:
            file_path = self.get_file_path_from_clipboard()
            return file_path if file_path else ""
        elif content_type == ClipboardContentType.TEXT:
            return self.get_text_from_clipboard()
        else:
            # For images or unknown types, return empty string
            return ""
