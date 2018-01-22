from random import randint
import math
import pygame
from pygame.locals import *
import sys
from character import Character

class PlayableCharacter(Character):

    def __init__(self, x, y, Vx=0, Vy=0, whichChar=1):
        Character.__init__(self, x, y, Vx, Vy, whichChar)

        # HUD images
        self.whichChar = whichChar
        self.heartEmpty = pygame.image.load('hud\\hud_heartEmpty.png').convert_alpha()
        self.heartHalf = pygame.image.load('hud\\hud_heartHalf.png').convert_alpha()
        self.heartFull = pygame.image.load('hud\\hud_heartFull.png').convert_alpha()
        self.heartWidth = pygame.Surface.get_width(self.heartFull)
        self.heartHeight = pygame.Surface.get_height(self.heartFull)
        self.coin = pygame.image.load('hud\\hud_coins.png').convert_alpha()
        self.coinWidth = pygame.Surface.get_width(self.coin)
        self.coinsMultiplier = pygame.image.load('hud\\hud_x.png').convert_alpha()
        self.hudNumber = []
        for i in range(0, 10):
            numberImage = pygame.image.load('hud\\hud_' + str(i) + '.png').convert_alpha()
            self.hudNumber.append(numberImage)
        self.hudTextWidth = pygame.Surface.get_width(self.hudNumber[0])
        self.playerCoins = []
        for i in range(0, 3):
            playerCoinImage = pygame.image.load('hud\\hud_p' + str(self.whichChar) + '.png').convert_alpha()
            self.playerCoins.append(playerCoinImage)
        self.key = pygame.image.load('hud\\hud_keyBlue.png').convert_alpha()
        self.noKey = pygame.image.load('hud\\hud_keyBlue_disabled.png').convert_alpha()

        # HUD variables
        self.spacing = 10
        self.coins = 0
        self.playerCoinCoords = (self.spacing, self.spacing)
        self.healthStart = (pygame.Surface.get_width(self.playerCoins[0]) + 2 * self.spacing, 10)
        self.healthInterval = self.spacing + self.heartWidth

        # Other variables
        if whichChar == 1:
            self.jumpSpeed = 22
            self.runSpeed = 8
            self.lives = 9
        else:
            self.jumpSpeed = 23
            self.runSpeed = 9
            self.lives = 4
        self.worldShiftCoefficient = 1.5

    # -----------------------------------------------------------------------------------------------------------------

    def update(self, platforms, ev, movableObjects, blocks, aiCharacters, mainChar, pool, surface, bgrdX=0, bgrdInvX=0,
               scrW=0, scrH=0, FPS=75):
        self.collide(platforms, blocks, aiCharacters, pool)
        self.determineLowestPlatform(platforms)
        self.move(ev, platforms, movableObjects, aiCharacters, bgrdX, bgrdInvX, scrW, scrH)
        self.draw(surface, FPS)
        if self.move(ev, platforms, movableObjects, aiCharacters, bgrdX, bgrdInvX, scrW, scrH):
            return True
        return False

    # -----------------------------------------------------------------------------------------------------------------

    def move(self, events, platforms, movableObjects, aiCharacters, bgrdX, bgrdInvX, scrW, scrH):

        # Call base class implementation
        Character.updateMotion(self, events, platforms, movableObjects, aiCharacters)
        self.x -= self.Vx

        keys = pygame.key.get_pressed()         # Get keyboard state

        # Enable horizontal motion
        if keys[K_LEFT]:
            self.Vx = -self.runSpeed
            self.movingLaterally = True
            self.direction = 0
        if keys[K_RIGHT]:
            self.Vx = self.runSpeed
            self.movingLaterally = True
            self.direction = 1
        if not keys[K_LEFT] and not keys[K_RIGHT]:
            self.Vx = 0
            self.movingLaterally = False
            self.direction = 2

        # Move world horizontally and vertically to follow player
        if self.y <= scrH:
            rightEdge = int(0.5 * scrW) + 2
            leftEdge = int(0.5 * scrW) - 2
            bottomEdge = int(0.5 * scrH) + 5
            topEdge = int(0.5 * scrH) - 5
            bgrdX -= self.Vx
            bgrdInvX -= self.Vx
            for obj in movableObjects:
                obj.x -= self.Vx
            for aiCharacter in aiCharacters:
                if aiCharacter.limit[0] != -1:
                    aiCharacter.limit[0] -= self.Vx
                if aiCharacter.limit[1] != -1:
                    aiCharacter.limit[1] -= self.Vx
            for obj in movableObjects:
                obj.y -= self.Vy
            if self.x >= rightEdge:
                self.x -= int(self.worldShiftCoefficient * self.runSpeed)
                bgrdX -= int(self.worldShiftCoefficient * self.runSpeed)
                bgrdInvX -= int(self.worldShiftCoefficient * self.runSpeed)
                for obj in movableObjects:
                    obj.x -= int(self.worldShiftCoefficient * self.runSpeed)
                for aiCharacter in aiCharacters:
                    if aiCharacter.limit[0] != -1:
                        aiCharacter.limit[0] -= int(self.worldShiftCoefficient * self.runSpeed)
                    if aiCharacter.limit[1] != -1:
                        aiCharacter.limit[1] -= int(self.worldShiftCoefficient * self.runSpeed)
            if self.x <= leftEdge:
                self.x += int(self.worldShiftCoefficient * self.runSpeed)
                for obj in movableObjects:
                    obj.x += int(self.worldShiftCoefficient * self.runSpeed)
                bgrdX += int(self.worldShiftCoefficient * self.runSpeed)
                bgrdInvX += int(self.worldShiftCoefficient * self.runSpeed)
                for aiCharacter in aiCharacters:
                    if aiCharacter.limit[0] != -1:
                        aiCharacter.limit[0] += int(self.worldShiftCoefficient * self.runSpeed)
                    if aiCharacter.limit[1] != -1:
                        aiCharacter.limit[1] += int(self.worldShiftCoefficient * self.runSpeed)
            if self.y <= topEdge:
                self.y += int(self.worldShiftCoefficient * self.runSpeed)
                for obj in movableObjects:
                    obj.y += int(self.worldShiftCoefficient * self.runSpeed)
            if self.y >= bottomEdge:
                self.y -= int(self.worldShiftCoefficient * self.runSpeed)
                for obj in movableObjects:
                    obj.y -= int(self.worldShiftCoefficient * self.runSpeed)
        elif randint(0, 10) == 0:
            self.health -= 1

        # Allow jumping
        if self.jumping and self.onGround:
            self.jumping = False
        if (keys[K_SPACE] or keys[K_UP]) and self.canJump and self.onGround:
            Character.jump(self)
            self.jumping = True
            self.canJump = False
            self.onGround = False
        if not keys[K_SPACE] and not keys[K_UP] and self.onGround:
            self.canJump = True

        # Reset player if dead
        if self.health <= 0:
            self.x = int(0.5 * platforms[0][0] + 0.5 * platforms[0][2])
            self.y = platforms[0][1] - self.height - 10
            self.Vy = 0
            self.Vx = 0
            self.health = self.recoveryHealth
            self.flashing = True
            self.lives -= 1
        if self.x <= 0 or self.x >= scrW:
            self.worldShiftCoefficient = 20
        else:
            self.worldShiftCoefficient = 1.5

        # Show game over screen if no lives are remaining
        if self.lives <= 0 and self.x != 0:
            return False

        # Check for any other I/O events
        for event in events:
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        return True

    # -----------------------------------------------------------------------------------------------------------------
    def draw(self, surface, FPS=75):
        Character.draw(self, surface)

        # DRAW HUD:
        # Player symbol
        surface.blit(self.playerCoins[self.whichChar - 1], self.playerCoinCoords)
        surface.blit(self.coinsMultiplier, (self.spacing + self.heartWidth, int(2.5 * self.spacing)))
        surface.blit(self.hudNumber[self.lives], (5 * self.spacing + self.heartWidth, int(1.5 * self.spacing)))
        # Health
        health = self.health / 2
        for filledHearts in range(1, int(math.floor(health) + 1)):
            if health >= 0:
                surface.blit(self.heartFull, (self.healthInterval * filledHearts - 55, 7 * self.spacing))
        if math.floor(health) != health and health >= 0:
            surface.blit(self.heartHalf, (self.healthInterval * math.ceil(health) - 55, 7 * self.spacing))
            # Coins
        surface.blit(self.coin, (self.spacing, 8 * self.spacing + self.heartHeight))
        surface.blit(self.coinsMultiplier, (self.spacing + self.heartWidth,
                                                  8 * self.spacing + self.heartHeight + 15))
        coinsAsList = []
        for i in str(self.coins):
            coinsAsList.append(int(i))
        for i in range(0, len(coinsAsList)):
            surface.blit(self.hudNumber[coinsAsList[i]], (3 * self.spacing + self.coinWidth + self.hudTextWidth *
                                                                (i + 1), 7 * self.spacing + self.heartHeight + 15))
            # Key
        if self.hasKey:
            surface.blit(self.key, (self.spacing, 13 * self.spacing + self.heartHeight + 15))
        else:
            surface.blit(self.noKey, (self.spacing, 13 * self.spacing + self.heartHeight + 15))