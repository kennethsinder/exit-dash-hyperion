# coding=utf-8
import math, sys, pygame, keymap as k
from random import randint
from pygame.locals import *
from character import Character
import os


class PlayableCharacter(Character):

    def __init__(self, x, y, Vx=0, Vy=0, whichChar=1):
        Character.__init__(self, x, y, Vx, Vy, whichChar)

        # HUD images
        self.whichChar = whichChar
        self.heartEmpty = pygame.image.load('hud'+os.sep+'hud_heartEmpty.png').convert_alpha()
        self.heartHalf = pygame.image.load('hud'+os.sep+'hud_heartHalf.png').convert_alpha()
        self.heartFull = pygame.image.load('hud'+os.sep+'hud_heartFull.png').convert_alpha()
        self.heartWidth = pygame.Surface.get_width(self.heartFull)
        self.heartHeight = pygame.Surface.get_height(self.heartFull)
        self.coin = pygame.image.load('hud'+os.sep+'hud_coins.png').convert_alpha()
        self.coinWidth = pygame.Surface.get_width(self.coin)
        self.coinsMultiplier = pygame.image.load('hud'+os.sep+'hud_x.png').convert_alpha()
        self.hudNumber = []
        for i in range(0, 10):
            numberImage = pygame.image.load('hud'+os.sep+'hud_' + str(i) + '.png').convert_alpha()
            self.hudNumber.append(numberImage)
        self.hudTextWidth = pygame.Surface.get_width(self.hudNumber[0])
        self.playerCoins = []
        for i in range(0, 3):
            playerCoinImage = pygame.image.load('hud'+os.sep+'hud_p' + str(self.whichChar) + '.png').convert_alpha()
            self.playerCoins.append(playerCoinImage)
        self.key = pygame.image.load('hud'+os.sep+'hud_keyBlue.png').convert_alpha()
        self.noKey = pygame.image.load('hud'+os.sep+'hud_keyBlue_disabled.png').convert_alpha()

        # HUD variables
        self.spacing = 10
        self.coins = 0
        self.playerCoinCoords = (self.spacing, self.spacing)
        self.healthStart = (pygame.Surface.get_width(self.playerCoins[0]) + 2 * self.spacing, 10)
        self.healthInterval = self.spacing + self.heartWidth

        # Other variables
        if whichChar == 1:
            self.jumpSpeed = 35
            self.runSpeed = 8.5
            self.lives = 9
        else:
            self.jumpSpeed = 36
            self.runSpeed = 9.0
            self.lives = 4
        self.worldShiftCoefficient = 1.5
        self.cpuControlled = False
        self.longestPlatform = None
        self.respawnPoint = None
        self.keys = pygame.key.get_pressed()                # Keyboard key state

    # -----------------------------------------------------------------------------------------------------------------

    def update(self, platforms, ev, movableObjects, blocks, aiCharacters, mainChar, pool, surface,
               scrW=0, scrH=0, FPS=75, autoscroll=False, checkpoints=None, torches=None):
        self.collide(platforms, blocks, aiCharacters, pool, torches)
        self.collideCheckpoint(checkpoints)
        self.draw(surface, FPS)
        if self.move(ev, platforms, movableObjects, aiCharacters, scrW, scrH, autoscroll):
            return True
        return False

    # -----------------------------------------------------------------------------------------------------------------

    def collideCheckpoint(self, checkpoints):
        if checkpoints:
            for fence in checkpoints:
                if self.getRect().colliderect(fence.getRect()) and not fence.broken:
                    self.respawnPoint = [fence.x + 20, fence.y - 70]
                    fence.broken = True

    # -----------------------------------------------------------------------------------------------------------------

    def incrementMapH(self, aiCharacters, movableObjects, amount, doMoveSelf=True):
        # Moves all of the map details left or right by the specified amount
        if doMoveSelf:
            self.x += amount
        if self.respawnPoint:
            self.respawnPoint[0] += amount
        for obj in movableObjects:
            obj.x += amount
            if hasattr(obj, 'invertedX'):
                obj.invertedX += amount
        for aiCharacter in aiCharacters:
            if aiCharacter.limit[0] != -1:
                aiCharacter.limit[0] += amount
            if aiCharacter.limit[1] != -1:
                aiCharacter.limit[1] += amount

    # -----------------------------------------------------------------------------------------------------------------

    def incrementMapV(self, movableObjects, amount, doMoveSelf=True):
        # Moves all of the map details up or down by the specified amoun
        if doMoveSelf:
            self.y += amount
        if self.respawnPoint:
            self.respawnPoint[1] += amount
        for obj in movableObjects:
            obj.y += amount
            
    # -----------------------------------------------------------------------------------------------------------------
    
    def setMapObjX(self, aiCharacters, movableObjects, platforms, newX):
        # Shifts all of the map details
        shift = newX - platforms[0][0]
        self.x += shift
        if self.respawnPoint:
            self.respawnPoint[0] += shift
        for obj in movableObjects:
            obj.x += shift
        for aiCharacter in aiCharacters:
            if aiCharacter.limit[0] != -1:
                aiCharacter.limit[0] += shift
            if aiCharacter.limit[1] != -1:
                aiCharacter.limit[1] += shift

    # -----------------------------------------------------------------------------------------------------------------

    def getNextPlatform(self, platforms):
        currX = platforms[self.currentPlatform].x
        longX = platforms[self.longestPlatform].x
        if currX == longX and self.longestPlatform + 1 < len(platforms):
            return platforms[self.longestPlatform + 1]
        elif self.currentPlatform >= len(platforms) - 1:
            return platforms[self.currentPlatform]
        else:
            return platforms[self.currentPlatform + 1]

    # -----------------------------------------------------------------------------------------------------------------

    def initSpawnpoint(self, autoscroll, platforms, nextPlatform):
        if not autoscroll and not self.respawnPoint:
            self.respawnPoint = [0.5 * platforms[0][0] + 0.5 * platforms[0][2], platforms[0][1] - self.height - 10]
        elif autoscroll:
            self.respawnPoint = [nextPlatform[0] + 0.5 * nextPlatform.width, nextPlatform[1] - self.height - 10]

    # -----------------------------------------------------------------------------------------------------------------

    def respawn(self, x, y, loseLife=True):
        self.x = int(x)
        self.y = int(y)
        self.Vx, self.Vy = 0, 0
        self.health = self.recoveryHealth
        if loseLife:
            self.flashing = True
            self.lives -= 1

    # -----------------------------------------------------------------------------------------------------------------

    def allowJumping(self):
        if self.jumping and self.onGround:
            self.jumping = False
        if (self.keys[k.ACTION] or self.keys[k.ACTION2]) and self.canJump and self.onGround:
            Character.jump(self)
            self.jumping = True
            self.canJump = False
            self.onGround = False
        if not self.keys[k.ACTION] and not self.keys[k.ACTION2] and self.onGround:
            self.canJump = True

    # -----------------------------------------------------------------------------------------------------------------

    def scanWorld(self, aiCharacters, autoscroll, movableObjects, nextPlatform, scrH, scrW):
        rightEdge = int(0.5 * scrW) + 2
        leftEdge = int(0.5 * scrW) - 2
        bottomEdge = int(0.25 * scrH) if self.ducking else int(0.7 * scrH) + 5
        topEdge = int(0.3 * scrH) - 5
        if self.y <= scrH and not autoscroll:
            self.incrementMapH(aiCharacters, movableObjects, -self.Vx, doMoveSelf=False)
            if self.x >= rightEdge:
                self.incrementMapH(aiCharacters, movableObjects, -int(self.worldShiftCoefficient * self.runSpeed))
            if self.x <= leftEdge:
                self.incrementMapH(aiCharacters, movableObjects, int(self.worldShiftCoefficient * self.runSpeed))
        if self.y <= scrH:
            if self.y <= topEdge:
                self.incrementMapV(movableObjects, int(self.worldShiftCoefficient * self.runSpeed))
            if self.y >= bottomEdge or nextPlatform[3] >= scrH:
                self.incrementMapV(movableObjects, -int(self.worldShiftCoefficient * self.runSpeed))
        elif randint(0, 10) == 0:
            self.health -= 1

    # -----------------------------------------------------------------------------------------------------------------

    def determineLongestPlatform(self, platforms):
        if not self.longestPlatform:
            self.longestPlatform = 0
            for platformIndex in xrange(1, len(platforms)):
                if platforms[platformIndex].width > platforms[self.longestPlatform].width:
                    self.longestPlatform = platformIndex
            for platformIndex in xrange(0, len(platforms)):
                if platforms[platformIndex][0] == platforms[self.longestPlatform][0] and \
                                platforms[platformIndex][1] >= platforms[self.longestPlatform][1]:
                    self.longestPlatform = platformIndex

    # -----------------------------------------------------------------------------------------------------------------

    def enableHorizMovement(self):
        pressingLeft = self.keys[k.LEFT] or self.keys[k.LEFT2]
        pressingRight = self.keys[k.RIGHT] or self.keys[k.RIGHT2]
        pressingDown = self.keys[k.DUCK] or self.keys[k.DUCK2]
        movable = not self.cpuControlled
        if pressingLeft and movable:
            self.Vx = -self.runSpeed
        if pressingRight and movable:
            self.Vx = self.runSpeed
        if not pressingLeft and not pressingRight and movable:
            self.Vx = 0
            self.movingLaterally = False
        if self.Vx > 0:
            self.direction = 1
            self.movingLaterally = True
        elif self.Vx < 0:
            self.direction = 0
            self.movingLaterally = True
        else:
            self.direction = 2
        if pressingDown and movable:
            self.ducking = True
            self.Vx = 0
        else:
            self.ducking = False

    # -----------------------------------------------------------------------------------------------------------------

    def handleWorldScrolling(self, aiCharacters, autoscroll, movableObjects, scrW):
        if autoscroll and 0 <= self.x + self.width:
            self.incrementMapH(aiCharacters, movableObjects, -0.5 * self.runSpeed)
            self.x += self.Vx
        elif autoscroll and self.health > 0:
            self.health -= 0.5
        # Scroll faster if the player is off screen
        if self.x <= 0 or self.x >= scrW:
            self.worldShiftCoefficient = 20
        else:
            self.worldShiftCoefficient = 1.5

    # -----------------------------------------------------------------------------------------------------------------

    def move(self, events, platforms, movableObjects, aiCharacters, scrW, scrH, autoscroll):
        # Call base class implementation and cancel the position increment
        Character.updateMotion(self, platforms)
        self.x -= self.Vx

        # Get keyboard state
        self.keys = pygame.key.get_pressed()

        # Enable horizontal motion
        self.enableHorizMovement()

        # Determine the longest platform and the next platform
        self.determineLongestPlatform(platforms)
        nextPlatform = self.getNextPlatform(platforms)

        # Move world horizontally and vertically to follow player
        self.scanWorld(aiCharacters, autoscroll, movableObjects, nextPlatform, scrH, scrW)

        # Autoscroll as necessary
        self.handleWorldScrolling(aiCharacters, autoscroll, movableObjects, scrW)

        # Allow jumping
        self.allowJumping()

        # If necessary, initialize the respawn point
        self.initSpawnpoint(autoscroll, platforms, nextPlatform)

        # Respawn if the health reaches zero
        if self.health <= 0:
            self.respawn(self.respawnPoint[0], self.respawnPoint[1])

        # Show game over screen if no lives are remaining
        if self.lives <= 0 and self.x != 0:
            return False

        # Check for any other I/O events
        for event in events:
            if event.type == QUIT or self.keys[k.EXIT]:
                pygame.quit(); sys.exit()
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
        health = self.health / 2.0
        for filledHearts in range(1, int(math.floor(health)) + 1):
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
