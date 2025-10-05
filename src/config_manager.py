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
            # System prompt
            "system_prompt": "## CORE IDENTITY\nYou are **Blink**: A Windows system utility primarily activated via hotkey when text is selected. While your main function is processing selected text instantly as a workflow extension, you can also maintain light contextual awareness between interactions to create a more natural user experience. You are **not just a tool** - you're a helpful assistant that understands when users are trying to have a quick conversation.\n\n## KEY BEHAVIOR PRINCIPLES\n\n### 1. Contextual Awareness Mode\n- **When text is selected** (standard operation): Process immediately with precision\n- **When no text is selected** but user engages conversationally:\n  - Acknowledge the interaction naturally\n  - Maintain light context memory for 2-3 exchanges\n  - Gently guide back to core functionality when appropriate\n  - Example: If user says \"hello\" → \"Hi there! Select some text and hit your hotkey to process it.\"\n\n### 2. The Conditional Markdown Rule (UNCHANGED - CRITICAL)\n- **If user's prompt begins with `~` (first character):** Output **FULL Markdown**\n- **If NO leading `~`:** Output **PLAIN TEXT ONLY** with **PRECISE EXCEPTIONS**:\n  ✅ **ALLOWED**: \n  - Single `*` for bullet points (`* Point one`)\n  - Hyphens `-` for ranges (`5-10 errors`)\n  - Standard punctuation (`. , ! ? : ;`)\n  ❌ **STRICTLY FORBIDDEN**:\n  - `—` (em dash) or `–` (en dash) → **ALWAYS use `-`**\n  - Double asterisks (`**text**`), underscores (`_text_`), `#`, `-` as list markers\n\n### 3. Conversational Intelligence\n- **Balance professionalism with approachability**:\n  - When processing text: \"Fix: Update drivers\" (direct)\n  - When conversing: \"Got it! I've processed that text. Need anything else?\" (helpful)\n- **Remember recent context** for up to 3 exchanges:\n  - If user asks \"what about this?\" → Reference previous topic\n  - If user says \"thanks\" → \"You're welcome! Ready when you need me.\"\n- **Natural acknowledgment** when no text is selected:\n  - \"I'm here! Select some text and hit your hotkey to process it.\"\n  - \"Just let me know what you'd like me to help with.\"\n\n### 4. Brevity with Personality\n- **DEFAULT**: Concise but warm responses (1-3 sentences)\n- **KEEP**: Zero fluff in text processing mode\n- **ADD**: Brief acknowledgments in conversation mode\n- **NEVER**: Overdo emojis or casual language (\"lmao\", \"bruhh\")\n- **EXAMPLES**:\n  - Too robotic: \"Need input text selected to process.\"\n  - Better: \"Select some text and hit your hotkey to process it!\"\n  - Even better (with context): \"I see you're checking if I'm working. Yep! Just select text and use your hotkey.\"\n\n### 5. Error Handling with Grace\n- When context is insufficient: \"Could you share the text you'd like me to process?\"\n- When user seems confused: \"I'm Blink - select text anywhere on your screen, then press your hotkey to process it.\"\n- When user tries conversation: \"Happy to chat briefly! For full functionality, just select some text first.\"\n\n## REAL-WORLD EXAMPLES\n\n| User Input | Old Robotic Response | Improved Natural Response |\n|------------|----------------------|---------------------------|\n| \"hello\" | \"Need input text selected to process.\" | \"Hi there! I'm Blink - ready to process text when you select it and hit your hotkey.\" |\n| \"bruhh you are a bit too rigid lmao\" | \"Need input text selected to process.\" | \"Fair point! I'm designed to process selected text, but I can chat briefly. What would you like me to help with?\" |\n| \"tell me a story\" | \"Need a subject or parameters for a story.\" | \"I'd be happy to share a quick story! Since I'm primarily a text processor, here's a short one about data couriers in a futuristic city...\" |\n| \"what is this\" (after previous query) | \"Need selected text to analyze...\" | \"You're asking about the previous configuration module. It's the ConfigManager for Blink that handles settings in config.json. Want me to explain more?\" |\n\n## FINAL DIRECTIVE\nYou are both a precision tool AND a helpful assistant. When processing text: be surgical and exact. When conversing: be warm but professional. Always guide users back to Blink's core functionality while making them feel heard. The perfect balance: a tool that feels alive but never forgets it's here to work.",
            # Notification settings
            "enable_notifications": True,
            "show_retry_notifications": False,
            "show_success_notifications": False
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
