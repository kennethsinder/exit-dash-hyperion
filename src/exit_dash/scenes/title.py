"""TitleScene: the entry screen. Pick a character (1/2/3) to start, Esc to quit."""

from __future__ import annotations

import pygame

from exit_dash.core import resources
from exit_dash.core.constants import (
    BLACK,
    LOGICAL_HEIGHT,
    LOGICAL_WIDTH,
    WHITE,
    WINDOW_TITLE,
    YELLOW,
)
from exit_dash.core.input import InputState
from exit_dash.core.paths import asset_path
from exit_dash.core.scene import Quit, Replace, Scene, Transition
from exit_dash.core.settings import Settings

_CHARACTER_KEYS = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3}


class TitleScene(Scene):
    def __init__(self, settings: Settings, *, audio: bool = True) -> None:
        self.settings = settings
        self.audio = audio
        self._background = resources.image("backgrounds", "main", "title.jpg", alpha=False)
        self._background = pygame.transform.smoothscale(
            self._background, (LOGICAL_WIDTH, LOGICAL_HEIGHT)
        )
        self._title_font = resources.font("jetset.ttf", 72)
        self._font = resources.font("jetset.ttf", 28)
        self._small = resources.font("atari.ttf", 16)
        self._character_previews = [
            resources.image("character", "main", f"p{i}_front.png") for i in (1, 2, 3)
        ]

    def on_enter(self) -> None:
        if self.audio and self.settings.music_enabled and pygame.mixer.get_init():
            try:
                pygame.mixer.music.load(str(asset_path("music", "menuloop.ogg")))
                pygame.mixer.music.set_volume(self.settings.volume)
                pygame.mixer.music.play(-1)
            except pygame.error:
                pass

    def handle_event(self, event: pygame.event.Event) -> Transition | None:
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            return Quit()
        if event.key in _CHARACTER_KEYS:
            from exit_dash.scenes.level import LevelScene

            char = _CHARACTER_KEYS[event.key]
            return Replace(LevelScene(1, char, self.settings, audio=self.audio))
        return None

    def update(self, dt: float, inp: InputState) -> Transition | None:
        return None

    def draw(self, surface: pygame.Surface, alpha: float) -> None:
        surface.fill(BLACK)
        surface.blit(self._background, (0, 0))

        title = self._title_font.render(WINDOW_TITLE, True, WHITE)
        surface.blit(title, title.get_rect(center=(LOGICAL_WIDTH // 2, 140)))

        prompt = self._font.render("Choose your character — press 1, 2 or 3", True, YELLOW)
        surface.blit(prompt, prompt.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 150)))

        # Character previews with their number.
        spacing = 220
        start_x = LOGICAL_WIDTH // 2 - spacing
        for i, preview in enumerate(self._character_previews):
            x = start_x + i * spacing
            rect = preview.get_rect(center=(x, LOGICAL_HEIGHT // 2))
            surface.blit(preview, rect)
            label = self._font.render(str(i + 1), True, WHITE)
            surface.blit(label, label.get_rect(center=(x, rect.bottom + 24)))

        footer = self._small.render(
            "Arrows move · Up/Space jump · Down duck · Esc quit", True, WHITE
        )
        surface.blit(footer, footer.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 60)))
