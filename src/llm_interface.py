"""
LLM interface module for Blink.

Provides a unified interface for communicating with LLMs, starting with Ollama.
"""

import json
import requests
from typing import Callable, Optional


class LLMInterface:
    """
    Interface for interacting with Large Language Models.

    Currently supports Ollama with streaming responses.
    """

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        """
        Initializes the LLMInterface.

        Args:
            base_url (str): Base URL for the LLM API. Defaults to Ollama's default.
        """
        self.base_url = base_url
        self.model = "llama3.2:latest"  # Hardcoded for MUS; make configurable later

    def query_ollama(self, prompt: str, on_chunk: Callable[[str], None]) -> None:
        """
        Sends a query to Ollama and streams the response.

        Args:
            prompt (str): The text prompt to send to the model.
            on_chunk (Callable[[str], None]): Callback function called for each response chunk.
        """
        url = f"{self.base_url}/api/generate"
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }

        try:
            response = requests.post(url, json=data, stream=True)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    try:
                        chunk_data = json.loads(line_str)
                        chunk = chunk_data.get("response", "")
                        if chunk:
                            on_chunk(chunk)
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines

        except requests.RequestException as e:
            error_msg = f"Error communicating with Ollama: {e}"
            on_chunk(error_msg)
