"""Settings: JSON round-trip, tolerant parsing, and legacy ``.cfg`` migration."""

from __future__ import annotations

from exit_dash.core.settings import (
    LEGACY_FILENAME,
    SETTINGS_FILENAME,
    Settings,
    load_settings,
    save_settings,
)

# The actual values from the original repo's settings.cfg.
LEGACY_CFG = (
    "Game Settings Configuration - DO NOT MODIFY THIS FILE! Change settings in-game!\n"
    "True\nTrue\nTrue\nTrue\nTrue\nTrue\n0.926315789474\n1080p"
)


def test_json_round_trip(tmp_path):
    settings = Settings(developer_mode=True, volume=0.3, resolution="720p", fullscreen=False)
    save_settings(settings, config_dir=tmp_path)
    assert load_settings(config_dir=tmp_path) == settings


def test_from_dict_ignores_unknown_and_defaults_missing():
    settings = Settings.from_dict({"volume": 0.7, "totally_unknown_key": 123})
    assert settings.volume == 0.7
    assert settings.antialiasing is True  # default preserved


def test_legacy_cfg_migration(tmp_path):
    (tmp_path / LEGACY_FILENAME).write_text(LEGACY_CFG, encoding="utf-8")

    settings = load_settings(config_dir=tmp_path)

    assert settings.developer_mode is True
    assert settings.antialiasing is True
    assert settings.decorations is True
    assert settings.music_enabled is True
    assert settings.fullscreen is True
    assert abs(settings.volume - 0.926315789474) < 1e-9
    assert settings.resolution == "1080p"

    # Migration writes JSON and is sticky: a second load reads JSON and matches.
    assert (tmp_path / SETTINGS_FILENAME).is_file()
    assert load_settings(config_dir=tmp_path) == settings


def test_from_legacy_cfg_parses_false_and_skips_stablefps():
    # body: developerMode, antialiasing, stableFPS, decorations, doPlayMusic, fullscreen, volume, resolution
    text = "header\nFalse\nFalse\nTrue\nFalse\nFalse\nTrue\n0.5\n720p"
    settings = Settings.from_legacy_cfg(text)
    assert settings.developer_mode is False
    assert settings.antialiasing is False
    assert settings.decorations is False  # body[3]
    assert settings.music_enabled is False  # body[4]
    assert settings.fullscreen is True  # body[5]
    assert settings.volume == 0.5
    assert settings.resolution == "720p"


def test_defaults_written_when_nothing_exists(tmp_path):
    settings = load_settings(config_dir=tmp_path)
    assert settings == Settings()
    assert (tmp_path / SETTINGS_FILENAME).is_file()
