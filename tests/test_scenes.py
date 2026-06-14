"""Scene-stack transitions between title, level and game-over screens."""

from __future__ import annotations

import pygame

from exit_dash.core.scene import SceneManager
from exit_dash.core.settings import Settings
from exit_dash.scenes.gameover import GameOverScene
from exit_dash.scenes.level import LevelScene
from exit_dash.scenes.title import TitleScene


def _settings() -> Settings:
    return Settings(music_enabled=False, developer_mode=False)


def test_title_starts_chosen_character(pygame_ready):
    manager = SceneManager(TitleScene(_settings(), audio=False))
    manager.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2))
    assert isinstance(manager.current, LevelScene)
    assert manager.current.which_char == 2


def test_title_quits_on_escape(pygame_ready):
    manager = SceneManager(TitleScene(_settings(), audio=False))
    manager.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert not manager.running


def test_gameover_returns_to_title(pygame_ready):
    manager = SceneManager(GameOverScene(won=True, settings=_settings(), audio=False))
    manager.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert isinstance(manager.current, TitleScene)


def test_level_win_goes_to_gameover(pygame_ready):
    scene = LevelScene(1, 1, _settings(), audio=False, final_level=1)
    # Completing the final level should hand off to a "won" game-over screen.
    transition = scene._advance_level()
    from exit_dash.core.scene import Replace

    assert isinstance(transition, Replace)
    assert isinstance(transition.scene, GameOverScene)
    assert transition.scene.won is True
