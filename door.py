# coding=utf-8
import pygame
from game import *


class Door(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.locked = True

        # Load images
        self.imageBottom = pygame.image.load('environment\\main\\door_openMid.png').convert_alpha()
        self.imageTop = pygame.image.load('environment\\main\\door_openTop.png').convert_alpha()
        self.imageBottomLocked = pygame.image.load('environment\\main\\door_closedMid.png').convert_alpha()
        self.imageTopLocked = pygame.image.load('environment\\main\\door_closedTop.png').convert_alpha()
        self.bottomHeight = pygame.Surface.get_height(self.imageBottom)
        self.topHeight = pygame.Surface.get_height(self.imageTop)
        self.topBlankSpace = 30
        self.height = self.bottomHeight + self.topHeight - self.topBlankSpace
        self.width = pygame.Surface.get_width(self.imageBottom)
        self.y -= self.bottomHeight + self.topHeight

    # -----------------------------------------------------------------------------------------------------------------
    def update(self, mainChar, surface, unlockable=True):
        charRect = pygame.Rect(mainChar.x, mainChar.y, mainChar.width, mainChar.height)
        selfRect = self.getRect()
        inDoor = charRect.colliderect(selfRect)
        hasKey = mainChar.hasKey
        if inDoor and hasKey and unlockable:
            self.locked = False
        if self.locked:
            surface.blit(self.imageTopLocked, (self.x, self.y))
            surface.blit(self.imageBottomLocked, (self.x, self.y + self.topHeight))
        elif unlockable:
            surface.blit(self.imageTop, (self.x, self.y))
            surface.blit(self.imageBottom, (self.x, self.y + self.topHeight))
        if not self.locked and inDoor and unlockable:
            return True
        return False

    # -----------------------------------------------------------------------------------------------------------------
    def getRect(self):
        return pygame.Rect(self.x, self.y + self.topBlankSpace, self.width, self.height)