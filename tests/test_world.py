"""World assembly from saved level data (the load path)."""

from __future__ import annotations

import random

import pytest

from exit_dash.core.paths import asset_path
from exit_dash.entities.player import PlayableCharacter
from exit_dash.world import loader
from exit_dash.world.world import World


@pytest.fixture
def player(pygame_ready):
    return PlayableCharacter(0, 0, which_char=1)


@pytest.mark.parametrize("level", [1, 2, 3, 4])
def test_world_builds_from_shipped_level(player, level):
    data = loader.read_level(asset_path("levels", f"lvl_{level}.dat"))
    world = World.from_level_data(
        data,
        player=player,
        screen_w=1280,
        screen_h=720,
        theme="stone",
        level=level,
        rng=random.Random(level),
    )

    assert len(world.platforms) >= 1
    assert world.door is not None
    assert world.fakedoor is not None
    assert world.keys, "a level must have at least one key to win"
    assert world.enemies, "generate_mobs places at least the patrol fly"
    # Player is placed on the first platform and starts as a CPU-driven walk-in.
    assert world.player.cpu_controlled is True
    # Everything that scrolls is registered with the camera's movable set.
    assert world.background is None or world.background in world.movable_objects


def test_world_is_deterministic_for_fixed_seed(player):
    data = loader.read_level(asset_path("levels", "lvl_1.dat"))
    p2 = PlayableCharacter(0, 0, which_char=1)
    w1 = World.from_level_data(
        data, player=player, screen_w=1280, screen_h=720, rng=random.Random(7)
    )
    w2 = World.from_level_data(data, player=p2, screen_w=1280, screen_h=720, rng=random.Random(7))
    assert len(w1.enemies) == len(w2.enemies)
    assert [e.mob_type for e in w1.enemies] == [e.mob_type for e in w2.enemies]
    assert w1.autoscroll == w2.autoscroll


def test_generated_level_is_reproducible_from_seed(player):
    p2 = PlayableCharacter(0, 0, which_char=1)
    w1 = World(player, 1280, 720, theme="stone", level=3, rng=random.Random()).generate(15, seed=42)
    w2 = World(p2, 1280, 720, theme="stone", level=3, rng=random.Random()).generate(15, seed=42)
    assert len(w1.platforms) == len(w2.platforms)
    assert [round(p.x, 3) for p in w1.platforms] == [round(p.x, 3) for p in w2.platforms]
    assert len(w1.blocks) == len(w2.blocks)
    assert [e.mob_type for e in w1.enemies] == [e.mob_type for e in w2.enemies]
    assert w1.door is not None and w1.keys
