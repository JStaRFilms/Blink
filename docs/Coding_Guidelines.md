# Coding Guidelines for Blink

This document outlines the architecture, technology stack, and coding conventions for the Blink project. Adherence to these guidelines is mandatory for all development.

### 1. Architecture

The project will follow a **Modular Architecture**. The core functionalities are decoupled into distinct Python modules, each responsible for a single concern. This promotes separation of concerns, testability, and easier maintenance.

The primary modules will be:
- **`main.py`**: The entry point of the application. Initializes the system tray icon and starts the hotkey listener.
- **`hotkey_manager.py`**: Responsible for setting up and listening for the global hotkey (`Ctrl + Shift + .`). Dispatches events when the hotkey is pressed.
- **`text_capturer.py`**: Handles the logic for capturing selected text. Initially, this will use the "clipboard hack," but will later be refactored to use UI Automation.
- **`llm_interface.py`**: A unified interface for communicating with different LLMs. It will contain classes or functions for interacting with Ollama and, later, cloud models. It handles the streaming logic.
- **`overlay_ui.py`**: Manages the PyQt6 GUI overlay. This includes creating the window, displaying the streaming text, and handling user interactions like "Copy" or "Close."
- **`config_manager.py`**: (For future use) Handles loading and saving user settings.

### 2. Technology Stack

- **Language:** Python 3.10+
- **GUI Framework:** PyQt6
- **System-wide Hooks:** pynput
- **Clipboard Management:** pyperclip
- **HTTP Requests:** requests (for Ollama), openai (for OpenAI API)
- **Packaging:** PyInstaller (for creating a distributable `.exe`)

### 3. Project Directory Structure

The project will follow a standard Python application structure to ensure clarity and scalability.

```
/Blink
|
├── /docs
│   ├── Project_Requirements.md
│   └── Coding_Guidelines.md
|
├── /src
│   ├── /assets
│   │   └── icon.png
│   ├── __main__.py
│   ├── config_manager.py
│   ├── hotkey_manager.py
│   ├── llm_interface.py
│   ├── overlay_ui.py
│   └── text_capturer.py
|
├── requirements.txt
├── main.py
└── README.md
```

- **/docs**: Contains all project documentation.
- **/src**: The main source code directory.
- **src/assets**: For static assets like icons.
- **`main.py`**: The main script to launch the application.
- **`requirements.txt`**: Lists all Python package dependencies.

### 4. Coding Style & Conventions

- **Formatting:** All Python code MUST adhere to the **PEP 8** style guide. Use an autoformatter like `black` or `autopep8` to ensure consistency.
- **Naming Conventions:**
    - `snake_case` for variables, functions, and modules.
    - `PascalCase` for classes.
    - `UPPER_SNAKE_CASE` for constants.
- **Type Hinting:** All function signatures and variable declarations MUST include type hints. This is crucial for maintaining a large codebase.
- **Docstrings:** All modules, classes, and functions MUST have Google-style docstrings explaining their purpose, arguments, and return values.
- **Logging:** Use the built-in `logging` module for application logging instead of `print()` statements for debugging.
- **Error Handling:** Use specific exceptions where possible. Avoid broad `except Exception:` clauses.
