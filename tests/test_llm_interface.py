"""
Tests for llm_interface.py
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.llm_interface import LLMInterface, LLMConnectionError, LLMAuthError, LLMConfigError


class TestLLMInterface:
    """Test cases for LLMInterface class."""

    def test_init_default(self):
        """Test initialization with default parameters."""
        interface = LLMInterface()

        assert interface.base_url == "http://localhost:11434"
        assert interface.lmstudio_base_url == "http://localhost:1234"
        assert interface.selected_model == "ollama:llama3.2:latest"

    @patch('src.llm_interface.requests.post')
    def test_query_ollama_success(self, mock_post):
        """Test successful Ollama query with mocked response."""
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'{"message": {"content": "Hello"}, "done": false}',
            b'{"message": {"content": " world"}, "done": false}',
            b'{"message": {"content": "!"}, "done": true}'
        ]
        mock_post.return_value = mock_response

        interface = LLMInterface()
        chunks = []

        def on_chunk(chunk):
            chunks.append(chunk)

        messages = [{"role": "user", "content": "Say hello"}]
        interface.query_ollama(messages, on_chunk, "llama3.2:latest")

        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/chat"

        # Check the JSON payload
        payload = call_args[1]['json']
        assert payload['model'] == "llama3.2:latest"
        assert payload['messages'] == messages
        assert payload['stream'] is True

        # Check the chunks received
        assert chunks == ["Hello", " world", "!"]

    @patch('src.llm_interface.requests.post')
    def test_query_ollama_connection_error(self, mock_post):
        """Test Ollama query with connection error."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        interface = LLMInterface()

        with pytest.raises(LLMConnectionError) as exc_info:
            interface.query_ollama([{"role": "user", "content": "test"}], lambda x: None)

        assert "Could not connect to Ollama server" in str(exc_info.value)

    @patch('src.llm_interface.requests.post')
    def test_query_ollama_timeout(self, mock_post):
        """Test Ollama query with timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        interface = LLMInterface()

        with pytest.raises(LLMConnectionError) as exc_info:
            interface.query_ollama([{"role": "user", "content": "test"}], lambda x: None)

        assert "Connection to Ollama server timed out" in str(exc_info.value)

    @patch('src.llm_interface.requests.post')
    def test_query_ollama_auth_error(self, mock_post):
        """Test Ollama query with authentication error."""
        import requests
        mock_response = Mock()
        mock_response.status_code = 401
        http_error = requests.HTTPError("401 Unauthorized")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        interface = LLMInterface()

        with pytest.raises(LLMAuthError) as exc_info:
            interface.query_ollama([{"role": "user", "content": "test"}], lambda x: None)

        assert "Authentication failed with Ollama server" in str(exc_info.value)

    @patch('src.llm_interface.requests.post')
    def test_query_ollama_http_error(self, mock_post):
        """Test Ollama query with HTTP error."""
        import requests
        mock_response = Mock()
        mock_response.status_code = 500
        http_error = requests.HTTPError("500 Internal Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        interface = LLMInterface()

        with pytest.raises(LLMConnectionError) as exc_info:
            interface.query_ollama([{"role": "user", "content": "test"}], lambda x: None)

        assert "Ollama server error: 500" in str(exc_info.value)

    @patch('src.llm_interface.requests.post')
    def test_query_ollama_malformed_json(self, mock_post):
        """Test Ollama query with malformed JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'{malformed json}',
            b'{"message": {"content": "good"}, "done": true}'
        ]
        mock_post.return_value = mock_response

        interface = LLMInterface()
        chunks = []

        def on_chunk(chunk):
            chunks.append(chunk)

        # Should not crash on malformed JSON, just skip it
        interface.query_ollama([{"role": "user", "content": "test"}], on_chunk)

        # Should still get the valid chunk
        assert "good" in chunks

    def test_query_openai_success(self):
        """Test successful OpenAI query."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_stream = Mock()

        # Create mock chunks with proper structure
        mock_chunk1 = Mock()
        mock_choice1 = Mock()
        mock_delta1 = Mock()
        mock_delta1.content = "Hello"
        mock_choice1.delta = mock_delta1
        mock_chunk1.choices = [mock_choice1]

        mock_chunk2 = Mock()
        mock_choice2 = Mock()
        mock_delta2 = Mock()
        mock_delta2.content = " world"
        mock_choice2.delta = mock_delta2
        mock_chunk2.choices = [mock_choice2]

        mock_chunk3 = Mock()
        mock_choice3 = Mock()
        mock_delta3 = Mock()
        mock_delta3.content = None
        mock_choice3.delta = mock_delta3
        mock_chunk3.choices = [mock_choice3]

        mock_stream.__iter__ = Mock(return_value=iter([mock_chunk1, mock_chunk2, mock_chunk3]))
        mock_client.chat.completions.create.return_value = mock_stream

        # Mock config manager
        mock_config = Mock()
        mock_config.get.return_value = "test-key"

        interface = LLMInterface(config_manager=mock_config)
        interface.openai_client = mock_client

        chunks = []
        def on_chunk(chunk):
            chunks.append(chunk)

        messages = [{"role": "user", "content": "Say hello"}]
        interface.query_openai(messages, on_chunk, "gpt-4")

        # Verify the call
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=messages,
            stream=True
        )

        # Check chunks
        assert chunks == ["Hello", " world"]

    def test_query_openai_no_client(self):
        """Test OpenAI query without configured client."""
        interface = LLMInterface()

        with pytest.raises(LLMConfigError) as exc_info:
            interface.query_openai([{"role": "user", "content": "test"}], lambda x: None)

        assert "OpenAI client not configured" in str(exc_info.value)

    @patch('src.llm_interface.requests.get')
    def test_get_available_models_ollama(self, mock_get):
        """Test getting available models from Ollama."""
        # Mock Ollama response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.2:latest"},
                {"name": "codellama:7b"}
            ]
        }
        mock_get.return_value = mock_response

        interface = LLMInterface()
        models = interface.get_available_models()

        assert "ollama:llama3.2:latest" in models
        assert "ollama:codellama:7b" in models

    @patch('src.llm_interface.requests.get')
    def test_get_available_models_ollama_fallback(self, mock_get):
        """Test fallback when Ollama API fails."""
        import requests
        mock_get.side_effect = requests.RequestException("Connection failed")

        interface = LLMInterface()
        models = interface.get_available_models()

        # Should have fallback models
        assert "ollama:llama3.2:latest" in models
        assert "ollama:llama2:latest" in models

    def test_set_selected_model(self):
        """Test setting selected model."""
        interface = LLMInterface()

        interface.set_selected_model("ollama:codellama:latest")
        assert interface.selected_model == "ollama:codellama:latest"

    def test_query_dispatch(self):
        """Test that query method dispatches to correct handler."""
        interface = LLMInterface()

        # Test Ollama dispatch
        interface.set_selected_model("ollama:test")
        with patch.object(interface, 'query_ollama') as mock_ollama:
            interface.query([], lambda x: None)
            mock_ollama.assert_called_once()

        # Test OpenAI dispatch
        interface.set_selected_model("openai:gpt-4")
        with patch.object(interface, 'query_openai') as mock_openai:
            interface.query([], lambda x: None)
            mock_openai.assert_called_once()

        # Test Gemini dispatch
        interface.set_selected_model("gemini:test")
        with patch.object(interface, 'query_gemini') as mock_gemini:
            interface.query([], lambda x: None)
            mock_gemini.assert_called_once()

        # Test LM Studio dispatch
        interface.set_selected_model("lmstudio:test")
        with patch.object(interface, 'query_lmstudio') as mock_lmstudio:
            interface.query([], lambda x: None)
            mock_lmstudio.assert_called_once()

        # Test unknown model
        interface.set_selected_model("unknown:test")
        chunks = []
        def on_chunk(chunk):
            chunks.append(chunk)

        interface.query([], on_chunk)
        assert chunks == ["Error: Unsupported model type"]
