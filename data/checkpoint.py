# coding=utf-8
import pygame
import os

class Checkpoint(object):

    def __init__(self, x, y, isBroken=False):
        self.x = x; self.y = y
        self.image = pygame.image.load('environment'+os.sep+'main'+os.sep+'fence.png').convert_alpha()
        self.imageBroken = pygame.image.load('environment'+os.sep+'main'+os.sep+'fenceBroken.png').convert_alpha()
        self.width = pygame.Surface.get_width(self.image)
        self.height = pygame.Surface.get_height(self.image)
        self.broken = isBroken

    def draw(self, surface):
        if self.broken:
            surface.blit(self.imageBroken, (self.x, self.y))
        else:
            surface.blit(self.image, (self.x, self.y))

    def getRect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
