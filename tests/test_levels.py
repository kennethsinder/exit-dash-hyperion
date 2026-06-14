"""Level ``.dat`` parsing: shipped levels load, round-trip, and tolerate line endings."""

from __future__ import annotations

import pytest

from exit_dash.core.paths import asset_path
from exit_dash.world import loader
from exit_dash.world.level import LevelData

SHIPPED_LEVELS = [1, 2, 3, 4]


def _level_path(n: int):
    return asset_path("levels", f"lvl_{n}.dat")


@pytest.mark.parametrize("n", SHIPPED_LEVELS)
def test_shipped_level_loads(n):
    level = loader.read_level(_level_path(n))
    assert isinstance(level, LevelData)
    assert level.platforms, "every level has at least one platform"
    assert level.door is not None


@pytest.mark.parametrize("n", SHIPPED_LEVELS)
def test_semantic_round_trip(n):
    level = loader.read_level(_level_path(n))
    reparsed = loader.loads(loader.dumps(level, level_number=n))
    assert reparsed == level


def test_level_1_known_values():
    level = loader.read_level(_level_path(1))
    first = level.platforms[0]
    assert (first.x, first.y, first.width) == (1820.0, 894.0, 1050.0)


def test_loads_is_line_ending_agnostic():
    lf = loader.dumps(loader.read_level(_level_path(1)), level_number=1)
    crlf = lf.replace("\n", "\r\n")
    cr = lf.replace("\n", "\r")
    assert loader.loads(lf) == loader.loads(crlf) == loader.loads(cr)


def test_too_short_raises():
    with pytest.raises(ValueError, match="expected at least"):
        loader.loads("header\n1\n2\n3\n")
