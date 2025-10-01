"""
Module entry point for the Blink application.

Allows running the application with `python -m src`.
"""

import sys
from PyQt6.QtWidgets import QApplication
from .text_capturer import TextCapturer
from .llm_interface import LLMInterface
from .overlay_ui import OverlayUI
from .hotkey_manager import HotkeyManager


def main() -> None:
    """
    Main function to start the Blink application.
    """
    app = QApplication(sys.argv)

    # Initialize components
    text_capturer = TextCapturer()
    llm_interface = LLMInterface()
    overlay_ui = OverlayUI()
    hotkey_manager = HotkeyManager(text_capturer, llm_interface, overlay_ui)

    # Start the hotkey listener
    hotkey_manager.start()

    # Run the Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
