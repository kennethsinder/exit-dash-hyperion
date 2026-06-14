"""PlayableCharacter: the player. Adds input-driven movement, the move-the-world camera,
the HUD, checkpoints, autoscroll and respawning on top of :class:`Character`.

The camera follows the "move the world" model from the original: rather than offsetting
at draw time, the player stays near screen-centre and every other object's world
coordinates shift. This is preserved deliberately — the AI patrol limits, parallax
offsets and the ``0 <= x <= 2000`` activation gates all depend on it.
"""

from __future__ import annotations

import math
from random import randint
from typing import TYPE_CHECKING

import pygame

from exit_dash.core import resources
from exit_dash.core.input import PlayerInput
from exit_dash.entities.character import Character

if TYPE_CHECKING:
    from collections.abc import Sequence

    from exit_dash.entities.checkpoint import Checkpoint
    from exit_dash.entities.enemy import AICharacter
    from exit_dash.entities.platform import Platform


class PlayableCharacter(Character):
    def __init__(self, x: float, y: float, vx: float = 0.0, vy: float = 0.0, which_char: int = 1):
        super().__init__(x, y, which_char=which_char, vx=vx, vy=vy)

        hud = ("hud",)
        self.heart_empty = resources.image(*hud, "hud_heartEmpty.png")
        self.heart_half = resources.image(*hud, "hud_heartHalf.png")
        self.heart_full = resources.image(*hud, "hud_heartFull.png")
        self.heart_width = self.heart_full.get_width()
        self.heart_height = self.heart_full.get_height()
        self.coin_image = resources.image(*hud, "hud_coins.png")
        self.coin_image_width = self.coin_image.get_width()
        self.coins_multiplier = resources.image(*hud, "hud_x.png")
        self.hud_numbers = [resources.image(*hud, f"hud_{i}.png") for i in range(10)]
        self.hud_text_width = self.hud_numbers[0].get_width()
        self.player_icon = resources.image(*hud, f"hud_p{which_char}.png")
        self.key_icon = resources.image(*hud, "hud_keyBlue.png")
        self.no_key_icon = resources.image(*hud, "hud_keyBlue_disabled.png")

        self.spacing = 10
        self.coins = 0
        self.player_icon_coords = (self.spacing, self.spacing)
        self.health_interval = self.spacing + self.heart_width

        if which_char == 1:
            self.jump_speed = 35
            self.run_speed = 8.5
            self.lives = 9
        else:
            self.jump_speed = 36
            self.run_speed = 9.0
            self.lives = 4
        self._recompute_jump_kinematics()

        self.world_shift_coefficient = 1.5
        self.cpu_controlled = False
        self.longest_platform: int | None = None
        self.respawn_point: list[float] | None = None

    # -- checkpoints ------------------------------------------------------------------

    def collide_checkpoint(self, checkpoints: Sequence[Checkpoint] | None) -> None:
        if not checkpoints:
            return
        for fence in checkpoints:
            if self.get_rect().colliderect(fence.get_rect()) and not fence.broken:
                self.respawn_point = [fence.x + 20, fence.y - 70]
                fence.broken = True

    # -- move-the-world camera --------------------------------------------------------

    def increment_map_h(
        self,
        ai_characters: Sequence[AICharacter],
        movable_objects: Sequence[object],
        amount: float,
        move_self: bool = True,
    ) -> None:
        if move_self:
            self.x += amount
        if self.respawn_point:
            self.respawn_point[0] += amount
        for obj in movable_objects:
            obj.x += amount  # type: ignore[attr-defined]
            if hasattr(obj, "inverted_x"):
                obj.inverted_x += amount
        for ai in ai_characters:
            if ai.limit[0] != -1:
                ai.limit[0] += amount
            if ai.limit[1] != -1:
                ai.limit[1] += amount

    def increment_map_v(
        self, movable_objects: Sequence[object], amount: float, move_self: bool = True
    ) -> None:
        if move_self:
            self.y += amount
        if self.respawn_point:
            self.respawn_point[1] += amount
        for obj in movable_objects:
            obj.y += amount  # type: ignore[attr-defined]

    def set_map_obj_x(
        self,
        ai_characters: Sequence[AICharacter],
        movable_objects: Sequence[object],
        platforms: Sequence[Platform],
        new_x: float,
    ) -> None:
        """Shift the whole world so platform 0's left edge lands at ``new_x``."""
        shift = new_x - platforms[0][0]
        self.x += shift
        if self.respawn_point:
            self.respawn_point[0] += shift
        for obj in movable_objects:
            obj.x += shift  # type: ignore[attr-defined]
        for ai in ai_characters:
            if ai.limit[0] != -1:
                ai.limit[0] += shift
            if ai.limit[1] != -1:
                ai.limit[1] += shift

    def get_next_platform(self, platforms: Sequence[Platform]) -> Platform:
        assert self.longest_platform is not None
        current_x = platforms[self.current_platform].x
        longest_x = platforms[self.longest_platform].x
        if current_x == longest_x and self.longest_platform + 1 < len(platforms):
            return platforms[self.longest_platform + 1]
        if self.current_platform >= len(platforms) - 1:
            return platforms[self.current_platform]
        return platforms[self.current_platform + 1]

    def init_spawnpoint(
        self, autoscroll: bool, platforms: Sequence[Platform], next_platform: Platform
    ) -> None:
        if not autoscroll and not self.respawn_point:
            self.respawn_point = [
                0.5 * platforms[0][0] + 0.5 * platforms[0][2],
                platforms[0][1] - self.height - 10,
            ]
        elif autoscroll:
            self.respawn_point = [
                next_platform[0] + 0.5 * next_platform.width,
                next_platform[1] - self.height - 10,
            ]

    def respawn(self, x: float, y: float, lose_life: bool = True) -> None:
        self.x = int(x)
        self.y = int(y)
        self.vx = self.vy = 0
        self.health = self.recovery_health
        if lose_life:
            self.flashing = True
            self.lives -= 1

    def determine_longest_platform(self, platforms: Sequence[Platform]) -> None:
        if self.longest_platform is not None:
            return
        self.longest_platform = 0
        for i in range(1, len(platforms)):
            if platforms[i].width > platforms[self.longest_platform].width:
                self.longest_platform = i
        for i in range(len(platforms)):
            if (
                platforms[i][0] == platforms[self.longest_platform][0]
                and platforms[i][1] >= platforms[self.longest_platform][1]
            ):
                self.longest_platform = i

    def scan_world(
        self,
        ai_characters: Sequence[AICharacter],
        autoscroll: bool,
        movable_objects: Sequence[object],
        next_platform: Platform,
        scr_h: int,
        scr_w: int,
    ) -> None:
        right_edge = int(0.5 * scr_w) + 2
        left_edge = int(0.5 * scr_w) - 2
        bottom_edge = int(0.25 * scr_h) if self.ducking else int(0.7 * scr_h) + 5
        top_edge = int(0.3 * scr_h) - 5
        shift = int(self.world_shift_coefficient * self.run_speed)
        if self.y <= scr_h and not autoscroll:
            self.increment_map_h(ai_characters, movable_objects, -self.vx, move_self=False)
            if self.x >= right_edge:
                self.increment_map_h(ai_characters, movable_objects, -shift)
            if self.x <= left_edge:
                self.increment_map_h(ai_characters, movable_objects, shift)
        if self.y <= scr_h:
            if self.y <= top_edge:
                self.increment_map_v(movable_objects, shift)
            if self.y >= bottom_edge or next_platform[3] >= scr_h:
                self.increment_map_v(movable_objects, -shift)
        elif randint(0, 10) == 0:
            self.health -= 1

    def handle_world_scrolling(
        self,
        ai_characters: Sequence[AICharacter],
        autoscroll: bool,
        movable_objects: Sequence[object],
        scr_w: int,
    ) -> None:
        if autoscroll and self.x + self.width >= 0:
            self.increment_map_h(ai_characters, movable_objects, -0.5 * self.run_speed)
            self.x += self.vx
        elif autoscroll and self.health > 0:
            self.health -= 0.5
        self.world_shift_coefficient = 20 if (self.x <= 0 or self.x >= scr_w) else 1.5

    # -- input-driven movement --------------------------------------------------------

    def enable_horizontal_movement(self, controls: PlayerInput) -> None:
        movable = not self.cpu_controlled
        if controls.left and movable:
            self.vx = -self.run_speed
        if controls.right and movable:
            self.vx = self.run_speed
        if not controls.left and not controls.right and movable:
            self.vx = 0
            self.moving_laterally = False
        if self.vx > 0:
            self.direction = 1
            self.moving_laterally = True
        elif self.vx < 0:
            self.direction = 0
            self.moving_laterally = True
        else:
            self.direction = 2
        if controls.duck and movable:
            self.ducking = True
            self.vx = 0
        else:
            self.ducking = False

    def allow_jumping(self, controls: PlayerInput) -> None:
        if self.jumping and self.on_ground:
            self.jumping = False
        if controls.jump and self.can_jump and self.on_ground:
            self.jump()
            self.jumping = True
            self.can_jump = False
            self.on_ground = False
        if not controls.jump and self.on_ground:
            self.can_jump = True

    def move(
        self,
        controls: PlayerInput,
        platforms: Sequence[Platform],
        movable_objects: Sequence[object],
        ai_characters: Sequence[AICharacter],
        scr_w: int,
        scr_h: int,
        autoscroll: bool,
    ) -> bool:
        """Advance the player one fixed step. Returns False when the game is over."""
        self.update_motion(platforms)
        self.x -= self.vx  # horizontal motion is expressed by scrolling the world instead

        self.enable_horizontal_movement(controls)
        self.determine_longest_platform(platforms)
        next_platform = self.get_next_platform(platforms)
        self.scan_world(ai_characters, autoscroll, movable_objects, next_platform, scr_h, scr_w)
        self.handle_world_scrolling(ai_characters, autoscroll, movable_objects, scr_w)
        self.allow_jumping(controls)
        self.init_spawnpoint(autoscroll, platforms, next_platform)

        if self.health <= 0 and self.respawn_point is not None:
            self.respawn(self.respawn_point[0], self.respawn_point[1])
        return not (self.lives <= 0 and self.x != 0)

    # -- rendering --------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        self.draw_hud(surface)

    def draw_hud(self, surface: pygame.Surface) -> None:
        s = self.spacing
        surface.blit(self.player_icon, self.player_icon_coords)
        surface.blit(self.coins_multiplier, (s + self.heart_width, int(2.5 * s)))
        surface.blit(self.hud_numbers[self.lives], (5 * s + self.heart_width, int(1.5 * s)))

        health = self.health / 2.0
        for filled in range(1, math.floor(health) + 1):
            if health >= 0:
                surface.blit(self.heart_full, (self.health_interval * filled - 55, 7 * s))
        if math.floor(health) != health and health >= 0:
            surface.blit(self.heart_half, (self.health_interval * math.ceil(health) - 55, 7 * s))

        surface.blit(self.coin_image, (s, 8 * s + self.heart_height))
        surface.blit(self.coins_multiplier, (s + self.heart_width, 8 * s + self.heart_height + 15))
        for i, digit in enumerate(str(self.coins)):
            surface.blit(
                self.hud_numbers[int(digit)],
                (
                    3 * s + self.coin_image_width + self.hud_text_width * (i + 1),
                    7 * s + self.heart_height + 15,
                ),
            )

        icon = self.key_icon if self.has_key else self.no_key_icon
        surface.blit(icon, (s, 13 * s + self.heart_height + 15))
