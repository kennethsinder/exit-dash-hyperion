#!/usr/bin/env python3
"""Audit which bundled assets are referenced by the game vs orphaned.

Run from the repo root: ``uv run python scripts/asset_manifest.py``.

"Referenced" is computed as the union of:

* every complete asset filename that appears as a string literal in the source, and
* the *dynamic* filename families the code builds by concatenation (terrain themes,
  key colours, slime colours, player walk frames, HUD digits, explosion frames, ...),
  which a plain string scan cannot see.

Matching is by basename, which deliberately *over-keeps* (a file is considered
referenced if its name is used anywhere), so the orphan list is conservative — safe to
delete. The script only reports; it never deletes anything.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ASSETS = REPO / "src" / "exit_dash" / "assets"
# Scan both the new package and the legacy reference tree for asset references.
SOURCE_DIRS = [REPO / "src" / "exit_dash", REPO / "data"]

ASSET_EXTS = ("png", "jpg", "jpeg", "bmp", "gif", "ogg", "mp3", "wav", "ttf", "otf")
_FILENAME_RE = re.compile(rf"[\w .()-]+?\.(?:{'|'.join(ASSET_EXTS)})")

THEMES = ["castle", "dirt", "grass", "sand", "snow", "stone"]
KEY_COLORS = ["blue", "green", "red", "yellow"]
SLIME_COLORS = ["Blue", "Green"]
PLAYERS = [1, 2, 3]
PLAYER_WALK_FRAMES = range(1, 12)  # p{n}_walk1..11
HUD_DIGITS = range(10)
EXPLOSION_FRAMES = range(3)


def dynamic_family_names() -> set[str]:
    """Concretely expand the filename families the code builds by concatenation."""
    names: set[str] = set()
    for theme in THEMES:
        names |= {f"{theme}Mid.png", f"{theme}CliffLeft.png", f"{theme}CliffRight.png"}
    names |= {f"key{c}.png" for c in KEY_COLORS}
    for c in SLIME_COLORS:
        names |= {f"slime{c}_{s}.png" for s in ("walk", "walkR", "squashed", "squashedR")}
    for n in PLAYERS:
        names |= {f"p{n}_front.png", f"p{n}_jump.png", f"p{n}_jump_l.png"}
        names |= {f"p{n}_duck.png", f"p{n}_duck_l.png"}
        names |= {f"p{n}_walk{i}.png" for i in PLAYER_WALK_FRAMES}
        names.add(f"hud_p{n}.png")
    names |= {f"hud_{d}.png" for d in HUD_DIGITS}
    names |= {f"explosion{i}.png" for i in EXPLOSION_FRAMES}
    return names


def referenced_names() -> set[str]:
    names = dynamic_family_names()
    for source_dir in SOURCE_DIRS:
        for py in source_dir.rglob("*.py"):
            for match in _FILENAME_RE.findall(py.read_text(encoding="utf-8")):
                names.add(match.strip().rsplit("/", 1)[-1].rsplit("\\", 1)[-1])
    return names


def _human(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"


def main() -> None:
    referenced = referenced_names()
    orphans: list[Path] = []
    orphan_bytes = 0
    kept = 0

    for path in sorted(ASSETS.rglob("*")):
        if not path.is_file() or path.name.endswith(".txt"):
            continue
        if path.name in referenced:
            kept += 1
        else:
            orphans.append(path)
            orphan_bytes += path.stat().st_size

    by_dir: dict[str, tuple[int, int]] = {}
    for path in orphans:
        top = path.relative_to(ASSETS).parts[0]
        count, size = by_dir.get(top, (0, 0))
        by_dir[top] = (count + 1, size + path.stat().st_size)

    print(f"Referenced names: {len(referenced)} | kept files: {kept} | orphans: {len(orphans)}")
    print(f"Reclaimable from orphans: {_human(orphan_bytes)}\n")
    print(f"{'directory':<16} {'orphans':>8} {'size':>10}")
    print("-" * 36)
    for top, (count, size) in sorted(by_dir.items(), key=lambda kv: -kv[1][1]):
        print(f"{top:<16} {count:>8} {_human(size):>10}")


if __name__ == "__main__":
    main()
