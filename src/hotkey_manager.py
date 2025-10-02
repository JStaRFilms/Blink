"""
Hotkey manager module for Blink.

Responsible for setting up and listening for the global hotkey with error recovery.
Uses the 'keyboard' library for more reliable hotkey handling on Windows.
"""

import threading
import keyboard as kb
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .text_capturer import TextCapturer
    from .llm_interface import LLMInterface
    from .overlay_ui import OverlayUI
    from .config_manager import ConfigManager

from .output_handler import DirectStreamHandler, StreamStatus
from .error_logger import logger
from .history_manager import get_conversation_history


class HotkeyManager:
    """
    Manages the global hotkey listener and triggers the text capture and AI processing flow.
    Includes error recovery and retry logic.
    """

    def __init__(self, text_capturer: 'TextCapturer', llm_interface: 'LLMInterface', 
                 overlay_ui: 'OverlayUI', config_manager: 'ConfigManager') -> None:
        """
        Initializes the HotkeyManager.
        """
        self.text_capturer = text_capturer
        self.llm_interface = llm_interface
        self.overlay_ui = overlay_ui
        self.config_manager = config_manager
        
        # Configure logging if enabled
        if config_manager.get("enable_error_logging", True):
            if config_manager.get("log_to_file", False):
                log_path = config_manager.get("log_file_path", "blink_errors.log")
                logger.configure_file_logging(log_path)
        
        # Hotkey state
        self.hotkey = 'ctrl+alt+.'
        self.clipboard_context_hotkey = self.config_manager.get("clipboard_context_hotkey", "ctrl+alt+/")
        self.is_processing = False
        self.hotkey_registered = False
        self.clipboard_context_hotkey_registered = False
        
        # Track last query for retry
        self.last_query_text = None
        self.last_query_rect = None

    def start(self) -> None:
        """Starts the global hotkey listener."""
        try:
            self.stop()
            kb.add_hotkey(self.hotkey, self.on_hotkey, suppress=True)
            self.hotkey_registered = True
            kb.add_hotkey(self.clipboard_context_hotkey, self.on_clipboard_context_hotkey, suppress=True)
            self.clipboard_context_hotkey_registered = True
            logger.info(f"Hotkey listeners started ({self.hotkey}, {self.clipboard_context_hotkey})")
        except Exception as e:
            logger.error(f"Failed to register hotkey: {e}")
            self.hotkey_registered = False
            self.clipboard_context_hotkey_registered = False

    def stop(self) -> None:
        """Stops the hotkey listener."""
        try:
            if self.hotkey_registered:
                kb.remove_hotkey(self.hotkey)
                self.hotkey_registered = False
            if self.clipboard_context_hotkey_registered:
                kb.remove_hotkey(self.clipboard_context_hotkey)
                self.clipboard_context_hotkey_registered = False
            logger.info("Hotkey listeners stopped")
        except Exception as e:
            logger.error(f"Error stopping hotkey listener: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop()
        kb.unhook_all()
        logger.info("Hotkey manager cleaned up")

    def on_hotkey(self) -> None:
        """Callback for when the hotkey is pressed."""
        if self.is_processing:
            logger.debug("Already processing a request, ignoring hotkey")
            return
            
        try:
            self.is_processing = True
            logger.info(f"HOTKEY TRIGGERED: {self.hotkey}")
            
            # Ensure all keys are released before proceeding
            kb.release('ctrl')
            kb.release('alt')
            kb.release('.')
            
            # Process in a separate thread to avoid blocking
            process_thread = threading.Thread(target=self.process, daemon=True)
            process_thread.start()
            
            # Wait a bit before allowing the next hotkey press
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error in hotkey handler: {e}")
        finally:
            self.is_processing = False

    def on_clipboard_context_hotkey(self) -> None:
        """Callback for when the clipboard context hotkey is pressed."""
        if self.is_processing:
            logger.debug("Already processing a request, ignoring clipboard context hotkey")
            return

        try:
            self.is_processing = True
            logger.info(f"CLIPBOARD CONTEXT HOTKEY TRIGGERED: {self.clipboard_context_hotkey}")

            # Ensure all keys are released before proceeding
            kb.release('ctrl')
            kb.release('alt')
            kb.release('/')

            # Process in a separate thread to avoid blocking
            process_thread = threading.Thread(target=self.process_clipboard_context, daemon=True)
            process_thread.start()

            # Wait a bit before allowing the next hotkey press
            time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in clipboard context hotkey handler: {e}")
        finally:
            self.is_processing = False

    def process_clipboard_context(self) -> None:
        """
        Processes the clipboard context hotkey event with retry logic if enabled.
        """
        try:
            # Add a small delay to ensure keys are released
            time.sleep(0.2)

            # Get config
            output_mode = self.config_manager.get("output_mode", "popup")
            enable_retry = self.config_manager.get("enable_retry", True)
            max_retries = self.config_manager.get("max_retries", 2)

            attempt = 0
            success = False

            while attempt <= max_retries and not success:
                if attempt > 0:
                    logger.info(f"Clipboard context retry attempt {attempt} of {max_retries}")
                    time.sleep(0.3)

                try:
                    # Get clipboard content
                    clipboard_content = self.text_capturer.get_clipboard_content()
                    if not clipboard_content or not clipboard_content.strip():
                        logger.warning(f"Clipboard is empty (attempt {attempt + 1}/{max_retries + 1})")
                        attempt += 1
                        continue

                    # Get selected instruction text
                    selected_instruction = self.text_capturer.capture_selected_text()
                    if not selected_instruction or not selected_instruction.strip():
                        logger.warning(f"No instruction text selected (attempt {attempt + 1}/{max_retries + 1})")
                        attempt += 1
                        continue

                    logger.debug(f"Captured instruction: {selected_instruction[:50]}..." if len(selected_instruction) > 50 else f"Captured instruction: {selected_instruction}")

                    # Format the final prompt
                    final_prompt = f"""
Please execute the following instruction:
---
{selected_instruction}
---

Apply the instruction to the following text content:
---
{clipboard_content}
---
"""

                    logger.debug(f"Clipboard context prompt formatted: {final_prompt[:100]}...")

                    # Process the query using existing logic
                    success = self._process_clipboard_context_query(final_prompt, output_mode)

                    if not success and enable_retry:
                        logger.info(f"Clipboard context query processing failed, will retry if attempts remain")

                except Exception as e:
                    logger.error(f"Error during clipboard context processing (attempt {attempt + 1}): {e}")
                    success = False

                attempt += 1

            if not success:
                logger.error("Failed to process clipboard context after all retry attempts")
                if output_mode == "popup":
                    try:
                        self.overlay_ui.reset_signal.emit()
                        self.overlay_ui.show_signal.emit()
                        self.overlay_ui.append_signal.emit(
                            "❌ Failed to process clipboard context after multiple attempts.\n"
                            "Check console for details."
                        )
                    except Exception as e:
                        logger.error(f"Error showing error message: {e}")

        except Exception as e:
            logger.error(f"Unexpected error in process_clipboard_context: {e}")

        finally:
            # Ensure keys are released
            kb.release('ctrl')
            kb.release('alt')
            kb.release('/')

    def process(self) -> None:
        """
        Processes the hotkey event with retry logic if enabled.
        """
        try:
            # Add a small delay to ensure keys are released
            time.sleep(0.2)
            
            # Get config
            output_mode = self.config_manager.get("output_mode", "popup")
            enable_retry = self.config_manager.get("enable_retry", True)
            max_retries = self.config_manager.get("max_retries", 2)
            
            attempt = 0
            success = False
            
            while attempt <= max_retries and not success:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt} of {max_retries}")
                    time.sleep(0.3)
                
                try:
                    # Capture text
                    logger.debug("Attempting to capture selected text...")
                    text, selection_rect = self.text_capturer.capture_selected_text_with_rect()
                    
                    if not text or not text.strip():
                        logger.warning(f"No text selected (attempt {attempt + 1}/{max_retries + 1})")
                        attempt += 1
                        continue
                        
                    logger.debug(f"Captured text: {text[:50]}..." if len(text) > 50 else f"Captured text: {text}")
                    
                    # Store for potential retry
                    self.last_query_text = text
                    self.last_query_rect = selection_rect
                    
                    # Process the query
                    success = self._process_query(text, selection_rect, output_mode, attempt)
                    
                    if not success and enable_retry:
                        logger.info(f"Query processing failed, will retry if attempts remain")
                    
                except Exception as e:
                    logger.error(f"Error during text capture (attempt {attempt + 1}): {e}")
                    success = False
                
                attempt += 1
                
            if not success:
                logger.error("Failed to process text after all retry attempts")
                # Only show error in popup mode
                if output_mode == "popup":
                    try:
                        self.overlay_ui.reset_signal.emit()
                        if 'selection_rect' in locals():
                            self.overlay_ui.position_near_selection(selection_rect)
                        self.overlay_ui.show_signal.emit()
                        self.overlay_ui.append_signal.emit(
                            "❌ Failed to process selected text after multiple attempts.\n"
                            "Check console for details."
                        )
                    except Exception as e:
                        logger.error(f"Error showing error message: {e}")
                
        except Exception as e:
            logger.error(f"Unexpected error in process: {e}")
            
        finally:
            # Just ensure keys are released, don't mess with overlay
            kb.release('ctrl')
            kb.release('alt')
            kb.release('.')

    def _process_query(self, text: str, selection_rect, output_mode: str, attempt: int) -> bool:
        """
        Processes a single query attempt.

        Returns:
            bool: True if successful, False if error occurred.
        """
        preview = text[:50] + "..." if len(text) > 50 else text
        logger.streaming_started(preview)

        # Get system prompt if configured
        system_prompt = self.config_manager.get("system_prompt", "").strip()
        system_messages = []
        if system_prompt:
            system_messages = [{"role": "system", "content": system_prompt}]

        # Get conversation history if memory is enabled
        memory_enabled = self.config_manager.get("memory_enabled", True)
        if memory_enabled:
            history_manager = get_conversation_history(self.config_manager)
            current_history = history_manager.get_history()
        else:
            current_history = []

        # Create new user message
        new_message = {"role": "user", "content": text}

        # Combine system prompt, history, and new message in correct order
        messages_to_send = system_messages + current_history + [new_message]

        if output_mode == "direct_stream":
            return self._process_direct_stream(messages_to_send, text, attempt)
        else:
            return self._process_popup(messages_to_send, text, selection_rect)

    def _process_clipboard_context_query(self, text: str, output_mode: str) -> bool:
        """
        Processes a clipboard context query.

        Returns:
            bool: True if successful, False if error occurred.
        """
        preview = text[:50] + "..." if len(text) > 50 else text
        logger.streaming_started(f"Clipboard Context: {preview}")

        # Get system prompt if configured
        system_prompt = self.config_manager.get("system_prompt", "").strip()
        system_messages = []
        if system_prompt:
            system_messages = [{"role": "system", "content": system_prompt}]

        # Get conversation history if memory is enabled
        memory_enabled = self.config_manager.get("memory_enabled", True)
        if memory_enabled:
            history_manager = get_conversation_history(self.config_manager)
            current_history = history_manager.get_history()
        else:
            current_history = []

        # Create new user message
        new_message = {"role": "user", "content": text}

        # Combine system prompt, history, and new message in correct order
        messages_to_send = system_messages + current_history + [new_message]

        if output_mode == "direct_stream":
            return self._process_clipboard_direct_stream(messages_to_send, text)
        else:
            return self._process_clipboard_popup(messages_to_send, text)

    def _process_direct_stream(self, messages: list[dict[str, str]], user_text: str, attempt: int) -> bool:
        """
        Processes query in direct stream mode with error handling.

        Returns:
            bool: True if successful, False otherwise.
        """
        timeout = self.config_manager.get("streaming_timeout", 120)

        def on_error(error_type: str, message: str) -> None:
            logger.streaming_error(error_type, message)

        handler = DirectStreamHandler(timeout=timeout, on_error=on_error)
        handler.start_streaming()

        # Accumulate full response for history
        full_response = []

        def on_chunk(chunk: str) -> None:
            handler.stream_token(chunk)
            full_response.append(chunk)

        try:
            self.llm_interface.query(messages, on_chunk)
            handler.stream_token(None)
            final_status = handler.wait_for_completion()

            if final_status == StreamStatus.COMPLETE:
                # Add to conversation history if enabled
                memory_enabled = self.config_manager.get("memory_enabled", True)
                if memory_enabled:
                    history_manager = get_conversation_history(self.config_manager)
                    history_manager.add_message("user", user_text)
                    history_manager.add_message("assistant", "".join(full_response))
                return True
            else:
                error_msg = handler.get_error_message()
                logger.error(f"Stream failed with status {final_status.value}: {error_msg}")
                return False

        except Exception as e:
            logger.streaming_error("llm_query_error", str(e))
            handler.stop_streaming()
            return False

    def _process_popup(self, messages: list[dict[str, str]], user_text: str, selection_rect) -> bool:
        """
        Processes query in popup mode.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Setup overlay ONCE at the start
            self.overlay_ui.reset_signal.emit()
            self.overlay_ui.position_near_selection(selection_rect)
            self.overlay_ui.show_signal.emit()

            # Track if any data received
            received_data = False

            # Accumulate full response for history
            full_response = []

            # Define streaming callback
            def on_chunk(chunk: str) -> None:
                nonlocal received_data
                received_data = True
                self.overlay_ui.append_signal.emit(chunk)
                full_response.append(chunk)

            # Query LLM (this blocks until streaming is complete)
            self.llm_interface.query(messages, on_chunk)

            # Check if we got any response
            if not received_data:
                logger.warning("No data received from LLM")
                self.overlay_ui.append_signal.emit(
                    "\n\n❌ Error: No response from LLM. Check your connection."
                )
                return False

            # Add to conversation history if enabled
            memory_enabled = self.config_manager.get("memory_enabled", True)
            if memory_enabled:
                history_manager = get_conversation_history(self.config_manager)
                history_manager.add_message("user", user_text)
                history_manager.add_message("assistant", "".join(full_response))

            # Success! The overlay stays open with the streamed text
            logger.info("Popup streaming completed successfully")
            return True

        except Exception as e:
            logger.streaming_error("popup_error", str(e))
            try:
                self.overlay_ui.append_signal.emit(f"\n\n❌ Error: {str(e)}")
            except Exception:
                pass
            return False

    def _process_clipboard_direct_stream(self, messages: list[dict[str, str]], user_text: str) -> bool:
        """
        Processes clipboard context query in direct stream mode with error handling.

        Returns:
            bool: True if successful, False otherwise.
        """
        timeout = self.config_manager.get("streaming_timeout", 120)

        def on_error(error_type: str, message: str) -> None:
            logger.streaming_error(error_type, message)

        handler = DirectStreamHandler(timeout=timeout, on_error=on_error)
        handler.start_streaming()

        # Accumulate full response for history
        full_response = []

        def on_chunk(chunk: str) -> None:
            handler.stream_token(chunk)
            full_response.append(chunk)

        try:
            self.llm_interface.query(messages, on_chunk)
            handler.stream_token(None)
            final_status = handler.wait_for_completion()

            if final_status == StreamStatus.COMPLETE:
                # Add to conversation history if enabled
                memory_enabled = self.config_manager.get("memory_enabled", True)
                if memory_enabled:
                    history_manager = get_conversation_history(self.config_manager)
                    history_manager.add_message("user", user_text)
                    history_manager.add_message("assistant", "".join(full_response))
                return True
            else:
                error_msg = handler.get_error_message()
                logger.error(f"Clipboard context stream failed with status {final_status.value}: {error_msg}")
                return False

        except Exception as e:
            logger.streaming_error("clipboard_context_llm_query_error", str(e))
            handler.stop_streaming()
            return False

    def _process_clipboard_popup(self, messages: list[dict[str, str]], user_text: str) -> bool:
        """
        Processes clipboard context query in popup mode.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Setup overlay ONCE at the start
            self.overlay_ui.reset_signal.emit()
            self.overlay_ui.show_signal.emit()

            # Track if any data received
            received_data = False

            # Accumulate full response for history
            full_response = []

            # Define streaming callback
            def on_chunk(chunk: str) -> None:
                nonlocal received_data
                received_data = True
                self.overlay_ui.append_signal.emit(chunk)
                full_response.append(chunk)

            # Query LLM (this blocks until streaming is complete)
            self.llm_interface.query(messages, on_chunk)

            # Check if we got any response
            if not received_data:
                logger.warning("No data received from LLM for clipboard context")
                self.overlay_ui.append_signal.emit(
                    "\n\n❌ Error: No response from LLM. Check your connection."
                )
                return False

            # Add to conversation history if enabled
            memory_enabled = self.config_manager.get("memory_enabled", True)
            if memory_enabled:
                history_manager = get_conversation_history(self.config_manager)
                history_manager.add_message("user", user_text)
                history_manager.add_message("assistant", "".join(full_response))

            # Success! The overlay stays open with the streamed text
            logger.info("Clipboard context popup streaming completed successfully")
            return True

        except Exception as e:
            logger.streaming_error("clipboard_context_popup_error", str(e))
            try:
                self.overlay_ui.append_signal.emit(f"\n\n❌ Error: {str(e)}")
            except Exception:
                pass
            return False

    def retry_last_query(self) -> None:
        """
        Manually retry the last query.
        """
        if self.last_query_text:
            logger.info("Manual retry triggered")
            text = self.last_query_text
            rect = self.last_query_rect
            output_mode = self.config_manager.get("output_mode", "popup")
            self._process_query(text, rect, output_mode, attempt=0)
        else:
            logger.warning("No previous query to retry")
