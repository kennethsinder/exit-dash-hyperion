"""World assembly from saved level data (the load path)."""

from __future__ import annotations

import random
import threading

import pytest

from exit_dash.core.paths import asset_path
from exit_dash.entities.player import PlayableCharacter
from exit_dash.world import loader
from exit_dash.world.level import DoorRec, LevelData, PlatformRec
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


def test_degenerate_level_does_not_hang(player):
    # Every non-spawn platform shares one x, so the longest platform is among them and the
    # rejection loop in generate_mobs can never find a differently-placed platform. The old
    # code spun forever here; the engine must now build the level (placing no ground mobs)
    # instead of hanging. Built on a watchdog thread so a regression fails loudly rather
    # than freezing the whole suite (pytest-timeout is not a dependency).
    data = LevelData(
        door=DoorRec(800, 400),
        platforms=[
            PlatformRec(-2000, 600, 300),  # spawn platform, at a distinct x
            PlatformRec(800, 600, 200),
            PlatformRec(800, 400, 400),  # widest non-spawn -> the "longest", at x=800
            PlatformRec(800, 200, 300),
        ],
        seed=1.0,
    )
    result: dict[str, World] = {}

    def build() -> None:
        result["world"] = World.from_level_data(
            data, player=player, screen_w=1280, screen_h=720, rng=random.Random(1)
        )

    worker = threading.Thread(target=build, daemon=True)
    worker.start()
    worker.join(timeout=15.0)
    assert not worker.is_alive(), (
        "generate_mobs hung on a degenerate level (infinite-loop regression)"
    )

    world = result["world"]
    # The level still builds and is winnable-shaped; only the patrol fly is placed, since
    # no platform is eligible to host a ground mob.
    assert [e.mob_type for e in world.enemies] == ["fly"]
    assert world.door is not None and world.keys


def test_single_platform_level_raises(player):
    # gather_platform_info() seeds its extremes from platforms[1]; one platform can't build.
    data = LevelData(door=DoorRec(0, 0), platforms=[PlatformRec(0, 600, 300)])
    with pytest.raises(ValueError, match="two platforms"):
        World.from_level_data(data, player=player, screen_w=1280, screen_h=720)
