# AGENTS.md

This project's agent/contributor guidance lives in **[CLAUDE.md](CLAUDE.md)** — it covers
the project layout, how to develop/run/test, coding conventions (fixed-timestep loop,
asset paths, typing/lint, DRY), and the modernization status. Please read it first.

Quick start:

```sh
uv sync --all-extras
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run mypy src
```
