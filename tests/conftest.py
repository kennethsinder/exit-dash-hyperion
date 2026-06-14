"""Shared pytest configuration.

Forces pygame to run with no real display or audio so the whole suite is headless and
CI-friendly. These environment variables must be set before pygame is first imported.
"""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest


@pytest.fixture
def pygame_ready():
    """Ensure pygame and a (dummy) display surface are initialized for the test.

    Robust to a prior test having torn pygame down (e.g. the app smoke test).
    """
    if not pygame.get_init():
        pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((64, 64))
    yield
