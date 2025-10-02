"""
Tests for config_manager.py
"""

import json
import os
import tempfile
import pytest
from src.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_load_default_config(self):
        """Test loading default configuration."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name

        try:
            # Create empty config file
            with open(temp_file, 'w') as f:
                f.write('{}')

            # Initialize ConfigManager with temp file
            config = ConfigManager(temp_file)

            # Check that defaults are loaded
            assert config.get('output_mode') == 'popup'
            assert config.get('enable_error_logging') is True
            assert config.get('streaming_timeout') == 120
            assert config.get('memory_enabled') is True
            assert config.get('memory_max_messages') == 50

        finally:
            os.unlink(temp_file)

    def test_set_and_get_value(self):
        """Test setting and getting configuration values."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name

        try:
            # Create empty config file
            with open(temp_file, 'w') as f:
                f.write('{}')

            config = ConfigManager(temp_file)

            # Test setting a value
            config.set('output_mode', 'direct')
            assert config.get('output_mode') == 'direct'

            # Test setting another value
            config.set('streaming_timeout', 300)
            assert config.get('streaming_timeout') == 300

            # Test getting non-existent key with default
            assert config.get('non_existent_key', 'default_value') == 'default_value'

        finally:
            os.unlink(temp_file)

    def test_save_and_load_config(self):
        """Test saving to and loading from file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name

        try:
            # Create empty config file
            with open(temp_file, 'w') as f:
                f.write('{}')

            config1 = ConfigManager(temp_file)

            # Set some values
            config1.set('output_mode', 'direct')
            config1.set('streaming_timeout', 300)
            config1.set('custom_key', 'custom_value')

            # Create new instance to test loading
            config2 = ConfigManager(temp_file)

            # Verify values were saved and loaded
            assert config2.get('output_mode') == 'direct'
            assert config2.get('streaming_timeout') == 300
            assert config2.get('custom_key') == 'custom_value'

        finally:
            os.unlink(temp_file)

    def test_load_corrupted_config(self):
        """Test loading corrupted configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name

        try:
            # Write invalid JSON
            with open(temp_file, 'w') as f:
                f.write('{invalid json')

            config = ConfigManager(temp_file)

            # Should load defaults despite corrupted file
            assert config.get('output_mode') == 'popup'
            assert config.get('enable_error_logging') is True

        finally:
            os.unlink(temp_file)

    def test_load_nonexistent_config(self):
        """Test loading when config file doesn't exist."""
        # Use a non-existent file path
        nonexistent_file = r'C:\nonexistent\config.json'

        config = ConfigManager(nonexistent_file)

        # Should load defaults
        assert config.get('output_mode') == 'popup'
        assert config.get('enable_error_logging') is True

        # File should be created with defaults (but will fail on Windows with invalid path)
        # Just verify defaults are loaded
