"""
Startup manager module for Blink.

Handles Windows Registry operations for automatic startup configuration.
"""

import sys
import os
from typing import Optional

try:
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class StartupManager:
    """
    Manages Windows startup registry entries for the Blink application.
    """

    def __init__(self) -> None:
        """
        Initializes the StartupManager.
        """
        if not WIN32_AVAILABLE:
            raise ImportError("pywin32 is required for startup management. Install with: pip install pywin32")

        self.RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
        self.APP_NAME = "Blink"

    def _get_executable_path(self) -> str:
        """
        Gets the path to the executable or script to run on startup.

        Returns:
            str: Path to the executable/script.
        """
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return sys.executable
        else:
            # Running as script
            script_path = os.path.abspath(sys.argv[0])
            python_exe = sys.executable
            return f'"{python_exe}" "{script_path}"'

    def is_enabled(self) -> bool:
        """
        Checks if the application is configured to start on system startup.

        Returns:
            bool: True if startup is enabled, False otherwise.
        """
        try:
            # Open the registry key
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER,
                self.RUN_KEY,
                0,
                win32con.KEY_READ
            )

            try:
                # Try to read the value
                value, _ = win32api.RegQueryValueEx(key, self.APP_NAME)
                return bool(value)
            except FileNotFoundError:
                return False
            finally:
                win32api.RegCloseKey(key)

        except Exception as e:
            print(f"Error checking startup status: {e}")
            return False

    def enable(self) -> None:
        """
        Enables automatic startup for the application.
        """
        try:
            # Open the registry key for writing
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER,
                self.RUN_KEY,
                0,
                win32con.KEY_SET_VALUE
            )

            try:
                # Set the value
                exe_path = self._get_executable_path()
                win32api.RegSetValueEx(key, self.APP_NAME, 0, win32con.REG_SZ, exe_path)
                print(f"Startup enabled: {exe_path}")
            finally:
                win32api.RegCloseKey(key)

        except Exception as e:
            raise RuntimeError(f"Failed to enable startup: {e}")

    def disable(self) -> None:
        """
        Disables automatic startup for the application.
        """
        try:
            # Open the registry key for writing
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER,
                self.RUN_KEY,
                0,
                win32con.KEY_SET_VALUE
            )

            try:
                # Delete the value
                win32api.RegDeleteValue(key, self.APP_NAME)
                print("Startup disabled")
            except FileNotFoundError:
                # Value doesn't exist, which is fine
                pass
            finally:
                win32api.RegCloseKey(key)

        except Exception as e:
            raise RuntimeError(f"Failed to disable startup: {e}")
