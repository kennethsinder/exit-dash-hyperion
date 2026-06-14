"""A per-frame snapshot of keyboard and mouse state.

The application polls this once per rendered frame; scenes read it during ``update``
instead of calling pygame's input functions directly. This keeps input testable (a
test can inject a fake snapshot) and gives edge detection ("pressed this frame") for
free. A higher-level action map is layered on top of this in :mod:`exit_dash` later.
"""

from __future__ import annotations

import pygame


class InputState:
    """Held/pressed keyboard state plus mouse position and click edges."""

    def __init__(self) -> None:
        self._keys: pygame.key.ScancodeWrapper | tuple[bool, ...] = ()
        self._prev_keys: pygame.key.ScancodeWrapper | tuple[bool, ...] = ()
        self.mouse_pos: tuple[int, int] = (0, 0)
        self._buttons: tuple[bool, ...] = (False, False, False)
        self._prev_buttons: tuple[bool, ...] = (False, False, False)

    def poll(self) -> None:
        """Capture the current keyboard and mouse state, remembering the previous one."""
        self._prev_keys = self._keys
        self._keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        self._prev_buttons = self._buttons
        self._buttons = pygame.mouse.get_pressed()

    def held(self, key: int) -> bool:
        """True while ``key`` (a ``pygame.K_*`` constant) is down."""
        return bool(self._keys) and bool(self._keys[key])

    def pressed(self, key: int) -> bool:
        """True only on the frame ``key`` transitions from up to down."""
        now = bool(self._keys) and bool(self._keys[key])
        was = bool(self._prev_keys) and bool(self._prev_keys[key])
        return now and not was

    @property
    def mouse_held(self) -> bool:
        """True while the left mouse button is down."""
        return self._buttons[0]

    @property
    def mouse_clicked(self) -> bool:
        """True only on the frame the left mouse button transitions from up to down."""
        return self._buttons[0] and not self._prev_buttons[0]
