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
  scenes/               # screens: title, level, game-over (options + editor: see below)
  entities/             # player, enemy, platform, block, pool, spike, door, key, ...
  world/                # LevelData + World, .dat loader, procedural generator, hints
  assets/               # bundled images, audio, fonts, level data (.dat)
tests/                  # pytest suite (headless via SDL dummy drivers)
```

Note: entities are plain typed classes (not `pygame.sprite.Sprite`) — the move-the-world
camera + bespoke per-entity rendering don't use sprite groups, so the base only added
friction. The camera lives on `PlayableCharacter` (the "move the world" methods).

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

## Status & not-yet-ported

The Python-2 → 3 + pygame-ce modernization is complete: the legacy `data/` tree has been
removed and `src/exit_dash/` is the only implementation. Behavior that had to be preserved
(collision feel, `.dat` level semantics, per-character stats, move-the-world camera,
autoscroll, torch/darkness, generator RNG order) is locked in by the tests.

**Not yet ported from the original** (the game is fully playable without them — good
next tasks):

- **Options menu** — settings exist (`core/settings.py`) and persist, but there's no
  in-game UI to change them yet. A `scenes/options.py` + `ui/widgets.py` (button/slider/
  toggle) would wire it up.
- **In-game level editor** — the original let you build/save custom levels to
  `lvl_custom.dat`; `world/loader.py` can already read/write the format, so this is an
  editor `Scene` on top of it.

## Gotchas

- Never load assets relative to the CWD (the original's biggest portability bug); use
  `core/paths.py` / `core/resources.py`.
- Level `.dat` files historically had mixed CRLF/LF line endings — the loader normalizes
  on read; `.gitattributes` keeps them LF.
- Audio/display may be unavailable in CI; guard with the patterns in `core/app.py`.
