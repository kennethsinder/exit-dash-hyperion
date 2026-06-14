# Exit Dash: Hyperion

A 2D platformer, originally written in 2014 (Python 2 + pygame 1.9.3) and modernized to
run on **Python 3.12+** with **[pygame-ce](https://pyga.me/)** across macOS, Linux, and
Windows.

Rebuilt with a scene manager, a fixed-timestep simulation, dataclasses and full type
hints, including an in-game options menu and a level editor. See [CLAUDE.md](CLAUDE.md)
for the architecture.

## Play

You need [uv](https://docs.astral.sh/uv/) (it manages Python and the dependencies for you):

```sh
git clone https://github.com/burincode/exit-dash-hyperion
cd exit-dash-hyperion
uv run exit-dash-hyperion
```

Run in a window instead of fullscreen:

```sh
uv run exit-dash-hyperion --windowed
```

### Controls

| Action | Keys |
| ------ | ---- |
| Move   | ← / → |
| Jump   | ↑ or Space |
| Duck   | ↓ |
| Quit   | Esc or Q |

From the title screen, press **O** for the options menu or **E** for the level editor.

### Level editor

Press **E** on the title screen to build a custom level: number keys pick a tool
(platform / coin / block / pool / ledge / door), left-click places and right-click
erases, `[`/`]` size the brush, the arrow keys pan, and `S`/`L` save and load
`lvl_custom.dat`. Press `P` to test-play; `H` toggles the on-screen help.

## Development

```sh
uv sync --all-extras        # create the venv and install dev tools
uv run pre-commit install   # enable lint/format on commit
uv run pytest               # tests (headless)
uv run ruff check . && uv run ruff format --check .
uv run mypy src
```

Tests, lint, format, type-check, and a headless smoke run are enforced in CI across
{macOS, Linux, Windows} × Python {3.12, 3.13, 3.14}.

## License

Code is MIT (see [LICENSE](LICENSE)). Art, audio, and fonts are third-party assets under
CC0 / open licenses — see [CREDITS.md](CREDITS.md).
