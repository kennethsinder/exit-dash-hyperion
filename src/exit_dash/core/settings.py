"""Game settings: a typed dataclass persisted as JSON in the user's config directory.

Replaces the original fragile positional ``settings.cfg``. On first run the old file (if
present) is migrated to JSON; thereafter JSON is the source of truth. Unknown keys are
ignored and missing keys fall back to defaults, so the format can evolve safely.

The obsolete ``stableFPS`` and FPS-preset options are dropped — they only existed to tame
a variable-rate loop the fixed-timestep engine no longer has.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

from exit_dash.core.paths import user_config_dir

SETTINGS_FILENAME = "settings.json"
LEGACY_FILENAME = "settings.cfg"


@dataclass
class Settings:
    """User-configurable game settings."""

    developer_mode: bool = False
    antialiasing: bool = True
    decorations: bool = True
    music_enabled: bool = True
    fullscreen: bool = True
    volume: float = 0.5
    resolution: str = "1080p"
    vsync: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Settings:
        """Build from a dict, ignoring unknown keys and defaulting missing ones."""
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    @classmethod
    def from_legacy_cfg(cls, text: str) -> Settings:
        """Parse the original positional ``settings.cfg`` text into :class:`Settings`.

        Layout (after the header line): developerMode, antialiasing, stableFPS,
        decorations, doPlayMusic, fullscreen, volume, resolution. Booleans were stored as
        ``True``/``False`` and read with a substring test.
        """
        body = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")[1:]

        def as_bool(value: str) -> bool:
            return "True" in value

        return cls(
            developer_mode=as_bool(body[0]),
            antialiasing=as_bool(body[1]),
            # body[2] was stableFPS — dropped.
            decorations=as_bool(body[3]),
            music_enabled=as_bool(body[4]),
            fullscreen=as_bool(body[5]),
            volume=float(body[6]),
            resolution=body[7].strip(),
        )


def settings_file(config_dir: Path | None = None) -> Path:
    return (config_dir or user_config_dir()) / SETTINGS_FILENAME


def save_settings(settings: Settings, config_dir: Path | None = None) -> None:
    """Persist settings as pretty JSON in the config directory."""
    directory = config_dir or user_config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    (directory / SETTINGS_FILENAME).write_text(
        json.dumps(settings.to_dict(), indent=2) + "\n", encoding="utf-8"
    )


def load_settings(config_dir: Path | None = None, legacy_path: Path | None = None) -> Settings:
    """Load settings, migrating a legacy ``settings.cfg`` on first run.

    Resolution order: existing ``settings.json`` -> legacy ``.cfg`` (migrated and saved as
    JSON) -> built-in defaults (saved as JSON).
    """
    directory = config_dir or user_config_dir()
    json_path = directory / SETTINGS_FILENAME
    if json_path.is_file():
        return Settings.from_dict(json.loads(json_path.read_text(encoding="utf-8")))

    legacy = legacy_path if legacy_path is not None else directory / LEGACY_FILENAME
    if legacy.is_file():
        settings = Settings.from_legacy_cfg(legacy.read_text(encoding="utf-8"))
    else:
        settings = Settings()

    save_settings(settings, config_dir=directory)
    return settings
