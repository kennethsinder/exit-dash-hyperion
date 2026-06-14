"""Pool: a water hazard with walkable platform edges and an open middle."""

from __future__ import annotations

import pygame

from exit_dash.core import resources

_ENV = ("environment", "main")


class Pool:
    def __init__(
        self, x: float, y: float, width: float, height: float, style: str = "grass"
    ) -> None:
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.width = float(width)
        self.height = float(height)

        self.image = resources.image(*_ENV, f"{style}Mid.png")
        self.plain_image = resources.image(*_ENV, f"{style}Center.png")
        self.left_image = resources.image(*_ENV, f"{style}CliffLeft.png")
        self.right_image = resources.image(*_ENV, f"{style}CliffRight.png")
        self.tile_width = self.image.get_width()

        self.water_filled = resources.image(*_ENV, "liquidWater.png")
        self.water_top = resources.image(*_ENV, "liquidWaterTop_mid.png")

        self.width -= self.width % self.tile_width
        self.height -= self.height % self.tile_width
        self.tiles_on_either_side = 2
        self.pool_start_x = int(self.x + self.tiles_on_either_side * self.tile_width)
        self.pool_end_x = int(self.x + self.width - 2 * self.tile_width)

    def update_motion(self) -> None:
        self.x += self.vx
        self.y += self.vy

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.left_image, (self.x, self.y))
        surface.blit(self.right_image, (self.x + self.width - self.tile_width, self.y))

        self.pool_start_x = int(self.x + self.tiles_on_either_side * self.tile_width)
        self.pool_end_x = int(
            self.x + self.width - (1 + self.tiles_on_either_side) * self.tile_width
        )
        for x in range(
            int(self.x) + self.tile_width, self.pool_start_x + self.tile_width, self.tile_width
        ):
            surface.blit(self.image, (x, self.y))
        for x in range(
            self.pool_end_x, int(self.x + self.width - self.tile_width), self.tile_width
        ):
            surface.blit(self.image, (x, self.y))

        for y in range(int(self.y + self.tile_width), int(self.y + self.height), self.tile_width):
            surface.blit(self.plain_image, (self.pool_start_x, y))
            surface.blit(self.plain_image, (self.pool_end_x, y))

        for x in range(self.pool_start_x, self.pool_end_x + self.tile_width, self.tile_width):
            surface.blit(self.plain_image, (x, self.y + self.height))

        for y in range(int(self.y + self.tile_width), int(self.y + self.height), self.tile_width):
            for x in range(self.pool_start_x + self.tile_width, self.pool_end_x, self.tile_width):
                surface.blit(self.water_filled, (x, y))
        for x in range(self.pool_start_x + self.tile_width, self.pool_end_x, self.tile_width):
            surface.blit(self.water_top, (x, self.y))
