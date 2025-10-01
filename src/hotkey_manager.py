"""
Hotkey manager module for Blink.

Responsible for setting up and listening for the global hotkey.
"""

import threading
from pynput import keyboard
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .text_capturer import TextCapturer
    from .llm_interface import LLMInterface
    from .overlay_ui import OverlayUI
    from .config_manager import ConfigManager

from .output_handler import DirectStreamHandler


class HotkeyManager:
    """
    Manages the global hotkey listener and triggers the text capture and AI processing flow.

    Attributes:
        text_capturer (TextCapturer): Instance for capturing selected text.
        llm_interface (LLMInterface): Instance for querying the LLM.
        overlay_ui (OverlayUI): Instance of the GUI overlay.
        listener (keyboard.GlobalHotKeys): The global hotkey listener.
    """

    def __init__(self, text_capturer: 'TextCapturer', llm_interface: 'LLMInterface', overlay_ui: 'OverlayUI', config_manager: 'ConfigManager') -> None:
        """
        Initializes the HotkeyManager.

        Args:
            text_capturer (TextCapturer): Text capturer instance.
            llm_interface (LLMInterface): LLM interface instance.
            overlay_ui (OverlayUI): Overlay UI instance.
            config_manager (ConfigManager): Configuration manager instance.
        """
        self.text_capturer = text_capturer
        self.llm_interface = llm_interface
        self.overlay_ui = overlay_ui
        self.config_manager = config_manager
        self.listener = keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+.': self.on_hotkey
        })

    def start(self) -> None:
        """
        Starts the global hotkey listener.
        """
        self.listener.start()

    def on_hotkey(self) -> None:
        """
        Callback for when the hotkey is pressed. Starts the processing in a separate thread.
        """
        threading.Thread(target=self.process, daemon=True).start()

    def process(self) -> None:
        """
        Processes the hotkey event: captures text, queries LLM, and outputs based on user setting.
        """
        text, selection_rect = self.text_capturer.capture_selected_text_with_rect()
        if not text.strip():
            return  # No text selected

        # Get output mode from config
        output_mode = self.config_manager.get("output_mode", "popup")

        if output_mode == "direct_stream":
            # Use direct stream handler
            handler = DirectStreamHandler()

            # Start the consumer thread
            handler.start_streaming()

            # Define callback for streaming chunks
            def on_chunk(chunk: str) -> None:
                handler.stream_token(chunk)

            # Query the LLM with streaming
            self.llm_interface.query(text, on_chunk)

            # Stop streaming and finalize any remaining buffered text
            handler.stop_streaming()
        else:
            # Use popup overlay (default behavior)
            # Reset and position overlay
            self.overlay_ui.reset_signal.emit()
            self.overlay_ui.position_near_selection(selection_rect)
            self.overlay_ui.show_signal.emit()

            # Define callback for streaming chunks
            def on_chunk(chunk: str) -> None:
                self.overlay_ui.append_signal.emit(chunk)

            # Query the LLM with streaming
            self.llm_interface.query(text, on_chunk)
