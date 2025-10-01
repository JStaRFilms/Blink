"""
Main entry point for the Blink application.

Initializes the application components and starts the hotkey listener.
"""

import sys
from PyQt6.QtWidgets import QApplication
from src.text_capturer import TextCapturer
from src.llm_interface import LLMInterface
from src.overlay_ui import OverlayUI
from src.hotkey_manager import HotkeyManager


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
