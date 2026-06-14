"""Checkpoint: a fence the player touches to set their respawn point."""

from __future__ import annotations

import pygame

from exit_dash.core import resources


class Checkpoint:
    def __init__(self, x: float, y: float, is_broken: bool = False) -> None:
        self.x = float(x)
        self.y = float(y)
        self.image = resources.image("environment", "main", "fence.png")
        self.image_broken = resources.image("environment", "main", "fenceBroken.png")
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.broken = is_broken

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image_broken if self.broken else self.image, (self.x, self.y))

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
