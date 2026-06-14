"""Key: collecting it lets the player open the level's door."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from exit_dash.core import resources

if TYPE_CHECKING:
    from exit_dash.entities.character import Character


class Key:
    def __init__(self, x: float, y: float, colour: str) -> None:
        self.x = float(x)
        self.y = float(y)
        self.visible = False
        self.image = resources.image("environment", "main", f"key{colour}.png")
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self, main_char: Character) -> None:
        key_rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        char_rect = pygame.Rect(
            int(main_char.x), int(main_char.y), int(main_char.width), int(main_char.height)
        )
        if key_rect.colliderect(char_rect):
            main_char.has_key = True
            self.visible = False

    def draw(self, surface: pygame.Surface) -> None:
        if self.visible:
            surface.blit(self.image, (self.x, self.y))
