"""Per-level hint text and ``{TOKEN}`` key-name interpolation.

A hint may embed one binding token in braces, e.g. ``"Use {DUCK} to duck"``, which is
replaced with the quoted human key name (``Use "down" to duck``). This reproduces the
original ``interpretHintString`` behavior: the *last* ``{...}`` pair is substituted, the
literal string ``"None"`` becomes empty, and text without braces is returned unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from exit_dash.core.paths import asset_path


def interpret_hint(hint: str, names: Mapping[str, str]) -> str:
    """Substitute a ``{TOKEN}`` in ``hint`` with the quoted key name from ``names``."""
    hint = str(hint)
    if hint == "None":
        return ""
    start_brace = hint.rfind("{")
    if start_brace == -1:
        return hint
    end_brace = hint.rfind("}")
    if end_brace <= start_brace:
        return hint
    token = hint[start_brace + 1 : end_brace]
    name = names.get(token, token)
    return f'{hint[:start_brace]}"{name}"{hint[end_brace + 1 :]}'


def hint_lines(path: Path | None = None) -> list[str]:
    """Return the raw hint lines (one per level), or an empty list if the file is absent."""
    path = asset_path("levels", "lvlhints.dat") if path is None else path
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return text.split("\n")


def hint_for_level(level: int, names: Mapping[str, str], lines: Sequence[str] | None = None) -> str:
    """Return the interpreted hint for a 1-based ``level``, or ``""`` if none exists."""
    if lines is None:
        lines = hint_lines()
    if not 1 <= level <= len(lines):
        return ""
    return interpret_hint(lines[level - 1], names)
