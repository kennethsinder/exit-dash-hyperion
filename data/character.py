# coding=utf-8
from random import randint
import math
import pygame
import os

class Character(object):

    def __init__(self, x, y, Vx=0, Vy=0, whichChar=1):
        # Initialize motion variables
        self.x = x
        self.y = y
        self.Vx = Vx
        self.Vy = Vy

        # Hard-code the gravity acceleration, jumping speed, and run speed
        self.gravity = 2.5
        self.jumpSpeed = 30
        self.runSpeed = 5

        # Initialize variables related to drawing and motion to zero/false
        self.walkFrame = 0
        self.mobJumping = False
        self.underwater = False
        self.movingLaterally = False
        self.jumping = False
        self.canJump = False
        self.onGround = False
        self.hasKey = False
        self.direction = 0
        self.currentPlatform = 0
        self.lowestPlatform = 0

        # Score and coins
        if whichChar == 1:
            self.health = 4
        elif whichChar == 2:
            self.health = 6
        else:
            self.health = 10
        self.recoveryHealth = self.health
        self.flashing = False
        self.flashTimer = 0
        self.coins = 0

        # Load images and save the height and width of the character
        filePrefix = 'character'+os.sep+'main'+os.sep+'p' + str(whichChar)
        self.standingImage = pygame.image.load(filePrefix + '_front.png').convert_alpha()
        self.jumpingImageL = pygame.image.load(filePrefix + '_jump_l.png').convert_alpha()
        self.jumpingImageR = pygame.image.load(filePrefix + '_jump.png').convert_alpha()
        self.duckL = pygame.image.load(filePrefix + '_duck_l.png').convert_alpha()
        self.duckR = pygame.image.load(filePrefix + '_duck.png').convert_alpha()
        self.duckHeight = pygame.Surface.get_height(self.duckL)
        self.ducking = False
        self.width = pygame.Surface.get_width(self.standingImage)
        self.height = pygame.Surface.get_height(self.standingImage)
        self.walkImagesR = [] * 11
        self.walkImagesL = [] * 11
        for i in range(1, 11):
            walkImage = pygame.image.load(filePrefix + '_walk'+os.sep+'PNG'+os.sep+'p' + str(whichChar) + '_walk' + str(i) +
                                          ".png").convert_alpha()
            self.walkImagesR.append(walkImage)
            walkImageL = pygame.transform.flip(walkImage, True, False)
            self.walkImagesL.append(walkImageL)

        # Use 2D kinematics to determine maximum jump height and length
        self.jumpTime = float(self.jumpSpeed) / self.gravity
        self.maxJumpHeight = int(0.5 * self.jumpSpeed * self.jumpTime)
        self.maxJumpLength = int(self.runSpeed * self.jumpTime)

        # Save the character ID
        self.whichChar = whichChar

        # Visibility
        self.visible = True

        # Other variables
        self.platformTolerance = 15

    # -----------------------------------------------------------------------------------------------------------------

    def platformInit(self, platforms):
        self.determineLowestPlatform(platforms)

    # -----------------------------------------------------------------------------------------------------------------

    def update(self, platforms, ev, movableObjects, blocks, aiCharacters, mainChar, pool, surface, FPS, torches=None):
        if self.visible:
            self.updateMotion(platforms)
            self.collide(platforms, blocks, aiCharacters, pool, torches)
            self.draw(surface, FPS)

    # -----------------------------------------------------------------------------------------------------------------

    def determineLowestPlatform(self, platforms):
        for platform in range(0, len(platforms)):
            if platforms[platform].y > platforms[self.lowestPlatform].y:
                self.lowestPlatform = platform

    # -----------------------------------------------------------------------------------------------------------------

    def jump(self, intensity=1.0):
        # Generic jump method that does not check if jumping is feasible
        self.Vy = math.floor(-intensity * self.jumpSpeed)

    # -----------------------------------------------------------------------------------------------------------------

    def updateMotion(self, platforms):
        # Increment position by velocity
        self.x += self.Vx
        self.y += self.Vy

        # Use 2D kinematics to update maximum jump height and length
        self.maxJumpHeight = math.floor(0.5 * self.jumpSpeed * self.jumpTime)
        self.maxJumpLength = math.floor(self.runSpeed * self.jumpTime)

        # Set a terminal velocity
        if self.Vy >= platforms[0].height:
            self.Vy = platforms[0].height - 5

        # Dispose if falling off screen
        if not self.onGround and self.Vy >= platforms[0].height - 5:
            self.dispose()

        # Apply gravity if necessary
        if self.onGround:
            self.Vy = 0
            self.mobJumping = False
        else:
            self.Vy += self.gravity

    # -----------------------------------------------------------------------------------------------------------------

    def blockCollide(self, blocks):
        # Local variables for player position
        left = self.x + 10
        right = self.x + self.width - 10
        top = self.y
        bottom = self.y + self.height

        for block in blocks:
            if 0 <= block.x <= 2000 and 0 <= block.y <= 2000:
                # Local variables for block position
                blockLeft = block.x
                blockRight = block.x + block.width
                blockTop = block.y
                blockBottom = block.y + block.height
                blockMiddleX = int(0.5 * blockLeft + 0.5 * blockRight)
                blockMiddleY = int(0.5 * blockBottom + 0.5 * blockTop)

                # Booleans for player position relative to block
                belowBlock = right >= blockLeft and left <= blockRight and blockMiddleY - 20 <= top <= blockBottom
                leftOfBlock = blockLeft <= right < blockMiddleX and bottom > blockTop and top < blockBottom
                rightOfBlock = blockRight >= left > blockMiddleX and bottom > blockTop and top < blockBottom
                aboveBlock = right >= blockLeft + 10 and left <= blockRight - 10 and blockBottom > bottom >= blockTop

                hitBlock = False
                if belowBlock and self.Vy <= 0:
                    self.y = block.y + block.height + 1
                    self.Vy = 0
                    hitBlock = True
                elif leftOfBlock:
                    self.x = blockLeft - self.width
                    self.Vx *= -1
                    return True
                elif rightOfBlock:
                    self.x = blockRight
                    self.Vx *= -1
                    return True
                elif aboveBlock and self.Vy >= 0:
                    self.y = blockTop - self.height
                    self.onGround = True
                if not block.disabled and hitBlock:
                    block.disable()
                    if block.willExplode and not self.flashing:
                        self.health -= 1
                        self.flashing = True
        return False

    # -----------------------------------------------------------------------------------------------------------------

    def coinCollide(self, blocks):
        selfRect = self.getRect()
        for block in blocks:
            if 0 <= block.x <= 2000 and 0 <= block.y <= 2000:
                coin = block.coinPos
                coinRect = pygame.Rect(coin[0], coin[1], block.coinWidth, block.coinHeight)
                starRect = pygame.Rect(coin[0], coin[1], block.starWidth, block.starHeight)
                if block.coinVisible and selfRect.colliderect(coinRect) and not block.yieldsStar:
                    # Coin effect
                    self.coins += 1
                    block.killcoin()
                elif block.coinVisible and selfRect.colliderect(starRect):
                    # Star effect
                    self.coins += 10
                    self.health += 2
                    block.killcoin()

    # -----------------------------------------------------------------------------------------------------------------

    def platformCollide(self, platforms, pool):
        # Check for collision with platforms
        for i in range(0, len(platforms)):
            if self.x + self.width >= platforms[i][0] + self.platformTolerance and self.x <= platforms[i][2] - \
                    self.platformTolerance and platforms[i][1] <= self.y + self.height <= platforms[i][3] + 35 and \
                            self.Vy >= 0:
                self.y = platforms[i][1] - self.height
                self.onGround = True
                self.currentPlatform = i
            if self.x + self.width >= platforms[i][0] + self.platformTolerance and self.x <= platforms[i][2] - \
                    self.platformTolerance and platforms[i][3] >= self.y >= platforms[i][1] - \
                    self.platformTolerance and self.Vy < 0:
                if self.x + self.width >= platforms[i][0] + platforms[i].tileWidth and \
                                self.x <= platforms[i][2] - platforms[i].tileWidth:
                    self.y = platforms[i][3]
                    self.Vy = 0
                elif self.y <= platforms[i][1] + self.platformTolerance + 30:
                    self.y = platforms[i][3]
                    self.Vy = 0

    # -----------------------------------------------------------------------------------------------------------------

    def aiCollide(self, aiCharacters):
        if not self in aiCharacters:
            for aiCharacter in aiCharacters:
                if 0 <= aiCharacter.x <= 2000 and 0 <= aiCharacter.y <= 2000:
                    aiCharacterRect = aiCharacter.getRect()
                    selfRect = self.getRect()
                    if selfRect.colliderect(aiCharacterRect) and aiCharacter.alive:
                        if self.Vy > 0 and aiCharacter.mobType != 'fly':
                            aiCharacter.health -= 5 - self.whichChar
                            self.jump(0.75)
                            self.mobJumping = True
                            self.onGround = False
                        elif self.Vy > 0:
                            self.jump(0.8)
                            self.onGround = False
                            aiCharacter.alive = False
                        elif not self.mobJumping and self.flashTimer == 0:
                            self.health -= 1
                            self.flashing = True

    # -----------------------------------------------------------------------------------------------------------------

    def poolCollide(self, platforms, pool):
        if pool and self.x not in range(int(platforms[self.currentPlatform][0]),
                                        int(platforms[self.currentPlatform][2])):
            PlayerLeftX = self.x
            PlayerRightX = self.x + self.width
            PlayerBottomY = self.y + self.height
            if pool.y <= PlayerBottomY <= pool.y + pool.tileWidth and ((PlayerRightX - 10 >= pool.x and PlayerLeftX + 10
                <= pool.poolStartX + pool.tileWidth) or (PlayerRightX - 10 >= pool.poolEndX and PlayerLeftX + 10
                <= pool.x + pool.width)) and self.Vy >= 0:
                self.onGround = True
                self.y = pool.y - self.height
            if PlayerLeftX + 10 >= pool.poolStartX and PlayerRightX - 10 <= pool.poolEndX + pool.tileWidth and \
                                            pool.y + pool.height <= PlayerBottomY <= pool.y + pool.height + pool.tileWidth and self.Vy >= 0:
                self.onGround = True
                self.y = pool.y + pool.height - self.height
            if pool.poolStartX + pool.tileWidth >= PlayerLeftX >= pool.poolStartX and \
                                    pool.y < PlayerBottomY <= pool.y + pool.height:
                self.x = pool.poolStartX + pool.tileWidth
                self.Vx *= -1
            if pool.poolEndX <= PlayerRightX <= pool.poolEndX + pool.tileWidth and \
                                    pool.y < PlayerBottomY <= pool.y + pool.height:
                self.x = pool.poolEndX - self.width
                self.Vx *= -1
            if PlayerRightX >= pool.poolStartX and PlayerLeftX <= pool.poolEndX and \
                                            pool.y + pool.height >= PlayerBottomY > pool.y:
                self.underwater = True

    # -----------------------------------------------------------------------------------------------------------------

    def prepCollisionDetection(self):
        self.onGround = False
        self.underwater = False

    # -----------------------------------------------------------------------------------------------------------------

    def torchCollide(self, torches):
        if torches:
            for torch in torches:
                if self.getRect().colliderect(torch.getRect()):
                    torch.burning = True

    # -----------------------------------------------------------------------------------------------------------------

    def collide(self, platforms, blocks, aiCharacters, pool, torches):
        self.prepCollisionDetection()
        self.blockCollide(blocks)
        self.coinCollide(blocks)
        self.platformCollide(platforms, pool)
        self.aiCollide(aiCharacters)
        self.poolCollide(platforms, pool)
        self.torchCollide(torches)

    # -----------------------------------------------------------------------------------------------------------------

    def draw(self, surface, FPS=60):
        
        # Increment the current frame of the player walking animation
        footstepRarity = 1
        if pygame.time.get_ticks() % footstepRarity == 0:
            self.walkFrame += 1
        if self.walkFrame >= 10:
            self.walkFrame = 0

        # Correctly display the current action of the player
        totalFlashTime = 4
        if self.flashing:
            self.flashTimer += 1
        else:
            self.flashTimer = 0
        if self.flashTimer >= (FPS * totalFlashTime):
            self.flashing = False
        if self.flashTimer == 0 or self.flashTimer % FPS < (FPS * 0.75):
            if self.ducking and self.direction == 0:
                surface.blit(self.duckL, (self.x, self.y + self.height - self.duckHeight))
            elif self.ducking:
                surface.blit(self.duckR, (self.x, self.y + self.height - self.duckHeight))
            elif self.jumping and self.direction == 1:
                surface.blit(self.jumpingImageR, (self.x, self.y))
            elif self.jumping and self.direction == 0:
                surface.blit(self.jumpingImageL, (self.x, self.y))
            elif self.onGround and self.movingLaterally and self.direction == 1:
                surface.blit(self.walkImagesR[self.walkFrame], (self.x, self.y))
            elif self.onGround and self.movingLaterally and self.direction == 0:
                surface.blit(self.walkImagesL[self.walkFrame], (self.x, self.y))
            else:
                surface.blit(self.standingImage, (self.x, self.y))

    # -----------------------------------------------------------------------------------------------------------------

    def getRect(self):
        return pygame.Rect(self.x + 10, self.y + 5, self.width - 10, self.height - 5)

    # -----------------------------------------------------------------------------------------------------------------

    def dispose(self):
        self.visible = False
