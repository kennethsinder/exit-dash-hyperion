# coding=utf-8
import pygame
from game import *

class BackgroundFoliage(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

        # Images
        self.whichProp = randint(0, 2)
        self.hill = pygame.image.load('environment\\main\\hill_small.png').convert_alpha()
        self.bush = pygame.image.load('items\\bush.png').convert_alpha()
        self.rock = pygame.image.load('items\\rock.png').convert_alpha()
        self.image = self.hill
        if self.whichProp == 1:
            self.image = self.bush
        elif self.whichProp == 2:
            self.image = self.rock
        self.width = pygame.Surface.get_width(self.image)
        self.height = pygame.Surface.get_height(self.image)

# -----------------------------------------------------------------------------------------------------------------
    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))