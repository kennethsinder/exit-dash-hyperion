# CLAUDE.md

Guidance for Claude Code (and other agents — see `AGENTS.md`) working in this repo.

## What this is

`exit-dash-hyperion` is a 2D platformer first written in 2014 in **Python 2 + pygame
1.9.3**. It is being modernized to **Python 3.12+ + pygame-ce**, cross-platform
(macOS/Linux/Windows), with a modern architecture and tooling.

## Project layout

```
src/exit_dash/          # the game (single source of truth)
  core/                 # engine: app loop, scene stack, input, settings, resources, paths
  scenes/               # screens: title, options, level, editor, game-over
  entities/             # sprites: player, enemy, platform, block, pool, spike, door, ...
  world/                # LevelData + World, camera, .dat loader, generator, hints
  ui/                   # reusable widgets (buttons, sliders, toggles)
  assets/               # bundled images, audio, fonts, level data (.dat)
tests/                  # pytest suite (headless via SDL dummy drivers)
data/                   # LEGACY Python-2 reference implementation — see "Migration" below
```

## Develop / run / test

This project uses **uv**. Common commands:

```sh
uv sync --all-extras                 # install deps + dev tools
uv run exit-dash-hyperion            # play (use --windowed / --headless / --frames N)
uv run pytest                        # tests
uv run ruff check . && uv run ruff format .
uv run mypy src
```

CI matrix: {ubuntu, macos, windows} × Python {3.12, 3.13, 3.14}.

## Conventions

- **Fixed-timestep simulation.** The loop in `core/app.py` advances scenes in fixed
  `FIXED_DT` (1/60 s) steps, decoupled from render rate. Physics constants are *not*
  scaled by `dt` inside a step — they are tuned per-step, exactly as the original
  per-frame code was. Do **not** introduce `pos += vel * dt`; it would change feel and
  cause collision tunnelling.
- **Assets via `core/paths.py`.** Never load assets relative to the CWD. Use
  `paths.asset_path(...)`; user-writable state (settings, custom levels) goes in
  `paths.user_config_dir()` / `paths.user_data_dir()`.
- **Typing + lint.** Full type hints; keep `ruff` and `mypy src` clean. Prefer
  `pathlib` over `os.path`, dataclasses for records, `pygame.math.Vector2` for positions.
- **DRY.** Reuse engine/core helpers; don't reintroduce the legacy god-class patterns.
- **Tests.** Add/extend tests in `tests/` for new behavior. Everything runs headless via
  `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy` (set in `tests/conftest.py`).

## Migration status

The legacy `data/` package is the **behavioral reference** during the rewrite and is
deleted once `src/exit_dash/` reaches parity. When porting logic, preserve:
collision/feel, the `.dat` level format (round-trips byte-for-byte), per-character stats,
camera "move-the-world" scrolling, autoscroll, and the torch/darkness mechanic. Capture
golden values from the reference before refactoring seed-sensitive code (the level
generator's RNG call order must be preserved). The full plan lives in
`~/.claude/plans/` (the approved "Aggressive Modernization Plan").

## Gotchas

- The legacy code assumed it ran from the repo root; the modernized code must not.
- Level `.dat` files historically had mixed CRLF/LF line endings — the loader normalizes
  on read; `.gitattributes` keeps them LF.
- Audio/display may be unavailable in CI; guard with the patterns in `core/app.py`.
