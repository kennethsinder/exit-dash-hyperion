"""Door: the level exit. Unlocks once the player has the key and is standing in it."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from exit_dash.core import resources

if TYPE_CHECKING:
    from exit_dash.entities.character import Character

_ENV = ("environment", "main")
_TOP_BLANK_SPACE = 30


class Door:
    def __init__(self, x: float, y: float) -> None:
        self.x = float(x)
        self.y = float(y)
        self.locked = True

        self.image_bottom = resources.image(*_ENV, "door_openMid.png")
        self.image_top = resources.image(*_ENV, "door_openTop.png")
        self.image_bottom_locked = resources.image(*_ENV, "door_closedMid.png")
        self.image_top_locked = resources.image(*_ENV, "door_closedTop.png")
        self.bottom_height = self.image_bottom.get_height()
        self.top_height = self.image_top.get_height()
        self.top_blank_space = _TOP_BLANK_SPACE
        self.height = self.bottom_height + self.top_height - self.top_blank_space
        self.width = self.image_bottom.get_width()
        self.y -= self.bottom_height + self.top_height
        self.image = self.image_top

    def update(self, main_char: Character, unlockable: bool = True) -> bool:
        """Update lock state; return True when the player exits through the door."""
        char_rect = pygame.Rect(
            int(main_char.x), int(main_char.y), int(main_char.width), int(main_char.height)
        )
        in_door = char_rect.colliderect(self.get_rect())
        if (in_door and main_char.has_key) or not unlockable:
            self.locked = False
        return not self.locked and in_door and unlockable

    def draw(self, surface: pygame.Surface) -> None:
        if self.locked:
            surface.blit(self.image_top_locked, (self.x, self.y))
            surface.blit(self.image_bottom_locked, (self.x, self.y + self.top_height))
        else:
            surface.blit(self.image_top, (self.x, self.y))
            surface.blit(self.image_bottom, (self.x, self.y + self.top_height))

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y + self.top_blank_space), self.width, self.height)
