"""GameOverScene: shown when the player wins or runs out of lives. Any key returns to title."""

from __future__ import annotations

import pygame

from exit_dash.core import resources
from exit_dash.core.constants import (
    BLACK,
    BRIGHT_GREEN,
    BRIGHT_RED,
    LOGICAL_HEIGHT,
    LOGICAL_WIDTH,
    WHITE,
)
from exit_dash.core.input import InputState
from exit_dash.core.paths import asset_path
from exit_dash.core.scene import Replace, Scene, Transition
from exit_dash.core.settings import Settings


class GameOverScene(Scene):
    def __init__(self, won: bool, settings: Settings, *, audio: bool = True) -> None:
        self.won = won
        self.settings = settings
        self.audio = audio
        self._title_font = resources.font("jetset.ttf", 72)
        self._font = resources.font("jetset.ttf", 28)

    def on_enter(self) -> None:
        if not (self.audio and self.settings.music_enabled and pygame.mixer.get_init()):
            return
        track = "char1_3.ogg" if self.won else "gameover.ogg"
        try:
            pygame.mixer.music.load(str(asset_path("music", track)))
            pygame.mixer.music.set_volume(self.settings.volume)
            pygame.mixer.music.play(-1 if self.won else 0)
        except pygame.error:
            pass

    def handle_event(self, event: pygame.event.Event) -> Transition | None:
        if event.type == pygame.KEYDOWN:
            from exit_dash.scenes.title import TitleScene

            return Replace(TitleScene(self.settings, audio=self.audio))
        return None

    def update(self, dt: float, inp: InputState) -> Transition | None:
        return None

    def draw(self, surface: pygame.Surface, alpha: float) -> None:
        surface.fill(BLACK)
        message, color = ("You Win!", BRIGHT_GREEN) if self.won else ("Game Over", BRIGHT_RED)
        label = self._title_font.render(message, True, color)
        surface.blit(label, label.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 30)))
        prompt = self._font.render("Press any key to return to the title", True, WHITE)
        surface.blit(prompt, prompt.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 50)))
