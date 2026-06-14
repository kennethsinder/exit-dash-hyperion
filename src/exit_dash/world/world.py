"""The World: every entity in a level, plus assembly from data or procedural generation.

This ports the original game's level-assembly methods (``loadLevel`` /
``generateRandomLevel`` and their shared helpers) onto one object. Randomness flows
through an injected ``random.Random`` so generated levels are reproducible from a seed
and tests are deterministic. The per-frame update/draw loop lives in
:class:`exit_dash.scenes.level.LevelScene`; this class owns the data and how it is built.
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from exit_dash.entities.background import Background
from exit_dash.entities.block import Block
from exit_dash.entities.checkpoint import Checkpoint
from exit_dash.entities.door import Door
from exit_dash.entities.enemy import AICharacter, MobType
from exit_dash.entities.foliage import BackgroundFoliage
from exit_dash.entities.key import Key
from exit_dash.entities.platform import Platform
from exit_dash.entities.pool import Pool
from exit_dash.entities.spike import FallingSpike
from exit_dash.entities.torch import Torch

if TYPE_CHECKING:
    from exit_dash.entities.player import PlayableCharacter
    from exit_dash.world.level import LevelData

DEFAULT_VALUE = -999
_MAX_TORCH_DISTANCE = 490


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


class World:
    def __init__(
        self,
        player: PlayableCharacter,
        screen_w: int,
        screen_h: int,
        *,
        theme: str = "stone",
        level: int = 1,
        decorations: bool = True,
        rng: random.Random | None = None,
        background: Background | None = None,
    ) -> None:
        self.player = player
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.theme = theme
        self.level = level
        self.decorations = decorations
        self.rng = rng if rng is not None else random.Random()
        self.background = background

        self.platforms: list[Platform] = []
        self.blocks: list[Block] = []
        self.keys: list[Key] = []
        self.enemies: list[AICharacter] = []
        self.mobs: list[AICharacter] = []
        self.icicles: list[FallingSpike] = []
        self.fences: list[Checkpoint] = []
        self.foliage: list[BackgroundFoliage] = []
        self.torches: list[Torch] = []
        self.pool: Pool | None = None
        self.door: Door | None = None
        self.fakedoor: Door | None = None
        self.movable_objects: list[object] = []

        self.autoscroll = False
        self.level_dark = False
        self.level_hint = ""
        self.seed: float = 0.0

        # Populated by gather_platform_info.
        self.longest_platform: Platform | None = None
        self.farthest_platform: Platform | None = None

    # -- shared assembly helpers (used by both load and generate) ---------------------

    def gather_platform_info(self) -> None:
        ref = self.platforms[1]
        topmost = lowest = shortest = longest = farthest = ref
        for p in self.platforms:
            if p[1] < topmost[1]:
                topmost = p
            if p[1] > lowest[1]:
                lowest = p
            if p.width > longest.width and p[0] != self.platforms[0][0]:
                longest = p
            if p[2] - p[0] < shortest[2] - shortest[0]:
                shortest = p
            if p[2] > farthest[2]:
                farthest = p
        self.longest_platform = longest
        self.farthest_platform = farthest

    def finalize_blocks(self) -> None:
        for block in self.blocks:
            if block.form == "regular" and not self.keys and not block.yields_star:
                key = Key(block.x, block.y - 80, "blue")
                self.keys.append(key)
                self.movable_objects.append(key)
            elif block.form == "regular" and self.rng.randint(0, 2) == 0:
                block.will_explode = True
            elif block.form == "regular":
                block.yields_star = True
            self.movable_objects.append(block)

    def _platform_collision(self, obj: object) -> bool:
        test_rect: pygame.Rect = obj.get_rect()  # type: ignore[attr-defined]
        return any(test_rect.colliderect(p.get_rect()) for p in self.platforms)

    def generate_mobs(self, longest: Platform, farthest: Platform) -> None:
        quantity = len(self.platforms) - 1
        sample = AICharacter(0, 0, 0, 0, ("slime", -1, -1))
        self.mobs = []
        for _ in range(quantity):
            which = self.rng.randint(1, len(self.platforms) - 1)
            while self.platforms[which][0] == longest[0]:
                which = self.rng.randint(1, len(self.platforms) - 1)
            p = self.platforms[which]
            mob_type: MobType = "slime" if self.rng.randint(0, 1) == 0 else "snail"
            self.mobs.append(
                AICharacter(
                    self.rng.randint(int(p[0]), int(p[2])),
                    p[3] - sample.height,
                    int(0.7 * self.player.run_speed),
                    0,
                    (mob_type, -1, -1),
                )
            )
        self.mobs.append(
            AICharacter(
                70,
                self.platforms[0][1] - 750,
                5,
                0,
                ("fly", int(self.platforms[0][0]), int(farthest[2])),
            )
        )
        if self.pool:
            self.mobs.append(
                AICharacter(
                    self.pool.pool_start_x + self.pool.tile_width,
                    self.pool.y + self.pool.tile_width,
                    5,
                    0,
                    ("fish", -1, -1),
                )
            )
        self.enemies.extend(self.mobs)
        self.movable_objects.extend(self.mobs)

    def generate_fences(self) -> None:
        sample = Checkpoint(DEFAULT_VALUE, DEFAULT_VALUE)
        self.fences = []
        for i in range(1, len(self.platforms), 5):
            if self.platforms[i].width >= 2 * sample.width and not self.autoscroll:
                self.fences.append(
                    Checkpoint(self.platforms[i][0] + 20, self.platforms[i][1] - sample.height)
                )
        self.movable_objects.extend(self.fences)

    def generate_foliage(self) -> None:
        self.foliage = []
        for platform in self.platforms:
            for x in range(int(platform.x), int(platform.x + platform.width - 100), 100):
                if self.rng.randint(0, 10) == 0 and self.decorations:
                    decoration = BackgroundFoliage(x, platform.y)
                    decoration.y -= decoration.height
                    self.movable_objects.append(decoration)
                    self.foliage.append(decoration)

    def generate_torches(self) -> None:
        if not self.level_dark:
            return
        assert self.farthest_platform is not None
        for block in self.blocks:
            torch = Torch(block.x, block.y - self.player.height - 25)
            if not self._platform_collision(torch) and torch.x <= self.farthest_platform[2]:
                self.torches.append(torch)
        for torch1 in list(self.torches):
            for torch2 in list(self.torches):
                if (
                    torch1 is not torch2
                    and _distance((torch1.x, torch1.y), (torch2.x, torch2.y)) < _MAX_TORCH_DISTANCE
                    and torch2 in self.torches
                ):
                    self.torches.remove(torch2)
        self.movable_objects.extend(self.torches)

    def decide_dark(self) -> None:
        self.level_dark = (self.rng.randint(0, 2) == 0 and self.level > 2) or self.level == 2

    def finalize_level(self, farthest: Platform) -> None:
        for key in self.keys:
            key.visible = False
        if not self.keys or self.autoscroll:
            key = Key(int(0.5 * (farthest[0] + farthest[2])), farthest[1] - 80, "blue")
            key.visible = True
            self.keys.append(key)
            self.movable_objects.append(key)
        self.player.x = self.platforms[0][0] + 20
        self.player.y = self.platforms[0][1] - self.player.height
        self.player.vx = 5
        self.player.cpu_controlled = True
        for c in [self.player, *self.mobs]:
            c.platform_init(self.platforms)
        self.player.set_map_obj_x(
            self.enemies, self.movable_objects, self.platforms, self.screen_w - 100
        )
        if self.background is not None:
            self.movable_objects.append(self.background)
        self.decide_dark()
        self.generate_torches()

    # -- build from saved level data --------------------------------------------------

    @classmethod
    def from_level_data(
        cls,
        data: LevelData,
        *,
        player: PlayableCharacter,
        screen_w: int,
        screen_h: int,
        theme: str = "stone",
        level: int = 1,
        decorations: bool = True,
        rng: random.Random | None = None,
        background: Background | None = None,
        hint: str = "",
    ) -> World:
        world = cls(
            player,
            screen_w,
            screen_h,
            theme=theme,
            level=level,
            decorations=decorations,
            rng=rng,
            background=background,
        )
        world.level_hint = hint
        world.seed = data.seed

        for rec in data.platforms:
            world.platforms.append(Platform(rec.x, rec.y, rec.width, style=theme))
        world.movable_objects.extend(world.platforms)
        world.gather_platform_info()

        if data.pool is not None:
            world.pool = Pool(data.pool.x, data.pool.y, data.pool.width, data.pool.height, theme)
            world.movable_objects.append(world.pool)

        for block_rec in data.blocks:
            world.blocks.append(
                Block(block_rec.x, block_rec.y, "coin" if block_rec.coin else "regular")
            )
        world.finalize_blocks()

        if data.ledge is not None:
            ledge = Platform(data.ledge.x, data.ledge.y, data.ledge.width, style="snow")
            world.platforms.append(ledge)
            world.movable_objects.append(ledge)
            for i in range(
                int(ledge[0] + ledge.tile_width * 2), int(ledge[2] - ledge.tile_width * 2), 40
            ):
                world.icicles.append(FallingSpike(i, ledge[3]))
            world.movable_objects.extend(world.icicles)

        assert world.longest_platform is not None and world.farthest_platform is not None
        world.generate_mobs(world.longest_platform, world.farthest_platform)

        world.door = Door(data.door.x, data.door.y)
        world.movable_objects.append(world.door)
        world.fakedoor = Door(world.platforms[0][0] + 10, world.platforms[0][1])
        world.movable_objects.append(world.fakedoor)

        if data.fences:
            world.generate_fences()
            world.autoscroll = False
        elif world.rng.randint(0, 3) == 0:
            world.autoscroll = True

        if data.foliage:
            world.generate_foliage()

        world.finalize_level(world.farthest_platform)
        return world

    # -- procedural generation --------------------------------------------------------

    def generate(self, num_platforms: int, seed: float | None = None) -> World:
        """Procedurally build a level (used when no saved level file exists)."""
        if seed is not None:
            self.rng.seed(seed)
            self.seed = seed
        player = self.player
        theme = self.theme

        # Step 1: lay out platforms with an iterative reachability-aware walk.
        first = Platform(
            self.rng.randint(-300, 500),
            self.rng.randint(self.screen_h - 200, self.screen_h - 50),
            self.rng.randint(800, 1500),
            style=theme,
        )
        overlap = True
        attempts = 3 * num_platforms
        max_h = player.max_jump_height - 10
        max_w = player.max_jump_length * 2
        while overlap and attempts >= 0:
            overlap = False
            attempts -= 1
            self.platforms = [first]
            for i in range(1, num_platforms):
                direction = [1, self.rng.randint(0, 1)]
                width = self.rng.randint(400, 2000)
                prev = self.platforms[i - 1]
                if direction[0] == 0 and direction[1] == 0:
                    right = prev[0] - self.rng.randint(int(0.5 * max_w), max_w)
                    left = right - width
                    top = prev[1] + self.rng.randint(int(0.75 * max_h), max_h)
                elif direction[0] == 0 and direction[1] == 1:
                    right = prev[0] - self.rng.randint(int(0.5 * max_w), max_w)
                    left = right - width
                    top = prev[1] - self.rng.randint(int(0.75 * max_h), max_h)
                elif direction[0] == 1 and direction[1] == 1:
                    left = prev[2] + self.rng.randint(int(0.5 * max_w), max_w)
                    top = prev[1] - self.rng.randint(int(0.75 * max_h), max_h)
                else:
                    left = prev[2] + self.rng.randint(int(1.2 * player.width), max_w)
                    top = prev[1] + self.rng.randint(int(0.5 * max_h), int(0.4 * self.screen_h))
                self.platforms.append(Platform(left, top, width, style=theme))
                overlap = self._platform_collision(self.platforms[i])
        self.movable_objects.extend(self.platforms)

        # Step 2: platform stats.
        self.gather_platform_info()
        assert self.longest_platform is not None and self.farthest_platform is not None
        focus_height = self.longest_platform[1] - 324

        # Step 3: a rare water pool (or a chance of autoscroll instead).
        self.pool = None
        if self.rng.randint(0, 2) == 0 or self.level <= 1:
            self.pool = Pool(
                self.farthest_platform[2] + int(0.9 * player.max_jump_length),
                self.farthest_platform[1],
                self.rng.randint(700, 900),
                4 * player.height,
                theme,
            )
            self.movable_objects.append(self.pool)
        elif self.rng.randint(0, 1) == 0:
            self.autoscroll = True

        # Step 4: bonus blocks.
        sample_block = Block(0, 0, "regular")
        block_height = math.floor(1.3 * player.height + sample_block.height)
        self.blocks = [
            Block(
                self.rng.randint(int(self.platforms[0][0] + 50), int(self.platforms[0][2] - 50)),
                self.platforms[0][1] - block_height,
                "coin",
            )
        ]
        self.keys = []
        for i in range(1, num_platforms):
            y = self.platforms[i][1] - block_height
            if self.platforms[i].x != self.longest_platform.x and self.rng.randint(0, 3) != 0:
                spread = int(0.4 * self.platforms[i].width)
                x = (
                    0.5 * self.platforms[i][0]
                    + 0.5 * self.platforms[i][2]
                    + self.rng.randint(-spread, spread)
                )
                self.blocks.append(Block(x, y, "coin"))
            elif self.platforms[i].x != self.longest_platform.x and not self.keys:
                spread = int(0.4 * self.platforms[i].width)
                x = (
                    0.5 * self.platforms[i][0]
                    + 0.5 * self.platforms[i][2]
                    + self.rng.randint(-spread, spread)
                )
                self.blocks.append(Block(x, y, "regular"))
        for block in self.blocks:
            for platform in self.platforms:
                if block.get_rect().colliderect(platform.get_rect()):
                    block.x += 550
        if self.pool:
            pool_block = Block(
                self.pool.pool_start_x + self.pool.tile_width,
                self.pool.y + self.pool.height - block_height,
                "regular",
            )
            pool_block.yields_star = True
            pool_block.will_explode = False
            self.blocks.append(pool_block)
        self.rng.shuffle(self.blocks)
        self.finalize_blocks()

        # Step 5: a snow ledge with icicles.
        self.icicles = []
        if self.longest_platform.y != self.platforms[0].y and (
            self.level == 1 or self.rng.randint(0, 1) == 0
        ):
            ledge = Platform(
                self.longest_platform[0], focus_height, self.longest_platform.width, style="snow"
            )
            for platform in self.platforms:
                if platform.get_rect().colliderect(ledge.get_rect()):
                    ledge.x, ledge.y = DEFAULT_VALUE, DEFAULT_VALUE
            self.platforms.append(ledge)
            self.movable_objects.append(ledge)
            for i in range(
                int(ledge[0] + ledge.tile_width * 2), int(ledge[2] - ledge.tile_width * 2), 40
            ):
                self.icicles.append(FallingSpike(i, ledge[3]))
            self.movable_objects.extend(self.icicles)

        # Steps 6-9: foliage, mobs, door, fences.
        self.generate_foliage()
        self.generate_mobs(self.longest_platform, self.farthest_platform)
        self.door = Door(self.farthest_platform[2] - 100, self.farthest_platform[1])
        self.movable_objects.append(self.door)
        self.fakedoor = Door(self.platforms[0].x + 10, self.platforms[0].y)
        self.movable_objects.append(self.fakedoor)
        self.generate_fences()

        # Step 10: finalize positions, camera and darkness.
        self.finalize_level(self.farthest_platform)
        return self

    # -- darkness rendering -----------------------------------------------------------

    @staticmethod
    def _illuminate(target: pygame.Surface, x: float, y: float, rng: random.Random) -> None:
        ix, iy = int(x), int(y)
        rad = rng.randint(215, 245)
        transp = 255
        delta = 3
        clr = 0
        while rad > 50:
            pygame.draw.circle(target, (clr, clr, 0, transp), (ix, iy), rad)
            rad -= delta
            transp -= delta
            clr += delta
        pygame.draw.circle(target, (clr, clr, 0, transp), (ix, iy), rad)

    def darken(self, surface: pygame.Surface, value: int) -> None:
        dark = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dark.set_alpha(value)
        for torch in self.torches:
            if torch.burning:
                self._illuminate(dark, torch.x + 0.5 * torch.width, torch.y + 5, self.rng)
        surface.blit(dark, (0, 0))
