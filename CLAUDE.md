# CLAUDE.md - Exit Dash: Hyperion

## Project Overview

A 2D platformer game built with Python and Pygame, created by Kenneth Sinder (2014). The project is approximately 30% complete. Players navigate through levels, avoiding hazards and enemies, collecting items, and reaching exit doors.

## Quick Start

```bash
pip install -r requirements.txt
python RunGame.py          # Preferred entry point (uses data/ package)
python MainGame.py         # Legacy monolithic entry point (not recommended)
```

The game runs in **fullscreen** mode by default at the native display resolution.

## Project Structure

```
exit-dash-hyperion/
├── RunGame.py               # Entry point — instantiates Game and runs the loop
├── MainGame.py              # Legacy monolithic version (~2900 lines, not maintained)
├── requirements.txt         # Single dependency: pygame==1.9.3
├── settings.cfg             # Auto-generated runtime settings (do not edit manually)
├── data/                    # Core game package (all game logic)
│   ├── game.py              # Main Game class — game loop, rendering, menus, level management
│   ├── character.py         # Base Character class (physics, collision, animation)
│   ├── playablecharacter.py # PlayableCharacter — player-controlled characters
│   ├── aicharacter.py       # AICharacter — enemy AI behavior
│   ├── platform.py          # Static/moving platforms
│   ├── block.py             # Breakable/interactive blocks
│   ├── pool.py              # Water pool hazards
│   ├── door.py              # Level exit doors
│   ├── key.py               # Keys (required for doors)
│   ├── spike.py             # FallingSpike hazard
│   ├── checkpoint.py        # Respawn checkpoint
│   ├── checkpointManager.py # Checkpoint tracking
│   ├── background.py        # Parallax scrolling backgrounds
│   ├── backgroundfoliage.py # Decorative foliage
│   ├── torch.py             # Decorative torches/lighting
│   └── keymap.py            # Keyboard input bindings
├── levels/                  # Binary .dat level files (lvl_1.dat through lvl_4.dat)
├── character/               # Character sprite assets
├── enemies/                 # Enemy sprite assets (slime, fly, fish, snail)
├── backgrounds/             # Background images (themed: aquatic, desert, castle, etc.)
├── environment/             # Tiles: platforms, blocks, hazards, decorations
├── items/                   # Collectibles: coins, gems, keys, weapons
├── hud/                     # HUD graphics (health, score, keys)
├── ui/                      # Menu UI button/widget sprites
├── fonts/                   # TTF/OTF font files
├── music/                   # Background music (MP3, OGG, WAV)
└── sounds/                  # Sound effects (OGG)
```

## Architecture

### Class Hierarchy

```
Character (base — physics, collision, sprites)
├── PlayableCharacter (input, health/lives, animations)
└── AICharacter (enemy patrol, attack patterns)

Game (central controller)
├── Game loop, rendering, state management
├── Level loading/saving (.dat binary format)
├── Menu screens (title, pause, options, game over)
└── Level editor
```

### Game Objects (standalone classes)

Platform, Block, Pool, Door, Key, FallingSpike, Checkpoint, Torch, Background, BackgroundFoliage

### Key Constants (in `data/game.py`)

- FPS presets: `SLOWFPS=25`, `VSYNCFPS=60`, `SMOOTHFPS=65`, `UNLIMITEDFPS=800`
- Color tuples: `white`, `black`, `red`, `green`, `blue`, `yellow`, etc.
- Default: 3 playable characters, 10 levels, fullscreen mode

### Input Bindings (`data/keymap.py`)

- Arrow keys for movement, Up/Space for action/jump, Down for duck, Escape/Q to exit

## Code Conventions

- **Naming**: Classes use PascalCase, methods use camelCase, constants use ALLCAPS or lowercase
- **Encoding**: All files declare `# coding=utf-8`
- **File paths**: Use `os.sep` for cross-platform compatibility
- **Images**: Always call `.convert()` or `.convert_alpha()` after loading for performance
- **Collision**: Rect-based via `pygame.Rect`
- **Physics**: Manual simulation (gravity, velocity) — no physics engine
- **Section markers**: Dashes `# ----` to separate method groups
- **Imports**: `import keymap as k`, `import random as r` are common aliases

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pygame  | 1.9.3   | Graphics, audio, input, collision, timing |

No other runtime dependencies. Install with `pip install -r requirements.txt`.

## Testing

No automated test suite exists. Testing is manual (run and play). There is no CI/CD pipeline configured.

## Asset Organization

Assets are organized into `main/`, `crossover/`, and `unused/` subdirectories:
- `main/` — Active assets used in the game
- `crossover/` — Alternative themed variants
- `unused/` — Legacy/deprecated assets

Level data is stored as binary `.dat` files in `levels/` containing X,Y coordinate pairs for object placement.

## Known Development Notes

The codebase has two parallel implementations:
1. **`data/` package** (recommended) — Modular OOP design, imported by `RunGame.py`
2. **`MainGame.py`** (legacy) — Single-file monolith (~2900 lines), kept for reference

When making changes, work in the `data/` package modules, not `MainGame.py`.

## Common Tasks

- **Add a new game object**: Create a new class in `data/`, follow the pattern of existing classes (constructor takes position + image path, has `update()` and `draw()` methods), import it in `game.py`
- **Add a new level**: Create a `.dat` file in `levels/` following the binary coordinate format
- **Change controls**: Edit `data/keymap.py`
- **Modify game settings**: Change defaults in `Game.__init__()` in `data/game.py`
