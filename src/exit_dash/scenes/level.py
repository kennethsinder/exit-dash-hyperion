"""LevelScene: plays one level. The per-frame simulation and rendering loop.

Update advances the simulation by one fixed step in the original game's order (enemies,
icicles, then the player, which also scrolls the move-the-world camera); draw renders
everything in the original blit order. Reaching the door advances to the next level;
running out of lives ends the run.
"""

from __future__ import annotations

import random

import pygame

from exit_dash.core import resources
from exit_dash.core.constants import BLACK, FIXED_FPS, LOGICAL_HEIGHT, LOGICAL_WIDTH, WHITE
from exit_dash.core.input import InputState, PlayerInput
from exit_dash.core.keybindings import DEFAULT_BINDINGS, key_names
from exit_dash.core.paths import asset_path
from exit_dash.core.scene import Quit, Replace, Scene, Transition
from exit_dash.core.settings import Settings
from exit_dash.entities.background import Background
from exit_dash.entities.player import PlayableCharacter
from exit_dash.world import hints, loader
from exit_dash.world.world import World

MAX_SHIPPED_LEVEL = 4
_HINT_FRAMES = 13 * FIXED_FPS  # show the level/hint banner for ~13s, like the original
_BACKGROUND_BY_THEME = {
    "stone": "bg_grasslands.png",
    "snow": "bg_castle.png",
    "castle": "bg_castle.png",
    "desert": "bg_desert.png",
}


class LevelScene(Scene):
    def __init__(
        self,
        level: int,
        which_char: int,
        settings: Settings,
        *,
        audio: bool = True,
        final_level: int = MAX_SHIPPED_LEVEL,
    ) -> None:
        self.level = level
        self.which_char = which_char
        self.settings = settings
        self.audio = audio
        self.final_level = final_level
        self.theme = "stone"
        self.player = PlayableCharacter(0, 0, which_char=which_char)
        self.world: World = self._build_world(level)
        self._banner_frames = _HINT_FRAMES
        self._allow_kill_bonus = True
        self._med_font = resources.font("jetset.ttf", 28)
        self._small_font = resources.font("atari.ttf", 16)

    # -- setup ------------------------------------------------------------------------

    def _make_background(self) -> Background:
        name = _BACKGROUND_BY_THEME.get(self.theme, "bg_grasslands.png")
        image = resources.image("backgrounds", "main", name, alpha=False)
        return Background(image, LOGICAL_WIDTH, LOGICAL_HEIGHT)

    def _build_world(self, level: int) -> World:
        background = self._make_background()
        rng = random.Random(level)
        level_path = asset_path("levels", f"lvl_{level}.dat")
        hint = hints.hint_for_level(level, key_names())
        if level_path.is_file() and level <= MAX_SHIPPED_LEVEL:
            data = loader.read_level(level_path)
            return World.from_level_data(
                data,
                player=self.player,
                screen_w=LOGICAL_WIDTH,
                screen_h=LOGICAL_HEIGHT,
                theme=self.theme,
                level=level,
                decorations=self.settings.decorations,
                rng=rng,
                background=background,
                hint=hint,
            )
        world = World(
            self.player,
            LOGICAL_WIDTH,
            LOGICAL_HEIGHT,
            theme=self.theme,
            level=level,
            decorations=self.settings.decorations,
            rng=rng,
            background=background,
        )
        world.level_hint = hint
        return world.generate(5 + 5 * level, seed=level)

    def on_enter(self) -> None:
        self._start_music()

    def _start_music(self) -> None:
        if not (self.audio and self.settings.music_enabled and pygame.mixer.get_init()):
            return
        try:
            pygame.mixer.music.load(str(asset_path("music", "char1_3.ogg")))
            pygame.mixer.music.set_volume(self.settings.volume)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    # -- input ------------------------------------------------------------------------

    @staticmethod
    def _player_input(inp: InputState) -> PlayerInput:
        b = DEFAULT_BINDINGS
        return PlayerInput(
            left=inp.held(b["LEFT"]),
            right=inp.held(b["RIGHT"]),
            jump=inp.held(b["ACTION"]) or inp.held(b["ACTION2"]),
            duck=inp.held(b["DUCK"]),
        )

    def handle_event(self, event: pygame.event.Event) -> Transition | None:
        if event.type == pygame.KEYDOWN and event.key in (
            DEFAULT_BINDINGS["EXIT"],
            DEFAULT_BINDINGS["EXIT2"],
        ):
            return Quit()
        return None

    # -- update -----------------------------------------------------------------------

    def update(self, dt: float, inp: InputState) -> Transition | None:
        world = self.world
        platforms = world.platforms
        controls = self._player_input(inp)

        # Hand control to the player once the intro CPU walk-in reaches mid-platform.
        if self.player.x >= platforms[0][0] + 0.5 * platforms[0].width:
            self.player.vx = 0
            self.player.cpu_controlled = False

        reached_exit = world.door.update(self.player) if world.door else False
        if world.fakedoor:
            world.fakedoor.update(self.player, unlockable=False)

        for platform in platforms:
            platform.update_motion((0, 0, world.screen_w, world.screen_h))
        for block in world.blocks:
            block.update_state()
        for enemy in world.enemies:
            enemy.step(platforms, world.blocks, world.enemies, world.pool, world.torches)
        for spike in world.icicles:
            spike.update_motion([self.player], platforms)
            spike.collide([self.player], platforms)

        self.player.collide(platforms, world.blocks, world.enemies, world.pool, world.torches)
        self.player.collide_checkpoint(world.fences)
        alive = self.player.move(
            controls,
            platforms,
            world.movable_objects,
            world.enemies,
            world.screen_w,
            world.screen_h,
            world.autoscroll,
        )
        for key in world.keys:
            key.update(self.player)

        self._update_kill_bonus()
        if self._banner_frames > 0:
            self._banner_frames -= 1

        if not alive:
            return self._game_over(won=False)
        if reached_exit:
            return self._advance_level()
        return None

    def _game_over(self, *, won: bool) -> Transition:
        from exit_dash.scenes.gameover import GameOverScene

        return Replace(GameOverScene(won, self.settings, audio=self.audio))

    def _update_kill_bonus(self) -> None:
        if self.player.mob_jumping and self._allow_kill_bonus:
            self._allow_kill_bonus = False
            self.player.coins += 2
        elif not self.player.mob_jumping:
            self._allow_kill_bonus = True

    def _advance_level(self) -> Transition | None:
        self.level += 1
        if self.level > self.final_level:
            return self._game_over(won=True)
        self.player.has_key = False
        self.world = self._build_world(self.level)
        self._banner_frames = _HINT_FRAMES
        return None

    # -- draw -------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, alpha: float) -> None:
        surface.fill(BLACK)
        world = self.world
        if world.background:
            world.background.update(surface)
        if world.fakedoor:
            world.fakedoor.draw(surface)
        if world.door:
            world.door.draw(surface)
        if world.pool:
            world.pool.draw(surface)
        for fence in world.fences:
            fence.draw(surface)
        for foliage in world.foliage:
            foliage.draw(surface)
        for torch in world.torches:
            torch.draw(surface)
        for platform in world.platforms:
            platform.draw(surface)
        for block in world.blocks:
            block.draw(world.keys, surface)
        for enemy in world.enemies:
            enemy.draw(surface)
        for spike in world.icicles:
            spike.draw(world.platforms, world.blocks, surface)
        self.player.draw(surface)
        for key in world.keys:
            key.draw(surface)

        if self._banner_frames > 0:
            self._draw_banner(surface)
        if world.level_dark:
            world.darken(surface, 130)

    def _draw_banner(self, surface: pygame.Surface) -> None:
        level_label = self._med_font.render(f"Level {self.level}", True, WHITE)
        surface.blit(level_label, (LOGICAL_WIDTH - 170, 40))
        if self.world.level_hint:
            hint_label = self._small_font.render(self.world.level_hint, True, WHITE)
            surface.blit(hint_label, (60, 180))
