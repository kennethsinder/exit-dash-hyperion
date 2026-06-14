"""Typed, format-agnostic level data.

These records describe everything a level needs, decoupled from both the on-disk ``.dat``
format (see :mod:`exit_dash.world.loader`) and the live sprite entities (built in
:mod:`exit_dash.world`). Keeping them as plain dataclasses makes level I/O trivially
testable without a display.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlatformRec:
    """A platform: top-left ``(x, y)`` and a ``width`` (height is tile-derived)."""

    x: float
    y: float
    width: float


@dataclass(frozen=True)
class PoolRec:
    """A water pool occupying a rectangle."""

    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class BlockRec:
    """A bonus block. ``coin`` distinguishes a coin block (type 0) from a regular one."""

    x: float
    y: float
    coin: bool


@dataclass(frozen=True)
class LedgeRec:
    """A snow ledge that spawns falling icicles along its span."""

    x: float
    y: float
    width: float


@dataclass(frozen=True)
class DoorRec:
    """The level-exit door. ``x``/``y`` are the raw stored coordinates."""

    x: float
    y: float


@dataclass
class LevelData:
    """A complete level definition."""

    door: DoorRec
    platforms: list[PlatformRec] = field(default_factory=list)
    blocks: list[BlockRec] = field(default_factory=list)
    pool: PoolRec | None = None
    ledge: LedgeRec | None = None
    fences: bool = True
    foliage: bool = True
    seed: float = 0.0
