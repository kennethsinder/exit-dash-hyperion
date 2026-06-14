"""Smoke-construct every entity headless to catch missing assets and import errors."""

from __future__ import annotations

import pytest

from exit_dash.entities.background import Background
from exit_dash.entities.block import Block
from exit_dash.entities.character import Character
from exit_dash.entities.checkpoint import Checkpoint
from exit_dash.entities.door import Door
from exit_dash.entities.enemy import AICharacter
from exit_dash.entities.foliage import BackgroundFoliage
from exit_dash.entities.key import Key
from exit_dash.entities.platform import Platform
from exit_dash.entities.player import PlayableCharacter
from exit_dash.entities.pool import Pool
from exit_dash.entities.spike import FallingSpike
from exit_dash.entities.torch import Torch


@pytest.mark.parametrize("which_char", [1, 2, 3])
def test_player_and_character_construct(pygame_ready, which_char):
    char = Character(0, 0, which_char=which_char)
    assert char.width > 0 and char.height > 0
    player = PlayableCharacter(0, 0, which_char=which_char)
    assert player.lives > 0


@pytest.mark.parametrize("mob", ["slime", "snail", "fly", "fish"])
def test_enemy_constructs_and_draws(pygame_ready, mob):
    import pygame

    enemy = AICharacter(0, 0, 2, 0, properties=(mob, -1, -1))
    surface = pygame.Surface((64, 64))
    enemy.draw(surface)  # forces lazy image selection for this mob type
    assert enemy.width > 0


def test_world_objects_construct(pygame_ready):
    Platform(0, 500, 300, style="stone")
    Block(100, 100, "coin")
    Block(100, 100, "explosive")
    Pool(0, 500, 300, 120, style="stone")
    FallingSpike(50, 50)
    Door(100, 500)
    Key(100, 100, "blue")
    Checkpoint(100, 100)
    BackgroundFoliage(100, 100)
    Torch(100, 100)


def test_background_constructs(pygame_ready):
    import pygame

    Background(pygame.Surface((200, 150)), 1280, 720)


def test_player_jump_and_hud_draw(pygame_ready):
    import pygame

    from exit_dash.core.input import PlayerInput

    player = PlayableCharacter(100, 400, which_char=1)
    platform = Platform(0, 500, 600, style="stone")
    player.on_ground = True
    player.can_jump = True  # jump was released on a prior frame (the latch is armed)
    # Pressing jump from the ground should launch the player.
    player.move(PlayerInput(jump=True), [platform], [], [], 1280, 720, autoscroll=False)
    assert player.jumping is True
    assert player.vy == -35  # PlayableCharacter jump_speed for char 1
    surface = pygame.Surface((1280, 720))
    player.draw(surface)  # HUD draw must not raise
