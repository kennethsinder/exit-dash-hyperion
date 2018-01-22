# coding=utf-8
from random import randint, choice
import pygame

class BackgroundFoliage(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

        # Images
        self.images = [pygame.image.load('items\\rock.png').convert_alpha(),
                       pygame.image.load('environment\\main\\hill_smallAlt.png').convert_alpha(),
                       pygame.image.load('items\\plant.png').convert_alpha(),
                       pygame.image.load('items\\bush.png').convert_alpha()]
        self.image = choice(self.images)
        self.width = pygame.Surface.get_width(self.image)
        self.height = pygame.Surface.get_height(self.image)

# -----------------------------------------------------------------------------------------------------------------

    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))