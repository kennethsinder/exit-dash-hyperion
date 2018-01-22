# coding=utf-8
import math, pygame

class Background(object):

    def __init__(self, img, scrW, scrH, imgInv=None, defaultPosition=(0, 0)):
        self.image = img
        self.invertedImage = imgInv
        self.targetWidth = scrW
        self.targetHeight = scrH
        self.correctMissingInvertedImage()

        self.width = pygame.Surface.get_width(self.image)
        self.height = pygame.Surface.get_height(self.image)

        self.x, self.y = defaultPosition

        self.scaleImages(False)
        self.invertedX = self.x + self.width

    # -----------------------------------------------------------------------------------------------------------------

    def correctMissingInvertedImage(self):
        if not self.invertedImage:
            self.invertedImage = pygame.transform.flip(self.image, 1, 0).convert()

    # -----------------------------------------------------------------------------------------------------------------

    def scaleImages(self, precise=True):
        badImageSize = self.width < self.targetWidth or self.height < self.targetHeight
        if precise and badImageSize:
            # Uses bilinear filtering to expand images that are too small
            widthScaleFactor = int(math.ceil(self.targetWidth / self.width))
            heightScaleFactor = int(math.ceil(self.targetHeight / self.height))
            scaleFactor = max(widthScaleFactor, heightScaleFactor)
            self.image = pygame.transform.smoothscale(self.image, (self.width * scaleFactor, self.height * scaleFactor))
            self.invertedImage = pygame.transform.smoothscale(self.invertedImage, (self.width * scaleFactor,
                                                                                   self.height * scaleFactor))
        elif badImageSize:
            while self.height < self.targetHeight:
                self.image = pygame.transform.scale2x(self.image)
                self.invertedImage = pygame.transform.scale2x(self.invertedImage)

    # -----------------------------------------------------------------------------------------------------------------
        
    def update(self, surface):
         # Swap background positions as needed
         if self.x < -self.width:
             self.x = self.width
         elif self.x > self.width:
             self.x = -self.width
         if self.invertedX < -self.width:
             self.invertedX = self.width
         elif self.invertedX > self.width:
             self.invertedX = -self.width
        
         # Verify corrent positioning of the backgrounds
         if self.x > self.invertedX:
             self.x = self.invertedX + self.width
         elif self.invertedX > self.x:
             self.invertedX = self.x + self.width

         # Draw the background image onto the input surface
         surface.blit(self.image, (self.x, 0))
         surface.blit(self.invertedImage, (self.invertedX, 0))

    # -----------------------------------------------------------------------------------------------------------------