"""Audio assets: the curated music tracks and sound effects load in pygame.

Guards the MP3/WAV->OGG conversion done in the asset pipeline. Skips automatically if no
audio mixer is available (some CI containers).
"""

from __future__ import annotations

import pygame
import pytest

from exit_dash.core.paths import asset_path

MUSIC = ["char1_3.ogg", "waking_devil.ogg", "gameover.ogg", "menuloop.ogg"]
SOUND_EFFECTS = ["synthetic_explosion_1.ogg"]


@pytest.fixture(scope="module")
def mixer():
    try:
        pygame.mixer.init()
    except pygame.error:
        pytest.skip("audio mixer unavailable")
    if pygame.mixer.get_init() is None:
        pytest.skip("audio mixer unavailable")
    yield
    pygame.mixer.quit()


@pytest.mark.parametrize("name", MUSIC)
def test_music_track_loads(mixer, name):
    pygame.mixer.music.load(str(asset_path("music", name)))


@pytest.mark.parametrize("name", SOUND_EFFECTS)
def test_sound_effect_loads(mixer, name):
    sound = pygame.mixer.Sound(str(asset_path("sounds", name)))
    assert sound.get_length() > 0
