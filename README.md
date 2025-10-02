# Blink

Blink is a Windows application that allows users to quickly capture selected text and get AI-powered responses using global hotkeys. Features both direct text capture and clipboard context mode for two-part tasks like translation and summarization.

## Features

- **Global Hotkey Listener**: Press `Ctrl + Alt + .` anywhere in Windows to trigger text capture.
- **Clipboard Context Mode**: Press `Ctrl + Alt + /` to use clipboard content as context for selected text instructions.
- **Conversational Memory**: Maintains context across multiple queries for natural follow-up conversations.
- **Text Capture**: Captures selected text using clipboard manipulation.
- **Multi-Model Support**: Works with Ollama (local), OpenAI, Google Gemini, and LM Studio.
- **Streaming GUI Overlay**: Displays AI responses in real-time in a frameless window.
- **System Tray Controls**: Access settings and memory controls via the system tray icon.
- **Memory Management**: Enable/disable memory, adjust history length (5-200 messages), and clear history.

## Requirements

- Python 3.10+
- Local Ollama instance running (default: http://localhost:11434)
- Windows OS

## Installation

1. Clone or download the project.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Ensure Ollama is running with a model (e.g., `ollama run llama3.2:latest`).

## Usage

Run the application:
```bash
python main.py
```

Or as a module:
```bash
python -m src
```

The application will run in the background. Select text in any application and press `Ctrl + Alt + .` to see the AI response overlay.

### Clipboard Context Mode

For two-part tasks like translation, summarization, or analysis:

1. **Copy the subject text** to your clipboard (the content you want to process)
2. **Select the instruction text** in any application (e.g., "translate this to French" or "summarize this article")
3. **Press `Ctrl + Alt + /`** to combine them

The AI will execute your instruction on the clipboard content. For example:
- Clipboard: "Hello world" + Selection: "translate to Spanish" → "Hola mundo"
- Clipboard: Long article + Selection: "give me a 2-sentence summary" → Concise summary

This feature includes retry logic and works with all supported AI models and output modes.

### Memory Controls

Right-click the system tray icon to access memory settings:
- **Enable Memory**: Toggle conversational context on/off
- **Max Messages**: Adjust history length (5-200 messages)
- **Clear History**: Reset conversation history

Memory maintains context across queries, allowing natural follow-up conversations like "make it shorter" or "explain that in simple terms".

### Customizing AI Behavior

Access the settings dialog from the system tray to customize the AI's behavior:
- **System Prompt**: Define a custom system prompt to tailor the AI's personality, tone, and response format
- **Model Selection**: Choose from available AI models (Ollama, OpenAI, Gemini, LM Studio)
- **Output Mode**: Switch between popup overlay and direct streaming modes

The system prompt is automatically prepended to every conversation, allowing you to create specialized AI assistants for different tasks.

## Project Structure

```
Blink/
├── docs/
│   ├── Project_Requirements.md
│   └── Coding_Guidelines.md
├── src/
│   ├── __main__.py
│   ├── config_manager.py
│   ├── error_logger.py
│   ├── history_manager.py
│   ├── hotkey_manager.py
│   ├── llm_interface.py
│   ├── output_handler.py
│   ├── overlay_ui.py
│   ├── settings_dialog.py
│   ├── system_tray.py
│   └── text_capturer.py
├── main.py
├── requirements.txt
├── config.json
└── README.md
```

## Architecture

The application follows a modular architecture with separate concerns:
- `hotkey_manager.py`: Global hotkey listening and conversation flow
- `text_capturer.py`: Text capture logic
- `llm_interface.py`: AI model communication (Ollama, OpenAI, Gemini, LM Studio)
- `overlay_ui.py`: GUI overlay management
- `history_manager.py`: Conversational memory management
- `system_tray.py`: System tray icon and menu controls
- `config_manager.py`: Configuration persistence and settings
- `error_logger.py`: Error logging and debugging utilities

## Future Enhancements

- UI Automation for non-destructive text capture
- Insert response functionality
- Context-aware overlay positioning
- Advanced memory features (save/load conversations)
- Theme customization

## License

This project is for educational purposes.
