"""OptionsScene: change settings in-game. Pushed from the title; Esc saves and returns.

Changes are applied to the live :class:`Settings` immediately and persisted to disk on
exit. Audio and fullscreen take effect right away; settings that only matter when a level
is (re)built — decorations, the developer overlay — apply the next time a level loads.
"""

from __future__ import annotations

import contextlib
from pathlib import Path

import pygame

from exit_dash.core import resources
from exit_dash.core.constants import BLACK, LOGICAL_WIDTH, WHITE
from exit_dash.core.input import InputState
from exit_dash.core.keybindings import DEFAULT_BINDINGS
from exit_dash.core.paths import asset_path
from exit_dash.core.scene import Pop, Scene, Transition
from exit_dash.core.settings import Settings, save_settings
from exit_dash.ui.widgets import Action, Menu, Slider, Toggle


class OptionsScene(Scene):
    def __init__(
        self,
        settings: Settings,
        *,
        audio: bool = True,
        config_dir: Path | None = None,
    ) -> None:
        self.settings = settings
        self.audio = audio
        self._config_dir = config_dir
        self._done = False
        self._title_font = resources.font("jetset.ttf", 64)
        self._item_font = resources.font("atari.ttf", 20)
        self.menu = Menu(
            [
                Toggle("Music", self._get_music, self._set_music),
                Slider("Volume", self._get_volume, self._set_volume),
                Toggle("Fullscreen", self._get_fullscreen, self._set_fullscreen),
                Toggle("Decorations", self._get_decorations, self._set_decorations),
                Toggle("Developer overlay", self._get_developer, self._set_developer),
                Action("Back", self._finish),
            ],
            self._item_font,
        )

    # -- setting accessors (getters/setters the widgets bind to) ----------------------

    def _get_music(self) -> bool:
        return self.settings.music_enabled

    def _set_music(self, value: bool) -> None:
        self.settings.music_enabled = value
        if value:
            self._start_music()
        elif pygame.mixer.get_init():
            pygame.mixer.music.stop()

    def _get_volume(self) -> float:
        return self.settings.volume

    def _set_volume(self, value: float) -> None:
        self.settings.volume = value
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(value)

    def _get_fullscreen(self) -> bool:
        return self.settings.fullscreen

    def _set_fullscreen(self, value: bool) -> None:
        self.settings.fullscreen = value
        # SCALED displays support a live toggle; if the driver refuses (e.g. headless),
        # the choice is still saved and honoured at the next launch.
        with contextlib.suppress(pygame.error):
            pygame.display.toggle_fullscreen()

    def _get_decorations(self) -> bool:
        return self.settings.decorations

    def _set_decorations(self, value: bool) -> None:
        self.settings.decorations = value

    def _get_developer(self) -> bool:
        return self.settings.developer_mode

    def _set_developer(self, value: bool) -> None:
        self.settings.developer_mode = value

    # -- music ------------------------------------------------------------------------

    def _start_music(self) -> None:
        if not (self.audio and pygame.mixer.get_init()):
            return
        try:
            pygame.mixer.music.load(str(asset_path("music", "menuloop.ogg")))
            pygame.mixer.music.set_volume(self.settings.volume)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    # -- lifecycle / input ------------------------------------------------------------

    def _finish(self) -> None:
        self._done = True

    def handle_event(self, event: pygame.event.Event) -> Transition | None:
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (DEFAULT_BINDINGS["EXIT"], DEFAULT_BINDINGS["EXIT2"]):
            self._finish()
        else:
            self.menu.handle_key(event.key)
        if self._done:
            save_settings(self.settings, config_dir=self._config_dir)
            return Pop()
        return None

    def update(self, dt: float, inp: InputState) -> Transition | None:
        return None

    def draw(self, surface: pygame.Surface, alpha: float) -> None:
        surface.fill(BLACK)
        title = self._title_font.render("Options", True, WHITE)
        surface.blit(title, title.get_rect(center=(LOGICAL_WIDTH // 2, 120)))
        self.menu.draw(surface, center_x=LOGICAL_WIDTH // 2, top=260, line_height=52)
