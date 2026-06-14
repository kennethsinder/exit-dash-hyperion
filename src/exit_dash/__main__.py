"""Command-line entry point: ``exit-dash-hyperion`` (or ``python -m exit_dash``).

Flags:
    --windowed        run in a window instead of fullscreen
    --no-vsync        disable vertical sync
    --headless        run with no real display/audio (for CI and smoke tests)
    --frames N        run exactly N frames then exit (implies a bounded run)
    --level N         start on level N (default 1)
    --character N     play as character 1, 2 or 3 (default 1)
"""

from __future__ import annotations

import argparse
import sys

from exit_dash import __version__
from exit_dash.core.constants import WINDOW_TITLE


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
    parser.add_argument("--level", type=int, default=1, metavar="N", help="start on level N")
    parser.add_argument(
        "--character", type=int, default=1, choices=(1, 2, 3), help="character to play as"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    # Import here so `--version`/`--help` stay fast and import-side-effect free.
    from exit_dash.core.app import Application
    from exit_dash.core.scene import Scene
    from exit_dash.core.settings import load_settings

    settings = load_settings()
    app = Application(
        headless=args.headless,
        fullscreen=not args.windowed and settings.fullscreen,
        vsync=not args.no_vsync and settings.vsync,
    )
    try:
        scene: Scene
        if args.headless:
            # In CI/smoke runs, exercise the actual gameplay loop rather than the title.
            from exit_dash.scenes.level import LevelScene

            scene = LevelScene(args.level, args.character, settings, audio=app.audio_enabled)
        else:
            from exit_dash.scenes.title import TitleScene

            scene = TitleScene(settings, audio=app.audio_enabled)
        app.run(scene, max_frames=args.frames)
    finally:
        app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
