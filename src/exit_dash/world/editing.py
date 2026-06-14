"""The level-editor's working model: a mutable, display-free level under construction.

This is deliberately decoupled from pygame so it can be unit-tested directly. It holds
the same records the ``.dat`` format stores (see :mod:`exit_dash.world.level`), enforces
the format's fixed-slot limits, and round-trips through :mod:`exit_dash.world.loader`.

:meth:`EditorModel.playability` encodes the structural rules a level must satisfy to be
*built* by :func:`exit_dash.world.world.World.from_level_data` without crashing or
hanging — most importantly that there are enough platforms with distinct x-positions
that the mob-placement loop in ``generate_mobs`` can always terminate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from exit_dash.world.level import (
    BlockRec,
    DoorRec,
    LedgeRec,
    LevelData,
    PlatformRec,
    PoolRec,
)
from exit_dash.world.loader import MAX_BLOCKS, MAX_PLATFORMS, read_level, write_level

#: Grid spacing placements snap to.
GRID = 20
#: Approximate object sizes used for the editor's schematic drawing and erase hit-tests.
#: (The real entities use their sprite dimensions; these only matter inside the editor.)
PLATFORM_HEIGHT = 70
BLOCK_SIZE = 70
DOOR_WIDTH = 70
DOOR_HEIGHT = 135
#: Default sizes for newly placed objects.
DEFAULT_PLATFORM_WIDTH = 300
DEFAULT_POOL_WIDTH = 400
DEFAULT_POOL_HEIGHT = 240
DEFAULT_LEDGE_WIDTH = 400
#: Custom levels are saved here (under the per-user data dir).
CUSTOM_LEVEL_NAME = "lvl_custom.dat"


def snap(value: float) -> float:
    """Snap a coordinate to the placement grid."""
    return round(value / GRID) * GRID


@dataclass
class EditorModel:
    """A level being edited. All coordinates are absolute world coordinates."""

    platforms: list[PlatformRec] = field(default_factory=list)
    blocks: list[BlockRec] = field(default_factory=list)
    pool: PoolRec | None = None
    ledge: LedgeRec | None = None
    door: DoorRec = field(default_factory=lambda: DoorRec(0, 0))
    fences: bool = True
    foliage: bool = True

    # -- construction -----------------------------------------------------------------

    @classmethod
    def blank(cls) -> EditorModel:
        """A minimal, immediately-playable starter level (spawn + two reachable steps)."""
        return cls(
            platforms=[
                PlatformRec(120, 480, 360),  # platforms[0] is always the spawn platform
                PlatformRec(620, 420, 300),
                PlatformRec(1040, 480, 300),
            ],
            blocks=[BlockRec(300, 400, coin=True)],
            door=DoorRec(1240, 480),
        )

    @classmethod
    def from_level_data(cls, data: LevelData) -> EditorModel:
        return cls(
            platforms=list(data.platforms),
            blocks=list(data.blocks),
            pool=data.pool,
            ledge=data.ledge,
            door=data.door,
            fences=data.fences,
            foliage=data.foliage,
        )

    def to_level_data(self) -> LevelData:
        return LevelData(
            door=self.door,
            platforms=list(self.platforms),
            blocks=list(self.blocks),
            pool=self.pool,
            ledge=self.ledge,
            fences=self.fences,
            foliage=self.foliage,
        )

    # -- editing operations -----------------------------------------------------------

    def add_platform(self, x: float, y: float, width: float) -> bool:
        """Add a platform; returns False if the format's platform limit is reached."""
        if len(self.platforms) >= MAX_PLATFORMS:
            return False
        self.platforms.append(PlatformRec(snap(x), snap(y), max(GRID, snap(width))))
        return True

    def add_block(self, x: float, y: float, *, coin: bool) -> bool:
        """Add a bonus block; returns False if the format's block limit is reached."""
        if len(self.blocks) >= MAX_BLOCKS:
            return False
        self.blocks.append(BlockRec(snap(x), snap(y), coin=coin))
        return True

    def set_pool(self, x: float, y: float, width: float, height: float) -> None:
        self.pool = PoolRec(snap(x), snap(y), max(GRID, snap(width)), max(GRID, snap(height)))

    def set_ledge(self, x: float, y: float, width: float) -> None:
        self.ledge = LedgeRec(snap(x), snap(y), max(GRID, snap(width)))

    def set_door(self, x: float, y: float) -> None:
        self.door = DoorRec(snap(x), snap(y))

    def erase_at(self, x: float, y: float) -> bool:
        """Remove the most-recently-added object under ``(x, y)``. Door is never erased."""
        for i in range(len(self.blocks) - 1, -1, -1):
            b = self.blocks[i]
            if b.x <= x <= b.x + BLOCK_SIZE and b.y <= y <= b.y + BLOCK_SIZE:
                del self.blocks[i]
                return True
        if self.pool and self._in(self.pool, x, y, self.pool.width, self.pool.height):
            self.pool = None
            return True
        if self.ledge and self._in(self.ledge, x, y, self.ledge.width, PLATFORM_HEIGHT):
            self.ledge = None
            return True
        for i in range(len(self.platforms) - 1, -1, -1):
            p = self.platforms[i]
            if p.x <= x <= p.x + p.width and p.y <= y <= p.y + PLATFORM_HEIGHT:
                del self.platforms[i]
                return True
        return False

    @staticmethod
    def _in(rec: object, x: float, y: float, w: float, h: float) -> bool:
        rx, ry = rec.x, rec.y  # type: ignore[attr-defined]
        return rx <= x <= rx + w and ry <= y <= ry + h

    # -- validation & persistence -----------------------------------------------------

    def playability(self) -> tuple[bool, str]:
        """Return ``(ok, reason)``. A non-ok level would crash/hang the level builder."""
        if len(self.platforms) < 3:
            return False, "need at least 3 platforms"
        # generate_mobs() loops until it finds a non-spawn platform whose x differs from
        # the longest platform's; that only terminates if the non-spawn platforms hold at
        # least two distinct x-positions.
        if len({p.x for p in self.platforms[1:]}) < 2:
            return False, "non-spawn platforms need at least 2 distinct x-positions"
        return True, "ready to play"

    def save(self, path: Path) -> None:
        write_level(path, self.to_level_data())

    @classmethod
    def load(cls, path: Path) -> EditorModel:
        return cls.from_level_data(read_level(path))
