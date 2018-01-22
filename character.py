# coding=utf-8
import pygame
from game import *
import aicharacter

class Character(object):

    def __init__(self, x, y, Vx=0, Vy=0, whichChar=1):
        # Initialize motion variables
        self.x = x
        self.y = y
        self.Vx = Vx
        self.Vy = Vy

        # Hard-code the gravity acceleration, jumping speed, and run speed
        self.gravity = 1.5
        self.jumpSpeed = 22
        self.runSpeed = 4

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
        self.flashing = True
        self.flashTimer = 0
        self.coins = 0

        # Load images and save the height and width of the character
        self.standingImage = pygame.image.load('character\main\p' + str(whichChar) + '_front.png').convert_alpha()
        self.jumpingImageL = pygame.image.load('character\main\p' + str(whichChar) + '_jump_l.png').convert_alpha()
        self.jumpingImageR = pygame.image.load('character\main\p' + str(whichChar) + '_jump.png').convert_alpha()
        self.width = pygame.Surface.get_width(self.standingImage)
        self.height = pygame.Surface.get_height(self.standingImage)
        self.walkImagesR = [] * 11
        self.walkImagesL = [] * 11
        for i in range(1, 11):
            walkImage = pygame.image.load('character\main\p' + str(whichChar) + '_walk\PNG\p' + str(whichChar) +
                                          '_walk' + str(i) + ".png").convert_alpha()
            self.walkImagesR.append(walkImage)
            walkImageL = pygame.transform.flip(walkImage, True, False)
            self.walkImagesL.append(walkImageL)

        # Use 2D kinematics to determine maximum jump height and length
        jumpTime = self.jumpSpeed / self.gravity
        self.maxJumpHeight = math.floor(0.5 * self.jumpSpeed * jumpTime)
        self.maxJumpLength = math.floor(abs(self.runSpeed * jumpTime))

        # Save the character ID
        self.whichChar = whichChar

    # -----------------------------------------------------------------------------------------------------------------
    def update(self, platforms, ev, movableObjects, blocks, aiCharacters, mainChar, pool, surface, FPS):
        # Perform all player updates
        self.updateMotion(ev, platforms, movableObjects, aiCharacters)
        self.collide(platforms, blocks, aiCharacters, pool)
        self.determineLowestPlatform(platforms)
        self.draw(surface, FPS)
        return True

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
    def updateMotion(self, ev, platforms, movableObjects, aiCharacters):
        # Increment position by velocity
        self.x += self.Vx
        self.y += self.Vy

        # Set a terminal velocity
        if self.Vy >= platforms[0].height:
            self.Vy = platforms[0][3] - platforms[0][1] - 5

        # Apply gravity if necessary
        if self.onGround:
            self.Vy = 0
            self.mobJumping = False
        else:
            self.Vy += self.gravity

    # -----------------------------------------------------------------------------------------------------------------
    def blockCollision(self, blocks):
        # Local variables for player position
        left = self.x + 10
        right = self.x + self.width - 10
        top = self.y
        bottom = self.y + self.height

        for block in blocks:
            # Local variables for block position
            blockLeft = block.x
            blockRight = block.x + block.width
            blockTop = block.y
            blockBottom = block.y + block.height
            blockMiddleX = int(0.5 * blockLeft + 0.5 * blockRight)
            blockMiddleY = int(0.5 * blockBottom + 0.5 * blockTop)

            # Booleans for player position relative to block
            belowBlock = right >= blockLeft and left <= blockRight and blockMiddleY <= top <= blockBottom
            leftOfBlock = blockLeft <= right < blockMiddleX and bottom > blockTop and top < blockBottom
            rightOfBlock = blockRight >= left > blockMiddleX and bottom > blockTop and top < blockBottom
            aboveBlock = right >= blockLeft + 10 and left <= blockRight - 10 and blockBottom > bottom >= blockTop

            hitBlock = False
            if belowBlock and self.jumping:
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
    def coinCollision(self, blocks):
        selfRect = pygame.Rect(self.x, self.y, self.width, self.height)
        for block in blocks:
            coin = block.coinPos
            coinRect = pygame.Rect(coin[0], coin[1], block.coinWidth, block.coinHeight)
            starRect = pygame.Rect(coin[0], coin[1], block.starWidth, block.starHeight)
            if block.coinVisible and selfRect.colliderect(coinRect) and not block.yieldsStar:
                self.coins += 1
                block.killcoin()
            elif block.coinVisible and selfRect.colliderect(starRect):
                self.coins += 10
                self.health += 2
                block.killcoin()

    # -----------------------------------------------------------------------------------------------------------------
    def platformCollision(self, platforms):
        platformTolerance = 15
        PlayerLeftX = self.x
        PlayerTopY = self.y
        PlayerRightX = self.x + self.width
        PlayerBottomY = self.y + self.height
        for i in range(0, len(platforms)):
            PlatformLeftX = platforms[i][0]
            PlatformTopY = platforms[i][1]
            PlatformRightX = platforms[i][2]
            PlatformBottomY = platforms[i][3]
            if PlayerRightX >= PlatformLeftX + platformTolerance and PlayerLeftX <= PlatformRightX - \
                    platformTolerance and PlatformTopY <= PlayerBottomY <= PlatformBottomY + 15 and self.Vy >= 0:
                self.y = PlatformTopY - self.height
                self.onGround = True
                self.currentPlatform = i
            if PlayerRightX >= PlatformLeftX + platformTolerance and PlayerLeftX <= PlatformRightX - platformTolerance \
                    and PlatformBottomY >= PlayerTopY >= PlatformTopY and self.Vy < 0:
                if PlayerRightX >= PlatformLeftX + platforms[i].tileWidth and \
                                PlayerLeftX <= PlatformRightX - platforms[i].tileWidth:
                    self.y = PlatformBottomY
                    self.Vy = 0
                elif PlayerTopY <= PlatformTopY + platformTolerance + 10:
                    self.y = PlatformBottomY
                    self.Vy = 0

    # -----------------------------------------------------------------------------------------------------------------
    def collide(self, platforms, blocks, aiCharacters, pool):
        # Initially assume the player is not on the ground and not underwater
        self.onGround = False
        self.underwater = False

        # Detect block collisions
        self.blockCollision(blocks)
        self.coinCollision(blocks)

        # Detect platform collision and adjust player motion accordingly
        self.platformCollision(platforms)

        # Detect collision with (other) AI characters
        if not isinstance(self, aicharacter.AICharacter):
            for aiCharacter in aiCharacters:
                aiCharacterRect = pygame.Rect(aiCharacter.x, aiCharacter.y, aiCharacter.width, aiCharacter.height)
                selfRect = pygame.Rect(self.x, self.y, self.width, self.height)
                if selfRect.colliderect(aiCharacterRect) and aiCharacter.alive:
                    if self.Vy > 0 and aiCharacter.mobType != 'fly':
                        aiCharacter.health -= 7 - self.whichChar
                        self.jump(0.6)
                        self.mobJumping = True
                    elif self.Vy > 0:
                        aiCharacter.alive = False
                    elif not self.flashing and not self.mobJumping:
                        self.health -= 1
                        self.flashing = True

        # Detect collision with pool platform
        if pool:
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
                self.x = pool.poolStartX + pool.tileWidth + 1
                self.Vx *= -1
            if pool.poolEndX <= PlayerRightX <= pool.poolEndX + pool.tileWidth and \
                    pool.y < PlayerBottomY <= pool.y + pool.height:
                self.x = pool.poolEndX - self.width - 1
                self.Vx *= -1
            if PlayerRightX >= pool.poolStartX and PlayerLeftX <= pool.poolEndX and \
                                            pool.y + pool.height >= PlayerBottomY > pool.y:
                self.underwater = True

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
            if self.jumping and self.direction == 1:
                surface.blit(self.jumpingImageR, (self.x, self.y))
            elif self.jumping and self.direction == 0:
                surface.blit(self.jumpingImageL, (self.x, self.y))
            elif self.onGround and self.movingLaterally and self.direction == 1:
                surface.blit(self.walkImagesR[self.walkFrame], (self.x, self.y))
            elif self.onGround and self.movingLaterally and self.direction == 0:
                surface.blit(self.walkImagesL[self.walkFrame], (self.x, self.y))
            else:
                surface.blit(self.standingImage, (self.x, self.y))
