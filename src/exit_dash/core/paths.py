"""Locate bundled assets and the user's writable data directory.

Assets are resolved relative to this package — never the current working directory —
so the game runs from any folder, from an installed wheel, and from a PyInstaller
bundle. User-writable state (settings, custom levels) goes in the per-user config/data
directories provided by :mod:`platformdirs`, which are writable even when the game is
installed read-only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import platformdirs

_APP_NAME = "ExitDashHyperion"
_APP_AUTHOR = "BurinCode"


def asset_root() -> Path:
    """Return the directory that contains the bundled ``assets`` tree."""
    bundle_dir = getattr(sys, "_MEIPASS", None)  # set by PyInstaller one-file bundles
    if bundle_dir:
        return Path(bundle_dir) / "exit_dash" / "assets"
    return Path(__file__).resolve().parent.parent / "assets"


def asset_path(*parts: str) -> Path:
    """Return the path to a bundled asset, e.g. ``asset_path("fonts", "atari.ttf")``."""
    return asset_root().joinpath(*parts)


def user_config_dir() -> Path:
    """Return (creating if needed) the per-user config directory for settings."""
    path = Path(platformdirs.user_config_dir(_APP_NAME, _APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def user_data_dir() -> Path:
    """Return (creating if needed) the per-user data directory for saves/custom levels."""
    path = Path(platformdirs.user_data_dir(_APP_NAME, _APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path
