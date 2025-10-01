"""
Settings dialog module for Blink.

Provides a GUI for configuring API keys and model selection.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QGroupBox, QMessageBox, QRadioButton, QButtonGroup
from PyQt6.QtCore import pyqtSignal
from typing import Optional


class SettingsDialog(QDialog):
    """
    Settings dialog for configuring API keys and model preferences.
    """

    settings_changed = pyqtSignal()

    def __init__(self, config_manager: 'ConfigManager', llm_interface: 'LLMInterface', parent=None) -> None:
        """
        Initializes the SettingsDialog.

        Args:
            config_manager: Configuration manager instance.
            llm_interface: LLM interface instance.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.llm_interface = llm_interface

        self.setWindowTitle("Blink Settings")
        self.setModal(True)
        self.resize(400, 300)

        self.setup_ui()
        self.load_settings()

    def setup_ui(self) -> None:
        """
        Sets up the user interface components.
        """
        layout = QVBoxLayout()

        # API Keys section
        api_group = QGroupBox("API Keys")
        api_layout = QVBoxLayout()

        # OpenAI API Key
        openai_layout = QHBoxLayout()
        openai_layout.addWidget(QLabel("OpenAI API Key:"))
        self.openai_key_edit = QLineEdit()
        self.openai_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        openai_layout.addWidget(self.openai_key_edit)
        api_layout.addLayout(openai_layout)

        # Gemini API Key
        gemini_layout = QHBoxLayout()
        gemini_layout.addWidget(QLabel("Gemini API Key:"))
        self.gemini_key_edit = QLineEdit()
        self.gemini_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        gemini_layout.addWidget(self.gemini_key_edit)
        api_layout.addLayout(gemini_layout)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # Model Selection section
        model_group = QGroupBox("Model Selection")
        model_layout = QVBoxLayout()

        model_layout.addWidget(QLabel("Default Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(self.llm_interface.get_available_models())
        model_layout.addWidget(self.model_combo)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Output Mode section
        output_group = QGroupBox("Output Mode")
        output_layout = QVBoxLayout()

        output_layout.addWidget(QLabel("Choose how AI responses are displayed:"))

        # Radio buttons for output mode
        self.output_mode_group = QButtonGroup()
        self.popup_radio = QRadioButton("Popup Overlay")
        self.direct_stream_radio = QRadioButton("Direct Stream")

        self.output_mode_group.addButton(self.popup_radio, 0)
        self.output_mode_group.addButton(self.direct_stream_radio, 1)

        output_layout.addWidget(self.popup_radio)
        output_layout.addWidget(self.direct_stream_radio)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_settings(self) -> None:
        """
        Loads current settings into the dialog.
        """
        # Load API keys
        openai_key = self.config_manager.get("openai_api_key", "")
        self.openai_key_edit.setText(openai_key)

        gemini_key = self.config_manager.get("gemini_api_key", "")
        self.gemini_key_edit.setText(gemini_key)

        # Load selected model
        selected_model = self.config_manager.get("selected_model", "ollama:llama3.2:latest")
        index = self.model_combo.findText(selected_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)

        # Load output mode
        output_mode = self.config_manager.get("output_mode", "popup")
        if output_mode == "direct_stream":
            self.direct_stream_radio.setChecked(True)
        else:
            self.popup_radio.setChecked(True)

    def save_settings(self) -> None:
        """
        Saves the settings from the dialog.
        """
        # Save OpenAI API key
        openai_key = self.openai_key_edit.text().strip()
        if openai_key:
            self.config_manager.set("openai_api_key", openai_key)
        else:
            # Remove if empty
            if "openai_api_key" in self.config_manager.config:
                del self.config_manager.config["openai_api_key"]
                self.config_manager.save_config()

        # Save Gemini API key
        gemini_key = self.gemini_key_edit.text().strip()
        if gemini_key:
            self.config_manager.set("gemini_api_key", gemini_key)
        else:
            # Remove if empty
            if "gemini_api_key" in self.config_manager.config:
                del self.config_manager.config["gemini_api_key"]
                self.config_manager.save_config()

        # Reinitialize OpenAI client if key changed
        if openai_key:
            try:
                from openai import OpenAI
                self.llm_interface.openai_client = OpenAI(api_key=openai_key)
            except ImportError:
                pass

        # Reinitialize Gemini client if key changed
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                self.llm_interface.gemini_available = True
            except ImportError:
                self.llm_interface.gemini_available = False

        # Capture the currently selected model before refreshing the combo box
        previously_selected_model = self.model_combo.currentText()

        # Refresh the model combo box with updated available models
        self.model_combo.clear()
        self.model_combo.addItems(self.llm_interface.get_available_models())

        # Restore the previously selected model if it's still available, otherwise use a default
        selected_model = previously_selected_model
        model_index = self.model_combo.findText(selected_model)
        if model_index >= 0:
            self.model_combo.setCurrentIndex(model_index)
        else:
            # If previously selected model is not available, use the first available model
            if self.model_combo.count() > 0:
                selected_model = self.model_combo.itemText(0)
                self.model_combo.setCurrentIndex(0)
            else:
                selected_model = "ollama:llama3.2:latest"  # fallback

        self.config_manager.set("selected_model", selected_model)
        self.llm_interface.set_selected_model(selected_model)

        # Save output mode
        if self.direct_stream_radio.isChecked():
            self.config_manager.set("output_mode", "direct_stream")
        else:
            self.config_manager.set("output_mode", "popup")

        self.settings_changed.emit()
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        self.accept()
