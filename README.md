# Blink

Blink is a Windows application that allows users to quickly capture selected text and get AI-powered responses using a global hotkey.

## Features (MUS - Minimum Usable State)

- **Global Hotkey Listener**: Press `Ctrl + Shift + .` anywhere in Windows to trigger text capture.
- **Text Capture**: Captures selected text using clipboard manipulation.
- **Ollama Integration**: Sends captured text to a local Ollama instance for processing.
- **Streaming GUI Overlay**: Displays AI responses in real-time in a frameless window.
- **Copy Functionality**: Copy the full response to clipboard with a button click.
- **Overlay Dismissal**: Close the overlay with `Esc` key or close button.

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

The application will run in the background. Select text in any application and press `Ctrl + Shift + .` to see the AI response overlay.

## Project Structure

```
Blink/
├── docs/
│   ├── Project_Requirements.md
│   └── Coding_Guidelines.md
├── src/
│   ├── __main__.py
│   ├── config_manager.py
│   ├── hotkey_manager.py
│   ├── llm_interface.py
│   ├── overlay_ui.py
│   └── text_capturer.py
├── main.py
├── requirements.txt
└── README.md
```

## Architecture

The application follows a modular architecture with separate concerns:
- `hotkey_manager.py`: Global hotkey listening
- `text_capturer.py`: Text capture logic
- `llm_interface.py`: AI model communication
- `overlay_ui.py`: GUI overlay management
- `config_manager.py`: Configuration handling (for future use)

## Future Enhancements

- UI Automation for non-destructive text capture
- Cloud model support (OpenAI, etc.)
- System tray icon and settings
- Configuration persistence
- Insert response functionality
- Context-aware overlay positioning

## License

This project is for educational purposes.
