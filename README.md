# Blink

Blink is a Windows application that allows users to quickly capture selected text and get AI-powered responses using global hotkeys. Features both direct text capture and clipboard context mode for two-part tasks like translation and summarization.

## Features

- **Global Hotkey Listener**: Press `Ctrl + Alt + .` anywhere in Windows to trigger text capture.
- **Adaptive Multimodal Input**: Intelligent clipboard processing that automatically handles mixed content types (text, images, documents) and adapts based on AI model capabilities.
- **Clipboard Context Mode**: Press `Ctrl + Alt + /` to use clipboard content as context for selected text instructions - now supports images and documents!
- **OCR Support**: Automatic text extraction from images for text-only AI models when Tesseract is installed.
- **Conversational Memory**: Maintains context across multiple queries for natural follow-up conversations.
- **Text Capture**: Captures selected text using clipboard manipulation.
- **Multi-Model Support**: Works with Ollama (local), OpenAI, Google Gemini, and LM Studio with automatic multimodal capability detection.
- **Streaming GUI Overlay**: Displays AI responses in real-time in a frameless window.
- **System Tray Controls**: Access settings and memory controls via the system tray icon.
- **Memory Management**: Enable/disable memory, adjust history length (5-200 messages), and clear history.
- **Centralized Settings Window**: Comprehensive tabbed settings interface for all configuration options.
- **Graceful Error Handling**: Non-blocking system tray notifications for connection, authentication, and configuration errors.
- **System Startup Integration**: Option to automatically launch the application when Windows starts.

## Requirements

- Python 3.10+
- Local Ollama instance running (default: http://localhost:11434)
- Windows OS
- **Optional**: Tesseract OCR for image text extraction (see installation below)

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

### Adaptive Multimodal Input

Blink now intelligently handles mixed clipboard content types and adapts processing based on your AI model's capabilities:

#### Multimodal Models (Vision-Capable)
When using models like GPT-4 Vision, Gemini Pro, or Ollama Llava:
- **Images**: Sent directly as base64-encoded data to the AI
- **Documents**: Text content extracted and included
- **Mixed Content**: All content types combined in a single multimodal prompt

#### Text-Only Models (with OCR)
When using models like Llama3 or other text-only AIs:
- **Images**: Automatically processed with OCR to extract text (requires Tesseract)
- **Documents**: Text content extracted normally
- **Fallback**: Graceful handling when OCR is unavailable

#### Examples:
- **Copy an image** + select "describe this image" → AI analyzes the visual content
- **Copy a PDF** + select "summarize this document" → AI processes the text content
- **Copy multiple files** (image + document) → AI handles both appropriately
- **Copy screenshot** + select "extract the text from this image" → OCR extracts readable text

#### Tesseract OCR Installation (Optional)

For image text extraction with text-only models:

1. **Download Tesseract**:
   ```bash
   # Option 1: Windows Installer (Recommended)
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   # Run the installer - it adds Tesseract to your PATH automatically

   # Option 2: Chocolatey (if installed)
   choco install tesseract
   ```

2. **Verify Installation**:
   ```bash
   tesseract --version
   ```

3. **Custom Path** (if needed):
   - If Tesseract isn't in PATH, set `tesseract_cmd` in Blink settings to the full path to `tesseract.exe`
   - Usually: `C:\Program Files\Tesseract-OCR\tesseract.exe`

**Note**: OCR is completely optional - Blink works perfectly without it, but provides enhanced capabilities when Tesseract is available.

### Memory Controls

Right-click the system tray icon to access memory settings:
- **Enable Memory**: Toggle conversational context on/off
- **Max Messages**: Adjust history length (5-200 messages)
- **Clear History**: Reset conversation history

Memory maintains context across queries, allowing natural follow-up conversations like "make it shorter" or "explain that in simple terms".

### Settings and Configuration

Access the comprehensive settings window from the system tray icon. The settings are organized in three tabs:

#### General Tab
- **Output Mode**: Choose between "Popup Overlay" (displays responses in a window) or "Direct Stream" (types responses directly into your active application)
- **System Startup**: Enable/disable automatic launch when Windows starts (requires administrator privileges for Registry access)

#### Models Tab
- **API Keys**: Securely store API keys for OpenAI and Google Gemini
- **Model Selection**: Choose from available AI models (Ollama, OpenAI, Gemini, LM Studio)

#### Prompts Tab
- **System Prompt**: Define a custom system prompt to tailor the AI's personality, tone, and response format

### Error Handling

Blink includes robust error handling with user-friendly notifications:
- **Connection Errors**: Notified when Ollama or cloud services are unreachable
- **Authentication Errors**: Alerted when API keys are invalid
- **Configuration Errors**: Guided when settings need adjustment

All errors are displayed as non-blocking system tray notifications, ensuring the application never crashes unexpectedly.

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
│   ├── startup_manager.py
│   ├── system_tray.py
│   └── text_capturer.py
├── main.py
├── requirements.txt
├── config.json
└── README.md
```

## Testing

Blink includes comprehensive testing to ensure reliability and stability.

### Automated Tests

Run the automated test suite:
```bash
python run_tests.py
```

Or run pytest directly:
```bash
python -m pytest tests/ -v
```

The test suite covers:
- **Configuration Management**: Loading, saving, and default value handling
- **Conversation History**: Message storage, capacity limits, and memory management
- **LLM Interface**: Mocked API calls, error handling, and response parsing
- **Startup Manager**: Registry operations and executable path detection

### Manual Testing

Before releasing, perform manual testing using the comprehensive checklist in `docs/Manual_Testing_Checklist.md`. This covers edge cases, integration issues, and user experience validation that automated tests cannot catch.

Key areas tested manually:
- Hotkey behavior in various applications and environments
- Large text processing and Unicode handling
- Network failure scenarios
- GUI responsiveness and positioning
- Cross-platform compatibility

## Architecture

The application follows a modular architecture with separate concerns:
- `hotkey_manager.py`: Global hotkey listening and conversation flow
- `text_capturer.py`: Text capture logic
- `llm_interface.py`: AI model communication (Ollama, OpenAI, Gemini, LM Studio)
- `overlay_ui.py`: GUI overlay management
- `history_manager.py`: Conversational memory management
- `system_tray.py`: System tray icon and menu controls
- `settings_dialog.py`: Centralized settings window with tabbed interface
- `startup_manager.py`: Windows Registry operations for system startup integration
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
