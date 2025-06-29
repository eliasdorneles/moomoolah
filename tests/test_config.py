"""Tests for config module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch


from moomoolah.config import get_default_state_file_path


def test_get_default_state_file_path_with_xdg_data_home():
    """Test that XDG_DATA_HOME is used when set."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch.dict(os.environ, {"XDG_DATA_HOME": temp_dir}):
            result = get_default_state_file_path()
            expected = Path(temp_dir) / "moomoolah" / "state.json"
            assert result == expected
            # Verify directory was created
            assert result.parent.exists()
            # Verify permissions are set correctly (0o700)
            assert oct(result.parent.stat().st_mode)[-3:] == "700"


def test_get_default_state_file_path_without_xdg_data_home():
    """Test that ~/.local/share is used when XDG_DATA_HOME is not set."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/mock/home")
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                with patch("pathlib.Path.chmod") as mock_chmod:
                    result = get_default_state_file_path()
                    expected = Path("/mock/home/.local/share/moomoolah/state.json")
                    assert result == expected
                    # Verify mkdir was called with correct arguments
                    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
                    # Verify chmod was called with correct permissions
                    mock_chmod.assert_called_once_with(0o700)


def test_get_default_state_file_path_creates_directory():
    """Test that the moomoolah directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_data_dir = Path(temp_dir) / "test_data"
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(test_data_dir)}):
            result = get_default_state_file_path()
            # Verify the full path structure was created
            assert result.parent.exists()
            assert result.parent.name == "moomoolah"
            assert result.name == "state.json"
