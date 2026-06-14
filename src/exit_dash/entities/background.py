"""Parallax background: two copies of an image (one flipped) tiled for seamless wrap."""

from __future__ import annotations

import math

import pygame


class Background:
    def __init__(
        self,
        image: pygame.Surface,
        screen_width: int,
        screen_height: int,
        inverted_image: pygame.Surface | None = None,
        default_position: tuple[float, float] = (0, 0),
    ) -> None:
        self.image = image
        self.inverted_image = inverted_image or pygame.transform.flip(image, True, False).convert()
        self.target_width = screen_width
        self.target_height = screen_height

        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.x, self.y = default_position

        self._scale_images(precise=False)
        self.inverted_x = self.x + self.width

    def _scale_images(self, precise: bool = True) -> None:
        too_small = self.width < self.target_width or self.height < self.target_height
        if precise and too_small:
            width_factor = math.ceil(self.target_width / self.width)
            height_factor = math.ceil(self.target_height / self.height)
            factor = max(width_factor, height_factor)
            size = (self.width * factor, self.height * factor)
            self.image = pygame.transform.smoothscale(self.image, size)
            self.inverted_image = pygame.transform.smoothscale(self.inverted_image, size)
        elif too_small:
            while self.height < self.target_height:
                self.image = pygame.transform.scale2x(self.image)
                self.inverted_image = pygame.transform.scale2x(self.inverted_image)
                self.width = self.image.get_width()
                self.height = self.image.get_height()

    def update(self, surface: pygame.Surface) -> None:
        if self.x < -self.width:
            self.x = self.width
        elif self.x > self.width:
            self.x = -self.width
        if self.inverted_x < -self.width:
            self.inverted_x = self.width
        elif self.inverted_x > self.width:
            self.inverted_x = -self.width

        if self.x > self.inverted_x:
            self.x = self.inverted_x + self.width
        elif self.inverted_x > self.x:
            self.inverted_x = self.x + self.width

        surface.blit(self.image, (self.x, 0))
        surface.blit(self.inverted_image, (self.inverted_x, 0))
