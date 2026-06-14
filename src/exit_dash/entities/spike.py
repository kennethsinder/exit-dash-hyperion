"""FallingSpike: an icicle that dislodges and falls when the player passes beneath it."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from exit_dash.core import resources

if TYPE_CHECKING:
    from collections.abc import Sequence

    from exit_dash.entities.block import Block
    from exit_dash.entities.character import Character
    from exit_dash.entities.platform import Platform

_GRAVITY_ACCELERATION = 1.5


class FallingSpike:
    def __init__(self, x: float, y: float) -> None:
        # ``x`` is the centre x of the spike.
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0

        self.image = resources.image("environment", "main", "spikeTop.png", alpha=False)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.x -= int(0.5 * self.width)

        self.visible = True
        self.gravity_acceleration = _GRAVITY_ACCELERATION
        self.dislodged = False

    def collide(self, chars: Sequence[Character], platforms: Sequence[Platform]) -> None:
        centre = (int(self.x + self.width / 2), self.y + int(0.5 * self.height))
        for char in chars:
            char_rect = pygame.Rect(int(char.x), int(char.y), int(char.width), int(char.height))
            if char_rect.collidepoint(centre) and self.visible and not char.flashing:
                char.health -= 1
                char.flashing = True
                self.visible = False

    def update_motion(self, chars: Sequence[Character], platforms: Sequence[Platform]) -> None:
        self.x += self.vx
        self.y += int(self.vy)
        if not (0 <= self.x <= 2000 and 0 <= self.y <= 2000):
            return
        for char in chars:
            if char.x + char.width >= self.x and char.x <= self.x + self.width and char.y >= self.y:
                self.dislodged = True
        if self.vy >= platforms[0].height:
            self.vy = platforms[0][3] - platforms[0][1] - 5
        if self.dislodged:
            self.vy += self.gravity_acceleration

    def draw(
        self,
        platforms: Sequence[Platform],
        blocks: Sequence[Block],
        surface: pygame.Surface,
    ) -> None:
        if self.visible:
            surface.blit(self.image, (self.x, self.y))
        if self.visible and self.dislodged and 0 <= self.x <= 2000 and 0 <= self.y <= 2000:
            for platform in platforms:
                if (
                    self.y + 0.5 * self.height >= platform[1] > self.y
                    and platform[0] <= self.x <= platform[2]
                ):
                    self.visible = False
            for block in blocks:
                if (
                    self.y + 0.5 * self.height >= block.y
                    and self.x + self.width >= block.x
                    and self.x <= block.x + block.width
                ):
                    self.visible = False
