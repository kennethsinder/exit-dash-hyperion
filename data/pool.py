# coding=utf-8
from game import *

class Pool(object):

    def __init__(self, x, y, width, height, style='grass'):
        self.x, self.y = x, y
        self.Vx, self.Vy = 0, 0
        self.width, self.height = width, height

        # Platform images
        self.image = pygame.image.load('environment\\main\\' + style + 'Mid.png').convert_alpha()
        self.plainImage = pygame.image.load('environment\\main\\' + style + 'Center.png')
        self.leftImage = pygame.image.load('environment\\main\\' + style + 'CliffLeft.png').convert_alpha()
        self.rightImage = pygame.image.load('environment\\main\\' + style + 'CliffRight.png').convert_alpha()
        self.tileWidth = pygame.Surface.get_width(self.image)

        # Water images
        self.waterFilled = pygame.image.load('environment\\main\\liquidWater.png').convert_alpha()
        self.waterTop = pygame.image.load('environment\\main\\liquidWaterTop_mid.png').convert_alpha()

        # Update coordinates
        self.width -= self.width % self.tileWidth
        self.height -= self.height % self.tileWidth
        self.poolStartX = int(self.x + 2 * self.tileWidth)
        self.poolEndX = int(self.x + self.width - 2 * self.tileWidth)

        # Other control variables
        self.tilesOnEitherSide = 2

    # -----------------------------------------------------------------------------------------------------------------

    def update(self, surface):
        self.updateMotion()
        self.draw(surface)

    # -----------------------------------------------------------------------------------------------------------------

    def updateMotion(self):
        # Increment position by velocity
        self.x += self.Vx
        self.y += self.Vy

    # -----------------------------------------------------------------------------------------------------------------

    def draw(self, surface):
         # Draw edge platforms
        surface.blit(self.leftImage, (self.x, self.y))
        surface.blit(self.rightImage, (self.x + self.width - self.tileWidth, self.y))

        # Draw platform tiles on either side of the pool
        self.poolStartX = int(self.x + self.tilesOnEitherSide * self.tileWidth)
        self.poolEndX = int(self.x + self.width - (1 + self.tilesOnEitherSide) * self.tileWidth)
        for x in range(int(self.x) + self.tileWidth, self.poolStartX + self.tileWidth, self.tileWidth):
            surface.blit(self.image, (x, self.y))
        for x in range(self.poolEndX, int(self.x + self.width - self.tileWidth), self.tileWidth):
            surface.blit(self.image, (x, self.y))

        # Draw pool side columns
        for y in range(int(self.y + self.tileWidth), int(self.y + self.height), self.tileWidth):
            surface.blit(self.plainImage, (self.poolStartX, y))
            surface.blit(self.plainImage, (self.poolEndX, y))

        # Draw bottom of pool
        for x in range(self.poolStartX, self.poolEndX + self.tileWidth, self.tileWidth):
            surface.blit(self.plainImage, (x, self.y + self.height))

        # Fill with water
        for y in range(int(self.y + self.tileWidth), int(self.y + self.height), self.tileWidth):
            for x in range(self.poolStartX + self.tileWidth, self.poolEndX, self.tileWidth):
                surface.blit(self.waterFilled, (x, y))
        for x in range(self.poolStartX + self.tileWidth, self.poolEndX, self.tileWidth):
            surface.blit(self.waterTop, (x, self.y))
