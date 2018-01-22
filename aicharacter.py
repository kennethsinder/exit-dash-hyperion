# coding=utf-8
import pygame, math
from character import Character

class AICharacter(Character):

    def __init__(self, x, y, Vx, Vy, properties=('slime', -1, -1)):
        # Properties should be a tuple of the form (STRING mobName, INT leftLimit,
        # INT rightLimit) where leftLimit and rightLimit can be -1 to remove the limit
        self.mobType = properties[0]
        self.limit = [properties[1], properties[2]]

        # Call base class implementation
        Character.__init__(self, x, y, Vx, Vy)

        # Load images
        self.slimeDL = pygame.image.load('enemies\\slime\\slimeGreen_squashed.png').convert_alpha()
        self.slimeDR = pygame.image.load('enemies\\slime\\slimeGreen_squashedR.png').convert_alpha()
        self.slimeL = pygame.image.load('enemies\\slime\\slimeGreen_walk.png').convert_alpha()
        self.slimeR = pygame.image.load('enemies\\slime\\slimeGreen_walkR.png').convert_alpha()
        self.flyDL = pygame.image.load('enemies\\fly\\fly_dead.png').convert_alpha()
        self.flyDR = pygame.image.load('enemies\\fly\\fly_dead_r.png').convert_alpha()
        self.flyL = pygame.image.load('enemies\\fly\\fly_fly.png').convert_alpha()
        self.flyR = pygame.image.load('enemies\\fly\\fly_fly_r.png').convert_alpha()
        self.fishDL = pygame.image.load('enemies\\other\\fishDead.png').convert_alpha()
        self.fishDR = pygame.image.load('enemies\\other\\fishDead_r.png').convert_alpha()
        self.fishL1 = pygame.image.load('enemies\\other\\fishSwim1.png').convert_alpha()
        self.fishL2 = pygame.image.load('enemies\\other\\fishSwim2.png').convert_alpha()
        self.fishR1 = pygame.image.load('enemies\\other\\fishSwim1R.png').convert_alpha()
        self.fishR2 = pygame.image.load('enemies\\other\\fishSwim2R.png').convert_alpha()
        self.snailL1 = pygame.image.load('enemies\\other\\snailWalk1.png').convert_alpha()
        self.snailL2 = pygame.image.load('enemies\\other\\snailWalk2.png').convert_alpha()
        self.snailR1 = pygame.image.load('enemies\\other\\snailWalk1R.png').convert_alpha()
        self.snailR2 = pygame.image.load('enemies\\other\\snailWalk2R.png').convert_alpha()
        self.snailDL = pygame.image.load('enemies\\other\\snailShell.png').convert_alpha()
        self.snailDR = pygame.image.load('enemies\\other\\snailShellR.png').convert_alpha()

        # Other control variables
        self.originalHeight = y
        self.alive = True
        self.health = 1
        self.gravity = 1
        self.runSpeed = abs(self.Vx)
        self.currentStep = 0
        self.takenAction = False

    # --------------------------------------------------------------------------------------------------------------

    def distance(self, p0, p1):
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
            self.Vy = platforms[0][3] - platforms[0][1] - 5

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
            testXLeft = self.x - 20
            testXRight = self.x + 20 + self.width
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
        if self.mobType == 'slime' or self.mobType == 'snail':
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
        elif self.mobType == 'fly' and self.alive:
            self.limit[0] = platforms[0][0]
            for i in range(0, len(platforms)):
                if self.x + self.width + 5 >= platforms[i][0] and self.x <= platforms[i][2] and \
                                        platforms[i][1] <= self.y <= platforms[i][3]:
                    self.limit[1] = platforms[i][0]
                    self.Vx *= -1
                    self.x -= self.runSpeed

    # -----------------------------------------------------------------------------------------------------------------
    def update(self, platforms, ev, movableObjects, blocks, aiCharacters, mainChar, pool, surface):
        # Collide with other objects
        Character.collide(self, platforms, blocks, aiCharacters, pool)

        # Update motion and AI actions
        self.updateAI(platforms, mainChar, blocks)

        # Draw correct character
        self.draw(surface)

    # -----------------------------------------------------------------------------------------------------------------
    def draw(self, surface):
        # Determine the correct image to use
        if self.mobType == 'slime':
            imageL1 = imageL2 = self.slimeL
            imageR1 = imageR2 = self.slimeR
            imageDL = self.slimeDL
            imageDR = self.slimeDR
        elif self.mobType == 'fly':
            imageL1 = imageL2 = self.flyL
            imageR1 = imageR2 = self.flyR
            imageDL = self.flyDL
            imageDR = self.flyDR
        elif self.mobType == 'fish':
            imageL1 = self.fishL1
            imageL2 = self.fishL2
            imageR1 = self.fishR1
            imageR2 = self.fishR2
            imageDL = self.fishDL
            imageDR = self.fishDR
        elif self.mobType == 'snail':
            imageL1 = self.snailL1
            imageL2 = self.snailL2
            imageR1 = self.snailR1
            imageR2 = self.snailR2
            imageDL = self.snailDL
            imageDR = self.snailDR

        # Get image widths and heights
        self.width = pygame.Surface.get_width(imageL1)
        self.height = pygame.Surface.get_height(imageL1)
        deadWidth = pygame.Surface.get_width(imageDL)
        deadHeight = pygame.Surface.get_height(imageDL)

        # Increment the walking/moving frame
        footstepRarity = 1
        if pygame.time.get_ticks() % footstepRarity == 0:
            self.walkFrame += 1
        if self.walkFrame > 1:
            self.walkFrame = 0

        if self.direction == 1 and self.alive and self.walkFrame == 0:
            surface.blit(imageR1, (self.x, self.y))
        elif self.direction == 0 and self.alive and self.walkFrame == 0:
            surface.blit(imageL1, (self.x, self.y))
        elif self.direction == 1 and self.alive and self.walkFrame == 1:
            surface.blit(imageR2, (self.x, self.y))
        elif self.direction == 0 and self.alive and self.walkFrame == 1:
            surface.blit(imageL2, (self.x, self.y))
        elif self.direction == 1 and not self.alive:
            surface.blit(imageDR, (self.x, self.y))
        elif self.direction == 0 and not self.alive:
            surface.blit(imageDL, (self.x, self.y))

        # Recalculate the image width and height, and stop horizontal motion if the AI char is dead
        if not self.alive:
            self.width = deadWidth
            self.height = deadHeight
            self.Vx = 0
    # -----------------------------------------------------------------------------------------------------------------