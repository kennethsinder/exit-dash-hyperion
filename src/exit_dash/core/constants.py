"""Engine-wide constants: timestep, colours, render layers and the logical resolution.

Gameplay tunables (gravity, jump/run speeds, etc.) live with the entities that use
them; this module holds only values shared across the whole engine.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Final

RGB = tuple[int, int, int]

# --- Timestep -------------------------------------------------------------------------
# The simulation advances in fixed steps so physics and collision behave identically
# regardless of how fast the machine renders. 60 Hz matches the ~60-65 FPS the original
# game was tuned for, so the per-step velocity/gravity constants carry over unchanged.
FIXED_FPS: Final = 60
FIXED_DT: Final = 1.0 / FIXED_FPS
# Cap how many simulation steps a single rendered frame may run, so a long stall
# (debugger breakpoint, window drag) can't trigger a "spiral of death".
MAX_STEPS_PER_FRAME: Final = 5
# Ignore frame deltas larger than this (seconds); the loop drops the backlog instead.
MAX_FRAME_TIME: Final = 0.25

# --- Logical resolution ---------------------------------------------------------------
# The game renders at this fixed internal size; pygame.SCALED upscales it to the window
# or monitor and auto-scales mouse coordinates, so the game looks right on any display.
LOGICAL_WIDTH: Final = 1280
LOGICAL_HEIGHT: Final = 720
LOGICAL_SIZE: Final[tuple[int, int]] = (LOGICAL_WIDTH, LOGICAL_HEIGHT)

WINDOW_TITLE: Final = "Exit Dash: Hyperion"

# --- Colours ------------------------------------------------------------------- -------
WHITE: Final[RGB] = (255, 255, 255)
GREY: Final[RGB] = (185, 185, 185)
BLACK: Final[RGB] = (0, 0, 0)
RED: Final[RGB] = (155, 0, 0)
BRIGHT_RED: Final[RGB] = (175, 20, 20)
GREEN: Final[RGB] = (0, 155, 0)
BRIGHT_GREEN: Final[RGB] = (20, 175, 20)
BLUE: Final[RGB] = (0, 0, 155)
BRIGHT_BLUE: Final[RGB] = (20, 20, 175)
YELLOW: Final[RGB] = (255, 255, 0)


class Layer(IntEnum):
    """Draw order for the level's sprite groups (lower is drawn first).

    Mirrors the original ``Game.updateAll`` blit sequence exactly.
    """

    BACKGROUND = 0
    FAKE_DOOR = 10
    DOOR = 20
    POOL = 30
    FENCE = 40
    FOLIAGE = 50
    TORCH = 60
    PLATFORM = 70
    BLOCK = 80
    ENEMY = 90
    SPIKE = 100
    KEY = 110
    PLAYER = 120
