"""The scene stack: a small state machine that replaces the original god-method loop.

Each screen (title, options, a level, the editor, game-over) is a :class:`Scene`.
A scene's :meth:`Scene.update` returns an optional :class:`Transition` telling the
:class:`SceneManager` how to change the stack — push a screen on top, pop back to the
previous one, replace the current one, or quit the game.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame

    from exit_dash.core.input import InputState


class Transition:
    """Base class for the values a scene may return from event/update handlers."""


@dataclass(frozen=True)
class Push(Transition):
    """Pause the current scene and run ``scene`` on top of it."""

    scene: Scene


@dataclass(frozen=True)
class Pop(Transition):
    """Leave the current scene and resume the one beneath it, passing ``result`` back."""

    result: object | None = None


@dataclass(frozen=True)
class Replace(Transition):
    """Swap the current scene for ``scene`` (the current one does not resume)."""

    scene: Scene


@dataclass(frozen=True)
class Quit(Transition):
    """Tear down the whole stack and exit the game loop."""


class Scene(ABC):
    """One screen of the game. Subclasses override the hooks they need."""

    #: Set by the manager when the scene is pushed; lets a scene start transitions.
    manager: SceneManager

    def on_enter(self) -> None:  # noqa: B027 — optional hook, no-op by default
        """Called once when the scene is first pushed/replaced onto the stack."""

    def on_exit(self) -> None:  # noqa: B027 — optional hook, no-op by default
        """Called once when the scene is popped/replaced off the stack."""

    def on_resume(self, result: object | None) -> None:  # noqa: B027 — optional hook
        """Called when a scene pushed on top of this one pops back, with its result."""

    def handle_event(self, event: pygame.event.Event) -> Transition | None:
        """Handle a single pygame event. Return a transition to change the stack."""
        return None

    @abstractmethod
    def update(self, dt: float, inp: InputState) -> Transition | None:
        """Advance the scene by one fixed step (``dt`` seconds)."""

    @abstractmethod
    def draw(self, surface: pygame.Surface, alpha: float) -> None:
        """Render the scene. ``alpha`` is the 0..1 interpolation factor (unused for now)."""


class SceneManager:
    """Owns the scene stack and applies the transitions scenes request."""

    def __init__(self, initial: Scene) -> None:
        self._stack: list[Scene] = []
        self._running = True
        self._push(initial)

    @property
    def running(self) -> bool:
        return self._running and bool(self._stack)

    @property
    def current(self) -> Scene:
        return self._stack[-1]

    def _push(self, scene: Scene) -> None:
        scene.manager = self
        self._stack.append(scene)
        scene.on_enter()

    def apply(self, transition: Transition | None) -> None:
        """Mutate the stack according to a transition returned by the current scene."""
        match transition:
            case None:
                return
            case Push(scene=scene):
                self._push(scene)
            case Pop(result=result):
                leaving = self._stack.pop()
                leaving.on_exit()
                if self._stack:
                    self.current.on_resume(result)
                else:
                    self._running = False
            case Replace(scene=scene):
                leaving = self._stack.pop()
                leaving.on_exit()
                self._push(scene)
            case Quit():
                while self._stack:
                    self._stack.pop().on_exit()
                self._running = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._stack:
            self.apply(self.current.handle_event(event))

    def update(self, dt: float, inp: InputState) -> None:
        if self._stack:
            self.apply(self.current.update(dt, inp))

    def draw(self, surface: pygame.Surface, alpha: float) -> None:
        if self._stack:
            self.current.draw(surface, alpha)
