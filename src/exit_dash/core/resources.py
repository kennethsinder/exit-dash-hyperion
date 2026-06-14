"""Cached, package-anchored loading of images, fonts and sounds.

All asset access goes through here so paths resolve from the package (never the CWD),
results are cached, and a missing asset degrades to a visible magenta placeholder with a
logged warning instead of crashing the game.
"""

from __future__ import annotations

import logging

import pygame

from exit_dash.core.paths import asset_path

_log = logging.getLogger(__name__)

_images: dict[tuple[tuple[str, ...], bool], pygame.Surface] = {}
_fonts: dict[tuple[tuple[str, ...], int], pygame.font.Font] = {}
_sounds: dict[tuple[str, ...], pygame.mixer.Sound] = {}

_PLACEHOLDER_SIZE = (32, 32)
_PLACEHOLDER_COLOR = (255, 0, 255)


def _placeholder() -> pygame.Surface:
    surface = pygame.Surface(_PLACEHOLDER_SIZE)
    surface.fill(_PLACEHOLDER_COLOR)
    return surface


def image(*parts: str, alpha: bool = True) -> pygame.Surface:
    """Load and cache an image. Missing files become a magenta placeholder.

    Set ``alpha=False`` for fully opaque images (uses ``convert`` instead of
    ``convert_alpha``), matching the original's per-image choice.
    """
    key = (parts, alpha)
    cached = _images.get(key)
    if cached is not None:
        return cached

    path = asset_path(*parts)
    try:
        surface = pygame.image.load(str(path))
    except (pygame.error, FileNotFoundError):
        _log.warning("missing image asset: %s", path)
        surface = _placeholder()
    surface = surface.convert_alpha() if alpha else surface.convert()
    _images[key] = surface
    return surface


def font(name: str, size: int) -> pygame.font.Font:
    """Load and cache a font from the bundled ``fonts`` directory."""
    key = ((name,), size)
    cached = _fonts.get(key)
    if cached is not None:
        return cached
    loaded = pygame.font.Font(str(asset_path("fonts", name)), size)
    _fonts[key] = loaded
    return loaded


def sound(*parts: str) -> pygame.mixer.Sound:
    """Load and cache a sound effect."""
    cached = _sounds.get(parts)
    if cached is not None:
        return cached
    loaded = pygame.mixer.Sound(str(asset_path(*parts)))
    _sounds[parts] = loaded
    return loaded


def clear_cache() -> None:
    """Drop all cached assets (e.g. after the display pixel format changes)."""
    _images.clear()
    _fonts.clear()
    _sounds.clear()
