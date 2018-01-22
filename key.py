# coding=utf-8
import pygame
from game import *


class Key:
    def __init__(self, x, y, colour):
        self.x = x
        self.y = y
        self.visible = False

        # Load image
        self.image = pygame.image.load('environment\\main\\key' + colour + '.png').convert_alpha()
        self.width = pygame.Surface.get_width(self.image)
        self.height = pygame.Surface.get_height(self.image)

    # -----------------------------------------------------------------------------------------------------------------
    def update(self, mainChar, surface):
        if self.visible:
            surface.blit(self.image, (self.x, self.y))
        keyRect = pygame.Rect(self.x, self.y, self.width, self.height)
        charRect = pygame.Rect(mainChar.x, mainChar.y, mainChar.width, mainChar.height)
        if keyRect.colliderect(charRect):
            mainChar.hasKey = True
            self.visible = False