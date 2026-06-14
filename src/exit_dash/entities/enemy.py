"""AICharacter: enemies (slime, snail, fly, fish) with simple patrol AI.

Behaviour is ported verbatim from the original, including its quirks (e.g. the
``slime or snail and ...`` operator precedence, which makes slimes always re-plan and
snails only sometimes). Enemies reuse :class:`Character`'s physics; their own sprites and
AI are layered on top.
"""

from __future__ import annotations

import math
from random import randint
from typing import TYPE_CHECKING, Literal

import pygame

from exit_dash.entities.character import Character

if TYPE_CHECKING:
    from collections.abc import Sequence

    from exit_dash.entities.block import Block
    from exit_dash.entities.platform import Platform
    from exit_dash.entities.pool import Pool
    from exit_dash.entities.torch import Torch

MobType = Literal["slime", "snail", "fly", "fish"]
_EXPLOSION_RADIUS = 400


class AICharacter(Character):
    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        properties: tuple[MobType, int, int] = ("slime", -1, -1),
    ) -> None:
        self.mob_type: MobType = properties[0]
        # Patrol bounds shift with the world camera, so they hold floats; -1 means "no limit".
        self.limit: list[float] = [properties[1], properties[2]]

        super().__init__(x, y, which_char=1, vx=vx, vy=vy)

        self.colour = "Blue"
        if self.mob_type == "slime" and randint(0, 1) == 0:
            self.colour = "Green"
        self._load_mob_images()

        self.image_l1: pygame.Surface | None = None
        self.image_l2: pygame.Surface | None = None
        self.image_r1: pygame.Surface | None = None
        self.image_r2: pygame.Surface | None = None
        self.image_dl: pygame.Surface | None = None
        self.image_dr: pygame.Surface | None = None
        self.dead_width = 0
        self.dead_height = 0

        self.original_height = y
        self.is_alive = True
        self.health = 1
        self.gravity = 1
        self.run_speed = abs(self.vx)
        self.current_step = 0
        self.taken_action = False
        self.update_frequency = 2

    def _load_mob_images(self) -> None:
        from exit_dash.core import resources

        slime = ("enemies", "slime")
        other = ("enemies", "other")
        fly = ("enemies", "fly")
        self.slime_dl = resources.image(*slime, f"slime{self.colour}_squashed.png")
        self.slime_dr = resources.image(*slime, f"slime{self.colour}_squashedR.png")
        self.slime_l = resources.image(*slime, f"slime{self.colour}_walk.png")
        self.slime_r = resources.image(*slime, f"slime{self.colour}_walkR.png")
        self.fly_dl = resources.image(*fly, "fly_dead.png")
        self.fly_dr = resources.image(*fly, "fly_dead_r.png")
        self.fly_l = resources.image(*fly, "fly_fly.png")
        self.fly_r = resources.image(*fly, "fly_fly_r.png")
        self.fish_dl = resources.image(*other, "fishGreen_dead.png")
        self.fish_dr = resources.image(*other, "fishGreen_dead_r.png")
        self.fish_l = resources.image(*other, "fishGreen_swim.png")
        self.fish_r = resources.image(*other, "fishGreen_swim_r.png")
        self.snail_l1 = resources.image(*other, "snailWalk1.png")
        self.snail_l2 = resources.image(*other, "snailWalk2.png")
        self.snail_r1 = resources.image(*other, "snailWalk1R.png")
        self.snail_r2 = resources.image(*other, "snailWalk2R.png")
        self.snail_dl = resources.image(*other, "snailShell.png")
        self.snail_dr = resources.image(*other, "snailShellR.png")

    @staticmethod
    def distance(p0: tuple[float, float], p1: tuple[float, float]) -> float:
        return math.sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)

    def update_ai(self, platforms: Sequence[Platform], blocks: Sequence[Block]) -> None:
        self.x += self.vx
        self.y += self.vy

        if self.vx > 0:
            self.direction = 1
        elif self.vx < 0:
            self.direction = 0

        if self.health <= 0:
            self.is_alive = False

        if self.vy >= platforms[0].height:
            self.vy = platforms[0].height - 5
        if (
            not self.on_ground
            and self.vy >= platforms[0].height - 15
            and self.y > platforms[self.lowest_platform][1]
        ):
            self.dispose()

        if self.on_ground:
            self.vy = 0
        elif ((self.mob_type == "fly" and not self.is_alive) or self.mob_type != "fly") and (
            self.mob_type != "fish" or (self.mob_type == "fish" and not self.is_alive)
        ):
            self.vy += self.gravity

        if self.limit[0] != -1 and self.x <= self.limit[0]:
            self.x += self.run_speed
            self.vx = abs(self.vx)
        if self.limit[1] != -1 and self.x >= self.limit[1]:
            self.x -= self.run_speed
            self.vx = -abs(self.vx)

        for block in blocks:
            distance_from_block = self.distance(
                (self.x + 0.5 * self.width, self.y + 0.5 * self.height),
                (block.x + 0.5 * block.width, block.y + 0.5 * block.height),
            )
            if (
                block.disabled
                and block.will_explode
                and block.explosion_step == 1
                and distance_from_block < _EXPLOSION_RADIUS
            ):
                self.health = 0

        if self.mob_type in ("slime", "snail"):
            self._avoid_falling_off_lowest(platforms)

        # NOTE: the original precedence is preserved: slimes always re-plan, snails sometimes.
        if self.mob_type == "slime" or (
            self.mob_type == "snail" and randint(0, 10 - self.update_frequency) == 0
        ):
            self._replan_ground_patrol(platforms)
        elif (
            self.mob_type == "fly" and self.is_alive and randint(0, 10 - self.update_frequency) == 0
        ):
            self._replan_fly_patrol(platforms)

        self.walk_frame = (self.walk_frame + 1) % 2

    def _avoid_falling_off_lowest(self, platforms: Sequence[Platform]) -> None:
        test_left = self.x - 25
        test_right = self.x + 25 + self.width
        lowest = platforms[self.lowest_platform]
        on_lowest = self.current_platform == self.lowest_platform
        if on_lowest and test_left <= lowest[0] and self.vx < 0:
            self.x += self.run_speed
            self.vx *= -1
        elif on_lowest and test_right >= lowest[2] and self.vx > 0:
            self.x -= self.run_speed
            self.vx *= -1

    def _replan_ground_patrol(self, platforms: Sequence[Platform]) -> None:
        current = platforms[self.current_platform]
        current_height = current[1]
        limit_backup = [self.limit[0], self.limit[1]]
        self.limit[0] = int(current[0] + 5)
        self.limit[1] = int(current[2] - 40)
        below = [p for p in platforms if p[1] > current_height]
        safe_left = any(p[0] < current[0] < p[2] for p in below)
        safe_right = any(p[0] < current[2] and p[2] > current[2] for p in below)
        if safe_left:
            self.limit[0] = limit_backup[0]
        if safe_right:
            self.limit[1] = limit_backup[1]

    def _replan_fly_patrol(self, platforms: Sequence[Platform]) -> None:
        self.limit[0] = int(platforms[0][0])
        for p in platforms:
            if self.x + self.width + 5 >= p[0] and self.x <= p[2] and p[1] <= self.y <= p[3]:
                self.limit[1] = int(p[0])
                self.vx *= -1
                self.x -= self.run_speed

    def step(
        self,
        platforms: Sequence[Platform],
        blocks: Sequence[Block],
        ai_characters: Sequence[AICharacter],
        pool: Pool | None,
        torches: Sequence[Torch] | None = None,
    ) -> None:
        """Advance one fixed timestep: collide first, then run AI/motion (original order)."""
        self.collide(platforms, blocks, ai_characters, pool, torches)
        self.update_ai(platforms, blocks)

    def _ensure_images(self) -> None:
        if self.image_l1 is not None:
            return
        if self.mob_type == "slime":
            self.image_l1 = self.image_l2 = self.slime_l
            self.image_r1 = self.image_r2 = self.slime_r
            self.image_dl, self.image_dr = self.slime_dl, self.slime_dr
        elif self.mob_type == "fly":
            self.image_l1 = self.image_l2 = self.fly_l
            self.image_r1 = self.image_r2 = self.fly_r
            self.image_dl, self.image_dr = self.fly_dl, self.fly_dr
        elif self.mob_type == "fish":
            self.image_l1 = self.image_l2 = self.fish_l
            self.image_r1 = self.image_r2 = self.fish_r
            self.image_dl, self.image_dr = self.fish_dl, self.fish_dr
        elif self.mob_type == "snail":
            self.image_l1, self.image_l2 = self.snail_l1, self.snail_l2
            self.image_r1, self.image_r2 = self.snail_r1, self.snail_r2
            self.image_dl, self.image_dr = self.snail_dl, self.snail_dr

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        self._ensure_images()
        assert self.image_l1 and self.image_dl  # for type-checkers; set by _ensure_images
        self.width = self.image_l1.get_width()
        self.height = self.image_l1.get_height()
        self.dead_width = self.image_dl.get_width()
        self.dead_height = self.image_dl.get_height()

        if self.is_alive and self.walk_frame == 0:
            image = self.image_r1 if self.direction == 1 else self.image_l1
        elif self.is_alive:
            image = self.image_r2 if self.direction == 1 else self.image_l2
        else:
            image = self.image_dr if self.direction == 1 else self.image_dl
        if image is not None:
            surface.blit(image, (self.x, self.y))

        if not self.is_alive:
            self.width = self.dead_width
            self.height = self.dead_height
            self.vx = 0
