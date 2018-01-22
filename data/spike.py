# coding=utf-8
from data.game import *

class FallingSpike(object):
    def __init__(self, x, y):
        # Initialize motion variables, "x" represents the x co-ordinate of the center of the spike
        self.x = x
        self.y = y
        self.Vx = 0
        self.Vy = 0

        # Initialize image
        self.image = pygame.image.load('environment\\main\\spikeTop.png')
        self.width = pygame.Surface.get_width(self.image)
        self.height = pygame.Surface.get_height(self.image)
        self.x -= int(0.5 * self.width)

        # Other control variables
        self.visible = True
        self.gravityAcceleration = 1.5
        self.dislodged = False

    # -----------------------------------------------------------------------------------------------------------------
    def update(self, platforms, chars, blocks, surface):
        self.updateMotion(chars, platforms)
        self.collide(chars, platforms)
        self.draw(platforms, blocks, surface)

    # -----------------------------------------------------------------------------------------------------------------
    def collide(self, chars, platforms):
        for char in chars:
            spikeCentre = (int(self.x + self.width / 2), self.y + int(0.5 * self.height))
            charRect = pygame.Rect(char.x, char.y, char.width, char.height)
            if charRect.collidepoint(spikeCentre) and self.visible and not char.flashing:
                char.health -= 1
                char.flashing = True
                self.visible = False

    # -----------------------------------------------------------------------------------------------------------------
    def updateMotion(self, chars, platforms):
        # Increment position by velocity
        self.x += self.Vx
        self.y += int(self.Vy)

        # Only update motion if the spike is in view
        if 0 <= self.x <= 2000 and 0 <= self.y <= 2000:

            # Check if spike should be dislodged
            for char in chars:
                if char.x + char.width >= self.x and char.x <= self.x + self.width and char.y >= self.y:
                    self.dislodged = True

            # Set a terminal velocity
            if self.Vy >= platforms[0].height:
                self.Vy = platforms[0][3] - platforms[0][1] - 5

            # Apply gravity if dislodged
            if self.dislodged:
                self.Vy += self.gravityAcceleration

    # -----------------------------------------------------------------------------------------------------------------
    def draw(self, platforms, blocks, surface):
        # Only draw if icicle is either stationary or falling and not yet hit an object
        if self.visible:
            surface.blit(self.image, (self.x, self.y))
        if self.visible and self.dislodged and 0 <= self.x <= 2000 and 0 <= self.y <= 2000:
            for platform in platforms:
                if self.y + 0.5 * self.height >= platform[1] > self.y and platform[0] <= self.x <= platform[2]:
                    self.visible = False
            for block in blocks:
                if self.y + 0.5 * self.height >= block[0][1] and self.x + \
                        self.width >= block[0][0] and self.x <= block[0][2]:
                    self.visible = False