"""A tiny keyboard-driven menu toolkit.

Menus here are a vertical list of :class:`Option` rows. The player moves a cursor with
up/down, changes the focused row with left/right (or activates it with Enter), and the
row pushes the change straight through getter/setter callbacks onto the live data. This
keeps screens like the options menu trivially testable — a test drives the menu with
plain key events and asserts on the underlying values, no mouse hit-testing needed.

Each row owns only *behaviour* (how it renders its value, how it responds to a nudge);
the owning scene draws the title and background and decides where the list sits.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import pygame

from exit_dash.core.constants import GREY, WHITE, YELLOW


class Option:
    """One selectable menu row. Subclasses define the value text and the response."""

    def __init__(self, label: str) -> None:
        self.label = label

    def value_text(self) -> str:
        """The right-hand value string shown for this row (empty for actions)."""
        return ""

    def adjust(self, direction: int) -> None:
        """Nudge the value left (``-1``) or right (``+1``). No-op by default."""

    def activate(self) -> None:
        """Respond to Enter. Defaults to a rightward nudge."""
        self.adjust(1)


class Toggle(Option):
    """An on/off row backed by a boolean getter/setter."""

    def __init__(self, label: str, get: Callable[[], bool], set: Callable[[bool], None]) -> None:
        super().__init__(label)
        self._get = get
        self._set = set

    def value_text(self) -> str:
        return "On" if self._get() else "Off"

    def adjust(self, direction: int) -> None:
        self._set(not self._get())

    def activate(self) -> None:
        self._set(not self._get())


class Slider(Option):
    """A clamped numeric row, rendered as a percentage with a little bar."""

    def __init__(
        self,
        label: str,
        get: Callable[[], float],
        set: Callable[[float], None],
        *,
        step: float = 0.1,
        lo: float = 0.0,
        hi: float = 1.0,
    ) -> None:
        super().__init__(label)
        self._get = get
        self._set = set
        self._step = step
        self._lo = lo
        self._hi = hi

    def adjust(self, direction: int) -> None:
        # Round to a step grid so repeated nudges don't accumulate float drift.
        raw = self._get() + direction * self._step
        clamped = max(self._lo, min(self._hi, raw))
        self._set(round(clamped / self._step) * self._step)

    def value_text(self) -> str:
        span = self._hi - self._lo
        fraction = 0.0 if span == 0 else (self._get() - self._lo) / span
        filled = round(fraction * 10)
        bar = "#" * filled + "-" * (10 - filled)
        return f"{round(fraction * 100):3d}%  [{bar}]"


class Choice(Option):
    """A row that cycles through a fixed list of string values."""

    def __init__(
        self,
        label: str,
        choices: Sequence[str],
        get: Callable[[], str],
        set: Callable[[str], None],
    ) -> None:
        super().__init__(label)
        self._choices = list(choices)
        self._get = get
        self._set = set

    def adjust(self, direction: int) -> None:
        try:
            i = self._choices.index(self._get())
        except ValueError:
            i = 0
        self._set(self._choices[(i + direction) % len(self._choices)])

    def value_text(self) -> str:
        return self._get()


class Action(Option):
    """A row that runs a callback when activated (e.g. "Back")."""

    def __init__(self, label: str, on_activate: Callable[[], None]) -> None:
        super().__init__(label)
        self._on_activate = on_activate

    def adjust(self, direction: int) -> None:
        """An action ignores left/right; only Enter triggers it."""

    def activate(self) -> None:
        self._on_activate()


class Menu:
    """A navigable list of :class:`Option` rows with a drawn cursor."""

    def __init__(self, options: Sequence[Option], item_font: pygame.font.Font) -> None:
        self.options = list(options)
        self._font = item_font
        self.index = 0

    @property
    def current(self) -> Option:
        return self.options[self.index]

    def move(self, delta: int) -> None:
        self.index = (self.index + delta) % len(self.options)

    def handle_key(self, key: int) -> None:
        """Apply a navigation/edit key to the menu (up/down/left/right/enter)."""
        if key in (pygame.K_UP, pygame.K_w):
            self.move(-1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.move(1)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.current.adjust(-1)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.current.adjust(1)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.current.activate()

    def draw(self, surface: pygame.Surface, *, center_x: int, top: int, line_height: int) -> None:
        for i, option in enumerate(self.options):
            selected = i == self.index
            color = YELLOW if selected else WHITE
            prefix = "> " if selected else "  "
            value = option.value_text()
            text = f"{prefix}{option.label}" + (f":  {value}" if value else "")
            label = self._font.render(text, True, color)
            rect = label.get_rect(center=(center_x, top + i * line_height))
            surface.blit(label, rect)
        # A faint reminder of the controls under the list.
        hint = self._font.render(
            "Up/Down select   Left/Right change   Enter toggle   Esc back", True, GREY
        )
        surface.blit(
            hint, hint.get_rect(center=(center_x, top + len(self.options) * line_height + 30))
        )
