# coding=utf-8
from random import randint
import pygame, math
from character import *

class AICharacter(Character):

    def __init__(self, x, y, Vx, Vy, properties=('slime', -1, -1)):
        # Properties should be a tuple of the form (STRING mobName, INT leftLimit,
        # INT rightLimit) where leftLimit and rightLimit can be -1 to remove the limit
        self.mobType = properties[0]
        self.limit = [properties[1], properties[2]]

        # Call base class implementation
        Character.__init__(self, x, y, Vx, Vy)

        # Decide colour if slime
        self.colour = 'Blue'
        if self.mobType == 'slime' and randint(0, 1) == 0:
            self.colour = 'Green'

        # Load images
        # slime
        self.slimeDL = pygame.image.load('enemies'+os.sep+'slime'+os.sep+'slime' + self.colour +'_squashed.png').convert_alpha()
        self.slimeDR = pygame.image.load('enemies'+os.sep+'slime'+os.sep+'slime' + self.colour + '_squashedR.png').convert_alpha()
        self.slimeL = pygame.image.load('enemies'+os.sep+'slime'+os.sep+'slime' + self.colour + '_walk.png').convert_alpha()
        self.slimeR = pygame.image.load('enemies'+os.sep+'slime'+os.sep+'slime' + self.colour + '_walkR.png').convert_alpha()
        # fly
        self.flyDL = pygame.image.load('enemies'+os.sep+'fly'+os.sep+'fly_dead.png').convert_alpha()
        self.flyDR = pygame.image.load('enemies'+os.sep+'fly'+os.sep+'fly_dead_r.png').convert_alpha()
        self.flyL = pygame.image.load('enemies'+os.sep+'fly'+os.sep+'fly_fly.png').convert_alpha()
        self.flyR = pygame.image.load('enemies'+os.sep+'fly'+os.sep+'fly_fly_r.png').convert_alpha()
        # fish
        self.fishDL = pygame.image.load('enemies'+os.sep+'other'+os.sep+'fishGreen_dead.png').convert_alpha()
        self.fishDR = pygame.image.load('enemies'+os.sep+'other'+os.sep+'fishGreen_dead_r.png').convert_alpha()
        self.fishL = pygame.image.load('enemies'+os.sep+'other'+os.sep+'fishGreen_swim.png').convert_alpha()
        self.fishR = pygame.image.load('enemies'+os.sep+'other'+os.sep+'fishGreen_swim_r.png').convert_alpha()
        # snail
        self.snailL1 = pygame.image.load('enemies'+os.sep+'other'+os.sep+'snailWalk1.png').convert_alpha()
        self.snailL2 = pygame.image.load('enemies'+os.sep+'other'+os.sep+'snailWalk2.png').convert_alpha()
        self.snailR1 = pygame.image.load('enemies'+os.sep+'other'+os.sep+'snailWalk1R.png').convert_alpha()
        self.snailR2 = pygame.image.load('enemies'+os.sep+'other'+os.sep+'snailWalk2R.png').convert_alpha()
        self.snailDL = pygame.image.load('enemies'+os.sep+'other'+os.sep+'snailShell.png').convert_alpha()
        self.snailDR = pygame.image.load('enemies'+os.sep+'other'+os.sep+'snailShellR.png').convert_alpha()
        # general image properties
        self.imageL1, self.imageL2, self.imageR1, self.imageR2, self.imageDL, self.imageDR = [None] * 6
        self.deadWidth, self.deadHeight = [None] * 2

        # Other control variables
        self.originalHeight = y
        self.alive = True
        self.health = 1
        self.gravity = 1
        self.runSpeed = abs(self.Vx)
        self.currentStep = 0
        self.takenAction = False
        self.updateFrequency = 2

    # -----------------------------------------------------------------------------------------------------------------

    @staticmethod
    def distance(p0, p1):
        return math.sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)

    # -----------------------------------------------------------------------------------------------------------------

    def updateAI(self, platforms, mainChar, blocks):
        # Increment position by velocity
        self.x += self.Vx
        self.y += self.Vy

        # Determine direction for draw() method
        if self.Vx > 0:
            self.direction = 1
        elif self.Vx < 0:
            self.direction = 0

        # Check if character is still alive
        if self.health <= 0:
            self.alive = False

        # Set a terminal velocity
        if self.Vy >= platforms[0].height:
            self.Vy = platforms[0].height - 5
        if not self.onGround and self.Vy >= platforms[0].height - 15  and self.y > platforms[self.lowestPlatform][1]:
            self.dispose()

        # Apply gravity if necessary
        if self.onGround:
            self.Vy = 0
        elif ((self.mobType == 'fly' and not self.alive) or self.mobType != 'fly') and (self.mobType != 'fish' or
                (self.mobType == 'fish' and not self.alive)):
            self.Vy += self.gravity

        # Keep character within bounds
        if self.limit[0] != -1 and self.x <= self.limit[0]:
            self.x += self.runSpeed
            self.Vx = abs(self.Vx)
        if self.limit[1] != -1 and self.x >= self.limit[1]:
            self.x -= self.runSpeed
            self.Vx = -abs(self.Vx)

        # Switch to a dead state if close to explosion
        explosionRadius = 400
        for block in blocks:
            distanceFromBlock = self.distance((self.x + 0.5 * self.width, self.y + 0.5 * self.height),
                                         (block.x + 0.5 * block.width, block.y + 0.5 * block.height))
            if block.disabled and block.willExplode and block.explosionStep == 1 and \
                            distanceFromBlock < explosionRadius:
                self.health = 0

        # Prevent AI from falling off the lowest platform
        if self.mobType == 'slime' or self.mobType == 'snail':
            testXLeft = self.x - 25
            testXRight = self.x + 25 + self.width
            lowestPlatLeft = platforms[self.lowestPlatform][0]
            lowestPlatRight = platforms[self.lowestPlatform][2]
            onLowestPlatform = self.currentPlatform == self.lowestPlatform
            if onLowestPlatform and testXLeft <= lowestPlatLeft and self.Vx < 0:
                self.x += self.runSpeed
                self.Vx *= -1
            elif onLowestPlatform and testXRight >= lowestPlatRight and self.Vx > 0:
                self.x -= self.runSpeed
                self.Vx *= -1

        # Implement simple AI
        if self.mobType == 'slime' or self.mobType == 'snail' and randint(0, 10 - self.updateFrequency) == 0:
            platformsBelowSelf = []
            currentPlatformHeight = platforms[self.currentPlatform][1]
            limitBackup = [self.limit[0], self.limit[1]]
            self.limit[0] = platforms[self.currentPlatform][0] + 5
            self.limit[1] = platforms[self.currentPlatform][2] - 40
            safePlatformDropLeft, safePlatformDropRight = False, False
            for i in range(0, len(platforms)):
                if platforms[i][1] > currentPlatformHeight:
                    platformsBelowSelf.append(platforms[i])
            for platform in platformsBelowSelf:
                if platform[0] < platforms[self.currentPlatform][0] < platform[2]:
                    safePlatformDropLeft = True
                if platform[0] < platforms[self.currentPlatform][2] and platform[2] > platforms[self.currentPlatform][
                    2]:
                    safePlatformDropRight = True
            if safePlatformDropLeft:
                self.limit[0] = limitBackup[0]
            if safePlatformDropRight:
                self.limit[1] = limitBackup[1]
        elif self.mobType == 'fly' and self.alive and randint(0, 10 - self.updateFrequency) == 0:
            self.limit[0] = platforms[0][0]
            for i in range(0, len(platforms)):
                if self.x + self.width + 5 >= platforms[i][0] and self.x <= platforms[i][2] and \
                                        platforms[i][1] <= self.y <= platforms[i][3]:
                    self.limit[1] = platforms[i][0]
                    self.Vx *= -1
                    self.x -= self.runSpeed

    # -----------------------------------------------------------------------------------------------------------------
    def update(self, platforms, ev, movableObjects, blocks, aiCharacters, mainChar, pool, surface, FPS, torches=None):
        # Collide with other objects
        Character.collide(self, platforms, blocks, aiCharacters, pool, torches)

        # Update motion and AI actions
        self.updateAI(platforms, mainChar, blocks)

        # Draw correct character
        self.draw(surface, FPS)

    # -----------------------------------------------------------------------------------------------------------------

    def draw(self, surface, fps=60):
        # Return immediately if mob is invisibile
        if not self.visible:
            return

        # Determine the correct image to use
        if self.mobType == 'slime' and not self.imageL1:
            self.imageL1 = self.imageL2 = self.slimeL
            self.imageR1 = self.imageR2 = self.slimeR
            self.imageDL = self.slimeDL
            self.imageDR = self.slimeDR
        elif self.mobType == 'fly' and not self.imageL1:
            self.imageL1 = self.imageL2 = self.flyL
            self.imageR1 = self.imageR2 = self.flyR
            self.imageDL = self.flyDL
            self.imageDR = self.flyDR
        elif self.mobType == 'fish' and not self.imageL1:
            self.imageL1 = self.fishL
            self.imageL2 = self.fishL
            self.imageR1 = self.fishR
            self.imageR2 = self.fishR
            self.imageDL = self.fishDL
            self.imageDR = self.fishDR
        elif self.mobType == 'snail' and not self.imageL1:
            self.imageL1 = self.snailL1
            self.imageL2 = self.snailL2
            self.imageR1 = self.snailR1
            self.imageR2 = self.snailR2
            self.imageDL = self.snailDL
            self.imageDR = self.snailDR

        # Get image widths and heights
        self.width = pygame.Surface.get_width(self.imageL1)
        self.height = pygame.Surface.get_height(self.imageL1)
        self.deadWidth = pygame.Surface.get_width(self.imageDL)
        self.deadHeight = pygame.Surface.get_height(self.imageDL)

        # Increment the walking/moving frame
        footstepRarity = 1
        if pygame.time.get_ticks() % footstepRarity == 0:
            self.walkFrame += 1
        if self.walkFrame > 1:
            self.walkFrame = 0

        if self.direction == 1 and self.alive and self.walkFrame == 0:
            surface.blit(self.imageR1, (self.x, self.y))
        elif self.direction == 0 and self.alive and self.walkFrame == 0:
            surface.blit(self.imageL1, (self.x, self.y))
        elif self.direction == 1 and self.alive and self.walkFrame == 1:
            surface.blit(self.imageR2, (self.x, self.y))
        elif self.direction == 0 and self.alive and self.walkFrame == 1:
            surface.blit(self.imageL2, (self.x, self.y))
        elif self.direction == 1 and not self.alive:
            surface.blit(self.imageDR, (self.x, self.y))
        elif self.direction == 0 and not self.alive:
            surface.blit(self.imageDL, (self.x, self.y))

        # Recalculate the image width and height, and stop horizontal motion if the AI char is dead
        if not self.alive:
            self.width = self.deadWidth
            self.height = self.deadHeight
            self.Vx = 0

    # -----------------------------------------------------------------------------------------------------------------
