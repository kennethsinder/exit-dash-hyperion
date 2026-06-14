"""Golden physics tests: the ported motion/collision must match the original exactly.

The fixed-timestep integration is deterministic, so the jump arc has exact expected
values. Terminal velocity (capped at ``platform.height - 5``) stays below the landing
band height (``platform.height + 35``), which is what prevents tunnelling — verified here.
"""

from __future__ import annotations

import pytest

from exit_dash.entities.character import Character
from exit_dash.entities.platform import Platform


@pytest.fixture
def platform(pygame_ready):
    # Wide stone platform with its top at y=500.
    return Platform(0, 500, 600, style="stone")


def test_jump_sets_expected_velocity(platform):
    char = Character(100, 100, which_char=1)
    char.on_ground = False
    char.jump()
    assert char.vy == -30  # floor(-1.0 * JUMP_SPEED)


def test_jump_arc_apex_is_deterministic(platform):
    char = Character(100, 100, which_char=1)
    char.on_ground = False
    char.jump()
    start_y = char.y

    # vy goes -30, -27.5, ... reaching 0 after 12 steps; total rise = 2.5*(1+..+12) = 195.
    for _ in range(12):
        char.update_motion([platform])

    assert char.vy == 0.0
    assert char.y == start_y - 195


def test_lands_on_platform_without_tunnelling(platform):
    char = Character(100, 0, which_char=1)
    char.on_ground = False
    # Feet just above the platform top, falling near terminal velocity.
    char.y = platform.y - char.height - 5
    char.vy = 60

    char.update_motion([platform])
    char.collide([platform], [], [], None, None)

    assert char.on_ground is True
    assert char.y == platform.y - char.height  # resting exactly on top, no overshoot


def test_terminal_velocity_is_capped(platform):
    char = Character(100, 0, which_char=1)
    char.on_ground = False
    char.vy = platform.height + 100  # way over terminal
    char.update_motion([platform])
    # Capped to platform.height - 5, then gravity is added once.
    assert char.vy == (platform.height - 5) + char.gravity


def test_max_jump_height_matches_kinematics(platform):
    char = Character(100, 100, which_char=1)
    # jump_time = 30 / 2.5 = 12; max_jump_height = floor(0.5 * 30 * 12) = 180.
    assert char.jump_time == 12.0
    assert char.max_jump_height == 180
