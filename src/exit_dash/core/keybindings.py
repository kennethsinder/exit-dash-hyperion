"""Default key bindings and human-readable key names.

This mirrors the original ``keymap.SUMMARY`` token table. It is the single source of
truth for which physical keys map to which game tokens, used both by the input layer
and by hint-text interpolation (``{DUCK}`` -> ``"down"``).
"""

from __future__ import annotations

from collections.abc import Mapping

import pygame

#: Game token -> pygame key constant.
DEFAULT_BINDINGS: dict[str, int] = {
    "ACTION": pygame.K_UP,
    "ACTION2": pygame.K_SPACE,
    "LEFT": pygame.K_LEFT,
    "RIGHT": pygame.K_RIGHT,
    "DUCK": pygame.K_DOWN,
    "EXIT": pygame.K_ESCAPE,
    "EXIT2": pygame.K_q,
}


def key_names(bindings: Mapping[str, int] | None = None) -> dict[str, str]:
    """Return a ``token -> human key name`` map (e.g. ``{"DUCK": "down"}``)."""
    bindings = DEFAULT_BINDINGS if bindings is None else bindings
    return {token: pygame.key.name(code) for token, code in bindings.items()}
