"""
First-run setup wizard for Blink AI Assistant.

Provides intelligent configuration for new users, including:
- Local model runner detection (Ollama, LM Studio)
- API key setup for cloud providers
- Model suggestions and guidance
"""

import os
import sys
import subprocess
import webbrowser
import winreg
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QApplication, QWizard, QWizardPage, QLabel, QVBoxLayout, QHBoxLayout,
    QRadioButton, QLineEdit, QPushButton, QTextEdit, QButtonGroup,
    QMessageBox, QProgressBar, QCheckBox, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

from .config_manager import ConfigManager


class RunnerDetectionThread(QThread):
    """Thread to detect local model runners without blocking UI."""
    detection_complete = pyqtSignal(dict)

    def run(self):
        """Detect installed model runners and their status."""
        results = {
            'ollama': self._detect_ollama(),
            'lmstudio': self._detect_lmstudio()
        }
        self.detection_complete.emit(results)

    def _detect_ollama(self) -> Dict[str, Any]:
        """Detect Ollama installation and running models."""
        try:
            # Check if ollama command exists
            result = subprocess.run(['ollama', 'list'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse the output to get available models
                lines = result.stdout.strip().split('\n')
                models = []
                if len(lines) > 1:  # Skip header
                    for line in lines[1:]:
                        if line.strip():
                            parts = line.split()
                            if parts:
                                models.append(parts[0])

                return {
                    'installed': True,
                    'running': True,
                    'models': models,
                    'version': self._get_ollama_version()
                }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Check if installed but not running
        try:
            result = subprocess.run(['where', 'ollama'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return {
                    'installed': True,
                    'running': False,
                    'models': [],
                    'version': None
                }
        except subprocess.TimeoutExpired:
            pass

        return {'installed': False, 'running': False, 'models': [], 'version': None}

    def _detect_lmstudio(self) -> Dict[str, Any]:
        """Detect LM Studio installation."""
        # Common LM Studio installation paths
        paths = [
            os.path.expandvars(r'%LOCALAPPDATA%\LM-Studio'),
            os.path.expandvars(r'%APPDATA%\LM-Studio'),
            r'C:\Program Files\LM Studio',
            r'C:\Program Files (x86)\LM Studio',
            os.path.expandvars(r'%USERPROFILE%\AppData\Local\LM-Studio'),
            os.path.expandvars(r'%USERPROFILE%\AppData\Roaming\LM-Studio')
        ]

        for path in paths:
            if os.path.exists(path):
                return {'installed': True, 'path': path}

        # Also check if LM Studio process is running
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if 'lm studio' in proc.info['name'].lower() or 'lm-studio' in proc.info['name'].lower():
                    return {'installed': True, 'path': 'Running (path unknown)', 'running': True}
        except:
            pass

        return {'installed': False, 'path': None}

    def _get_ollama_version(self) -> Optional[str]:
        """Get Ollama version."""
        try:
            result = subprocess.run(['ollama', 'version'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except subprocess.TimeoutExpired:
            pass
        return None


class WelcomePage(QWizardPage):
    """Welcome page for the first-run wizard."""

    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to Blink! 🚀")
        self.setSubTitle("Your AI sidekick is almost ready")

        layout = QVBoxLayout()

        welcome_label = QLabel(
            "Welcome to Blink AI Assistant!\n\n"
            "This wizard will help you set up your AI provider and get you started "
            "with the perfect model for your needs.\n\n"
            "We'll detect your existing setup and guide you through any missing pieces."
        )
        welcome_label.setWordWrap(True)
        welcome_label.setStyleSheet("font-size: 12px; line-height: 1.5;")
        layout.addWidget(welcome_label)

        self.setLayout(layout)


class ProviderSelectionPage(QWizardPage):
    """Page for selecting AI provider."""

    def __init__(self):
        super().__init__()
        self.setTitle("Choose Your AI Provider")
        self.setSubTitle("How would you like to connect to AI?")

        self.provider_group = QButtonGroup()

        layout = QVBoxLayout()

        # Local Models option
        local_group = QGroupBox("🤖 Local Models (Recommended for Privacy)")
        local_layout = QVBoxLayout()

        self.local_radio = QRadioButton("Run AI models locally on your computer")
        self.local_radio.setChecked(True)
        self.provider_group.addButton(self.local_radio, 0)

        local_desc = QLabel(
            "• No API keys required\n"
            "• Works offline\n"
            "• Private - your data stays on your computer\n"
            "• May require downloading models (free)"
        )
        local_desc.setStyleSheet("font-size: 11px; color: #666; margin-left: 20px;")

        local_layout.addWidget(self.local_radio)
        local_layout.addWidget(local_desc)
        local_group.setLayout(local_layout)
        layout.addWidget(local_group)

        # OpenAI option
        openai_group = QGroupBox("⚡ OpenAI (Cloud - Requires API Key)")
        openai_layout = QVBoxLayout()

        self.openai_radio = QRadioButton("Use OpenAI's GPT models")
        self.provider_group.addButton(self.openai_radio, 1)

        openai_desc = QLabel(
            "• Access to GPT-4, GPT-3.5\n"
            "• Fast and reliable\n"
            "• Requires API key and internet\n"
            "• Pay per usage"
        )
        openai_desc.setStyleSheet("font-size: 11px; color: #666; margin-left: 20px;")

        openai_layout.addWidget(self.openai_radio)
        openai_layout.addWidget(openai_desc)
        openai_group.setLayout(openai_layout)
        layout.addWidget(openai_group)

        # Gemini option
        gemini_group = QGroupBox("🌟 Google Gemini (Cloud - Requires API Key)")
        gemini_layout = QVBoxLayout()

        self.gemini_radio = QRadioButton("Use Google's Gemini models")
        self.provider_group.addButton(self.gemini_radio, 2)

        gemini_desc = QLabel(
            "• Access to Gemini 1.5, 2.0\n"
            "• Free tier available\n"
            "• Requires API key and internet\n"
            "• Good multimodal capabilities"
        )
        gemini_desc.setStyleSheet("font-size: 11px; color: #666; margin-left: 20px;")

        gemini_layout.addWidget(self.gemini_radio)
        gemini_layout.addWidget(gemini_desc)
        gemini_group.setLayout(gemini_layout)
        layout.addWidget(gemini_group)

        layout.addStretch()
        self.setLayout(layout)

    def nextId(self):
        """Determine next page based on selection."""
        if self.local_radio.isChecked():
            return 2  # Local setup page
        elif self.openai_radio.isChecked() or self.gemini_radio.isChecked():
            return 3  # API key page
        else:
            return 2  # Default to local setup


class LocalSetupPage(QWizardPage):
    """Page for local model setup."""

    def __init__(self):
        super().__init__()
        self.setTitle("Local AI Setup")
        self.setSubTitle("Let's get your local AI running")

        self.detection_results = None
        self.selected_runner = None

        layout = QVBoxLayout()

        self.status_label = QLabel("Detecting local AI runners...")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)

        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)
        self.results_area.setMaximumHeight(200)
        layout.addWidget(self.results_area)

        self.runner_combo = QComboBox()
        self.runner_combo.setVisible(False)
        layout.addWidget(self.runner_combo)

        self.model_combo = QComboBox()
        self.model_combo.setVisible(False)
        layout.addWidget(self.model_combo)

        self.install_button = QPushButton("Install Ollama (Recommended)")
        self.install_button.clicked.connect(self.install_ollama)
        self.install_button.setVisible(False)
        layout.addWidget(self.install_button)

        layout.addStretch()
        self.setLayout(layout)

        # Start detection
        self.detect_runners()

    def detect_runners(self):
        """Start runner detection in background thread."""
        self.detection_thread = RunnerDetectionThread()
        self.detection_thread.detection_complete.connect(self.on_detection_complete)
        self.detection_thread.start()

    def on_detection_complete(self, results: Dict[str, Any]):
        """Handle detection results."""
        self.detection_results = results
        self.progress_bar.setVisible(False)
        self.status_label.setText("Detection complete!")

        ollama = results.get('ollama', {})
        lmstudio = results.get('lmstudio', {})

        result_text = "🔍 Detection Results:\n\n"

        if ollama.get('installed'):
            result_text += f"✅ Ollama: {'Running' if ollama.get('running') else 'Installed (not running)'}\n"
            if ollama.get('version'):
                result_text += f"   Version: {ollama['version']}\n"
            if ollama.get('models'):
                result_text += f"   Available models: {', '.join(ollama['models'][:3])}{'...' if len(ollama['models']) > 3 else ''}\n"
        else:
            result_text += "❌ Ollama: Not installed\n"

        if lmstudio.get('installed'):
            result_text += f"✅ LM Studio: Installed at {lmstudio.get('path', 'Unknown')}\n"
        else:
            result_text += "❌ LM Studio: Not installed\n"

        self.results_area.setPlainText(result_text)

        # Show options based on results
        if ollama.get('installed') or lmstudio.get('installed'):
            self.show_model_selection()
        else:
            self.show_installation_options()

    def show_model_selection(self):
        """Show model selection when runners are available."""
        self.runner_combo.clear()
        self.model_combo.clear()

        ollama = self.detection_results.get('ollama', {})
        lmstudio = self.detection_results.get('lmstudio', {})

        if ollama.get('installed'):
            self.runner_combo.addItem("Ollama", "ollama")
        if lmstudio.get('installed'):
            self.runner_combo.addItem("LM Studio", "lmstudio")

        self.runner_combo.setVisible(True)
        self.runner_combo.currentIndexChanged.connect(self.on_runner_changed)

        self.model_combo.setVisible(True)

        # Select first runner
        if self.runner_combo.count() > 0:
            self.on_runner_changed(0)

    def on_runner_changed(self, index):
        """Handle runner selection change."""
        if index < 0:
            return

        runner = self.runner_combo.itemData(index)
        self.selected_runner = runner

        self.model_combo.clear()

        if runner == "ollama":
            ollama = self.detection_results.get('ollama', {})
            models = ollama.get('models', [])

            # Suggest good models
            suggestions = []
            if not models:
                suggestions = ["llama3.2:latest", "llama3.1:latest", "mistral:latest"]
                self.model_combo.addItem("No models installed - install one below", "")
            else:
                suggestions = models[:5]  # Show first 5 available

            for model in suggestions:
                self.model_combo.addItem(model, model)

        elif runner == "lmstudio":
            self.model_combo.addItem("Configure in LM Studio app", "")

    def show_installation_options(self):
        """Show installation options when no runners found."""
        self.install_button.setVisible(True)
        self.results_area.append("\n💡 Recommendation: Install Ollama for the best experience!")

    def install_ollama(self):
        """Open Ollama installation page."""
        webbrowser.open("https://ollama.ai/download")
        QMessageBox.information(
            self, "Ollama Installation",
            "Follow the instructions on the Ollama website to install it.\n\n"
            "Once installed, restart Blink and we'll detect it automatically!"
        )

    def validatePage(self):
        """Validate the page before proceeding."""
        if not self.detection_results:
            return False

        ollama = self.detection_results.get('ollama', {})
        lmstudio = self.detection_results.get('lmstudio', {})

        if not (ollama.get('installed') or lmstudio.get('installed')):
            QMessageBox.warning(
                self, "No Local Runners",
                "Please install Ollama or LM Studio first, then restart Blink."
            )
            return False

        return True


class ApiKeyPage(QWizardPage):
    """Page for entering API keys."""

    def __init__(self):
        super().__init__()
        self.setTitle("API Key Setup")
        self.setSubTitle("Enter your API key to connect to the service")

        layout = QVBoxLayout()

        self.provider_label = QLabel("Provider: ")
        layout.addWidget(self.provider_label)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter your API key here...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.key_input)

        # Help links
        self.help_layout = QHBoxLayout()

        self.get_key_button = QPushButton("🔗 Get API Key")
        self.get_key_button.clicked.connect(self.open_api_key_page)
        self.help_layout.addWidget(self.get_key_button)

        self.help_layout.addStretch()
        layout.addLayout(self.help_layout)

        self.warning_label = QLabel(
            "⚠️ Your API key will be stored securely in your local configuration.\n"
            "It will never be sent anywhere except to the AI provider."
        )
        self.warning_label.setStyleSheet("color: #666; font-size: 11px;")
        self.warning_label.setWordWrap(True)
        layout.addWidget(self.warning_label)

        layout.addStretch()
        self.setLayout(layout)

    def initializePage(self):
        """Initialize page based on selected provider."""
        wizard = self.wizard()
        provider_page = wizard.page(1)  # ProviderSelectionPage

        if provider_page.openai_radio.isChecked():
            self.provider_label.setText("Provider: OpenAI")
            self.get_key_button.setText("🔗 Get OpenAI API Key")
            self.key_input.setPlaceholderText("sk-...")
        elif provider_page.gemini_radio.isChecked():
            self.provider_label.setText("Provider: Google Gemini")
            self.get_key_button.setText("🔗 Get Gemini API Key")
            self.key_input.setPlaceholderText("Enter your Gemini API key...")

    def open_api_key_page(self):
        """Open the appropriate API key page."""
        wizard = self.wizard()
        provider_page = wizard.page(1)

        if provider_page.openai_radio.isChecked():
            webbrowser.open("https://platform.openai.com/api-keys")
        elif provider_page.gemini_radio.isChecked():
            webbrowser.open("https://aistudio.google.com/app/apikey")

    def validatePage(self):
        """Validate API key input."""
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "API Key Required",
                              "Please enter your API key to continue.")
            return False

        # Basic validation
        wizard = self.wizard()
        provider_page = wizard.page(1)

        if provider_page.openai_radio.isChecked() and not key.startswith("sk-"):
            QMessageBox.warning(self, "Invalid API Key",
                              "OpenAI API keys should start with 'sk-'.")
            return False

        return True


class ModelSelectionPage(QWizardPage):
    """Page for selecting specific AI models."""

    def __init__(self):
        super().__init__()
        self.setTitle("Choose Your AI Model")
        self.setSubTitle("Select the specific model you want to use")

        layout = QVBoxLayout()

        self.provider_label = QLabel("Available models:")
        layout.addWidget(self.provider_label)

        self.model_combo = QComboBox()
        layout.addWidget(self.model_combo)

        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("font-size: 11px; color: #666; margin-top: 10px;")
        layout.addWidget(self.description_label)

        layout.addStretch()
        self.setLayout(layout)

    def initializePage(self):
        """Initialize page based on selected provider."""
        wizard = self.wizard()
        provider_page = wizard.page(1)  # ProviderSelectionPage

        self.model_combo.clear()

        # Use the exact model lists from llm_interface.py
        if provider_page.openai_radio.isChecked():
            self.provider_label.setText("OpenAI Models:")
            # Exact OpenAI models from llm_interface.py
            openai_models = [
                "gpt-5",
                "gpt-5-mini",
                "gpt-5-nano",
                "gpt-5-chat-latest",
                "gpt-5-thinking",
                "gpt-5-thinking-mini",
                "gpt-5-thinking-nano",
                "gpt-5-main",
                "gpt-5-main-mini",
                "gpt-4.1",
                "gpt-4o",
                "gpt-3.5-turbo"
            ]
            for model_name in openai_models:
                # Add descriptions based on model names
                if "gpt-5" in model_name and "thinking" in model_name:
                    desc = "GPT-5 Thinking - Advanced reasoning with chain-of-thought"
                elif "gpt-5" in model_name:
                    desc = "Latest GPT-5 series - Most advanced"
                elif "gpt-4o" in model_name:
                    desc = "GPT-4 Optimized - Fast and intelligent"
                elif "gpt-4" in model_name:
                    desc = "GPT-4 series - Advanced reasoning"
                elif "gpt-3.5" in model_name:
                    desc = "GPT-3.5 Turbo - Fast and affordable"
                else:
                    desc = "OpenAI model"
                self.model_combo.addItem(f"{model_name} - {desc}", model_name)

        elif provider_page.gemini_radio.isChecked():
            self.provider_label.setText("Google Gemini Models:")
            # Exact Gemini models from llm_interface.py
            gemini_models = [
                "gemini-2.5-pro",
                "gemini-2.5-flash",
                "gemini-flash-latest",
                "gemini-2.5-flash-lite",
                "gemini-flash-lite-latest",
                "gemini-2.5-flash-image-preview"
            ]
            for model_name in gemini_models:
                # Add descriptions based on model names
                if "2.5-pro" in model_name:
                    desc = "Gemini 2.5 Pro - Strongest reasoning"
                elif "2.5-flash" in model_name and "image-preview" in model_name:
                    desc = "Gemini 2.5 Flash - Image capabilities"
                elif "2.5-flash" in model_name:
                    desc = "Gemini 2.5 Flash - Balanced speed/cost"
                elif "flash-lite" in model_name:
                    desc = "Gemini Flash Lite - Lightweight and fast"
                elif "flash-latest" in model_name:
                    desc = "Gemini Flash Latest - Most recent"
                else:
                    desc = "Gemini model"
                self.model_combo.addItem(f"{model_name} - {desc}", model_name)

        # Update description when selection changes
        self.model_combo.currentIndexChanged.connect(self.update_description)

        # Set initial description
        if self.model_combo.count() > 0:
            self.update_description(0)

    def update_description(self, index):
        """Update the description based on selected model."""
        if index >= 0:
            current_text = self.model_combo.itemText(index)
            # Extract description from the text after the dash
            if " - " in current_text:
                desc = current_text.split(" - ", 1)[1]
                self.description_label.setText(f"Selected: {desc}")
            else:
                self.description_label.setText("")


class CompletionPage(QWizardPage):
    """Final completion page."""

    def __init__(self):
        super().__init__()
        self.setTitle("Setup Complete! 🎉")
        self.setSubTitle("You're all set to start using Blink")

        layout = QVBoxLayout()

        completion_label = QLabel(
            "Blink is now configured and ready to use!\n\n"
            "• Press Ctrl+Alt+. to select text and get AI responses\n"
            "• Press Ctrl+Alt+/ to combine clipboard content with instructions\n"
            "• Right-click the system tray icon for settings and help\n\n"
            "Happy AI assisting! 🚀"
        )
        completion_label.setWordWrap(True)
        completion_label.setStyleSheet("font-size: 12px; line-height: 1.5;")
        layout.addWidget(completion_label)

        layout.addStretch()
        self.setLayout(layout)


class FirstRunWizard(QWizard):
    """Main first-run setup wizard."""

    def __init__(self, config_manager: ConfigManager):
        super().__init__()

        self.config_manager = config_manager
        self.selected_provider = None
        self.api_key = None
        self.selected_model = None

        self.setWindowTitle("Blink AI Assistant - First Time Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        # Try to set icon
        try:
            icon_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd(),
                                   "assets", "icon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass

        # Add pages
        self.setPage(0, WelcomePage())
        self.setPage(1, ProviderSelectionPage())
        self.setPage(2, LocalSetupPage())
        self.setPage(3, ApiKeyPage())
        self.setPage(4, ModelSelectionPage())
        self.setPage(5, CompletionPage())

        # Set startup size
        self.resize(600, 500)

    def accept(self):
        """Handle wizard completion."""
        self.save_configuration()
        super().accept()

    def save_configuration(self):
        """Save the user's configuration."""
        # Get selections from pages
        provider_page = self.page(1)
        local_page = self.page(2)
        api_page = self.page(3)
        model_page = self.page(4)

        if provider_page.local_radio.isChecked():
            # Local model setup
            if local_page.selected_runner and local_page.model_combo.currentData():
                model = f"{local_page.selected_runner}:{local_page.model_combo.currentData()}"
                self.config_manager.set("selected_model", model)
            else:
                # Default fallback
                self.config_manager.set("selected_model", "ollama:llama3.2:latest")

        elif provider_page.openai_radio.isChecked():
            # Use selected OpenAI model
            selected_model = model_page.model_combo.currentData()
            if selected_model:
                self.config_manager.set("selected_model", f"openai:{selected_model}")
            else:
                self.config_manager.set("selected_model", "openai:gpt-4o")
            self.config_manager.set("openai_api_key", api_page.key_input.text().strip())

        elif provider_page.gemini_radio.isChecked():
            # Use selected Gemini model
            selected_model = model_page.model_combo.currentData()
            if selected_model:
                self.config_manager.set("selected_model", f"gemini:{selected_model}")
            else:
                self.config_manager.set("selected_model", "gemini:gemini-2.0-flash-exp")
            self.config_manager.set("gemini_api_key", api_page.key_input.text().strip())

        # Save other defaults
        self.config_manager.set("output_mode", "popup")
        self.config_manager.set("memory_enabled", True)

        # Clear first-run flag
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Blink", 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "FirstRun")
            winreg.CloseKey(key)
        except:
            pass  # Ignore if registry access fails


def check_first_run() -> bool:
    """Check if this is the first run by looking for registry flag."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Blink", 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "FirstRun")
        winreg.CloseKey(key)
        return value == 1
    except FileNotFoundError:
        return False
    except Exception:
        return False


def run_first_run_wizard(config_manager: ConfigManager) -> bool:
    """Run the first-run wizard if needed."""
    if not check_first_run():
        return True  # Not first run, continue normally

    # Create and run wizard
    wizard = FirstRunWizard(config_manager)
    result = wizard.exec()

    return result == QWizard.DialogCode.Accepted
