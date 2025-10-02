"""
Tests for history_manager.py
"""

import pytest
from src.history_manager import ConversationHistory, get_conversation_history


class TestConversationHistory:
    """Test cases for ConversationHistory class."""

    def test_add_message(self):
        """Test adding messages to history."""
        history = ConversationHistory(maxlen=10)

        # Add a user message
        history.add_message("user", "Hello")
        messages = history.get_history()

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"

        # Add an assistant message
        history.add_message("assistant", "Hi there!")
        messages = history.get_history()

        assert len(messages) == 2
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hi there!"

    def test_history_capacity(self):
        """Test that history is capped at maxlen."""
        maxlen = 3
        history = ConversationHistory(maxlen=maxlen)

        # Add messages up to capacity
        for i in range(maxlen):
            history.add_message("user", f"Message {i}")

        assert len(history.get_history()) == maxlen

        # Add one more message - should drop the oldest
        history.add_message("user", "Message overflow")

        messages = history.get_history()
        assert len(messages) == maxlen
        # First message should be gone
        assert messages[0]["content"] == "Message 1"
        assert messages[1]["content"] == "Message 2"
        assert messages[2]["content"] == "Message overflow"

    def test_clear_history(self):
        """Test clearing the conversation history."""
        history = ConversationHistory(maxlen=10)

        # Add some messages
        history.add_message("user", "Hello")
        history.add_message("assistant", "Hi")
        history.add_message("user", "How are you?")

        assert len(history.get_history()) == 3
        assert not history.is_empty()

        # Clear history
        history.clear()

        assert len(history.get_history()) == 0
        assert history.is_empty()

    def test_is_empty(self):
        """Test is_empty method."""
        history = ConversationHistory(maxlen=10)

        assert history.is_empty()

        history.add_message("user", "Hello")
        assert not history.is_empty()

        history.clear()
        assert history.is_empty()

    def test_update_maxlen(self):
        """Test updating maxlen when config changes."""
        # Create mock config manager
        class MockConfigManager:
            def __init__(self, max_messages):
                self.max_messages = max_messages

            def get(self, key, default=None):
                if key == "memory_max_messages":
                    return self.max_messages
                return default

        # Start with maxlen 5
        config = MockConfigManager(5)
        history = ConversationHistory(config_manager=config, maxlen=5)

        # Add 5 messages
        for i in range(5):
            history.add_message("user", f"Message {i}")

        assert len(history.get_history()) == 5

        # Update config to maxlen 3
        config.max_messages = 3
        history.update_maxlen()

        # Should now be capped at 3, keeping the most recent
        messages = history.get_history()
        assert len(messages) == 3
        assert messages[0]["content"] == "Message 2"
        assert messages[1]["content"] == "Message 3"
        assert messages[2]["content"] == "Message 4"

    def test_config_manager_integration(self):
        """Test integration with config manager."""
        class MockConfigManager:
            def get(self, key, default=None):
                if key == "memory_max_messages":
                    return 4
                return default

        config = MockConfigManager()
        history = ConversationHistory(config_manager=config)

        # Should use config value for maxlen
        assert history._get_maxlen() == 4

        # Add messages up to config limit
        for i in range(5):  # One more than limit
            history.add_message("user", f"Message {i}")

        assert len(history.get_history()) == 4  # Should be capped at 4


class TestConversationHistorySingleton:
    """Test cases for the singleton conversation history."""

    def test_singleton_behavior(self):
        """Test that get_conversation_history returns the same instance."""
        # Reset singleton for testing
        import src.history_manager
        src.history_manager.conversation_history = None

        history1 = get_conversation_history()
        history2 = get_conversation_history()

        assert history1 is history2

    def test_singleton_with_config(self):
        """Test singleton with config manager."""
        import src.history_manager
        src.history_manager.conversation_history = None

        class MockConfigManager:
            def get(self, key, default=None):
                if key == "memory_max_messages":
                    return 2
                return default

        config = MockConfigManager()

        history1 = get_conversation_history(config_manager=config)
        history2 = get_conversation_history(config_manager=config)

        assert history1 is history2
        assert history1._get_maxlen() == 2

        # Test updating config
        class NewMockConfigManager:
            def get(self, key, default=None):
                if key == "memory_max_messages":
                    return 3
                return default

        new_config = NewMockConfigManager()
        history3 = get_conversation_history(config_manager=new_config)

        assert history3 is history1  # Same instance
        assert history3.config_manager is new_config
        assert history3._get_maxlen() == 3
