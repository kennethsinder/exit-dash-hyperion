"""OptionsScene: edits live settings, persists on exit, and renders headless."""

from __future__ import annotations

import pygame
import pytest

from exit_dash.core.scene import Pop
from exit_dash.core.settings import Settings, load_settings
from exit_dash.scenes.options import OptionsScene


def _key(scene: OptionsScene, key: int):
    return scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))


def test_options_edits_and_persists(pygame_ready, tmp_path):
    settings = Settings(music_enabled=False, volume=0.5)
    scene = OptionsScene(settings, audio=False, config_dir=tmp_path)

    # Row 0 is Music: a rightward nudge toggles it on.
    _key(scene, pygame.K_RIGHT)
    assert settings.music_enabled is True

    # Row 1 is Volume: step it down once.
    _key(scene, pygame.K_DOWN)
    _key(scene, pygame.K_LEFT)
    assert settings.volume == pytest.approx(0.4)

    # Esc finishes: it returns a Pop and writes the settings to disk.
    transition = _key(scene, pygame.K_ESCAPE)
    assert isinstance(transition, Pop)

    reloaded = load_settings(config_dir=tmp_path)
    assert reloaded.music_enabled is True
    assert reloaded.volume == pytest.approx(0.4)


def test_options_back_action_exits(pygame_ready, tmp_path):
    settings = Settings(music_enabled=False)
    scene = OptionsScene(settings, audio=False, config_dir=tmp_path)
    # Walk the cursor to the final "Back" row and activate it.
    for _ in range(len(scene.menu.options) - 1):
        _key(scene, pygame.K_DOWN)
    transition = _key(scene, pygame.K_RETURN)
    assert isinstance(transition, Pop)


def test_options_draws_without_error(pygame_ready):
    scene = OptionsScene(Settings(music_enabled=False), audio=False)
    surface = pygame.Surface((1280, 720))
    scene.draw(surface, 0.0)
