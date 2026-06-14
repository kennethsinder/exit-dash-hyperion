"""Smoke test: the engine boots headless and runs a bounded, deterministic loop."""

from __future__ import annotations

import pygame

from exit_dash.core.app import Application
from exit_dash.core.input import InputState
from exit_dash.core.scene import Scene, Transition


class _NullScene(Scene):
    """A scene that counts its fixed-step updates and draws a solid fill."""

    def __init__(self) -> None:
        self.updates = 0

    def update(self, dt: float, inp: InputState) -> Transition | None:
        self.updates += 1
        return None

    def draw(self, surface: pygame.Surface, alpha: float) -> None:
        surface.fill((0, 0, 0))


def test_headless_runs_exact_frame_count():
    app = Application(headless=True)
    scene = _NullScene()
    try:
        frames = app.run(scene, max_frames=120)
    finally:
        app.quit()
    # Deterministic headless mode advances exactly one fixed step per rendered frame.
    assert frames == 120
    assert scene.updates == 120
