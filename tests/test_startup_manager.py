"""
Tests for startup_manager.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.startup_manager import StartupManager


class TestStartupManager:
    """Test cases for StartupManager class."""

    def test_init_success(self):
        """Test successful initialization."""
        with patch('src.startup_manager.WIN32_AVAILABLE', True):
            manager = StartupManager()
            assert manager.RUN_KEY == r"Software\Microsoft\Windows\CurrentVersion\Run"
            assert manager.APP_NAME == "Blink"

    def test_init_no_win32(self):
        """Test initialization when win32 is not available."""
        with patch('src.startup_manager.WIN32_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                StartupManager()
            assert "pywin32 is required" in str(exc_info.value)

    @patch('src.startup_manager.WIN32_AVAILABLE', True)
    @patch('src.startup_manager.win32api')
    @patch('src.startup_manager.sys')
    @patch('src.startup_manager.os')
    def test_get_executable_path_script(self, mock_os, mock_sys, mock_win32api):
        """Test getting executable path for script mode."""
        # Mock as script (not frozen)
        mock_sys.frozen = None
        mock_sys.argv = [r"C:\path\to\script.py"]
        mock_sys.executable = r"C:\Python\python.exe"
        mock_os.path.abspath.return_value = r"C:\path\to\script.py"

        manager = StartupManager()
        path = manager._get_executable_path()

        expected = r'"C:\Python\python.exe" "C:\path\to\script.py"'
        assert path == expected

    @patch('src.startup_manager.WIN32_AVAILABLE', True)
    @patch('src.startup_manager.win32api')
    @patch('src.startup_manager.sys')
    def test_get_executable_path_frozen(self, mock_sys, mock_win32api):
        """Test getting executable path for frozen executable."""
        # Mock as frozen executable
        mock_sys.frozen = True
        mock_sys.executable = r"C:\path\to\app.exe"

        manager = StartupManager()
        path = manager._get_executable_path()

        assert path == r"C:\path\to\app.exe"

    @patch('src.startup_manager.WIN32_AVAILABLE', True)
    @patch('src.startup_manager.win32api')
    def test_is_enabled_true(self, mock_win32api):
        """Test checking if startup is enabled - returns True."""
        # Mock successful registry read
        mock_key = Mock()
        mock_win32api.RegOpenKeyEx.return_value = mock_key
        mock_win32api.RegQueryValueEx.return_value = (r"C:\path\to\app.exe", None)
        mock_win32api.RegCloseKey = Mock()

        manager = StartupManager()
        result = manager.is_enabled()

        assert result is True
        mock_win32api.RegOpenKeyEx.assert_called_once()
        mock_win32api.RegCloseKey.assert_called_once_with(mock_key)

    @patch('src.startup_manager.WIN32_AVAILABLE', True)
    @patch('src.startup_manager.win32api')
    def test_is_enabled_false_no_value(self, mock_win32api):
        """Test checking if startup is enabled - no value exists."""
        # Mock registry key exists but value doesn't
        mock_key = Mock()
        mock_win32api.RegOpenKeyEx.return_value = mock_key
        mock_win32api.RegQueryValueEx.side_effect = FileNotFoundError()
        mock_win32api.RegCloseKey = Mock()

        manager = StartupManager()
        result = manager.is_enabled()

        assert result is False

    @patch('src.startup_manager.WIN32_AVAILABLE', True)
    @patch('src.startup_manager.win32api')
    def test_is_enabled_false_empty_value(self, mock_win32api):
        """Test checking if startup is enabled - empty value."""
        # Mock empty value
        mock_key = Mock()
        mock_win32api.RegOpenKeyEx.return_value = mock_key
        mock_win32api.RegQueryValueEx.return_value = ("", None)
        mock_win32api.RegCloseKey = Mock()

        manager = StartupManager()
        result = manager.is_enabled()

        assert result is False

    @patch('src.startup_manager.WIN32_AVAILABLE', True)
    @patch('src.startup_manager.win32api')
    def test_is_enabled_exception(self, mock_win32api):
        """Test checking if startup is enabled - registry access fails."""
        # Mock registry access failure
        mock_win32api.RegOpenKeyEx.side_effect = Exception("Registry error")

        manager = StartupManager()
        result = manager.is_enabled()

        assert result is False

    @patch('src.startup_manager.WIN32_AVAILABLE', True)
    @patch('src.startup_manager.win32api')
    @patch.object(StartupManager, '_get_executable_path')
    def test_enable_success(self, mock_get_path, mock_win32api):
        """Test enabling startup successfully."""
        mock_get_path.return_value = r"C:\path\to\app.exe"

        # Mock registry operations
        mock_key = Mock()
        mock_win32api.RegOpenKeyEx.return_value = mock_key
        mock_win32api.RegCloseKey = Mock()
        mock_win32api.REG_SZ = 1  # Windows REG_SZ constant

        manager = StartupManager()
        manager.enable()

        # Verify registry operations
        mock_win32api.RegOpenKeyEx.assert_called_once()
        mock_win32api.RegSetValueEx.assert_called_once_with(
            mock_key, "Blink", 0, 1, r"C:\path\to\app.exe"
        )
        mock_win32api.RegCloseKey.assert_called_once_with(mock_key)

    @patch('src.startup_manager.WIN32_AVAILABLE', True)
    @patch('src.startup_manager.win32api')
    def test_enable_failure(self, mock_win32api):
        """Test enabling startup with failure."""
        # Mock registry operation failure
        mock_win32api.RegOpenKeyEx.side_effect = Exception("Registry write failed")

        manager = StartupManager()

        with pytest.raises(RuntimeError) as exc_info:
            manager.enable()

        assert "Failed to enable startup" in str(exc_info.value)

    @patch('src.startup_manager.WIN32_AVAILABLE', True)
    @patch('src.startup_manager.win32api')
    def test_disable_success(self, mock_win32api):
        """Test disabling startup successfully."""
        # Mock registry operations
        mock_key = Mock()
        mock_win32api.RegOpenKeyEx.return_value = mock_key
        mock_win32api.RegCloseKey = Mock()

        manager = StartupManager()
        manager.disable()

        # Verify registry operations
        mock_win32api.RegOpenKeyEx.assert_called_once()
        mock_win32api.RegDeleteValue.assert_called_once_with(mock_key, "Blink")
        mock_win32api.RegCloseKey.assert_called_once_with(mock_key)

    @patch('src.startup_manager.WIN32_AVAILABLE', True)
    @patch('src.startup_manager.win32api')
    def test_disable_no_value(self, mock_win32api):
        """Test disabling startup when value doesn't exist."""
        # Mock value doesn't exist
        mock_key = Mock()
        mock_win32api.RegOpenKeyEx.return_value = mock_key
        mock_win32api.RegDeleteValue.side_effect = FileNotFoundError()
        mock_win32api.RegCloseKey = Mock()

        manager = StartupManager()
        # Should not raise exception
        manager.disable()

        mock_win32api.RegDeleteValue.assert_called_once_with(mock_key, "Blink")

    @patch('src.startup_manager.WIN32_AVAILABLE', True)
    @patch('src.startup_manager.win32api')
    def test_disable_failure(self, mock_win32api):
        """Test disabling startup with failure."""
        # Mock registry operation failure
        mock_win32api.RegOpenKeyEx.side_effect = Exception("Registry access failed")

        manager = StartupManager()

        with pytest.raises(RuntimeError) as exc_info:
            manager.disable()

        assert "Failed to disable startup" in str(exc_info.value)
