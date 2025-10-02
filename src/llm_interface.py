"""
LLM interface module for Blink.

Provides a unified interface for communicating with LLMs, supporting Ollama and cloud models.
"""

import json
import requests
import time
from typing import Callable, Optional
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

    def set_selected_model(self, model: str) -> None:
        """
        Sets the selected model for queries.

        Args:
            model (str): Model identifier (e.g., "ollama:llama3.2:latest" or "openai:gpt-4").
        """
        self.selected_model = model

    def query(self, messages: list[dict[str, str]], on_chunk: Callable[[str], None]) -> None:
        """
        Sends a query to the selected LLM and streams the response.

        Args:
            messages (list[dict[str, str]]): List of message dictionaries with 'role' and 'content' keys.
            on_chunk (Callable[[str], None]): Callback function called for each response chunk.
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

    def query_ollama(self, messages: list[dict[str, str]], on_chunk: Callable[[str], None], model: str = "llama3.2:latest") -> None:
        """
        Sends a query to Ollama and streams the response.

        Args:
            messages (list[dict[str, str]]): List of message dictionaries.
            on_chunk (Callable[[str], None]): Callback function called for each response chunk.
            model (str): Ollama model name.
        """
        url = f"{self.base_url}/api/chat"

        data = {
            "model": model,
            "messages": messages,
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

    def query_openai(self, messages: list[dict[str, str]], on_chunk: Callable[[str], None], model: str = "gpt-4") -> None:
        """
        Sends a query to OpenAI and streams the response.

        Args:
            messages (list[dict[str, str]]): List of message dictionaries.
            on_chunk (Callable[[str], None]): Callback function called for each response chunk.
            model (str): OpenAI model name.
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

    def query_gemini(self, messages: list[dict[str, str]], on_chunk: Callable[[str], None], model: str = "gemini-pro") -> None:
        """
        Sends a query to Google Gemini and streams the response.

        Args:
            messages (list[dict[str, str]]): List of message dictionaries.
            on_chunk (Callable[[str], None]): Callback function called for each response chunk.
            model (str): Gemini model name.
        """
        if not self.gemini_available:
            on_chunk("Error: Gemini client not configured. Please set API key in settings.")
            return

        try:
            # For Gemini, concatenate messages into a single prompt for now
            # TODO: Implement proper multi-turn conversation using chat sessions
            prompt_parts = []
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "system":
                    prompt_parts.append(f"System: {content}")
                elif role == "user":
                    prompt_parts.append(f"User: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")
            full_prompt = "\n\n".join(prompt_parts)

            gemini_model = genai.GenerativeModel(model)
            response = gemini_model.generate_content(full_prompt, stream=True)

            for chunk in response:
                if chunk.text:
                    on_chunk(chunk.text)

        except Exception as e:
            error_msg = f"Error communicating with Gemini: {e}"
            on_chunk(error_msg)

    def query_lmstudio(self, messages: list[dict[str, str]], on_chunk: Callable[[str], None], model: str = "local-model") -> None:
        """
        Sends a query to LM Studio and streams the response.

        Args:
            messages (list[dict[str, str]]): List of message dictionaries.
            on_chunk (Callable[[str], None]): Callback function called for each response chunk.
            model (str): LM Studio model name.
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
            models.extend(["openai:gpt-4", "openai:gpt-3.5-turbo"])
        if self.gemini_available:
            models.extend(["gemini:gemini-flash-latest", "gemini:gemini-flash-lite-latest"])

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
