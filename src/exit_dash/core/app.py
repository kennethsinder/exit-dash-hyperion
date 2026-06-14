"""The application: window/display setup and the fixed-timestep main loop.

The loop decouples simulation from rendering. Real elapsed time accumulates, and the
active scene is advanced in fixed ``FIXED_DT`` steps — zero or more per rendered frame —
so physics is frame-rate independent yet behaves exactly as the original per-frame code
did (no ``dt`` scaling inside the step, which would let fast objects tunnel through
collisions). Rendering then happens once per frame.
"""

from __future__ import annotations

import os

import pygame

from exit_dash.core import resources
from exit_dash.core.constants import (
    BLACK,
    FIXED_DT,
    LOGICAL_SIZE,
    MAX_FRAME_TIME,
    MAX_STEPS_PER_FRAME,
    WINDOW_TITLE,
)
from exit_dash.core.input import InputState
from exit_dash.core.scene import Quit, Scene, SceneManager


class Application:
    """Owns the pygame display and runs the fixed-timestep loop over a scene stack."""

    def __init__(
        self,
        *,
        headless: bool = False,
        fullscreen: bool = True,
        vsync: bool = True,
        render_fps_cap: int = 0,
    ) -> None:
        self.headless = headless
        self.fullscreen = fullscreen
        self.vsync = vsync
        self.render_fps_cap = render_fps_cap
        self.frame_count = 0

        if headless:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        pygame.display.init()
        pygame.font.init()
        self.audio_enabled = self._init_audio()
        self.screen = self._create_display()
        pygame.display.set_caption(WINDOW_TITLE)
        self.input = InputState()

    def _init_audio(self) -> bool:
        """Initialise the mixer, tolerating headless/CI environments with no audio."""
        try:
            pygame.mixer.init()
        except pygame.error:
            return False
        return pygame.mixer.get_init() is not None

    def _create_display(self) -> pygame.Surface:
        if self.headless:
            # The dummy SDL video driver dislikes SCALED/vsync; a plain surface is enough
            # and still lets Surface.convert()/convert_alpha() work.
            return pygame.display.set_mode(LOGICAL_SIZE)
        flags = pygame.SCALED | pygame.RESIZABLE
        if self.fullscreen:
            flags |= pygame.FULLSCREEN
        try:
            return pygame.display.set_mode(LOGICAL_SIZE, flags, vsync=1 if self.vsync else 0)
        except pygame.error:
            # vsync isn't available on every driver; fall back without it.
            return pygame.display.set_mode(LOGICAL_SIZE, flags)

    def run(self, initial_scene: Scene, max_frames: int | None = None) -> int:
        """Run the loop until the scene stack empties or ``max_frames`` is reached.

        Returns the number of rendered frames. When ``max_frames`` is set (headless
        tests/CI) each frame advances the simulation by exactly one fixed step, so the
        run is deterministic and "frames == simulation steps".
        """
        manager = SceneManager(initial_scene)
        clock = pygame.time.Clock()
        accumulator = 0.0
        deterministic = self.headless and max_frames is not None

        while manager.running:
            if max_frames is not None and self.frame_count >= max_frames:
                break

            elapsed = clock.tick(self.render_fps_cap) / 1000.0
            frame_time = FIXED_DT if deterministic else min(elapsed, MAX_FRAME_TIME)
            accumulator += frame_time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    manager.apply(Quit())
                else:
                    manager.handle_event(event)
                if not manager.running:
                    break

            self.input.poll()

            steps = 0
            while accumulator >= FIXED_DT and steps < MAX_STEPS_PER_FRAME and manager.running:
                manager.update(FIXED_DT, self.input)
                accumulator -= FIXED_DT
                steps += 1
            if steps == MAX_STEPS_PER_FRAME:
                accumulator = 0.0  # drop the backlog rather than spiral

            self.screen.fill(BLACK)
            if manager.running:
                manager.draw(self.screen, accumulator / FIXED_DT)
            pygame.display.flip()
            self.frame_count += 1

        return self.frame_count

    def quit(self) -> None:
        # Cached surfaces/fonts are bound to this pygame session; drop them so a later
        # session (e.g. the next test) reloads fresh assets instead of stale handles.
        resources.clear_cache()
        pygame.quit()
