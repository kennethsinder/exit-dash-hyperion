"""Exit Dash: Hyperion — a 2D platformer, modernized for Python 3 and pygame-ce.

This package is the single source of truth for the game. It is laid out as:

* :mod:`exit_dash.core`      — the engine: app loop, scene stack, input, settings, resources.
* :mod:`exit_dash.scenes`    — the screens: title, options, level, editor, game-over.
* :mod:`exit_dash.entities`  — the sprites: player, enemies, platforms, blocks, etc.
* :mod:`exit_dash.world`     — levels, camera, the procedural generator, hints.
* :mod:`exit_dash.ui`        — reusable widgets (buttons, sliders, toggles).
* :mod:`exit_dash.assets`    — bundled images, audio, fonts and level data.
"""

from __future__ import annotations

import os

# Suppress pygame's "Hello from the pygame community" banner on import. Must be set
# before pygame is first imported; this package is imported before any submodule that
# imports pygame, so setting it here covers the whole game.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

__version__ = "2.0.0"
__all__ = ["__version__"]
