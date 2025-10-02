"""
Configuration management module for Blink.

Handles loading and saving user settings, including error recovery options.
"""

import json
import os
from typing import Dict, Any

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

    def __init__(self) -> None:
        """
        Initializes the ConfigManager.
        """
        self.config_path = get_config_path()
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
            "streaming_timeout": 300,  # seconds
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
            }
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
    
    def is_multimodal_model(self, model_name: str) -> bool:
        """
        Checks if a model supports multimodal input.
        
        Args:
            model_name (str): The model name to check.
            
        Returns:
            bool: True if the model is multimodal, False otherwise.
        """
        multimodal_models = self.get("multimodal_models", {})
        model_name_lower = model_name.lower()
        
        # Check for exact matches
        if model_name_lower in multimodal_models:
            return multimodal_models[model_name_lower]
        
        # Check for partial matches
        for model_key in multimodal_models:
            if model_key in model_name_lower:
                return multimodal_models[model_key]
                
        return False
    
    def get_tesseract_cmd(self) -> str:
        """
        Gets the Tesseract command path.
        
        Returns:
            str: Path to tesseract.exe or empty string if not set.
        """
        return self.get("tesseract_cmd", "")