"""Configuration and default paths for moomoolah."""

import os
from pathlib import Path


def get_default_state_file_path() -> Path:
    """Get the default path for the state file following XDG Base Directory specification."""
    # XDG_DATA_HOME or ~/.local/share on Linux/Unix
    xdg_data_home = os.environ.get("XDG_DATA_HOME")

    if xdg_data_home:
        data_dir = Path(xdg_data_home)
    else:
        data_dir = Path.home() / ".local" / "share"

    # Create moomoolah directory
    app_data_dir = data_dir / "moomoolah"
    app_data_dir.mkdir(parents=True, exist_ok=True)

    # Set appropriate permissions (user read/write only)
    app_data_dir.chmod(0o700)

    return app_data_dir / "state.json"
