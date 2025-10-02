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
from src.config_manager import ConfigManager
from src.system_tray import SystemTrayManager
from src.settings_dialog import SettingsDialog


def main() -> None:
    """
    Main function to start the Blink application.
    """
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep app running even when windows close

    # Initialize config manager
    config_manager = ConfigManager()

    # Initialize components
    text_capturer = TextCapturer()
    llm_interface = LLMInterface(config_manager=config_manager)
    overlay_ui = OverlayUI()
    hotkey_manager = HotkeyManager(text_capturer, llm_interface, overlay_ui, config_manager)

    # Load saved model selection
    selected_model = config_manager.get("selected_model", "ollama:llama3.2:latest")
    llm_interface.set_selected_model(selected_model)

    # Initialize system tray
    system_tray = SystemTrayManager(app, config_manager)

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
