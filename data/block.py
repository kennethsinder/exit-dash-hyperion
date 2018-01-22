# coding=utf-8
from random import randint
from game import *

class Block(object):

    def __init__(self, x, y, form):
        # The argument for the "form" parameter should be one of the following strings:
        # 'locked'/'coin'/'regular'/'explosive'
        self.form = form

        # Initialize position
        self.x = x
        self.y = y

        # Load images
        self.lockedImage = pygame.image.load('environment\\main\\lock_blue.png').convert_alpha()
        self.coinBlockImage = pygame.image.load('environment\\main\\boxCoin.png').convert_alpha()
        self.coinBlockUsedImage = pygame.image.load('environment\\main\\boxCoin_disabled.png').convert_alpha()
        self.explosiveImage = pygame.image.load('environment\\main\\boxExplosive.png').convert_alpha()
        self.explosiveUsedImage = pygame.image.load('environment\\main\\boxExplosive_disabled.png').convert_alpha()
        self.regularImage = pygame.image.load('environment\\main\\boxItem.png').convert_alpha()
        self.regularUsedImage = pygame.image.load('environment\\main\\boxItem_disabled.png').convert_alpha()
        self.explosion = []
        for i in range(0, 3):
            explosionImage = pygame.image.load('environment\\main\\explosion' + str(i) + '.png').convert_alpha()
            explosionImage = pygame.transform.scale2x(explosionImage)
            self.explosion.append(explosionImage)
        self.width = pygame.Surface.get_width(self.regularImage)
        self.height = pygame.Surface.get_height(self.regularImage)

        # Load sounds
        self.explosionSfx = pygame.mixer.Sound('sounds\\synthetic_explosion_1.ogg')

        # Coin images and variables
        self.coinImage = pygame.image.load('environment\\main\\coinGold.png').convert_alpha()
        self.coinWidth = pygame.Surface.get_width(self.coinImage)
        self.coinHeight = pygame.Surface.get_height(self.coinImage)
        self.coinPos = [self.x - 15, self.y - self.coinHeight + 10,
                        self.x + self.coinWidth - 15, self.y + 10]
        self.coinVisible = False

        # Other images and related variables
        self.starImage = pygame.image.load('items\\star.png').convert_alpha()
        self.starWidth = pygame.Surface.get_width(self.starImage)
        self.starHeight = pygame.Surface.get_height(self.starImage)

        # Other variables to track state of block
        self.disabled = False
        self.willExplode = False
        self.yieldsStar = False
        if self.form == 'explosive':
            self.willExplode = True
        self.explosionStep = 0

    # -----------------------------------------------------------------------------------------------------------------

    def __getitem__(self, i):
        if i == 0:
            return self.x, self.y, self.x + self.width, self.y + self.height
        else:
            return self.coinPos[i - 1]

    # -----------------------------------------------------------------------------------------------------------------

    @staticmethod
    def distance(p0, p1):
        return math.sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)

    # -----------------------------------------------------------------------------------------------------------------

    def update(self, keys, surface):
        self.updateState()
        self.draw(keys, surface)

    # -----------------------------------------------------------------------------------------------------------------

    def updateState(self):
        self.coinPos = [self.x - 15, self.y - self.coinHeight + 10,
                        self.x + self.coinWidth - 15, self.y + 10]

    # -----------------------------------------------------------------------------------------------------------------

    def disable(self):
        self.coinVisible = True
        self.disabled = True

    # -----------------------------------------------------------------------------------------------------------------

    def killcoin(self):
        self.coinVisible = False

    # -----------------------------------------------------------------------------------------------------------------

    def draw(self, keys, surface):
        
        # Draw the correct type of block
        if self.form == 'locked':
            image = self.lockedImage
        elif self.form == 'coin' and self.disabled:
            image = self.coinBlockUsedImage
        elif self.form == 'coin' and not self.disabled:
            image = self.coinBlockImage
        elif self.form == 'regular' and self.disabled:
            image = self.regularUsedImage
        elif self.form == 'regular' and not self.disabled:
            image = self.regularImage
        elif self.form == 'explosive' and self.disabled:
            image = self.explosiveUsedImage
        elif self.form == 'explosive' and not self.disabled:
            image = self.explosiveImage
        else:
            image = self.regularImage
        surface.blit(image, (self.x, self.y))

        # Draw any coins or other objects that may be present
        if self.form == 'coin':
            for i in range(0, len(self.coinPos)):
                if self.coinVisible:
                    surface.blit(self.coinImage, (self.coinPos[0], self.coinPos[1]))
        if self.form == 'regular':
            for key in keys:
                if self.coinVisible and self.disabled and self.distance((self.x, self.y), (key.x, key.y)) < \
                                1.5 * key.height:
                    key.visible = True
                    self.coinVisible = False
        if self.willExplode and self.disabled:
            if randint(0, 2) == 0 and self.explosionStep < len(self.explosion):
                self.explosionStep += 1
            if self.explosionStep < len(self.explosion):
                surface.blit(self.explosion[self.explosionStep], (self.x - 65, self.y - 135))
                self.explosionSfx.play()
        if self.yieldsStar and self.disabled and self.coinVisible:
            surface.blit(self.starImage, (self.coinPos[0] + 20, self.coinPos[1] + 30))

    # -----------------------------------------------------------------------------------------------------------------

    def getRect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)