"""EditorScene: build, save and test-play custom levels.

A schematic, mouse-driven editor over :class:`~exit_dash.world.editing.EditorModel`.
Left-click places the current tool at the (grid-snapped) cursor; right-click erases.
Number keys pick a tool, the arrow keys pan the camera, and the level can be saved to
``lvl_custom.dat`` in the user data dir and test-played in place. The heavy lifting
(records, limits, validity, I/O) lives in the model; this scene is input + drawing.
"""

from __future__ import annotations

import pygame

from exit_dash.core import resources
from exit_dash.core.constants import (
    BLUE,
    BRIGHT_GREEN,
    BRIGHT_RED,
    GREY,
    LOGICAL_HEIGHT,
    LOGICAL_WIDTH,
    WHITE,
    YELLOW,
)
from exit_dash.core.input import InputState
from exit_dash.core.keybindings import DEFAULT_BINDINGS
from exit_dash.core.paths import asset_path, user_data_dir
from exit_dash.core.scene import Pop, Push, Scene, Transition
from exit_dash.core.settings import Settings
from exit_dash.world import editing
from exit_dash.world.editing import (
    BLOCK_SIZE,
    CUSTOM_LEVEL_NAME,
    DEFAULT_POOL_HEIGHT,
    DOOR_HEIGHT,
    DOOR_WIDTH,
    PLATFORM_HEIGHT,
    EditorModel,
)

# Tools, selectable with the number keys.
PLATFORM, COIN_BLOCK, REGULAR_BLOCK, POOL, LEDGE, DOOR = range(6)
_TOOL_NAMES = {
    PLATFORM: "Platform",
    COIN_BLOCK: "Coin block",
    REGULAR_BLOCK: "Block",
    POOL: "Pool",
    LEDGE: "Ledge",
    DOOR: "Door",
}
_TOOL_KEYS = {
    pygame.K_1: PLATFORM,
    pygame.K_2: COIN_BLOCK,
    pygame.K_3: REGULAR_BLOCK,
    pygame.K_4: POOL,
    pygame.K_5: LEDGE,
    pygame.K_6: DOOR,
}
_PAN_SPEED = 14  # world px per fixed step while an arrow key is held
_STATUS_FRAMES = 150


class EditorScene(Scene):
    def __init__(self, settings: Settings, *, audio: bool = True) -> None:
        self.settings = settings
        self.audio = audio
        self.model = EditorModel.blank()
        self.tool = PLATFORM
        self.brush_width = editing.DEFAULT_PLATFORM_WIDTH
        self.cam_x = 0.0
        self.cam_y = 0.0
        self._mouse = (LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2)
        self._status = "New level — left-click to build, H toggles help"
        self._status_frames = _STATUS_FRAMES
        self._show_help = True
        self._font = resources.font("atari.ttf", 16)

    # -- music -------------------------------------------------------------------------

    def on_enter(self) -> None:
        self._start_music()

    def on_resume(self, result: object | None) -> None:
        # Coming back from a test-play: restore the editor's menu music.
        self._start_music()

    def _start_music(self) -> None:
        if not (self.audio and self.settings.music_enabled and pygame.mixer.get_init()):
            return
        try:
            pygame.mixer.music.load(str(asset_path("music", "menuloop.ogg")))
            pygame.mixer.music.set_volume(self.settings.volume)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    # -- coordinate helpers ------------------------------------------------------------

    def _to_world(self, screen_pos: tuple[int, int]) -> tuple[float, float]:
        return screen_pos[0] + self.cam_x, screen_pos[1] + self.cam_y

    def _to_screen(self, wx: float, wy: float) -> tuple[int, int]:
        return int(wx - self.cam_x), int(wy - self.cam_y)

    def _set_status(self, message: str) -> None:
        self._status = message
        self._status_frames = _STATUS_FRAMES

    # -- input -------------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> Transition | None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._on_click(event)
        if event.type == pygame.KEYDOWN:
            return self._on_key(event)
        return None

    def _on_click(self, event: pygame.event.Event) -> Transition | None:
        wx, wy = self._to_world(event.pos)
        if event.button == 1:
            self._place(wx, wy)
        elif event.button == 3:
            if self._erasing_protected_door(wx, wy):
                self._set_status("The door can't be erased — use the Door tool to move it")
            elif not self.model.erase_at(wx, wy):
                self._set_status("Nothing to erase here")
        return None

    def _erasing_protected_door(self, wx: float, wy: float) -> bool:
        d = self.model.door
        return d.x <= wx <= d.x + DOOR_WIDTH and d.y - DOOR_HEIGHT <= wy <= d.y

    def _place(self, wx: float, wy: float) -> None:
        if self.tool == PLATFORM:
            if not self.model.add_platform(wx, wy, self.brush_width):
                self._set_status("Platform limit reached (25)")
        elif self.tool in (COIN_BLOCK, REGULAR_BLOCK):
            if not self.model.add_block(wx, wy, coin=self.tool == COIN_BLOCK):
                self._set_status("Block limit reached (25)")
        elif self.tool == POOL:
            self.model.set_pool(wx, wy, self.brush_width, DEFAULT_POOL_HEIGHT)
        elif self.tool == LEDGE:
            self.model.set_ledge(wx, wy, self.brush_width)
        elif self.tool == DOOR:
            self.model.set_door(wx, wy)

    def _on_key(self, event: pygame.event.Event) -> Transition | None:
        key = event.key
        if key in (DEFAULT_BINDINGS["EXIT"], DEFAULT_BINDINGS["EXIT2"]):
            return Pop()
        if key in _TOOL_KEYS:
            self.tool = _TOOL_KEYS[key]
            self._set_status(f"Tool: {_TOOL_NAMES[self.tool]}")
        elif key == pygame.K_LEFTBRACKET:
            self.brush_width = max(editing.GRID, self.brush_width - editing.GRID)
        elif key == pygame.K_RIGHTBRACKET:
            self.brush_width += editing.GRID
        elif key == pygame.K_f:
            self.model.fences = not self.model.fences
            self._set_status(f"Fences (checkpoints): {'on' if self.model.fences else 'off'}")
        elif key == pygame.K_g:
            self.model.foliage = not self.model.foliage
            self._set_status(f"Foliage: {'on' if self.model.foliage else 'off'}")
        elif key == pygame.K_c:
            self.model = EditorModel.blank()
            self._set_status("Cleared to a new level")
        elif key == pygame.K_h:
            self._show_help = not self._show_help
        elif key == pygame.K_s:
            self._save()
        elif key == pygame.K_l:
            self._load()
        elif key in (pygame.K_p, pygame.K_RETURN, pygame.K_KP_ENTER):
            return self._test_play()
        return None

    def _save(self) -> None:
        path = user_data_dir() / CUSTOM_LEVEL_NAME
        self.model.save(path)
        self._set_status(f"Saved to {path}")

    def _load(self) -> None:
        path = user_data_dir() / CUSTOM_LEVEL_NAME
        if path.is_file():
            self.model = EditorModel.load(path)
            self._set_status(f"Loaded {path}")
        else:
            self._set_status("No saved custom level found")

    def _test_play(self) -> Transition | None:
        ok, reason = self.model.playability()
        if not ok:
            self._set_status(f"Can't play yet: {reason}")
            return None
        from exit_dash.scenes.level import LevelScene

        return Push(
            LevelScene(
                1,
                1,
                self.settings,
                audio=self.audio,
                final_level=1,
                custom_data=self.model.to_level_data(),
                sandbox=True,
            )
        )

    # -- update ------------------------------------------------------------------------

    def update(self, dt: float, inp: InputState) -> Transition | None:
        self._mouse = inp.mouse_pos
        if inp.held(pygame.K_LEFT):
            self.cam_x -= _PAN_SPEED
        if inp.held(pygame.K_RIGHT):
            self.cam_x += _PAN_SPEED
        if inp.held(pygame.K_UP):
            self.cam_y -= _PAN_SPEED
        if inp.held(pygame.K_DOWN):
            self.cam_y += _PAN_SPEED
        if self._status_frames > 0:
            self._status_frames -= 1
        return None

    # -- draw --------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, alpha: float) -> None:
        surface.fill((24, 26, 34))
        self._draw_grid(surface)
        self._draw_objects(surface)
        self._draw_cursor(surface)
        self._draw_hud(surface)

    def _draw_grid(self, surface: pygame.Surface) -> None:
        spacing = editing.GRID * 4
        color = (40, 43, 54)
        first_x = int(-self.cam_x % spacing)
        for x in range(first_x, LOGICAL_WIDTH, spacing):
            pygame.draw.line(surface, color, (x, 0), (x, LOGICAL_HEIGHT))
        first_y = int(-self.cam_y % spacing)
        for y in range(first_y, LOGICAL_HEIGHT, spacing):
            pygame.draw.line(surface, color, (0, y), (LOGICAL_WIDTH, y))

    def _draw_objects(self, surface: pygame.Surface) -> None:
        m = self.model
        if m.pool:
            self._rect(surface, m.pool.x, m.pool.y, m.pool.width, m.pool.height, BLUE)
        for p in m.platforms:
            self._rect(surface, p.x, p.y, p.width, PLATFORM_HEIGHT, (120, 92, 60))
        # Mark the spawn platform so it's obvious where the player starts.
        if m.platforms:
            sp = m.platforms[0]
            self._rect(surface, sp.x, sp.y, sp.width, PLATFORM_HEIGHT, (90, 150, 90), border=3)
        if m.ledge:
            self._rect(surface, m.ledge.x, m.ledge.y, m.ledge.width, PLATFORM_HEIGHT // 2, GREY)
        for b in m.blocks:
            color = YELLOW if b.coin else (200, 140, 80)
            self._rect(surface, b.x, b.y, BLOCK_SIZE, BLOCK_SIZE, color, border=2)
        # The door is drawn with its base at door.y, growing upward.
        self._rect(surface, m.door.x, m.door.y - DOOR_HEIGHT, DOOR_WIDTH, DOOR_HEIGHT, BRIGHT_GREEN)

    def _rect(
        self,
        surface: pygame.Surface,
        wx: float,
        wy: float,
        w: float,
        h: float,
        color: tuple[int, int, int],
        *,
        border: int = 0,
    ) -> None:
        sx, sy = self._to_screen(wx, wy)
        rect = pygame.Rect(sx, sy, int(w), int(h))
        # Skip anything fully off-screen to keep large levels cheap to draw.
        if (
            rect.right < 0
            or rect.left > LOGICAL_WIDTH
            or rect.bottom < 0
            or rect.top > LOGICAL_HEIGHT
        ):
            return
        pygame.draw.rect(surface, color, rect, border)

    def _draw_cursor(self, surface: pygame.Surface) -> None:
        wx, wy = self._to_world(self._mouse)
        wx, wy = editing.snap(wx), editing.snap(wy)
        sx, sy = self._to_screen(wx, wy)
        if self.tool == PLATFORM:
            size = (self.brush_width, PLATFORM_HEIGHT)
        elif self.tool in (COIN_BLOCK, REGULAR_BLOCK):
            size = (BLOCK_SIZE, BLOCK_SIZE)
        elif self.tool == POOL:
            size = (self.brush_width, DEFAULT_POOL_HEIGHT)
        elif self.tool == LEDGE:
            size = (self.brush_width, PLATFORM_HEIGHT // 2)
        else:  # DOOR
            sy -= DOOR_HEIGHT
            size = (DOOR_WIDTH, DOOR_HEIGHT)
        ghost = pygame.Rect(sx, sy, int(size[0]), int(size[1]))
        pygame.draw.rect(surface, WHITE, ghost, 1)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        m = self.model
        ok, reason = m.playability()
        status_color = BRIGHT_GREEN if ok else BRIGHT_RED
        top = self._font.render(
            f"Tool: {_TOOL_NAMES[self.tool]}   Brush width: {self.brush_width}"
            f"   Platforms: {len(m.platforms)}   Blocks: {len(m.blocks)}"
            f"   Fences: {'on' if m.fences else 'off'}   Foliage: {'on' if m.foliage else 'off'}",
            True,
            WHITE,
        )
        surface.blit(top, (16, 12))
        validity = self._font.render(reason, True, status_color)
        surface.blit(validity, (16, 36))

        if self._status_frames > 0:
            msg = self._font.render(self._status, True, YELLOW)
            surface.blit(msg, msg.get_rect(midbottom=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 14)))

        if self._show_help:
            self._draw_help(surface)

    _HELP_LINES = (
        "LEVEL EDITOR",
        "1-6  pick tool: platform / coin / block / pool / ledge / door",
        "Left-click place    Right-click erase",
        "[ ]  brush width    Arrows  pan",
        "F fences   G foliage   C clear",
        "S save   L load   P or Enter  test-play",
        "H toggle this help   Esc back to title",
    )

    def _draw_help(self, surface: pygame.Surface) -> None:
        panel = pygame.Surface((520, 24 * len(self._HELP_LINES) + 16), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 170))
        surface.blit(panel, (16, LOGICAL_HEIGHT - panel.get_height() - 40))
        y = LOGICAL_HEIGHT - panel.get_height() - 32
        for i, line in enumerate(self._HELP_LINES):
            color = YELLOW if i == 0 else WHITE
            surface.blit(self._font.render(line, True, color), (28, y + i * 24))
