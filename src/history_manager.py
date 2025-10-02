"""
History manager module for Blink.

Manages conversational memory using an in-memory capped deque.
"""

from collections import deque
from typing import List, Dict


class ConversationHistory:
    """
    Manages conversation history using a capped deque for memory efficiency.

    Stores the last N messages in the conversation, automatically
    dropping the oldest when the limit is exceeded.
    """

    def __init__(self, config_manager=None, maxlen: int = 50) -> None:
        """
        Initializes the conversation history.

        Args:
            config_manager: Configuration manager to get memory settings from.
            maxlen (int): Maximum number of messages to store. Defaults to 50.
                         For modern LLMs (256k-1M+ context), 50 messages provides
                         excellent context depth while keeping conversations focused
                         and relevant. Scales well from 256k to 1M+ token models.
        """
        self.config_manager = config_manager
        self._maxlen = maxlen
        self.history = deque(maxlen=self._get_maxlen())

    def _get_maxlen(self) -> int:
        """Gets the maximum length from config or default."""
        if self.config_manager:
            return self.config_manager.get("memory_max_messages", self._maxlen)
        return self._maxlen

    def update_maxlen(self) -> None:
        """Updates the maxlen if config changed."""
        new_maxlen = self._get_maxlen()
        if new_maxlen != self.history.maxlen:
            # Create new deque with updated maxlen and copy existing history
            current_history = list(self.history)
            self.history = deque(current_history, maxlen=new_maxlen)

    def add_message(self, role: str, content: str) -> None:
        """
        Adds a new message to the conversation history.

        Args:
            role (str): Role of the message sender ('user' or 'assistant').
            content (str): The message content.
        """
        message = {"role": role, "content": content}
        self.history.append(message)

    def get_history(self) -> List[Dict[str, str]]:
        """
        Returns a copy of the current conversation history.

        Returns:
            List[Dict[str, str]]: List of message dictionaries with 'role' and 'content' keys.
        """
        return list(self.history)

    def clear(self) -> None:
        """
        Clears all conversation history.
        """
        self.history.clear()

    def is_empty(self) -> bool:
        """
        Checks if the conversation history is empty.

        Returns:
            bool: True if no messages in history, False otherwise.
        """
        return len(self.history) == 0


# Singleton instance for the application - will be initialized with config later
conversation_history = None

def get_conversation_history(config_manager=None) -> ConversationHistory:
    """Gets or creates the conversation history singleton with config."""
    global conversation_history
    if conversation_history is None:
        conversation_history = ConversationHistory(config_manager=config_manager)
    elif config_manager and conversation_history.config_manager != config_manager:
        # Update config if different
        conversation_history.config_manager = config_manager
        conversation_history.update_maxlen()
    return conversation_history
