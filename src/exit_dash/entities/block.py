"""Block: a bonus box (coin / regular / explosive / locked).

Hitting a block disables it and may reveal a coin, a star, a key, or trigger an
explosion. Supports ``block[0]`` (its bounding tuple) and ``block[i>0]`` (coin-position
components) indexing, relied on by the collision and falling-spike code.
"""

from __future__ import annotations

import math
from random import randint
from typing import TYPE_CHECKING, Literal

import pygame

from exit_dash.core import resources

if TYPE_CHECKING:
    from collections.abc import Sequence

    from exit_dash.entities.key import Key

BlockForm = Literal["locked", "coin", "regular", "explosive"]
_ENV = ("environment", "main")


class Block:
    def __init__(self, x: float, y: float, form: BlockForm) -> None:
        self.form: BlockForm = form
        self.x = float(x)
        self.y = float(y)

        self.locked_image = resources.image(*_ENV, "lock_blue.png")
        self.coin_block_image = resources.image(*_ENV, "boxCoin.png")
        self.coin_block_used_image = resources.image(*_ENV, "boxCoin_disabled.png")
        self.explosive_image = resources.image(*_ENV, "boxExplosive.png")
        self.explosive_used_image = resources.image(*_ENV, "boxExplosive_disabled.png")
        self.regular_image = resources.image(*_ENV, "boxItem.png")
        self.regular_used_image = resources.image(*_ENV, "boxItem_disabled.png")
        self.explosion = [
            pygame.transform.scale2x(resources.image(*_ENV, f"explosion{i}.png")) for i in range(3)
        ]
        self.width = self.regular_image.get_width()
        self.height = self.regular_image.get_height()
        self.image = self.regular_image

        # Sound effects need a mixer; tolerate headless/no-audio environments.
        self._explosion_sfx = (
            resources.sound("sounds", "synthetic_explosion_1.ogg")
            if pygame.mixer.get_init()
            else None
        )

        self.coin_image = resources.image(*_ENV, "coinGold.png")
        self.coin_width = self.coin_image.get_width()
        self.coin_height = self.coin_image.get_height()
        self.coin_pos = self._coin_position()
        self.coin_visible = False

        self.star_image = resources.image("items", "star.png")
        self.star_width = self.star_image.get_width()
        self.star_height = self.star_image.get_height()

        self.disabled = False
        self.will_explode = form == "explosive"
        self.yields_star = False
        self.explosion_step = 0

    def _coin_position(self) -> list[float]:
        return [
            self.x - 15,
            self.y - self.coin_height + 10,
            self.x + self.coin_width - 15,
            self.y + 10,
        ]

    def __getitem__(self, i: int) -> tuple[float, float, float, float] | float:
        if i == 0:
            return (self.x, self.y, self.x + self.width, self.y + self.height)
        return self.coin_pos[i - 1]

    @staticmethod
    def distance(p0: tuple[float, float], p1: tuple[float, float]) -> float:
        return math.sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)

    def update_state(self) -> None:
        self.coin_pos = self._coin_position()

    def disable(self) -> None:
        self.coin_visible = True
        self.disabled = True

    def kill_coin(self) -> None:
        self.coin_visible = False

    def _block_image(self) -> pygame.Surface:
        match (self.form, self.disabled):
            case ("locked", _):
                return self.locked_image
            case ("coin", True):
                return self.coin_block_used_image
            case ("coin", False):
                return self.coin_block_image
            case ("regular", True):
                return self.regular_used_image
            case ("regular", False):
                return self.regular_image
            case ("explosive", True):
                return self.explosive_used_image
            case ("explosive", False):
                return self.explosive_image
            case _:
                return self.regular_image

    def draw(self, keys: Sequence[Key], surface: pygame.Surface) -> None:
        surface.blit(self._block_image(), (self.x, self.y))

        if self.form == "coin" and self.coin_visible:
            surface.blit(self.coin_image, (self.coin_pos[0], self.coin_pos[1]))
        if self.form == "regular":
            for key in keys:
                if (
                    self.coin_visible
                    and self.disabled
                    and self.distance((self.x, self.y), (key.x, key.y)) < 1.5 * key.height
                ):
                    key.visible = True
                    self.coin_visible = False
        if self.will_explode and self.disabled:
            if randint(0, 2) == 0 and self.explosion_step < len(self.explosion):
                self.explosion_step += 1
            if self.explosion_step < len(self.explosion):
                surface.blit(self.explosion[self.explosion_step], (self.x - 65, self.y - 135))
                if self._explosion_sfx is not None:
                    self._explosion_sfx.play()
        if self.yields_star and self.disabled and self.coin_visible:
            surface.blit(self.star_image, (self.coin_pos[0] + 20, self.coin_pos[1] + 30))

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
