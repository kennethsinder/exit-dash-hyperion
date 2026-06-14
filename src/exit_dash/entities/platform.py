"""Platform: a tiled, walkable surface.

Supports ``platform[0..3]`` indexing (left, top, right, bottom) because the collision
code treats platforms like rects — preserved verbatim from the original. The full tiled
surface is composited once into ``image`` for fast drawing.
"""

from __future__ import annotations

import pygame

from exit_dash.core import resources


class Platform:
    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        *,
        vx: float = 0.0,
        vy: float = 0.0,
        style: str = "grass",
    ) -> None:
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.style = style
        self.width = float(width)
        self._correct_reversed_coords()

        tile = resources.image("environment", "main", f"{style}Mid.png")
        self.tile_width = tile.get_width()
        # Snap width to a whole number of tiles, as the original did.
        self.width -= self.width % self.tile_width
        self.height = tile.get_height()

        left = resources.image("environment", "main", f"{style}CliffLeft.png")
        right = resources.image("environment", "main", f"{style}CliffRight.png")

        self.image = pygame.Surface((int(self.width), self.height), pygame.SRCALPHA)
        self.image.blit(left, (0, 0))
        self.image.blit(right, (int(self.width - self.tile_width), 0))
        for i in range(self.tile_width, int(self.width - self.tile_width), self.tile_width):
            self.image.blit(tile, (i, 0))

    def _correct_reversed_coords(self) -> None:
        if self.width < 0:
            self.x += self.width
            self.width *= -1

    def __getitem__(self, i: int) -> float:
        # 0..3 -> left x, top y, right x, bottom y.
        if i == 0:
            return self.x
        if i == 1:
            return self.y
        if i == 2:
            return self.x + self.width
        if i == 3:
            return self.y + self.height
        return i

    def __setitem__(self, k: int, v: float) -> None:
        if k == 0:
            self.x = v
        elif k == 1:
            self.y = v
        elif k == 2:
            self.x = v - self.width
        elif k == 3:
            self.y = v - self.height

    def update_motion(self, borders: tuple[float, float, float, float]) -> None:
        """Move by velocity, wrapping around the level borders (left, top, right, bottom)."""
        self.x += self.vx
        self.y += self.vy
        if self.x >= borders[2] and self.vx > 0:
            self.x = borders[0] - self.width
        elif (self.x - self.width) <= borders[0] and self.vx < 0:
            self.x = borders[2]
        elif self.y >= borders[3] and self.vy > 0:
            self.y = borders[1] - self.height
        elif (self.y + self.height) <= borders[1] and self.vy < 0:
            self.y = borders[3]

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, (self.x, self.y))

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
