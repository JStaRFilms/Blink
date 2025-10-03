"""
LLM interface module for Blink.

Provides a unified interface for communicating with LLMs, supporting Ollama and cloud models.
"""

import json
import requests
import time
import base64
from typing import Callable, Optional, Dict, Any, List, Union
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .file_reader import FileReader
from .clipboard_manager import ClipboardManager


class LLMConnectionError(Exception):
    """Raised when unable to connect to an LLM service."""
    pass


class LLMAuthError(Exception):
    """Raised when authentication fails with an LLM service."""
    pass


class LLMConfigError(Exception):
    """Raised when LLM configuration is invalid."""
    pass


class LLMInterface:
    """
    Interface for interacting with Large Language Models.

    Supports Ollama (local), OpenAI (cloud), and Google Gemini (cloud) models.
    """

    def __init__(self, base_url: str = "http://localhost:11434", config_manager: Optional['ConfigManager'] = None) -> None:
        """
        Initializes the LLMInterface.

        Args:
            base_url (str): Base URL for the LLM API. Defaults to Ollama's default.
            config_manager: Configuration manager for API keys and settings.
        """
        self.base_url = base_url
        self.lmstudio_base_url = "http://localhost:1234"  # LM Studio default
        self.config_manager = config_manager
        self.selected_model = "ollama:llama3.2:latest"  # Default model
        self._cached_models: Optional[list[str]] = None
        self._models_cache_time: Optional[float] = None
        self._cache_timeout = 300  # Cache models for 5 minutes

        if OPENAI_AVAILABLE and self.config_manager:
            api_key = self.config_manager.get("openai_api_key")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
            else:
                self.openai_client = None
        else:
            self.openai_client = None

        if GEMINI_AVAILABLE and self.config_manager:
            api_key = self.config_manager.get("gemini_api_key")
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_available = True
            else:
                self.gemini_available = False
        else:
            self.gemini_available = False

        self.file_reader = FileReader(self.config_manager)

    def set_selected_model(self, model: str) -> None:
        """
        Sets the selected model for queries.

        Args:
            model (str): Model identifier (e.g., "ollama:llama3.2:latest" or "openai:gpt-4").
        """
        self.selected_model = model

    def is_multimodal(self) -> bool:
        """
        Checks if the current selected model supports multimodal input.
        
        Returns:
            bool: True if the model is multimodal, False otherwise.
        """
        if not self.config_manager:
            return False
            
        model_name = self.selected_model.split(":", 1)[1] if ":" in self.selected_model else self.selected_model
        return self.config_manager.is_multimodal_model(model_name)

    def query(self, messages: List[Dict[str, Union[str, List[Dict[str, Any]]]]], on_chunk: Callable[[str], None]) -> None:
        """
        Sends a query to the selected LLM and streams the response.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
                      Content can be a string or a list of content items (for multimodal).
            on_chunk: Callback function called for each response chunk.
        """
        if self.selected_model.startswith("ollama:"):
            model_name = self.selected_model.split(":", 1)[1]
            self.query_ollama(messages, on_chunk, model_name)
        elif self.selected_model.startswith("openai:"):
            model_name = self.selected_model.split(":", 1)[1]
            self.query_openai(messages, on_chunk, model_name)
        elif self.selected_model.startswith("gemini:"):
            model_name = self.selected_model.split(":", 1)[1]
            self.query_gemini(messages, on_chunk, model_name)
        elif self.selected_model.startswith("lmstudio:"):
            model_name = self.selected_model.split(":", 1)[1]
            self.query_lmstudio(messages, on_chunk, model_name)
        else:
            on_chunk("Error: Unsupported model type")

    def query_ollama(self, messages: List[Dict[str, Union[str, List[Dict[str, Any]]]]], 
                    on_chunk: Callable[[str], None], model: str = "llama3.2:latest") -> None:
        """
        Sends a query to Ollama and streams the response.

        Args:
            messages: List of message dictionaries.
            on_chunk: Callback function called for each response chunk.
            model: Ollama model name.
        """
        url = f"{self.base_url}/api/chat"

        # Process messages to handle multimodal content
        processed_messages = []
        for message in messages:
            if isinstance(message.get("content"), list):
                # For multimodal content, convert to Ollama format
                content_list = message["content"]
                text_parts = []
                images = []
                
                for item in content_list:
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "image_url":
                        # Extract base64 image data
                        image_url = item.get("image_url", {}).get("url", "")
                        if image_url.startswith("data:image/"):
                            # Remove data:image/...;base64, prefix
                            base64_data = image_url.split(",", 1)[1]
                            images.append(base64_data)
                
                processed_message = {
                    "role": message.get("role"),
                    "content": " ".join(text_parts),
                    "images": images
                }
                processed_messages.append(processed_message)
            else:
                # Regular text message
                processed_messages.append(message)

        data = {
            "model": model,
            "messages": processed_messages,
            "stream": True
        }

        try:
            response = requests.post(url, json=data, stream=True, timeout=10)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    try:
                        chunk_data = json.loads(line_str)
                        chunk = chunk_data.get("message", {}).get("content", "")
                        if chunk:
                            on_chunk(chunk)
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines

        except requests.exceptions.ConnectionError:
            raise LLMConnectionError("Could not connect to Ollama server. Please ensure Ollama is running.")
        except requests.exceptions.Timeout:
            raise LLMConnectionError("Connection to Ollama server timed out.")
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise LLMAuthError("Authentication failed with Ollama server.")
            else:
                raise LLMConnectionError(f"Ollama server error: {e.response.status_code}")
        except requests.RequestException as e:
            raise LLMConnectionError(f"Network error communicating with Ollama: {e}")

    def query_openai(self, messages: List[Dict[str, Union[str, List[Dict[str, Any]]]]], 
                    on_chunk: Callable[[str], None], model: str = "gpt-4") -> None:
        """
        Sends a query to OpenAI and streams the response.

        Args:
            messages: List of message dictionaries.
            on_chunk: Callback function called for each response chunk.
            model: OpenAI model name.
        """
        if not self.openai_client:
            raise LLMConfigError("OpenAI client not configured. Please set API key in settings.")

        try:
            stream = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    on_chunk(chunk.choices[0].delta.content)

        except Exception as e:
            # Check for authentication errors
            error_str = str(e).lower()
            if "authentication" in error_str or "api key" in error_str or "unauthorized" in error_str:
                raise LLMAuthError("Invalid OpenAI API key. Please check your settings.")
            else:
                raise LLMConnectionError(f"Error communicating with OpenAI: {e}")

    def query_gemini(self, messages: List[Dict[str, Union[str, List[Dict[str, Any]]]]], 
                    on_chunk: Callable[[str], None], model: str = "gemini-pro") -> None:
        """
        Sends a query to Google Gemini and streams the response.

        Args:
            messages: List of message dictionaries.
            on_chunk: Callback function called for each response chunk.
            model: Gemini model name.
        """
        if not self.gemini_available:
            on_chunk("Error: Gemini client not configured. Please set API key in settings.")
            return

        try:
            # Process messages to handle multimodal content
            contents = []
            for message in messages:
                role = message.get("role")
                content = message.get("content")
                
                if role == "system":
                    # System messages in Gemini are added as a user message with a prefix
                    if isinstance(content, str):
                        contents.append({"role": "user", "parts": [{"text": f"System: {content}"}]})
                    else:
                        # For multimodal system messages, convert to text
                        text_parts = []
                        for item in content:
                            if item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                        contents.append({"role": "user", "parts": [{"text": f"System: {' '.join(text_parts)}"}]})
                elif role == "user":
                    if isinstance(content, str):
                        contents.append({"role": "user", "parts": [{"text": content}]})
                    else:
                        # Multimodal content
                        parts = []
                        for item in content:
                            if item.get("type") == "text":
                                parts.append({"text": item.get("text", "")})
                            elif item.get("type") == "image_url":
                                # Extract base64 image data
                                image_url = item.get("image_url", {}).get("url", "")
                                if image_url.startswith("data:image/"):
                                    # Extract MIME type and base64 data
                                    mime_type = image_url.split(":", 1)[1].split(";", 1)[0]
                                    base64_data = image_url.split(",", 1)[1]
                                    import base64
                                    image_data = base64.b64decode(base64_data)
                                    parts.append({"inline_data": {"mime_type": mime_type, "data": image_data}})
                        contents.append({"role": "user", "parts": parts})
                elif role == "assistant":
                    if isinstance(content, str):
                        contents.append({"role": "model", "parts": [{"text": content}]})
                    else:
                        # For multimodal assistant messages, convert to text
                        text_parts = []
                        for item in content:
                            if item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                        contents.append({"role": "model", "parts": [{"text": " ".join(text_parts)}]})

            # Start chat with Gemini
            gemini_model = genai.GenerativeModel(model)
            chat = gemini_model.start_chat(history=contents[:-1])
            
            # Send the last message and stream the response
            response = chat.send_message(contents[-1]["parts"], stream=True)

            for chunk in response:
                if chunk.text:
                    on_chunk(chunk.text)

        except Exception as e:
            error_msg = f"Error communicating with Gemini: {e}"
            on_chunk(error_msg)

    def query_lmstudio(self, messages: List[Dict[str, Union[str, List[Dict[str, Any]]]]], 
                      on_chunk: Callable[[str], None], model: str = "local-model") -> None:
        """
        Sends a query to LM Studio and streams the response.

        Args:
            messages: List of message dictionaries.
            on_chunk: Callback function called for each response chunk.
            model: LM Studio model name.
        """
        try:
            # Create OpenAI client for LM Studio (OpenAI-compatible API)
            lmstudio_client = OpenAI(base_url=self.lmstudio_base_url + "/v1", api_key="not-needed")

            stream = lmstudio_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    on_chunk(chunk.choices[0].delta.content)

        except Exception as e:
            error_msg = f"Error communicating with LM Studio: {e}"
            on_chunk(error_msg)

    def get_available_models(self) -> list[str]:
        """
        Returns a list of available models with caching to improve performance.

        Returns:
            list[str]: List of model identifiers.
        """
        current_time = time.time()

        # Return cached models if they're still valid
        if (self._cached_models is not None and
            self._models_cache_time is not None and
            current_time - self._models_cache_time < self._cache_timeout):
            return self._cached_models.copy()

        # Fetch fresh model list
        models = []

        # Fetch Ollama models dynamically
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)  # Reduced timeout
            if response.status_code == 200:
                data = response.json()
                ollama_models = data.get("models", [])
                for model in ollama_models:
                    models.append(f"ollama:{model['name']}")
            else:
                # Fallback to hardcoded if API fails
                models.extend(["ollama:llama3.2:latest", "ollama:llama2:latest"])
        except requests.RequestException:
            # Fallback if Ollama not running
            models.extend(["ollama:llama3.2:latest", "ollama:llama2:latest"])

        # Fetch LM Studio models dynamically
        try:
            response = requests.get(f"{self.lmstudio_base_url}/v1/models", timeout=2)  # Reduced timeout
            if response.status_code == 200:
                data = response.json()
                lmstudio_models = data.get("data", [])
                for model in lmstudio_models:
                    models.append(f"lmstudio:{model['id']}")
        except requests.RequestException:
            # LM Studio not running, skip
            pass

        # Add cloud models if configured
        if self.openai_client:
            models.extend([
                "openai:gpt-5",
                "openai:gpt-5-mini",
                "openai:gpt-5-nano",
                "openai:gpt-5-chat-latest",
                "openai:gpt-5-thinking",
                "openai:gpt-5-thinking-mini",
                "openai:gpt-5-thinking-nano",
                "openai:gpt-5-main",
                "openai:gpt-5-main-mini",
                # keep older / fallback models too
                "openai:gpt-4.1",
                "openai:gpt-4o",
                "openai:gpt-3.5-turbo",
            ])
            
        if self.gemini_available:
            models.extend([
                "gemini:gemini-2.5-pro",    # strongest reasoning model :contentReference[oaicite:6]{index=6}  
                "gemini:gemini-2.5-flash",  # balanced speed / cost model :contentReference[oaicite:7]{index=7} 
                "gemini:gemini-flash-latest",   # balanced speed / cost model :contentReference[oaicite:7]{index=7}
                "gemini:gemini-2.5-flash-lite", # lightweight fast version (preview) :contentReference[oaicite:8]{index=8}  
                "gemini:gemini-flash-lite-latest",  # lightweight fast version (preview) :contentReference[oaicite:9]{index=9}  
                "gemini:gemini-2.5-flash-image-preview",    # for image/visual capabilities :contentReference[oaicite:10]{index=10}  
            ])

        # Cache the results
        self._cached_models = models.copy()
        self._models_cache_time = current_time

        return models

    def refresh_models_cache(self) -> None:
        """
        Forces a refresh of the cached model list.
        """
        self._cached_models = None
        self._models_cache_time = None

    def query_with_context(self, clipboard_items: List[Dict[str, str]], user_query: str, on_chunk: Callable[[str], None]) -> None:
        """Adaptive query router based on multimodal capability."""
        if not self.config_manager:
            on_chunk("Error: Config manager not available")
            return

        is_multimodal = self.config_manager.get_current_model_is_multimodal()
        system_prompt = self.config_manager.get("system_prompt", "").strip()
        system_messages = [{"role": "system", "content": system_prompt}] if system_prompt else []

        memory_enabled = self.config_manager.get("memory_enabled", True)
        if memory_enabled:
            from .history_manager import get_conversation_history
            history_manager = get_conversation_history(self.config_manager)
            current_history = history_manager.get_history()
        else:
            current_history = []

        if is_multimodal:
            # Multimodal path: preserve images as base64, docs as text
            content_parts = []
            if user_query.strip():
                content_parts.append({"type": "text", "text": user_query})

            for item in clipboard_items:
                if item["type"] == "document":
                    try:
                        text = self.file_reader.read_text_from_file(item["path"])
                        if text.strip():
                            content_parts.append({"type": "text", "text": text})
                    except Exception as e:
                        content_parts.append({"type": "text", "text": f"[Error reading {item['path']}: {e}]"})
                elif item["type"] == "image":
                    try:
                        if item["path"] == "__clipboard_image__":
                            image = ClipboardManager().get_image_from_clipboard()
                            if image:
                                encoded, mime = self.file_reader.get_pil_image_data(image)
                            else:
                                raise ValueError("No image on clipboard")
                        else:
                            encoded, mime = self.file_reader.get_image_data(item["path"])
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{encoded}"}
                        })
                    except Exception as e:
                        content_parts.append({"type": "text", "text": f"[Error processing image {item['path']}: {e}]"})
                elif item["type"] == "text":
                    content_parts.append({"type": "text", "text": item["content"]})

            user_message = {"role": "user", "content": content_parts}
            messages_to_send = system_messages + current_history + [user_message]

        else:
            # Text-only path: OCR images, extract text from docs
            all_text = []
            if user_query.strip():
                all_text.append(f"Instruction:\n{user_query}\n\nContext:\n")

            for item in clipboard_items:
                try:
                    if item["type"] == "document":
                        text = self.file_reader.read_text_from_file(item["path"])
                    elif item["type"] == "image":
                        if item["path"] == "__clipboard_image__":
                            image = ClipboardManager().get_image_from_clipboard()
                            text = self.file_reader.read_text_from_image(image) if image else "[No image]"
                        else:
                            text = self.file_reader.extract_text_from_image(item["path"])
                    elif item["type"] == "text":
                        text = item["content"]
                    else:
                        text = ""
                    if text.strip():
                        all_text.append(text)
                except Exception as e:
                    all_text.append(f"[Error processing {item.get('path', 'item')}: {e}]")

            full_prompt = "\n---\n".join(all_text)
            user_message = {"role": "user", "content": full_prompt}
            messages_to_send = system_messages + current_history + [user_message]

        self.query(messages_to_send, on_chunk)
