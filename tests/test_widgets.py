"""Unit tests for the keyboard-driven menu widgets."""

from __future__ import annotations

import pygame
import pytest

from exit_dash.ui.widgets import Action, Choice, Menu, Slider, Toggle


def test_toggle_flips_through_callbacks():
    box = {"v": False}
    toggle = Toggle("X", lambda: box["v"], lambda v: box.update(v=v))
    assert toggle.value_text() == "Off"
    toggle.adjust(1)
    assert box["v"] is True
    assert toggle.value_text() == "On"
    toggle.activate()
    assert box["v"] is False


def test_slider_steps_and_clamps():
    box = {"v": 0.5}
    slider = Slider("Vol", lambda: box["v"], lambda v: box.update(v=v), step=0.1, lo=0.0, hi=1.0)
    slider.adjust(1)
    assert box["v"] == pytest.approx(0.6)
    for _ in range(10):
        slider.adjust(1)
    assert box["v"] == pytest.approx(1.0)  # clamped at the top
    for _ in range(30):
        slider.adjust(-1)
    assert box["v"] == pytest.approx(0.0)  # clamped at the bottom


def test_choice_cycles_with_wraparound():
    box = {"v": "a"}
    choice = Choice("C", ["a", "b", "c"], lambda: box["v"], lambda v: box.update(v=v))
    choice.adjust(1)
    assert box["v"] == "b"
    choice.adjust(-1)
    choice.adjust(-1)
    assert box["v"] == "c"  # wrapped past the start


def test_action_only_fires_on_activate():
    fired = {"n": 0}
    action = Action("Go", lambda: fired.update(n=fired["n"] + 1))
    action.adjust(1)  # left/right does nothing
    assert fired["n"] == 0
    action.activate()
    assert fired["n"] == 1


def test_menu_navigation_wraps_and_edits(pygame_ready):
    font = pygame.font.Font(None, 20)
    box = {"on": False}
    options = [
        Toggle("a", lambda: box["on"], lambda v: box.update(on=v)),
        Action("b", lambda: None),
    ]
    menu = Menu(options, font)
    assert menu.index == 0
    menu.handle_key(pygame.K_DOWN)
    assert menu.index == 1
    menu.handle_key(pygame.K_DOWN)
    assert menu.index == 0  # wrapped
    menu.handle_key(pygame.K_UP)
    assert menu.index == 1  # wrapped back
    menu.handle_key(pygame.K_RIGHT)  # edits row 1 (the action — no effect)
    menu.index = 0
    menu.handle_key(pygame.K_RIGHT)
    assert box["on"] is True
