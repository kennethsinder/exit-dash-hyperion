"""Read and write the level ``.dat`` format.

The format is a header line followed by newline-separated numbers in fixed positions:

* 25 platform slots, each ``(x, y, width)``
* 1 pool ``(x, y, width, height)``
* 25 block slots, each ``(x, y, kind)`` where ``kind`` is ``0`` (coin) or ``1`` (regular)
* 1 ledge ``(x, y, width)``
* 1 door ``(x, y)``
* fences flag, foliage flag, seed

Unused slots are filled with the sentinel ``-999``. The reader normalizes line endings
(historically files mixed CRLF and LF) and skips blank lines, so it is robust to the
inconsistencies in the original data files. The writer always emits ``\\n`` line endings.
"""

from __future__ import annotations

from pathlib import Path

from exit_dash.world.level import (
    BlockRec,
    DoorRec,
    LedgeRec,
    LevelData,
    PlatformRec,
    PoolRec,
)

EMPTY = -999.0
MAX_PLATFORMS = 25
MAX_BLOCKS = 25
_PLATFORM_FIELDS = 3
_POOL_FIELDS = 4
_BLOCK_FIELDS = 3
_LEDGE_FIELDS = 3
_DOOR_FIELDS = 2
#: Total number of numeric values expected after the header line.
EXPECTED_VALUES = (
    MAX_PLATFORMS * _PLATFORM_FIELDS
    + _POOL_FIELDS
    + MAX_BLOCKS * _BLOCK_FIELDS
    + _LEDGE_FIELDS
    + _DOOR_FIELDS
    + 3  # fences flag, foliage flag, seed
)


def _is_empty(value: float) -> bool:
    return value == EMPTY


def loads(text: str) -> LevelData:
    """Parse level text (header + numbers) into :class:`LevelData`."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.strip() for ln in normalized.split("\n")]
    # Drop the header (first non-empty line) and any blank lines.
    numbers: list[float] = []
    for line in lines[1:]:
        if line:
            numbers.append(float(line))

    if len(numbers) < EXPECTED_VALUES:
        raise ValueError(
            f"level data has {len(numbers)} values, expected at least {EXPECTED_VALUES}"
        )

    cursor = 0

    platforms: list[PlatformRec] = []
    for _ in range(MAX_PLATFORMS):
        x, y, width = numbers[cursor : cursor + _PLATFORM_FIELDS]
        if not _is_empty(x):
            platforms.append(PlatformRec(x, y, width))
        cursor += _PLATFORM_FIELDS

    pool: PoolRec | None = None
    px, py, pw, ph = numbers[cursor : cursor + _POOL_FIELDS]
    if not _is_empty(px):
        pool = PoolRec(px, py, pw, ph)
    cursor += _POOL_FIELDS

    blocks: list[BlockRec] = []
    for _ in range(MAX_BLOCKS):
        x, y, kind = numbers[cursor : cursor + _BLOCK_FIELDS]
        if not _is_empty(x):
            blocks.append(BlockRec(x, y, coin=(kind == 0)))
        cursor += _BLOCK_FIELDS

    ledge: LedgeRec | None = None
    lx, ly, lw = numbers[cursor : cursor + _LEDGE_FIELDS]
    if not _is_empty(lx):
        ledge = LedgeRec(lx, ly, lw)
    cursor += _LEDGE_FIELDS

    door = DoorRec(numbers[cursor], numbers[cursor + 1])
    cursor += _DOOR_FIELDS

    fences = numbers[cursor] != 0
    foliage = numbers[cursor + 1] != 0
    seed = numbers[cursor + 2]

    return LevelData(
        door=door,
        platforms=platforms,
        blocks=blocks,
        pool=pool,
        ledge=ledge,
        fences=fences,
        foliage=foliage,
        seed=seed,
    )


def _fmt(value: float) -> str:
    """Format a number, dropping a trailing ``.0`` from whole values to keep files tidy."""
    return str(int(value)) if float(value).is_integer() else repr(float(value))


def dumps(level: LevelData, *, level_number: int = 0) -> str:
    """Serialize :class:`LevelData` back to the ``.dat`` text format."""
    out: list[str] = [f"Position Data For Level {level_number} - DO NOT MODIFY THIS FILE!"]
    empty = _fmt(EMPTY)

    for i in range(MAX_PLATFORMS):
        if i < len(level.platforms):
            p = level.platforms[i]
            out += [_fmt(p.x), _fmt(p.y), _fmt(p.width)]
        else:
            out += [empty] * _PLATFORM_FIELDS

    if level.pool is not None:
        out += [
            _fmt(level.pool.x),
            _fmt(level.pool.y),
            _fmt(level.pool.width),
            _fmt(level.pool.height),
        ]
    else:
        out += [empty] * _POOL_FIELDS

    for i in range(MAX_BLOCKS):
        if i < len(level.blocks):
            b = level.blocks[i]
            out += [_fmt(b.x), _fmt(b.y), "0" if b.coin else "1"]
        else:
            out += [empty] * _BLOCK_FIELDS

    if level.ledge is not None:
        out += [_fmt(level.ledge.x), _fmt(level.ledge.y), _fmt(level.ledge.width)]
    else:
        out += [empty] * _LEDGE_FIELDS

    out += [_fmt(level.door.x), _fmt(level.door.y)]
    out.append("1" if level.fences else "0")
    out.append("1" if level.foliage else "0")
    out.append(_fmt(level.seed))

    return "\n".join(out) + "\n"


def read_level(path: Path) -> LevelData:
    """Read a level from a ``.dat`` file."""
    return loads(path.read_text(encoding="utf-8"))


def write_level(path: Path, level: LevelData, *, level_number: int = 0) -> None:
    """Write a level to a ``.dat`` file (always LF line endings)."""
    path.write_text(dumps(level, level_number=level_number), encoding="utf-8", newline="\n")
