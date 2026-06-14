"""Asset existence: every referenced asset is present on disk, case-sensitively.

This guards against two real bugs: (1) case-mismatched filenames that work on macOS/Windows
but break on Linux, and (2) deleting an asset during the prune/optimize pass that the game
actually loads via a dynamically-constructed path (which static scans miss). The dynamic
families below are expanded explicitly.
"""

from __future__ import annotations

import pytest

from exit_dash.core.paths import asset_root

THEMES = ["castle", "dirt", "grass", "sand", "snow", "stone"]
KEY_COLORS = ["blue", "green", "red", "yellow"]
SLIME_COLORS = ["Blue", "Green"]
PLAYERS = [1, 2, 3]


def _exists_case_sensitive(*parts: str) -> bool:
    """True only if every path component exists with exactly this case under the assets root."""
    current = asset_root()
    for part in parts:
        if not current.is_dir():
            return False
        if part not in {child.name for child in current.iterdir()}:
            return False
        current = current / part
    return True


def _check(*parts: str) -> None:
    assert _exists_case_sensitive(*parts), f"missing asset: {'/'.join(parts)}"


def test_asset_root_exists():
    assert asset_root().is_dir()


@pytest.mark.parametrize("theme", THEMES)
def test_terrain_tiles(theme):
    for suffix in ("Mid", "CliffLeft", "CliffRight"):
        _check("environment", "main", f"{theme}{suffix}.png")


@pytest.mark.parametrize("color", KEY_COLORS)
def test_keys(color):
    _check("environment", "main", f"key{color}.png")


def test_doors():
    for piece in ("door_openMid", "door_openTop", "door_closedMid", "door_closedTop"):
        _check("environment", "main", f"{piece}.png")


def test_hud_digits():
    for digit in range(10):
        _check("hud", f"hud_{digit}.png")


def test_explosion_frames():
    for frame in range(3):
        _check("environment", "main", f"explosion{frame}.png")


@pytest.mark.parametrize("color", SLIME_COLORS)
def test_slime_frames(color):
    for suffix in ("walk", "walkR", "squashed", "squashedR"):
        _check("enemies", "slime", f"slime{color}_{suffix}.png")


@pytest.mark.parametrize("player", PLAYERS)
def test_player_sprites(player):
    _check("character", "main", f"p{player}_front.png")
    _check("character", "main", f"p{player}_walk", "PNG", f"p{player}_walk1.png")
