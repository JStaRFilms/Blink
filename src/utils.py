"""
Utility functions for the Blink application.

Provides helper functions for path resolution and other common operations.
"""

import sys
import os


def get_asset_path(filename: str) -> str:
    """
    Gets the absolute path to an asset file, handling both
    normal execution and a PyInstaller bundled executable.

    Args:
        filename: The name of the asset file (e.g., 'icon.ico')

    Returns:
        The absolute path to the asset file
    """
    if getattr(sys, 'frozen', False):
        # We are running in a PyInstaller bundle (e.g., the .exe).
        # The assets are unpacked to a temporary folder in sys._MEIPASS.
        base_path = sys._MEIPASS
    else:
        # We are running in a normal Python environment (from source).
        # The path is relative to the project root.
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    return os.path.join(base_path, 'assets', filename)
