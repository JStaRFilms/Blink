"""
Hotkey manager module for Blink.

Responsible for setting up and listening for the global hotkey with error recovery.
Uses the 'keyboard' library for more reliable hotkey handling on Windows.
"""

import threading
import keyboard as kb
import time
import os
from typing import TYPE_CHECKING, Union, List, Dict
from PyQt6.QtWidgets import QSystemTrayIcon

if TYPE_CHECKING:
    from .text_capturer import TextCapturer
    from .llm_interface import LLMInterface
    from .overlay_ui import OverlayUI
    from .config_manager import ConfigManager

from .output_handler import DirectStreamHandler, StreamStatus
from .error_logger import logger
from .history_manager import get_conversation_history
from .llm_interface import LLMConnectionError, LLMAuthError, LLMConfigError
from .clipboard_manager import ClipboardManager, ClipboardContentType
from .file_reader import FileReader


class HotkeyManager:
    """
    Manages the global hotkey listener and triggers the text capture and AI processing flow.
    Includes error recovery and retry logic.
    """

    def __init__(self, text_capturer: 'TextCapturer', llm_interface: 'LLMInterface',
                 overlay_ui: 'OverlayUI', config_manager: 'ConfigManager', system_tray=None) -> None:
        """
        Initializes the HotkeyManager.
        """
        self.text_capturer = text_capturer
        self.llm_interface = llm_interface
        self.overlay_ui = overlay_ui
        self.config_manager = config_manager
        self.system_tray = system_tray
        self.file_reader = FileReader()
        
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
                    # Get clipboard content using clipboard manager with robust type detection
                    clipboard_manager = ClipboardManager()
                    content_type = clipboard_manager.get_clipboard_content_type()

                    clipboard_content = None
                    image_data = None

                    if content_type == ClipboardContentType.FILE:
                        file_path = clipboard_manager.get_file_path_from_clipboard()
                        if not file_path or not os.path.exists(file_path):
                            logger.warning(f"No valid file path found on clipboard (attempt {attempt + 1}/{max_retries + 1})")
                            attempt += 1
                            continue
                        logger.debug(f"Detected file via CF_HDROP on clipboard: {file_path}")
                        
                        # Check if it's an image file
                        if self.file_reader.is_image_file(file_path):
                            # For image files, check if model supports multimodal input
                            if self.llm_interface.is_multimodal():
                                logger.debug(f"Processing image file for multimodal model: {file_path}")
                                try:
                                    image_data, mime_type = self.file_reader.get_image_data(file_path)
                                    logger.debug(f"Successfully extracted image data ({len(image_data)} characters)")
                                except (ValueError, FileNotFoundError, PermissionError) as e:
                                    logger.warning(f"Could not read image file {file_path}: {e} (attempt {attempt + 1}/{max_retries + 1})")
                                    attempt += 1
                                    continue
                            else:
                                # For text-only models, use OCR
                                logger.debug(f"Processing image file with OCR: {file_path}")
                                try:
                                    clipboard_content = self.file_reader.read_text_from_file(file_path)
                                    logger.debug(f"Successfully OCR'd image to text ({len(clipboard_content)} characters)")
                                except (ValueError, FileNotFoundError, PermissionError) as e:
                                    logger.warning(f"Could not OCR image file {file_path}: {e} (attempt {attempt + 1}/{max_retries + 1})")
                                    attempt += 1
                                    continue
                        else:
                            # For non-image files, read as text
                            logger.debug(f"Processing text file: {file_path}")
                            try:
                                clipboard_content = self.file_reader.read_text_from_file(file_path)
                                logger.debug(f"Successfully read file content ({len(clipboard_content)} characters)")
                            except (ValueError, FileNotFoundError, PermissionError) as e:
                                logger.warning(f"Could not read file {file_path}: {e} (attempt {attempt + 1}/{max_retries + 1})")
                                attempt += 1
                                continue

                    elif content_type == ClipboardContentType.TEXT:
                        text_content = clipboard_manager.get_text_from_clipboard()
                        if not text_content or not text_content.strip():
                            logger.warning(f"Clipboard text is empty (attempt {attempt + 1}/{max_retries + 1})")
                            attempt += 1
                            continue

                        text_content_stripped = text_content.strip()
                        is_file_path = (
                            len(text_content_stripped) > 0 and (
                                text_content_stripped.startswith('/') or
                                text_content_stripped.startswith('\\') or
                                (len(text_content_stripped) > 3 and text_content_stripped[1:3] == ':\\') or
                                (len(text_content_stripped) > 2 and text_content_stripped[0] == '.' and text_content_stripped[1] in '/\\')
                            ) and os.path.exists(text_content_stripped)
                        )

                        if is_file_path:
                            logger.debug(f"Detected file path in text clipboard: {text_content_stripped}")
                            
                            # Check if it's an image file
                            if self.file_reader.is_image_file(text_content_stripped):
                                # For image files, check if model supports multimodal input
                                if self.llm_interface.is_multimodal():
                                    logger.debug(f"Processing image file for multimodal model: {text_content_stripped}")
                                    try:
                                        image_data, mime_type = self.file_reader.get_image_data(text_content_stripped)
                                        logger.debug(f"Successfully extracted image data ({len(image_data)} characters)")
                                    except (ValueError, FileNotFoundError, PermissionError) as e:
                                        logger.warning(f"Could not read image file {text_content_stripped}: {e} (attempt {attempt + 1}/{max_retries + 1})")
                                        attempt += 1
                                        continue
                                else:
                                    # For text-only models, use OCR
                                    logger.debug(f"Processing image file with OCR: {text_content_stripped}")
                                    try:
                                        clipboard_content = self.file_reader.read_text_from_file(text_content_stripped)
                                        logger.debug(f"Successfully OCR'd image to text ({len(clipboard_content)} characters)")
                                    except (ValueError, FileNotFoundError, PermissionError) as e:
                                        logger.warning(f"Could not OCR image file {text_content_stripped}: {e} (attempt {attempt + 1}/{max_retries + 1})")
                                        attempt += 1
                                        continue
                            else:
                                # For non-image files, read as text
                                logger.debug(f"Processing text file: {text_content_stripped}")
                                try:
                                    clipboard_content = self.file_reader.read_text_from_file(text_content_stripped)
                                    logger.debug(f"Successfully read file content ({len(clipboard_content)} characters)")
                                except (ValueError, FileNotFoundError, PermissionError) as e:
                                    logger.warning(f"Could not read file {text_content_stripped}: {e} (attempt {attempt + 1}/{max_retries + 1})")
                                    attempt += 1
                                    continue
                        else:
                            clipboard_content = text_content
                            logger.debug(f"Detected regular text on clipboard ({len(clipboard_content)} characters)")

                    elif content_type == ClipboardContentType.IMAGE:
                        # For images, check if model supports multimodal input
                        if self.llm_interface.is_multimodal():
                            logger.debug("Processing clipboard image for multimodal model")
                            image = clipboard_manager.get_image_from_clipboard()
                            if image is None:
                                logger.warning(f"Could not retrieve image from clipboard (attempt {attempt + 1}/{max_retries + 1})")
                                attempt += 1
                                continue
                            try:
                                image_data, mime_type = self.file_reader.get_pil_image_data(image)
                                logger.debug(f"Successfully extracted image data ({len(image_data)} characters)")
                            except (ValueError, ImportError) as e:
                                logger.warning(f"Could not process clipboard image: {e} (attempt {attempt + 1}/{max_retries + 1})")
                                attempt += 1
                                continue
                        else:
                            # For text-only models, use OCR
                            logger.debug("Processing clipboard image with OCR")
                            image = clipboard_manager.get_image_from_clipboard()
                            if image is None:
                                logger.warning(f"Could not retrieve image from clipboard (attempt {attempt + 1}/{max_retries + 1})")
                                attempt += 1
                                continue
                            try:
                                clipboard_content = self.file_reader.read_text_from_image(image)
                                if not clipboard_content or not clipboard_content.strip():
                                    logger.warning(f"OCR returned no text (attempt {attempt + 1}/{max_retries + 1})")
                                    attempt += 1
                                    continue
                                logger.debug(f"Successfully OCR'd image to text ({len(clipboard_content)} characters)")
                            except (ValueError, ImportError) as e:
                                logger.warning(f"Could not OCR image from clipboard: {e} (attempt {attempt + 1}/{max_retries + 1})")
                                attempt += 1
                                continue

                    else:
                        # UNKNOWN: try to fall back to text anyway
                        text_content = clipboard_manager.get_text_from_clipboard()
                        if text_content and text_content.strip():
                            text_content_stripped = text_content.strip()
                            is_file_path = (
                                len(text_content_stripped) > 0 and (
                                    text_content_stripped.startswith('/') or
                                    text_content_stripped.startswith('\\') or
                                    (len(text_content_stripped) > 3 and text_content_stripped[1:3] == ':\\') or
                                    (len(text_content_stripped) > 2 and text_content_stripped[0] == '.' and text_content_stripped[1] in '/\\')
                                ) and os.path.exists(text_content_stripped)
                            )
                            if is_file_path:
                                logger.debug(f"Detected file path when falling back to text: {text_content_stripped}")
                                
                                # Check if it's an image file
                                if self.file_reader.is_image_file(text_content_stripped):
                                    # For image files, check if model supports multimodal input
                                    if self.llm_interface.is_multimodal():
                                        logger.debug(f"Processing image file for multimodal model: {text_content_stripped}")
                                        try:
                                            image_data, mime_type = self.file_reader.get_image_data(text_content_stripped)
                                            logger.debug(f"Successfully extracted image data ({len(image_data)} characters)")
                                        except (ValueError, FileNotFoundError, PermissionError) as e:
                                            logger.warning(f"Could not read image file {text_content_stripped}: {e} (attempt {attempt + 1}/{max_retries + 1})")
                                            attempt += 1
                                            continue
                                    else:
                                        # For text-only models, use OCR
                                        logger.debug(f"Processing image file with OCR: {text_content_stripped}")
                                        try:
                                            clipboard_content = self.file_reader.read_text_from_file(text_content_stripped)
                                            logger.debug(f"Successfully OCR'd image to text ({len(clipboard_content)} characters)")
                                        except (ValueError, FileNotFoundError, PermissionError) as e:
                                            logger.warning(f"Could not OCR image file {text_content_stripped}: {e} (attempt {attempt + 1}/{max_retries + 1})")
                                            attempt += 1
                                            continue
                                else:
                                    # For non-image files, read as text
                                    logger.debug(f"Processing text file: {text_content_stripped}")
                                    try:
                                        clipboard_content = self.file_reader.read_text_from_file(text_content_stripped)
                                        logger.debug(f"Successfully read file content ({len(clipboard_content)} characters)")
                                    except (ValueError, FileNotFoundError, PermissionError) as e:
                                        logger.warning(f"Could not read file {text_content_stripped}: {e} (attempt {attempt + 1}/{max_retries + 1})")
                                        attempt += 1
                                        continue
                            else:
                                clipboard_content = text_content
                                logger.debug(f"Falling back to text clipboard content ({len(clipboard_content)} characters)")
                        else:
                            logger.warning(f"Unsupported or empty clipboard content type: {content_type.value} (attempt {attempt + 1}/{max_retries + 1})")
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
                    if image_data:
                        # For multimodal models, include image data
                        final_prompt = self._format_multimodal_prompt(selected_instruction, image_data, mime_type)
                    else:
                        # For text-only content or OCR results
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
                    success = self._process_clipboard_context_query(final_prompt, output_mode, image_data is not None)

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

    def _format_multimodal_prompt(self, instruction: str, image_data: str, mime_type: str) -> list[dict]:
        """
        Formats a prompt for multimodal models with image data.
        
        Args:
            instruction: The instruction text.
            image_data: Base64 encoded image data.
            mime_type: MIME type of the image.
            
        Returns:
            list[dict]: Formatted messages for multimodal model.
        """
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Please execute the following instruction:\n---\n{instruction}\n---\n\nApply the instruction to the image provided:"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}"
                        }
                    }
                ]
            }
        ]

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

    def _process_clipboard_context_query(self, prompt: Union[str, List[Dict]], output_mode: str, is_multimodal: bool) -> bool:
        """
        Processes a clipboard context query.

        Args:
            prompt: The formatted prompt (string for text-only, list for multimodal)
            output_mode: Output mode (popup or direct_stream)
            is_multimodal: Whether the prompt contains image data

        Returns:
            bool: True if successful, False if error occurred.
        """
        if isinstance(prompt, str):
            preview = prompt[:50] + "..." if len(prompt) > 50 else prompt
        else:
            preview = "Multimodal prompt with image data"
        
        logger.streaming_started(f"Clipboard Context: {preview}")

        # Get system prompt if configured
        system_prompt = self.config_manager.get("system_prompt", "").strip()
        system_messages = []
        if system_prompt:
            if is_multimodal:
                # For multimodal models, include system prompt as text
                system_messages = [{"role": "system", "content": system_prompt}]
            else:
                system_messages = [{"role": "system", "content": system_prompt}]

        # Get conversation history if memory is enabled
        memory_enabled = self.config_manager.get("memory_enabled", True)
        if memory_enabled:
            history_manager = get_conversation_history(self.config_manager)
            current_history = history_manager.get_history()
        else:
            current_history = []

        # Combine system prompt, history, and new message in correct order
        if is_multimodal:
            # For multimodal, prompt is already a list of messages
            messages_to_send = system_messages + current_history + prompt
        else:
            # For text-only, create a user message with the prompt text
            new_message = {"role": "user", "content": prompt}
            messages_to_send = system_messages + current_history + [new_message]

        if output_mode == "direct_stream":
            return self._process_clipboard_direct_stream(messages_to_send, prompt, is_multimodal)
        else:
            return self._process_clipboard_popup(messages_to_send, prompt, is_multimodal)

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

        except LLMConnectionError as e:
            error_msg = str(e)
            logger.streaming_error("llm_connection_error", error_msg)
            try:
                self.overlay_ui.append_signal.emit(f"\n\n❌ Connection Error: {error_msg}")
            except Exception:
                pass
            # Show system tray notification
            if self.system_tray:
                self.system_tray.show_message("Blink - Connection Error", error_msg, QSystemTrayIcon.MessageIcon.Warning)
            return False
        except LLMAuthError as e:
            error_msg = str(e)
            logger.streaming_error("llm_auth_error", error_msg)
            try:
                self.overlay_ui.append_signal.emit(f"\n\n❌ Authentication Error: {error_msg}")
            except Exception:
                pass
            # Show system tray notification
            if self.system_tray:
                self.system_tray.show_message("Blink - Authentication Error", error_msg, QSystemTrayIcon.MessageIcon.Warning)
            return False
        except LLMConfigError as e:
            error_msg = str(e)
            logger.streaming_error("llm_config_error", error_msg)
            try:
                self.overlay_ui.append_signal.emit(f"\n\n❌ Configuration Error: {error_msg}")
            except Exception:
                pass
            # Show system tray notification
            if self.system_tray:
                self.system_tray.show_message("Blink - Configuration Error", error_msg, QSystemTrayIcon.MessageIcon.Warning)
            return False
        except Exception as e:
            logger.streaming_error("popup_error", str(e))
            try:
                self.overlay_ui.append_signal.emit(f"\n\n❌ Error: {str(e)}")
            except Exception:
                pass
            return False

    def _process_clipboard_direct_stream(self, messages: list[dict[str, str]], user_prompt: Union[str, List[Dict]], is_multimodal: bool) -> bool:
        """
        Processes clipboard context query in direct stream mode with error handling.

        Args:
            messages: List of messages to send to LLM
            user_prompt: The original user prompt (string or list for multimodal)
            is_multimodal: Whether the prompt contains image data

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
                    # For multimodal prompts, convert to a text representation for history
                    if is_multimodal:
                        user_text = "Multimodal query with image and instruction"
                    else:
                        user_text = user_prompt if isinstance(user_prompt, str) else str(user_prompt)
                    
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

    def _process_clipboard_popup(self, messages: list[dict[str, str]], user_prompt: Union[str, List[Dict]], is_multimodal: bool) -> bool:
        """
        Processes clipboard context query in popup mode.

        Args:
            messages: List of messages to send to LLM
            user_prompt: The original user prompt (string or list for multimodal)
            is_multimodal: Whether the prompt contains image data

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
                # For multimodal prompts, convert to a text representation for history
                if is_multimodal:
                    user_text = "Multimodal query with image and instruction"
                else:
                    user_text = user_prompt if isinstance(user_prompt, str) else str(user_prompt)
                
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
