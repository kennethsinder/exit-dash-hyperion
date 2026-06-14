"""BackgroundFoliage: a decorative rock/hill/plant/bush placed near platforms."""

from __future__ import annotations

from random import choice

import pygame

from exit_dash.core import resources


class BackgroundFoliage:
    def __init__(self, x: float, y: float) -> None:
        self.x = float(x)
        self.y = float(y)
        self.images = [
            resources.image("items", "rock.png"),
            resources.image("environment", "main", "hill_smallAlt.png"),
            resources.image("items", "plant.png"),
            resources.image("items", "bush.png"),
        ]
        self.image = choice(self.images)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, (self.x, self.y))
