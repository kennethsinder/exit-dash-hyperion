"""Torch: a wall light that the player can ignite to illuminate dark levels."""

from __future__ import annotations

from random import randint

import pygame

from exit_dash.core import resources

_ENV = ("environment", "main")


class Torch:
    def __init__(self, x: float, y: float) -> None:
        self.x = float(x)
        self.y = float(y)
        self.burning = False
        self.on_image_1 = resources.image(*_ENV, "torchLit.png")
        self.on_image_2 = resources.image(*_ENV, "torchLit2.png")
        self.off_image = resources.image(*_ENV, "torch.png")
        self.width = self.off_image.get_width()
        self.height = self.off_image.get_height()
        self.image = self.off_image

    def draw(self, surface: pygame.Surface) -> None:
        if not self.burning:
            surface.blit(self.off_image, (self.x, self.y))
        elif randint(0, 1) == 1:
            surface.blit(self.on_image_1, (self.x, self.y))
        else:
            surface.blit(self.on_image_2, (self.x, self.y))

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
