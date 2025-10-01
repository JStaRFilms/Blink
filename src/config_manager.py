"""
Configuration management module for Blink.

Handles loading and saving user settings. For MUS, this is a placeholder
with basic structure for future expansion.
"""

import json
import os
from typing import Dict, Any


class ConfigManager:
    """
    Manages application configuration settings.

    Attributes:
        config_file (str): Path to the configuration file.
        config (Dict[str, Any]): Dictionary holding configuration data.
    """

    def __init__(self, config_file: str = "config.json") -> None:
        """
        Initializes the ConfigManager.

        Args:
            config_file (str): Path to the configuration file. Defaults to "config.json".
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """
        Loads configuration from the file if it exists.
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}")
                self.config = {}

    def save_config(self) -> None:
        """
        Saves the current configuration to the file.
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
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
