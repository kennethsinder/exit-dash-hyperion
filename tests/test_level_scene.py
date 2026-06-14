"""LevelScene integration: a real level boots and runs headless without the player dying."""

from __future__ import annotations

import pytest

from exit_dash.core.app import Application
from exit_dash.core.settings import Settings
from exit_dash.scenes.level import LevelScene


@pytest.mark.parametrize("level", [1, 2])
def test_level_runs_headless(level):
    settings = Settings(music_enabled=False, developer_mode=False, decorations=True)
    app = Application(headless=True)
    scene = LevelScene(level, which_char=1, settings=settings, audio=False)
    try:
        frames = app.run(scene, max_frames=200)
    finally:
        app.quit()

    assert frames == 200, "the level loop should run to completion without crashing"
    assert scene.player.visible, "player should not have fallen out of the world"
    assert scene.player.lives > 0, "player should survive the intro walk-in with no input"
