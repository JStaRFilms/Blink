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
from src.history_manager import get_conversation_history

# Import modules that PyInstaller might miss
try:
    import psutil
except ImportError:
    psutil = None

# Ensure pywin32 modules are bundled and available at runtime
try:
    import pywintypes
    import pythoncom
    import win32clipboard
    import win32gui
    import win32api
    import win32con
except ImportError:
    pass  # Will fail later if truly missing


def main() -> None:
    """
    Main function to start the Blink application.
    """
    # Check for existing instance
    import os
    lock_file = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd(), 'blink.lock')

    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            # Check if process is still running
            import psutil
            if psutil.pid_exists(pid):
                print("Another instance of Blink is already running.")
                return
        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
            pass  # Lock file is stale, continue

    # Create lock file with current PID
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
    except Exception:
        pass  # Ignore if we can't create lock file

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep app running even when windows close

    # Initialize config manager
    config_manager = ConfigManager()

    # Initialize components
    text_capturer = TextCapturer()
    llm_interface = LLMInterface(config_manager=config_manager)
    overlay_ui = OverlayUI()

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
        print("Quit requested")
        app.quit()

    def restart_application():
        """Restarts the application by saving history and relaunching."""
        try:
            # Save history before restart
            history_manager = get_conversation_history(config_manager)
            history_manager.save_history()

            # Relaunch the executable and quit current instance
            import sys, os
            os.startfile(sys.executable)  # Re-launches the .exe
            app.quit()  # Closes the current instance
        except Exception as e:
            print(f"Error during restart: {e}")

    system_tray.settings_requested.connect(show_settings)
    system_tray.quit_requested.connect(quit_app)
    system_tray.restart_requested.connect(restart_application)

    # Initialize hotkey manager with system tray reference
    hotkey_manager = HotkeyManager(text_capturer, llm_interface, overlay_ui, config_manager, system_tray)

    # Start the hotkey listener
    hotkey_manager.start()

    # Connect application shutdown to save history and cleanup
    def save_history_on_quit():
        try:
            history_manager = get_conversation_history(config_manager)
            history_manager.save_history()
        except Exception as e:
            print(f"Warning: Could not save history on shutdown: {e}")

        # Clean up lock file
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except Exception:
            pass

    app.aboutToQuit.connect(save_history_on_quit)

    # Run the Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
