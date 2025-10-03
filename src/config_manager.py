"""
Configuration management module for Blink.

Handles loading and saving user settings, including error recovery options.
"""

import json
import os
from typing import Dict, Any, Optional

# Define the application name and the config file name
APP_NAME = "Blink"
CONFIG_FILE = "config.json"


def get_app_data_path():
    """Gets the path to the application's data folder in AppData/Roaming."""
    # os.getenv('APPDATA') is the reliable way to get this path
    app_data_dir = os.path.join(os.getenv('APPDATA'), APP_NAME)

    # Create the directory if it doesn't exist
    os.makedirs(app_data_dir, exist_ok=True)

    return app_data_dir


def get_config_path():
    """Gets the full path to the config.json file."""
    return os.path.join(get_app_data_path(), CONFIG_FILE)


class ConfigManager:
    """
    Manages application configuration settings.

    Attributes:
        config_path (str): Path to the configuration file.
        config (Dict[str, Any]): Dictionary holding configuration data.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initializes the ConfigManager.

        Args:
            config_path (Optional[str]): Custom path to config file. If None, uses default path.
        """
        self.config_path = config_path or get_config_path()
        self.config: Dict[str, Any] = {}
        self.load_config()
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        """
        Ensures default configuration values exist.
        """
        defaults = {
            "output_mode": "popup",
            "enable_error_logging": True,
            "log_to_file": False,
            "log_file_path": "blink_errors.log",
            "streaming_timeout": 120,  # seconds
            "enable_retry": True,
            "max_retries": 5,
            "clipboard_context_hotkey": "ctrl+alt+/",
            "memory_enabled": True,
            "memory_max_messages": 50,
            # New settings for OCR and multimodal support
            "tesseract_cmd": "",  # Custom path to tesseract.exe
            "multimodal_models": {
                "gemini": True,
                "gpt-4-vision": True,
                "gpt-4o": True,
                "claude-3": True,
                "llava": True
            },
            # Notification settings
            "enable_notifications": True
        }
        
        changed = False
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
                changed = True
        
        if changed:
            self.save_config()

    def load_config(self) -> None:
        """
        Loads configuration from the file if it exists.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}")
                self.config = {}

    def save_config(self) -> None:
        """
        Saves the current configuration to the file.
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Gets a configuration value.

        Args:
            key (str): The configuration key.
            default (Any): Default value if key not found.

        Returns:
            Any: The configuration value.
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Sets a configuration value.

        Args:
            key (str): The configuration key.
            value (Any): The value to set.
        """
        self.config[key] = value
        self.save_config()
    
    def is_multimodal_model(self, full_model_name: str) -> bool:
        """
        Enhanced multimodal detection supporting local model heuristics.

        Args:
            full_model_name (str): Full model identifier (e.g., "ollama:llava" or "openai:gpt-4o")

        Returns:
            bool: True if the model is multimodal, False otherwise.
        """
        # Handle full model identifiers like "ollama:llava" or "openai:gpt-4o"
        if ":" in full_model_name:
            provider, model_id = full_model_name.split(":", 1)
            model_id_lower = model_id.lower()

            # Local models: use name heuristics
            if provider == "ollama":
                vision_keywords = ["llava", "moondream", "bakllava", "vision", "cogvlm", "llama-vision", "gemma"]
                return any(kw in model_id_lower for kw in vision_keywords)
            elif provider == "lmstudio":
                # LM Studio models often mirror HuggingFace names
                vision_keywords = ["llava", "moondream", "vision", "bakllava", "gemma"]
                return any(kw in model_id_lower for kw in vision_keywords)

            # Cloud models: fall through to legacy check using model_id
            model_name_to_check = model_id
        else:
            model_name_to_check = full_model_name

        # Legacy fallback for cloud models (gemini, gpt-4o, etc.)
        multimodal_models = self.get("multimodal_models", {})
        model_name_lower = model_name_to_check.lower()
        if model_name_lower in multimodal_models:
            return multimodal_models[model_name_lower]
        for model_key in multimodal_models:
            if model_key in model_name_lower:
                return multimodal_models[model_key]
        return False
    
    def get_current_model_is_multimodal(self) -> bool:
        """Determines if the currently selected model is multimodal using heuristics."""
        selected_model = self.get("selected_model", "ollama:llama3.2:latest")
        return self.is_multimodal_model(selected_model)

    def get_tesseract_cmd(self) -> str:
        """
        Gets the Tesseract command path.

        Returns:
            str: Path to tesseract.exe or empty string if not set.
        """
        return self.get("tesseract_cmd", "")

    def get_app_data_path(self) -> str:
        """
        Gets the path to the application's data folder in AppData/Roaming.

        Returns:
            str: Path to the app data directory.
        """
        return get_app_data_path()
