import pygame


class Platform(object):

    def __init__(self, x, y, Vx, Vy, width, style='grass'):
        self.x = x
        self.y = y
        self.Vx = Vx
        self.Vy = Vy

        # Load platform image
        self.image = pygame.image.load('environment\\main\\' + style + 'Mid.png').convert_alpha()
        self.width = width
        self.tileWidth = pygame.Surface.get_width(self.image)
        self.width -= self.width % self.tileWidth
        self.height = pygame.Surface.get_height(self.image)

        # Load platform edge images
        self.leftImage = pygame.image.load('environment\\main\\' + style + 'CliffLeft.png').convert_alpha()
        self.rightImage = pygame.image.load('environment\\main\\' + style + 'CliffRight.png').convert_alpha()

    # -----------------------------------------------------------------------------------------------------------------
    def __getitem__(self, i):
        # This method allows iteration of platform objects
        # From [0] to [3], it returns the left X, top Y,
        # rightX, and bottom Y, respectively
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        elif i == 2:
            return self.x + self.width
        elif i == 3:
            return self.y + self.height
        else:
            return i

    # -----------------------------------------------------------------------------------------------------------------
    def __setitem__(self, k, v):
        if k == 0:
            self.x = v
        elif k == 1:
            self.y = v
        elif k == 2:
            self.x = v - self.width
        elif k == 3:
            self.y = v - self.height

    # -----------------------------------------------------------------------------------------------------------------
    def update(self, levelBorders, surface):
        self.updateMotion(levelBorders)
        self.draw(surface)

    # -----------------------------------------------------------------------------------------------------------------
    def updateMotion(self, levelBorders):
        # Increment the position of the platform by the velocity
        self.x += self.Vx
        self.y += self.Vy

        # Wrap the motion of the platform around the level edges
        if self.x >= levelBorders[2] and self.Vx > 0:
            self.x = levelBorders[0] - self.width
        elif (self.x - self.width) <= levelBorders[0] and self.Vx < 0:
            self.x = levelBorders[2]
        elif self.y >= levelBorders[3] and self.Vy > 0:
            self.y = levelBorders[1] - self.height
        elif (self.y + self.height) <= levelBorders[1] and self.Vy < 0:
            self.y = levelBorders[3]

    # -----------------------------------------------------------------------------------------------------------------
    def draw(self, surface):
        # Draw platform edges
        surface.blit(self.leftImage, (self.x, self.y))
        surface.blit(self.rightImage, (self.x + self.width - self.tileWidth, self.y))

        # Fill in the platform between the two edges
        for i in range(self.x + self.tileWidth, self.x + self.width - self.tileWidth, self.tileWidth):
            surface.blit(self.image, (i, self.y))