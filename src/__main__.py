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
from .config_manager import ConfigManager
from .system_tray import SystemTrayManager
from .settings_dialog import SettingsDialog


def main() -> None:
    """
    Main function to start the Blink application.
    """
    app = QApplication(sys.argv)

    # Initialize config manager
    config_manager = ConfigManager()

    # Initialize components
    text_capturer = TextCapturer()
    llm_interface = LLMInterface(config_manager=config_manager)
    overlay_ui = OverlayUI()
    hotkey_manager = HotkeyManager(text_capturer, llm_interface, overlay_ui)

    # Load saved model selection
    selected_model = config_manager.get("selected_model", "ollama:llama3.2:latest")
    llm_interface.set_selected_model(selected_model)

    # Initialize system tray
    system_tray = SystemTrayManager(app)

    # Connect system tray signals
    def show_settings():
        settings_dialog = SettingsDialog(config_manager, llm_interface, overlay_ui)
        settings_dialog.exec()

    def quit_app():
        app.quit()

    system_tray.settings_requested.connect(show_settings)
    system_tray.quit_requested.connect(quit_app)

    # Start the hotkey listener
    hotkey_manager.start()

    # Run the Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
