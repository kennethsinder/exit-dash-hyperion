"""Command-line entry point: ``exit-dash-hyperion`` (or ``python -m exit_dash``).

Flags:
    --windowed        run in a window instead of fullscreen
    --no-vsync        disable vertical sync
    --headless        run with no real display/audio (for CI and smoke tests)
    --frames N        run exactly N frames then exit (implies a bounded run)
"""

from __future__ import annotations

import argparse
import sys

import pygame

from exit_dash import __version__
from exit_dash.core.constants import LOGICAL_SIZE, WINDOW_TITLE
from exit_dash.core.input import InputState
from exit_dash.core.scene import Quit, Scene, Transition


class _SkeletonScene(Scene):
    """Temporary placeholder shown until the real scenes land in later phases."""

    def __init__(self) -> None:
        self._font = pygame.font.SysFont(None, 48)
        self._tick = 0

    def handle_event(self, event: pygame.event.Event) -> Transition | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return Quit()
        return None

    def update(self, dt: float, inp: InputState) -> Transition | None:
        self._tick += 1
        return None

    def draw(self, surface: pygame.Surface, alpha: float) -> None:
        surface.fill((12, 14, 28))
        label = self._font.render(WINDOW_TITLE, True, (235, 235, 245))
        rect = label.get_rect(center=(LOGICAL_SIZE[0] // 2, LOGICAL_SIZE[1] // 2))
        surface.blit(label, rect)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="exit-dash-hyperion", description=WINDOW_TITLE)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--windowed", action="store_true", help="run in a window")
    parser.add_argument("--no-vsync", action="store_true", help="disable vertical sync")
    parser.add_argument(
        "--headless", action="store_true", help="run with no display/audio (CI/tests)"
    )
    parser.add_argument(
        "--frames", type=int, default=None, metavar="N", help="run exactly N frames then exit"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    # Importing here keeps `--version`/`--help` fast and import-side-effect free.
    from exit_dash.core.app import Application

    app = Application(
        headless=args.headless,
        fullscreen=not args.windowed,
        vsync=not args.no_vsync,
    )
    try:
        app.run(_SkeletonScene(), max_frames=args.frames)
    finally:
        app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
