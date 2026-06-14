"""Character: the shared physics/collision base for the player and enemies.

The motion and collision arithmetic is preserved verbatim from the original game so the
feel is unchanged; only the structure, names and types are modernized. Positions are
floats (sub-pixel precision); the integer ``rect`` is derived for drawing. The simulation
runs at a fixed timestep, so per-step velocity/gravity constants carry over directly and
animation/flash timing is keyed to the fixed rate (no longer frame-rate dependent).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from exit_dash.core import resources
from exit_dash.core.constants import FIXED_FPS

if TYPE_CHECKING:
    from collections.abc import Sequence

    from exit_dash.entities.block import Block
    from exit_dash.entities.enemy import AICharacter
    from exit_dash.entities.platform import Platform
    from exit_dash.entities.pool import Pool
    from exit_dash.entities.torch import Torch

_WALK_FRAMES = 10
_FLASH_SECONDS = 4
_HEALTH_BY_CHARACTER = {1: 4, 2: 6}
_DEFAULT_HEALTH = 10


class Character:
    GRAVITY = 2.5
    JUMP_SPEED = 30
    RUN_SPEED = 5
    PLATFORM_TOLERANCE = 15

    def __init__(self, x: float, y: float, which_char: int = 1, vx: float = 0.0, vy: float = 0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)

        self.gravity: float = self.GRAVITY
        self.jump_speed: float = self.JUMP_SPEED
        self.run_speed: float = self.RUN_SPEED

        self.walk_frame = 0
        self.mob_jumping = False
        self.underwater = False
        self.moving_laterally = False
        self.jumping = False
        self.can_jump = False
        self.on_ground = False
        self.has_key = False
        self.direction = 0  # 0 = facing left, 1 = facing right
        self.current_platform = 0
        self.lowest_platform = 0

        self.health: float = _HEALTH_BY_CHARACTER.get(which_char, _DEFAULT_HEALTH)
        self.recovery_health: float = self.health
        self.flashing = False
        self.flash_timer = 0
        self.coins = 0

        self.which_char = which_char
        self.visible = True
        self.ducking = False
        self.platform_tolerance = self.PLATFORM_TOLERANCE

        self._load_appearance(which_char)
        self._recompute_jump_kinematics()

    # -- appearance -------------------------------------------------------------------

    def _load_appearance(self, which_char: int) -> None:
        prefix = ("character", "main")
        stem = f"p{which_char}"
        self.standing_image = resources.image(*prefix, f"{stem}_front.png")
        self.jumping_image_left = resources.image(*prefix, f"{stem}_jump_l.png")
        self.jumping_image_right = resources.image(*prefix, f"{stem}_jump.png")
        self.duck_left = resources.image(*prefix, f"{stem}_duck_l.png")
        self.duck_right = resources.image(*prefix, f"{stem}_duck.png")
        self.duck_height = self.duck_left.get_height()
        self.width = self.standing_image.get_width()
        self.height = self.standing_image.get_height()
        self.image = self.standing_image

        self.walk_images_right: list[pygame.Surface] = []
        self.walk_images_left: list[pygame.Surface] = []
        for i in range(1, _WALK_FRAMES + 1):
            frame = resources.image(*prefix, f"{stem}_walk", "PNG", f"{stem}_walk{i}.png")
            self.walk_images_right.append(frame)
            self.walk_images_left.append(pygame.transform.flip(frame, True, False))

    def _recompute_jump_kinematics(self) -> None:
        self.jump_time = float(self.jump_speed) / self.gravity
        self.max_jump_height = math.floor(0.5 * self.jump_speed * self.jump_time)
        self.max_jump_length = math.floor(self.run_speed * self.jump_time)

    # -- motion -----------------------------------------------------------------------

    def platform_init(self, platforms: Sequence[Platform]) -> None:
        self.determine_lowest_platform(platforms)

    def determine_lowest_platform(self, platforms: Sequence[Platform]) -> None:
        for index in range(len(platforms)):
            if platforms[index].y > platforms[self.lowest_platform].y:
                self.lowest_platform = index

    def jump(self, intensity: float = 1.0) -> None:
        """Set upward velocity for a jump (does not check whether jumping is allowed)."""
        self.vy = math.floor(-intensity * self.jump_speed)

    def update_motion(self, platforms: Sequence[Platform]) -> None:
        self.x += self.vx
        self.y += self.vy
        self._recompute_jump_kinematics()

        terminal = platforms[0].height
        if self.vy >= terminal:
            self.vy = terminal - 5
        if not self.on_ground and self.vy >= terminal - 5:
            self.dispose()

        if self.on_ground:
            self.vy = 0
            self.mob_jumping = False
        else:
            self.vy += self.gravity

    # -- collision --------------------------------------------------------------------

    def block_collide(self, blocks: Sequence[Block]) -> bool:
        left = self.x + 10
        right = self.x + self.width - 10
        top = self.y
        bottom = self.y + self.height

        for block in blocks:
            if not (0 <= block.x <= 2000 and 0 <= block.y <= 2000):
                continue
            block_left = block.x
            block_right = block.x + block.width
            block_top = block.y
            block_bottom = block.y + block.height
            block_middle_x = int(0.5 * block_left + 0.5 * block_right)
            block_middle_y = int(0.5 * block_bottom + 0.5 * block_top)

            below = (
                right >= block_left
                and left <= block_right
                and block_middle_y - 20 <= top <= block_bottom
            )
            left_of = (
                block_left <= right < block_middle_x and bottom > block_top and top < block_bottom
            )
            right_of = (
                block_right >= left > block_middle_x and bottom > block_top and top < block_bottom
            )
            above = (
                right >= block_left + 10
                and left <= block_right - 10
                and block_bottom > bottom >= block_top
            )

            hit = False
            if below and self.vy <= 0:
                self.y = block.y + block.height + 1
                self.vy = 0
                hit = True
            elif left_of:
                self.x = block_left - self.width
                self.vx *= -1
                return True
            elif right_of:
                self.x = block_right
                self.vx *= -1
                return True
            elif above and self.vy >= 0:
                self.y = block_top - self.height
                self.on_ground = True
            if not block.disabled and hit:
                block.disable()
                if block.will_explode and not self.flashing:
                    self.health -= 1
                    self.flashing = True
        return False

    def coin_collide(self, blocks: Sequence[Block]) -> None:
        self_rect = self.get_rect()
        for block in blocks:
            if not (0 <= block.x <= 2000 and 0 <= block.y <= 2000):
                continue
            coin_pos = block.coin_pos
            coin_rect = pygame.Rect(coin_pos[0], coin_pos[1], block.coin_width, block.coin_height)
            star_rect = pygame.Rect(coin_pos[0], coin_pos[1], block.star_width, block.star_height)
            if block.coin_visible and self_rect.colliderect(coin_rect) and not block.yields_star:
                self.coins += 1
                block.kill_coin()
            elif block.coin_visible and self_rect.colliderect(star_rect):
                self.coins += 10
                self.health += 2
                block.kill_coin()

    def platform_collide(self, platforms: Sequence[Platform], pool: Pool | None) -> None:
        tol = self.platform_tolerance
        for i in range(len(platforms)):
            p = platforms[i]
            if (
                self.x + self.width >= p[0] + tol
                and self.x <= p[2] - tol
                and p[1] <= self.y + self.height <= p[3] + 35
                and self.vy >= 0
            ):
                self.y = p[1] - self.height
                self.on_ground = True
                self.current_platform = i
            if (  # noqa: SIM102 — guard then landing-rule reads clearer than one boolean
                self.x + self.width >= p[0] + tol
                and self.x <= p[2] - tol
                and p[3] >= self.y >= p[1] - tol
                and self.vy < 0
            ):
                if (
                    self.x + self.width >= p[0] + p.tile_width and self.x <= p[2] - p.tile_width
                ) or self.y <= p[1] + tol + 30:
                    self.y = p[3]
                    self.vy = 0

    def ai_collide(self, ai_characters: Sequence[AICharacter]) -> None:
        if self in ai_characters:
            return
        for ai in ai_characters:
            if not (0 <= ai.x <= 2000 and 0 <= ai.y <= 2000):
                continue
            if self.get_rect().colliderect(ai.get_rect()) and ai.is_alive:
                if self.vy > 0 and ai.mob_type != "fly":
                    ai.health -= 5 - self.which_char
                    self.jump(0.75)
                    self.mob_jumping = True
                    self.on_ground = False
                elif self.vy > 0:
                    self.jump(0.8)
                    self.on_ground = False
                    ai.is_alive = False
                elif not self.mob_jumping and self.flash_timer == 0:
                    self.health -= 1
                    self.flashing = True

    def pool_collide(self, platforms: Sequence[Platform], pool: Pool | None) -> None:
        if not pool:
            return
        current = platforms[self.current_platform]
        if int(current[0]) <= self.x < int(current[2]):
            return

        left_x = self.x
        right_x = self.x + self.width
        bottom_y = self.y + self.height

        if (
            pool.y <= bottom_y <= pool.y + pool.tile_width
            and (
                (right_x - 10 >= pool.x and left_x + 10 <= pool.pool_start_x + pool.tile_width)
                or (right_x - 10 >= pool.pool_end_x and left_x + 10 <= pool.x + pool.width)
            )
            and self.vy >= 0
        ):
            self.on_ground = True
            self.y = pool.y - self.height
        if (
            left_x + 10 >= pool.pool_start_x
            and right_x - 10 <= pool.pool_end_x + pool.tile_width
            and pool.y + pool.height <= bottom_y <= pool.y + pool.height + pool.tile_width
            and self.vy >= 0
        ):
            self.on_ground = True
            self.y = pool.y + pool.height - self.height
        if (
            pool.pool_start_x + pool.tile_width >= left_x >= pool.pool_start_x
            and pool.y < bottom_y <= pool.y + pool.height
        ):
            self.x = pool.pool_start_x + pool.tile_width
            self.vx *= -1
        if (
            pool.pool_end_x <= right_x <= pool.pool_end_x + pool.tile_width
            and pool.y < bottom_y <= pool.y + pool.height
        ):
            self.x = pool.pool_end_x - self.width
            self.vx *= -1
        if (
            right_x >= pool.pool_start_x
            and left_x <= pool.pool_end_x
            and pool.y + pool.height >= bottom_y > pool.y
        ):
            self.underwater = True

    def torch_collide(self, torches: Sequence[Torch] | None) -> None:
        if not torches:
            return
        for torch in torches:
            if self.get_rect().colliderect(torch.get_rect()):
                torch.burning = True

    def prep_collision_detection(self) -> None:
        self.on_ground = False
        self.underwater = False

    def collide(
        self,
        platforms: Sequence[Platform],
        blocks: Sequence[Block],
        ai_characters: Sequence[AICharacter],
        pool: Pool | None,
        torches: Sequence[Torch] | None,
    ) -> None:
        self.prep_collision_detection()
        self.block_collide(blocks)
        self.coin_collide(blocks)
        self.platform_collide(platforms, pool)
        self.ai_collide(ai_characters)
        self.pool_collide(platforms, pool)
        self.torch_collide(torches)

    # -- per-step orchestration -------------------------------------------------------

    def step(
        self,
        platforms: Sequence[Platform],
        blocks: Sequence[Block],
        ai_characters: Sequence[AICharacter],
        pool: Pool | None,
        torches: Sequence[Torch] | None = None,
    ) -> None:
        """Advance one fixed timestep: motion, collision, then animation."""
        if not self.visible:
            return
        self.update_motion(platforms)
        self.collide(platforms, blocks, ai_characters, pool, torches)
        self.advance_animation()

    def advance_animation(self) -> None:
        self.walk_frame = (self.walk_frame + 1) % _WALK_FRAMES
        if self.flashing:
            self.flash_timer += 1
        else:
            self.flash_timer = 0
        if self.flash_timer >= FIXED_FPS * _FLASH_SECONDS:
            self.flashing = False

    # -- rendering --------------------------------------------------------------------

    @property
    def _visible_this_frame(self) -> bool:
        # During invincibility the character blinks (visible ~75% of each second).
        return self.flash_timer == 0 or self.flash_timer % FIXED_FPS < (FIXED_FPS * 0.75)

    def _current_frame(self) -> tuple[pygame.Surface, tuple[float, float]]:
        if self.ducking:
            image = self.duck_left if self.direction == 0 else self.duck_right
            return image, (self.x, self.y + self.height - self.duck_height)
        if self.jumping:
            image = self.jumping_image_right if self.direction == 1 else self.jumping_image_left
            return image, (self.x, self.y)
        if self.on_ground and self.moving_laterally:
            frames = self.walk_images_right if self.direction == 1 else self.walk_images_left
            return frames[self.walk_frame], (self.x, self.y)
        return self.standing_image, (self.x, self.y)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible or not self._visible_this_frame:
            return
        image, position = self._current_frame()
        surface.blit(image, position)

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x + 10), int(self.y + 5), int(self.width - 10), int(self.height - 5)
        )

    def dispose(self) -> None:
        self.visible = False
