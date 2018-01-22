# coding=utf-8
import pygame, random, os


class Torch(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.burning = False
        self.onImage1 = pygame.image.load('environment'+os.sep+'main'+os.sep+'torchLit.png').convert_alpha()
        self.onImage2 = pygame.image.load('environment'+os.sep+'main'+os.sep+'torchLit2.png').convert_alpha()
        self.offImage = pygame.image.load('environment'+os.sep+'main'+os.sep+'torch.png').convert_alpha()
        self.width = pygame.Surface.get_width(self.offImage)
        self.height = pygame.Surface.get_height(self.offImage)

    # -----------------------------------------------------------------------------------------------------------------

    def draw(self, surface):
        if not self.burning:
            surface.blit(self.offImage, [self.x, self.y])
        elif random.randint(0, 1) == 1:
            surface.blit(self.onImage1, [self.x, self.y])
        else:
            surface.blit(self.onImage2, [self.x, self.y])

    # -----------------------------------------------------------------------------------------------------------------

    def getRect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
