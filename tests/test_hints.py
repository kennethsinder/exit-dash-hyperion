"""Hint text: ``{TOKEN}`` interpolation and per-level lookup."""

from __future__ import annotations

from exit_dash.core.keybindings import key_names
from exit_dash.world.hints import hint_for_level, interpret_hint

FAKE_NAMES = {"DUCK": "down", "ACTION": "up", "LEFT": "left", "RIGHT": "right"}


def test_token_is_substituted_and_quoted():
    assert interpret_hint("Use {DUCK} to duck", FAKE_NAMES) == 'Use "down" to duck'


def test_none_becomes_empty():
    assert interpret_hint("None", FAKE_NAMES) == ""


def test_text_without_token_is_unchanged():
    assert interpret_hint("Hey, who turned out the lights?", FAKE_NAMES) == (
        "Hey, who turned out the lights?"
    )


def test_token_only():
    assert interpret_hint("{ACTION}", FAKE_NAMES) == '"up"'


def test_trailing_newline_preserved():
    assert interpret_hint("Jump with {ACTION}\n", FAKE_NAMES) == 'Jump with "up"\n'


def test_key_names_resolve_real_keys(pygame_ready):
    names = key_names()
    assert names["DUCK"] == "down"
    assert names["ACTION"] == "up"


def test_level_1_hint_substitutes_token(pygame_ready):
    hint = hint_for_level(1, key_names())
    assert hint  # level 1 has a hint
    assert "{" not in hint and "}" not in hint  # token was substituted


def test_out_of_range_level_returns_empty(pygame_ready):
    assert hint_for_level(999, key_names()) == ""
