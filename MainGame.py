# Kenneth Sinder
# Exit Dash: Hyperion (2D Platform Game)
# Last Modified: February 2, 2014

# 30% complete
# BUGS: none so far
# TODO: implement fall damage, improve AI, add ending, add bosses, add checkpoints,
# TODO: add autoscrolling levels, select final theme, add rocket for final level, add file I/O for pregenerated levels,
# TODO: implement level editor, redesign title screen, add additional powerups, optimize display updates,
# TODO: add precipitation particles, add torches, add more mobs

# Import statements for pygame and related modules
import sys
import os
import math
import pygame
from random import *
from pygame.locals import *

# Initialize pygame module
pygame.init()

# Initialize control variables for the game at the module level
DeveloperMode = True
Antialiasing = True
StableFPS = True
Decorations = True
FPSClock = pygame.time.Clock()
DesiredFPS = 75
FPS, MeasuredFPS = DesiredFPS, DesiredFPS
ScreenWidth = pygame.display.list_modes()[0][0]
ScreenHeight = pygame.display.list_modes()[0][1]
Caption = 'Exit Dash - Hyperion'
ScreenSurface = pygame.display.set_mode((ScreenWidth, ScreenHeight), pygame.FULLSCREEN | pygame.HWACCEL |
            pygame.ASYNCBLIT | pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption(Caption)
ShouldDisplayOptions = False
AllMovableObjects, Enemies = [], []
DefaultValue = -999
TimeBetweenLevels = 50
DevX = ScreenWidth - 350
DevY = 50
DevSpacing = 32
MouseX, MouseY, MouseX_Hover, MouseY_Hover = 0, 0, 0, 0
Level = 0

# Colours
white = (255, 255, 255)
grey = (185, 185, 185)
black = (0, 0, 0)
red = (155, 0, 0)
brightred = (175, 20, 20)
green = (0, 155, 0)
brightgreen = ( 20, 175, 20)
blue = (0, 0, 155)
brightblue = (20, 20, 175)
yellow = (255, 255, 0)

# Fonts
genericFont = pygame.font.Font('fonts' + os.sep + 'gamecuben.ttf', 32)
mediumFont = pygame.font.Font('fonts' + os.sep + 'jetset.ttf', 24)
smallFont = pygame.font.Font('fonts' + os.sep + 'atari.ttf', 16)

# Backgrounds
origin = (0, 0)
bgrdTitle = pygame.image.load('backgrounds' + os.sep + 'main' + os.sep + 'aquatiled_jordan_irwin.png').convert()
bgrdGloomy = pygame.image.load('backgrounds' + os.sep + 'main' + os.sep + 'red_sky.jpg').convert()
bgrdGloomyInv = pygame.image.load('backgrounds' + os.sep + 'main' + os.sep + 'red_sky_inverted.jpg').convert()
bgrdYellowSky = pygame.image.load('backgrounds' + os.sep + 'main' + os.sep + 'yellow-sky.jpg').convert()
bgrdYellowSkyInv = pygame.image.load('backgrounds' + os.sep + 'main' + os.sep + 'yellow-sky-inverted.jpg').convert()
bgrdCastle = pygame.image.load('backgrounds' + os.sep + 'main' + os.sep + 'bg_castle.png').convert()
bgrdCastleInv = pygame.image.load('backgrounds' + os.sep + 'main' + os.sep + 'bg_castle_inv.png').convert()
bgrdCastle = pygame.transform.smoothscale(bgrdCastle, (3 * pygame.Surface.get_width(bgrdCastle),
                                                       3 * pygame.Surface.get_height(bgrdCastle)))
bgrdCastleInv = pygame.transform.smoothscale(bgrdCastleInv, (pygame.Surface.get_width(bgrdCastle),
                                                             pygame.Surface.get_height(bgrdCastle)))
bgrdDesert = pygame.image.load('backgrounds' + os.sep + 'main' + os.sep + 'bg_desert.png').convert()
bgrdDesertInv = pygame.image.load('backgrounds' + os.sep + 'main' + os.sep + 'bg_desert_inv.png').convert()
initialBgrdSetup = True
bgrdX, bgrdY, bgrdInvX = 0, 0, 0

# =====================================================================================================================
class Character:
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
        self.standingImage = pygame.image.load('character'+os.sep+'main'+os.sep+'p' + str(whichChar) + '_front.png').convert_alpha()
        self.jumpingImageL = pygame.image.load('character'+os.sep+'main'+os.sep+'p' + str(whichChar) + '_jump_l.png').convert_alpha()
        self.jumpingImageR = pygame.image.load('character'+os.sep+'main'+os.sep+'p' + str(whichChar) + '_jump.png').convert_alpha()
        self.width = pygame.Surface.get_width(self.standingImage)
        self.height = pygame.Surface.get_height(self.standingImage)
        self.walkImagesR = [] * 11
        self.walkImagesL = [] * 11
        for i in range(1, 11):
            walkImage = pygame.image.load('character'+os.sep+'main'+os.sep+'p' + str(whichChar) + '_walk'+os.sep+'PNG'+os.sep+'p' + str(whichChar) +
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
    def update(self, platforms, ev, movableObjects, blocks, aiCharacters, mainChar, pool):
        # Perform all player updates
        self.updateMotion(ev, platforms, movableObjects, aiCharacters)
        self.collide(platforms, blocks, aiCharacters, pool)
        self.determineLowestPlatform(platforms)
        self.draw()

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
        if not isinstance(self, AICharacter):
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
    def draw(self):
        global ScreenSurface        # Allow writing to display surface object

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
                ScreenSurface.blit(self.jumpingImageR, (self.x, self.y))
            elif self.jumping and self.direction == 0:
                ScreenSurface.blit(self.jumpingImageL, (self.x, self.y))
            elif self.onGround and self.movingLaterally and self.direction == 1:
                ScreenSurface.blit(self.walkImagesR[self.walkFrame], (self.x, self.y))
            elif self.onGround and self.movingLaterally and self.direction == 0:
                ScreenSurface.blit(self.walkImagesL[self.walkFrame], (self.x, self.y))
            else:
                ScreenSurface.blit(self.standingImage, (self.x, self.y))

# =====================================================================================================================
class PlayableCharacter(Character):
    def __init__(self, x, y, Vx=0, Vy=0, whichChar=1):
        Character.__init__(self, x, y, Vx, Vy, whichChar)

        # HUD images
        self.whichChar = whichChar
        self.heartEmpty = pygame.image.load('hud' + os.sep + 'hud_heartEmpty.png').convert_alpha()
        self.heartHalf = pygame.image.load('hud' + os.sep + 'hud_heartHalf.png').convert_alpha()
        self.heartFull = pygame.image.load('hud' + os.sep + 'hud_heartFull.png').convert_alpha()
        self.heartWidth = pygame.Surface.get_width(self.heartFull)
        self.heartHeight = pygame.Surface.get_height(self.heartFull)
        self.coin = pygame.image.load('hud' + os.sep + 'hud_coins.png').convert_alpha()
        self.coinWidth = pygame.Surface.get_width(self.coin)
        self.coinsMultiplier = pygame.image.load('hud' + os.sep + 'hud_x.png').convert_alpha()
        self.hudNumber = []
        for i in range(0, 10):
            numberImage = pygame.image.load('hud' + os.sep + 'hud_' + str(i) + '.png').convert_alpha()
            self.hudNumber.append(numberImage)
        self.hudTextWidth = pygame.Surface.get_width(self.hudNumber[0])
        self.playerCoins = []
        for i in range(0, 3):
            playerCoinImage = pygame.image.load('hud' + os.sep + 'hud_p' + str(self.whichChar) + '.png').convert_alpha()
            self.playerCoins.append(playerCoinImage)
        self.key = pygame.image.load('hud' + os.sep + 'hud_keyBlue.png').convert_alpha()
        self.noKey = pygame.image.load('hud' + os.sep + 'hud_keyBlue_disabled.png').convert_alpha()

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
    def updateMotion(self, events, platforms, movableObjects, aiCharacters):         # Override
        global bgrdX, bgrdY, bgrdInvX

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
        if self.y <= ScreenHeight:
            rightEdge = int(0.5 * ScreenWidth) + 2
            leftEdge = int(0.5 * ScreenWidth) - 2
            bottomEdge = int(0.5 * ScreenHeight) + 5
            topEdge = int(0.5 * ScreenHeight) - 5
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
        if self.x <= 0 or self.x >= ScreenWidth:
            self.worldShiftCoefficient = 20
        else:
            self.worldShiftCoefficient = 1.5

        # Show game over screen if no lives are remaining
        if self.lives <= 0:
            showGameOverScreen(False)

        # Check for any other I/O events
        for event in events:
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    # -----------------------------------------------------------------------------------------------------------------
    def draw(self):
        Character.draw(self)

        # DRAW HUD:
        # Player symbol
        ScreenSurface.blit(self.playerCoins[self.whichChar - 1], self.playerCoinCoords)
        ScreenSurface.blit(self.coinsMultiplier, (self.spacing + self.heartWidth, int(2.5 * self.spacing)))
        ScreenSurface.blit(self.hudNumber[self.lives], (5 * self.spacing + self.heartWidth, int(1.5 * self.spacing)))
        # Health
        health = self.health / 2
        for filledHearts in range(1, int(health) + 1):
            if health >= 0:
                ScreenSurface.blit(self.heartFull, (self.healthInterval * filledHearts - 55, 7 * self.spacing))
        if math.floor(health) != health and health >= 0:
            ScreenSurface.blit(self.heartHalf, (self.healthInterval * math.ceil(health) - 55, 7 * self.spacing))
            # Coins
        ScreenSurface.blit(self.coin, (self.spacing, 8 * self.spacing + self.heartHeight))
        ScreenSurface.blit(self.coinsMultiplier, (self.spacing + self.heartWidth,
                                                  8 * self.spacing + self.heartHeight + 15))
        coinsAsList = []
        for i in str(self.coins):
            coinsAsList.append(int(i))
        for i in range(0, len(coinsAsList)):
            ScreenSurface.blit(self.hudNumber[coinsAsList[i]], (3 * self.spacing + self.coinWidth + self.hudTextWidth *
                                                                (i + 1), 7 * self.spacing + self.heartHeight + 15))
            # Key
        if self.hasKey:
            ScreenSurface.blit(self.key, (self.spacing, 13 * self.spacing + self.heartHeight + 15))
        else:
            ScreenSurface.blit(self.noKey, (self.spacing, 13 * self.spacing + self.heartHeight + 15))

# =====================================================================================================================
class AICharacter(Character):
    def __init__(self, x, y, Vx, Vy, properties=('slime', -1, -1)):
        # Properties should be a tuple of the form (STRING mobName, INT leftLimit,
        # INT rightLimit) where leftLimit and rightLimit can be -1 to remove the limit
        self.mobType = properties[0]
        self.limit = [properties[1], properties[2]]

        # Call base class implementation
        Character.__init__(self, x, y, Vx, Vy)

        # Load images
        self.slimeDL = pygame.image.load('enemies' + os.sep + 'slime' + os.sep + 'slimeGreen_squashed.png').convert_alpha()
        self.slimeDR = pygame.image.load('enemies' + os.sep + 'slime' + os.sep + 'slimeGreen_squashedR.png').convert_alpha()
        self.slimeL = pygame.image.load('enemies' + os.sep + 'slime' + os.sep + 'slimeGreen_walk.png').convert_alpha()
        self.slimeR = pygame.image.load('enemies' + os.sep + 'slime' + os.sep + 'slimeGreen_walkR.png').convert_alpha()
        self.flyDL = pygame.image.load('enemies' + os.sep + 'fly' + os.sep + 'fly_dead.png').convert_alpha()
        self.flyDR = pygame.image.load('enemies' + os.sep + 'fly' + os.sep + 'fly_dead_r.png').convert_alpha()
        self.flyL = pygame.image.load('enemies' + os.sep + 'fly' + os.sep + 'fly_fly.png').convert_alpha()
        self.flyR = pygame.image.load('enemies' + os.sep + 'fly' + os.sep + 'fly_fly_r.png').convert_alpha()
        self.fishDL = pygame.image.load('enemies' + os.sep + 'other' + os.sep + 'fishDead.png').convert_alpha()
        self.fishDR = pygame.image.load('enemies' + os.sep + 'other' + os.sep + 'fishDead_r.png').convert_alpha()
        self.fishL1 = pygame.image.load('enemies' + os.sep + 'other' + os.sep + 'fishSwim1.png').convert_alpha()
        self.fishL2 = pygame.image.load('enemies' + os.sep + 'other' + os.sep + 'fishSwim2.png').convert_alpha()
        self.fishR1 = pygame.image.load('enemies' + os.sep + 'other' + os.sep + 'fishSwim1R.png').convert_alpha()
        self.fishR2 = pygame.image.load('enemies' + os.sep + 'other' + os.sep + 'fishSwim2R.png').convert_alpha()
        self.snailL1 = pygame.image.load('enemies' + os.sep + 'other' + os.sep + 'snailWalk1.png').convert_alpha()
        self.snailL2 = pygame.image.load('enemies' + os.sep + 'other' + os.sep + 'snailWalk2.png').convert_alpha()
        self.snailR1 = pygame.image.load('enemies' + os.sep + 'other' + os.sep + 'snailWalk1R.png').convert_alpha()
        self.snailR2 = pygame.image.load('enemies' + os.sep + 'other' + os.sep + 'snailWalk2R.png').convert_alpha()
        self.snailDL = pygame.image.load('enemies' + os.sep + 'other' + os.sep + 'snailShell.png').convert_alpha()
        self.snailDR = pygame.image.load('enemies' + os.sep + 'other' + os.sep + 'snailShellR.png').convert_alpha()

        # Other control variables
        self.originalHeight = y
        self.alive = True
        self.health = 1
        self.gravity = 1
        self.runSpeed = abs(self.Vx)
        self.currentStep = 0
        self.takenAction = False

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
            distanceFromBlock = distance((self.x + 0.5 * self.width, self.y + 0.5 * self.height),
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
    def update(self, platforms, ev, movableObjects, blocks, aiCharacters, mainChar, pool):
        # Collide with other objects
        Character.collide(self, platforms, blocks, aiCharacters, pool)

        # Update motion and AI actions
        self.updateAI(platforms, mainChar, blocks)

        # Draw correct character
        self.draw()

    # -----------------------------------------------------------------------------------------------------------------
    def draw(self):
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
            ScreenSurface.blit(imageR1, (self.x, self.y))
        elif self.direction == 0 and self.alive and self.walkFrame == 0:
            ScreenSurface.blit(imageL1, (self.x, self.y))
        elif self.direction == 1 and self.alive and self.walkFrame == 1:
            ScreenSurface.blit(imageR2, (self.x, self.y))
        elif self.direction == 0 and self.alive and self.walkFrame == 1:
            ScreenSurface.blit(imageL2, (self.x, self.y))
        elif self.direction == 1 and not self.alive:
            ScreenSurface.blit(imageDR, (self.x, self.y))
        elif self.direction == 0 and not self.alive:
            ScreenSurface.blit(imageDL, (self.x, self.y))

        # Recalculate the image width and height, and stop horizontal motion if the AI char is dead
        if not self.alive:
            self.width = deadWidth
            self.height = deadHeight
            self.Vx = 0
    # -----------------------------------------------------------------------------------------------------------------

# =====================================================================================================================
class BackgroundFoliage:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        # Images
        self.whichProp = randint(0, 2)
        self.hill = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'hill_small.png').convert_alpha()
        self.bush = pygame.image.load('items' + os.sep + 'bush.png').convert_alpha()
        self.rock = pygame.image.load('items' + os.sep + 'rock.png').convert_alpha()
        self.image = self.hill
        if self.whichProp == 1:
            self.image = self.bush
        elif self.whichProp == 2:
            self.image = self.rock
        self.width = pygame.Surface.get_width(self.image)
        self.height = pygame.Surface.get_height(self.image)

# -----------------------------------------------------------------------------------------------------------------
    def draw(self):
        ScreenSurface.blit(self.image, (self.x, self.y))

# =====================================================================================================================
class Block:
    def __init__(self, x, y, form):
        # The argument for the "form" parameter should be one of the following strings:
        # 'locked'/'coin'/'regular'/'explosive'
        self.form = form

        # Initialize position
        self.x = x
        self.y = y

        # Load images
        self.lockedImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'lock_blue.png').convert_alpha()
        self.coinBlockImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'boxCoin.png').convert_alpha()
        self.coinBlockUsedImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'boxCoin_disabled.png').convert_alpha()
        self.explosiveImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'boxExplosive.png').convert_alpha()
        self.explosiveUsedImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'boxExplosive_disabled.png').convert_alpha()
        self.regularImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'boxItem.png').convert_alpha()
        self.regularUsedImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'boxItem_disabled.png').convert_alpha()
        self.explosion = []
        for i in range(0, 3):
            explosionImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'explosion' + str(i) + '.png').convert_alpha()
            explosionImage = pygame.transform.scale2x(explosionImage)
            self.explosion.append(explosionImage)
        self.width = pygame.Surface.get_width(self.regularImage)
        self.height = pygame.Surface.get_height(self.regularImage)

        # Load sounds
        self.explosionSfx = pygame.mixer.Sound('sounds' + os.sep + 'synthetic_explosion_1.ogg')

        # Coin images and variables
        self.coinImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'coinGold.png').convert_alpha()
        self.coinWidth = pygame.Surface.get_width(self.coinImage)
        self.coinHeight = pygame.Surface.get_height(self.coinImage)
        self.coinPos = [self.x - 15, self.y - self.coinHeight + 10,
                        self.x + self.coinWidth - 15, self.y + 10]
        self.coinVisible = False

        # Other images and related variables
        self.starImage = pygame.image.load('items' + os.sep + 'star.png').convert_alpha()
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
    def update(self, keys):
        self.updateState()
        self.draw(keys)

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
    def draw(self, keys):
        global ScreenSurface

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
        ScreenSurface.blit(image, (self.x, self.y))

        # Draw any coins or other objects that may be present
        if self.form == 'coin':
            for i in range(0, len(self.coinPos)):
                if self.coinVisible:
                    ScreenSurface.blit(self.coinImage, (self.coinPos[0], self.coinPos[1]))
        if self.form == 'regular':
            for key in keys:
                if self.coinVisible and self.disabled and distance((self.x, self.y), (key.x, key.y)) < 1.5 * key.height:
                    key.visible = True
                    self.coinVisible = False
        if self.willExplode and self.disabled:
            if randint(0, 2) == 0 and self.explosionStep < len(self.explosion):
                self.explosionStep += 1
            if self.explosionStep < len(self.explosion):
                ScreenSurface.blit(self.explosion[self.explosionStep], (self.x - 65, self.y - 135))
                self.explosionSfx.play()
        if self.yieldsStar and self.disabled and self.coinVisible:
            ScreenSurface.blit(self.starImage, (self.coinPos[0] + 20, self.coinPos[1] + 30))

    # -----------------------------------------------------------------------------------------------------------------

# =====================================================================================================================
class Platform:
    def __init__(self, x, y, Vx, Vy, width, style='grass'):
        self.x = x
        self.y = y
        self.Vx = Vx
        self.Vy = Vy

        # Load platform image
        self.image = pygame.image.load('environment' + os.sep + 'main' + os.sep + '' + style + 'Mid.png').convert_alpha()
        self.width = width
        self.tileWidth = pygame.Surface.get_width(self.image)
        self.width -= self.width % self.tileWidth
        self.height = pygame.Surface.get_height(self.image)

        # Load platform edge images
        self.leftImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + '' + style + 'CliffLeft.png').convert_alpha()
        self.rightImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + '' + style + 'CliffRight.png').convert_alpha()

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
    def update(self, levelBorders):
        self.updateMotion(levelBorders)
        self.draw()

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
    def draw(self):
        # Draw platform edges
        ScreenSurface.blit(self.leftImage, (self.x, self.y))
        ScreenSurface.blit(self.rightImage, (self.x + self.width - self.tileWidth, self.y))

        # Fill in the platform between the two edges
        for i in range(self.x + self.tileWidth, self.x + self.width - self.tileWidth, self.tileWidth):
            ScreenSurface.blit(self.image, (i, self.y))

# =====================================================================================================================
class Pool:
    def __init__(self, x, y, width, height, style='grass'):
        self.x, self.y = x, y
        self.Vx, self.Vy = 0, 0
        self.width, self.height = width, height

        # Platform images
        self.image = pygame.image.load('environment' + os.sep + 'main' + os.sep + '' + style + 'Mid.png').convert_alpha()
        self.plainImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + '' + style + 'Center.png')
        self.leftImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + '' + style + 'CliffLeft.png').convert_alpha()
        self.rightImage = pygame.image.load('environment' + os.sep + 'main' + os.sep + '' + style + 'CliffRight.png').convert_alpha()
        self.tileWidth = pygame.Surface.get_width(self.image)

        # Water images
        self.waterFilled = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'liquidWater.png').convert_alpha()
        self.waterTop = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'liquidWaterTop_mid.png').convert_alpha()

        # Update coordinates
        self.width -= self.width % self.tileWidth
        self.height -= self.height % self.tileWidth
        self.poolStartX = int(self.x + 2 * self.tileWidth)
        self.poolEndX = int(self.x + self.width - 2 * self.tileWidth)

        # Other control variables
        self.tilesOnEitherSide = 2

    # -----------------------------------------------------------------------------------------------------------------
    def update(self):
        self.updateMotion()
        self.draw()

    # -----------------------------------------------------------------------------------------------------------------
    def updateMotion(self):
        # Increment position by velocity
        self.x += self.Vx
        self.y += self.Vy

    # -----------------------------------------------------------------------------------------------------------------
    def draw(self):
         # Draw edge platforms
        ScreenSurface.blit(self.leftImage, (self.x, self.y))
        ScreenSurface.blit(self.rightImage, (self.x + self.width - self.tileWidth, self.y))

        # Draw platform tiles on either side of the pool
        self.poolStartX = int(self.x + self.tilesOnEitherSide * self.tileWidth)
        self.poolEndX = int(self.x + self.width - (1 + self.tilesOnEitherSide) * self.tileWidth)
        for x in range(int(self.x + self.tileWidth), self.poolStartX + self.tileWidth, self.tileWidth):
            ScreenSurface.blit(self.image, (x, self.y))
        for x in range(self.poolEndX, int(self.x) + self.width - self.tileWidth, self.tileWidth):
            ScreenSurface.blit(self.image, (x, self.y))

        # Draw pool side columns
        for y in range(int(self.y + self.tileWidth), int(self.y + self.height), self.tileWidth):
            ScreenSurface.blit(self.plainImage, (self.poolStartX, y))
            ScreenSurface.blit(self.plainImage, (self.poolEndX, y))

        # Draw bottom of pool
        for x in range(self.poolStartX, self.poolEndX + self.tileWidth, self.tileWidth):
            ScreenSurface.blit(self.plainImage, (x, self.y + self.height))

        # Fill with water
        for y in range(int(self.y + self.tileWidth), int(self.y + self.height), self.tileWidth):
            for x in range(self.poolStartX + self.tileWidth, self.poolEndX, self.tileWidth):
                ScreenSurface.blit(self.waterFilled, (x, y))
        for x in range(self.poolStartX + self.tileWidth, self.poolEndX, self.tileWidth):
            ScreenSurface.blit(self.waterTop, (x, self.y))

# =====================================================================================================================
class FallingSpike:
    def __init__(self, x, y):
        # Initialize motion variables, "x" represents the x co-ordinate of the center of the spike
        self.x = x
        self.y = y
        self.Vx = 0
        self.Vy = 0

        # Initialize image
        self.image = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'spikeTop.png')
        self.width = pygame.Surface.get_width(self.image)
        self.height = pygame.Surface.get_height(self.image)
        self.x -= int(0.5 * self.width)

        # Other control variables
        self.visible = True
        self.gravityAcceleration = 1.5
        self.dislodged = False

    # -----------------------------------------------------------------------------------------------------------------
    def update(self, platforms, chars, blocks):
        self.updateMotion(chars, platforms)
        self.collide(chars, platforms)
        self.draw(platforms, blocks)

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
    def draw(self, platforms, blocks):
        # Allow writing to display Surface
        global ScreenSurface

        # Only draw if icicle is either stationary or falling and not yet hit an object
        if self.visible:
            ScreenSurface.blit(self.image, (self.x, self.y))
        for platform in platforms:
            if self.y + 0.5 * self.height >= platform[1] > self.y and platform[0] <= self.x <= platform[2]:
                self.visible = False
        for block in blocks:
            if self.y + 0.5 * self.height >= block[0][1] and self.x + \
                    self.width >= block[0][0] and self.x <= block[0][2]:
                self.visible = False

# =====================================================================================================================
class Door:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.locked = True

        # Load images
        self.imageBottom = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'door_openMid.png').convert_alpha()
        self.imageTop = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'door_openTop.png').convert_alpha()
        self.imageBottomLocked = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'door_closedMid.png').convert_alpha()
        self.imageTopLocked = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'door_closedTop.png').convert_alpha()
        self.bottomHeight = pygame.Surface.get_height(self.imageBottom)
        self.topHeight = pygame.Surface.get_height(self.imageTop)
        self.topBlankSpace = 30
        self.height = self.bottomHeight + self.topHeight - self.topBlankSpace
        self.width = pygame.Surface.get_width(self.imageBottom)
        self.y -= self.bottomHeight + self.topHeight

    # -----------------------------------------------------------------------------------------------------------------
    def update(self, mainChar, unlockable=True):
        charRect = pygame.Rect(mainChar.x, mainChar.y, mainChar.width, mainChar.height)
        selfRect = self.getRect()
        inDoor = charRect.colliderect(selfRect)
        hasKey = mainChar.hasKey
        if inDoor and hasKey and unlockable:
            self.locked = False
        if self.locked:
            ScreenSurface.blit(self.imageTopLocked, (self.x, self.y))
            ScreenSurface.blit(self.imageBottomLocked, (self.x, self.y + self.topHeight))
        elif unlockable:
            ScreenSurface.blit(self.imageTop, (self.x, self.y))
            ScreenSurface.blit(self.imageBottom, (self.x, self.y + self.topHeight))
        if not self.locked and inDoor and unlockable:
            return True
        return False

    # -----------------------------------------------------------------------------------------------------------------
    def getRect(self):
        return pygame.Rect(self.x, self.y + self.topBlankSpace, self.width, self.height)

# =====================================================================================================================
class Key:
    def __init__(self, x, y, colour):
        self.x = x
        self.y = y
        self.visible = False

        # Load image
        self.image = pygame.image.load('environment' + os.sep + 'main' + os.sep + 'key' + colour + '.png').convert_alpha()
        self.width = pygame.Surface.get_width(self.image)
        self.height = pygame.Surface.get_height(self.image)

    # -----------------------------------------------------------------------------------------------------------------
    def update(self, mainChar):
        if self.visible:
            ScreenSurface.blit(self.image, (self.x, self.y))
        keyRect = pygame.Rect(self.x, self.y, self.width, self.height)
        charRect = pygame.Rect(mainChar.x, mainChar.y, mainChar.width, mainChar.height)
        if keyRect.colliderect(charRect):
            mainChar.hasKey = True
            self.visible = False

# =====================================================================================================================
class LevelData:
    def generateRandomLevel(self, theme, numberofplatforms, lvl):
        global p, c, b, mobs, AllMovableObjects, Enemies, spikes, initialBgrdSetup, door, keys, propDoor, textTimer, \
            foliage, poolPlatform, MeasuredFPS, FPS

        # Step 0: Clear all data from the previous level
        mobs, AllMovableObjects, Enemies, spikes = [], [], [], []
        initialBgrdSetup = True
        textTimer = 0
        c.hasKey = False
        MeasuredFPS, FPS = DesiredFPS, DesiredFPS

        # Step 1: Generate the necessary number of platforms using an iterative strategy
        firstPlatform = Platform(randint(-300, 500), randint(ScreenHeight - 200, ScreenHeight - 50),
                                 0, 0, randint(800, 1500), theme)
        overlap = True
        attempts = 2 * numberofplatforms                   # Reduce number of attempts for slower computers
        maxHeightDifference = c.maxJumpHeight - 10
        maxWidthDifference = c.maxJumpLength * 2
        while overlap and attempts >= 0:
            overlap = False
            attempts -= 1
            p = [firstPlatform]
            for i in range(1, numberofplatforms):
                randomDirection = [1, randint(0, 1)]
                platformWidth = randint(400, 2000)
                prevPlatform = p[i - 1]
                if randomDirection[0] == 0 and randomDirection[1] == 0:
                    platformRight = prevPlatform[0] - randint(int(0.5 * maxWidthDifference), maxWidthDifference)
                    platformLeft = platformRight - platformWidth
                    platformTop = prevPlatform[1] + randint(int(0.75 * maxHeightDifference), maxHeightDifference)
                elif randomDirection[0] == 0 and randomDirection[1] == 1:
                    platformRight = prevPlatform[0] - randint(int(0.5 * maxWidthDifference), maxWidthDifference)
                    platformLeft = platformRight - platformWidth
                    platformTop = prevPlatform[1] - randint(int(0.75 * maxHeightDifference), maxHeightDifference)
                elif randomDirection[0] == 1 and randomDirection[1] == 1:
                    platformLeft = prevPlatform[2] + randint(int(0.5 * maxWidthDifference), maxWidthDifference)
                    platformTop = prevPlatform[1] - randint(int(0.75 * maxHeightDifference), maxHeightDifference)
                else:
                    platformLeft = prevPlatform[2] + randint(int(1.2 * c.width), maxWidthDifference)
                    platformTop = prevPlatform[1] + randint(int(0.5 * maxHeightDifference), int(0.4 * ScreenHeight))
                p.append(Platform(platformLeft, platformTop, 0, 0, platformWidth, theme))
                for x1 in range(p[i][0] - 50, p[i][2] + 50, int(p[i].width / 20)):
                    for x2 in range(p[i - 1][0] - 50, p[i - 1][2] + 50, int(p[i - 1].width / 20)):
                        if abs(x2 - x1) < max(p[i].width / 20, p[i - 1].width / 20) and \
                                        abs(p[i][3] - p[i - 1][1]) < 100:
                            overlap = True
        for platform in p:
            AllMovableObjects.append(platform)

        # Step 2: Gather platform info
        topmostPlatform, lowestPlatform, shortestPlatform, longestPlatform, farthestPlatform = p[1], p[1], p[1], p[1], \
                                                                                               p[1]
        for platform in p:
            if platform[1] < topmostPlatform[1]:
                topmostPlatform = platform
            if platform[1] > lowestPlatform[1]:
                lowestPlatform = platform
            if platform[2] - platform[0] > longestPlatform[2] - longestPlatform[0] and platform[0] != p[0]:
                longestPlatform = platform
            if platform[2] - platform[0] < shortestPlatform[2] - shortestPlatform[0]:
                shortestPlatform = platform
            if platform[2] > farthestPlatform[2]:
                farthestPlatform = platform
        focusHeight = longestPlatform[1] - 0.3 * ScreenHeight

        # Step 3: Generate rare pool platform
        poolPlatform = None
        if randint(0, 2) == 0 or Level <= 1:
            poolX = farthestPlatform[2] + int(0.5 * c.maxJumpLength)
            poolY = farthestPlatform[1]
            poolWidth = randint(700, 900)
            poolHeight = 3 * c.maxJumpHeight
            poolPlatform = Pool(poolX, poolY, poolWidth, poolHeight, theme)
            AllMovableObjects.append(poolPlatform)

        # Step 4: Generate blocks
        quantityBlocks = numberofplatforms
        sampleBlock = Block(0, 0, 'bonus')
        blockHeight = 2 * c.height + sampleBlock.height
        b = [Block(randint(p[0][0] + 50, p[0][2] - 50), p[0][1] - blockHeight, 'coin')]
        blockplatform = [0]
        keys = []
        for i in range(1, quantityBlocks):
            y = p[i][1] - blockHeight
            if p[i].x != longestPlatform.x and randint(0, 3) != 0:
                x = 0.5 * p[i][0] + 0.5 * p[i][2] + randint(int(-0.4 * p[i].width), int(0.4 * p[i].width))
                b.append(Block(x, y, 'coin'))
                blockplatform.append(i)
            elif p[i].x != longestPlatform.x and not keys:
                x = 0.5 * p[i][0] + 0.5 * p[i][2] + randint(int(-0.4 * p[i].width), int(0.4 * p[i].width))
                b.append(Block(x, y, 'regular'))
                blockplatform.append(i)
        if poolPlatform:
            poolBlock = Block(poolPlatform.poolStartX + poolPlatform.tileWidth,
                              poolPlatform.y + poolPlatform.height - blockHeight, 'regular')
            poolBlock.yieldsStar = True
            b.append(poolBlock)
        shuffle(b)
        for block in b:
            if block.form == 'regular' and not keys and not block.yieldsStar:
                key = Key(block[0][0], block[0][1] - 80, 'blue')
                keys.append(key)
                AllMovableObjects.append(key)
            elif block.form == 'regular' and randint(0, 2) == 0:
                block.willExplode = True
            elif block.form == 'regular':
                block.yieldsStar = True
            AllMovableObjects.append(block)

        # Step 5: Generate spikes if necessary by first creating a platform to use as a ledge
        spikes = []
        if lvl == 1 or randint(0, 1) == 0:
            ledge = Platform(longestPlatform[0], focusHeight, 0, 0, longestPlatform.width, 'snow')
            p.append(ledge), AllMovableObjects.append(ledge)
            for i in range(ledge[0] + ledge.tileWidth * 2, ledge[2] - ledge.tileWidth * 2, 40):
                spikes.append(FallingSpike(i, ledge[3]))
            for spike in spikes:
                AllMovableObjects.append(spike)

        # Step 6: Add foliage to enhance the atmosphere
        foliage = []
        for platform in p:
            for x in range(platform.x, platform.x + platform.width - 100, 100):
                if randint(0, 10) == 0 and Decorations:
                    decoration = BackgroundFoliage(x, platform.y)
                    decoration.y -= decoration.height
                    AllMovableObjects.append(decoration)
                    foliage.append(decoration)

        # Step 7: Generate mobs
        quantityMobs = len(p) - 1
        mainMobType = 'slime'
        sampleMob = AICharacter(0, 0, 0, 0, (mainMobType, -1, -1))
        mobs = []
        for i in range(0, quantityMobs):
            whichPlatform = randint(1, len(p) - 1)
            while p[whichPlatform][0] == longestPlatform[0]:
                whichPlatform = randint(1, len(p) - 1)
            if randint(0, 1) == 0:
                mobs.append(AICharacter(randint(p[whichPlatform][0], p[whichPlatform][2]),
                                        p[whichPlatform][3] - sampleMob.height, int(0.7 * c.runSpeed),
                                        0, (mainMobType, -1, -1)))
            else:
                mobs.append(AICharacter(randint(p[whichPlatform][0], p[whichPlatform][2]),
                                        p[whichPlatform][3] - sampleMob.height, int(0.7 * c.runSpeed),
                                        0, ('snail', -1, -1)))
        mobs.append(AICharacter(70, p[0][1] - 750, 5, 0, ('fly', p[0][0], farthestPlatform[2])))
        if poolPlatform:
            mobs.append(AICharacter(poolPlatform.poolStartX + poolPlatform.tileWidth, poolPlatform.y +
                    poolPlatform.tileWidth, 5, 0, ('fish', -1, -1)))
        for enemy in mobs:
            Enemies.append(enemy)
            AllMovableObjects.append(enemy)

        # Step 8: Place a door
        doorX = farthestPlatform[2] - 100
        doorY = farthestPlatform[1]
        door = Door(doorX, doorY)
        AllMovableObjects.append(door)
        propDoor = Door(p[0].x + 10, p[0].y)
        AllMovableObjects.append(propDoor)

        # Step 9: Ensure there is a way out of the level
        if not keys:
            key = Key(int(0.5 * (farthestPlatform[0] + farthestPlatform[2])), farthestPlatform[1] - 80, 'blue')
            keys.append(key)
            AllMovableObjects.append(key)
        for key in keys:
            key.visible = False

        # Step 10: Move the player to the leftmost platform
        c.x = int(0.5 * p[0][0] + 0.5 * p[0][2])
        c.y = p[0][1] - c.height

    # -----------------------------------------------------------------------------------------------------------------
    def loadLevel(self, level):
        fileName = 'levels/data_' + str(level[0]) + '_' + str(level[1]) + \
                   '.txt'
        data = open(fileName)

# =====================================================================================================================
def printText(text, font, colour, coords):
    global ScreenSurface
    textSurf = font.render(text, Antialiasing, colour)
    textRect = textSurf.get_rect()
    textRect.topleft = coords
    ScreenSurface.blit(textSurf, textRect)
    return textRect

# =====================================================================================================================
def checkForQuit():
    keys = pygame.key.get_pressed()
    if keys[K_ESCAPE]:
        pygame.quit(), sys.exit()

# =====================================================================================================================
def distance(p0, p1):
    return math.sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)

# =====================================================================================================================
def drawBgrd(environment):
    global bgrdX, bgrdInvX, bgrdY, bgrdWidth, initialBgrdSetup

    # Determine correct background
    if environment == 'gloomy':
        bgrd = bgrdGloomy
        bgrdInv = bgrdGloomyInv
    elif environment == 'yellow':
        bgrd = bgrdYellowSky
        bgrdInv = bgrdYellowSkyInv
    elif environment == 'castle':
        bgrd = bgrdCastle
        bgrdInv = bgrdCastleInv
    elif environment == 'desert':
        bgrd = bgrdDesert
        bgrdInv = bgrdDesertInv
    bgrdWidth = pygame.Surface.get_width(bgrd)

    # Swap background positions as needed
    if bgrdX < -bgrdWidth:
        bgrdX = bgrdWidth
    elif bgrdX > bgrdWidth:
        bgrdX = -bgrdWidth
    if bgrdInvX < -bgrdWidth:
        bgrdInvX = bgrdWidth
    elif bgrdInvX > bgrdWidth:
        bgrdInvX = -bgrdWidth

    # Verify corrent positioning of the backgrounds
    if bgrdX > bgrdInvX:
        bgrdX = bgrdInvX + bgrdWidth
    elif bgrdInvX > bgrdX:
        bgrdInvX = bgrdX + bgrdWidth

    # If necessary, perform initial setup
    if initialBgrdSetup:
        initialBgrdSetup = False
        bgrdX, bgrdY = 0, 0
        bgrdInvX = -bgrdWidth
    ScreenSurface.blit(bgrd, (bgrdX, bgrdY))
    ScreenSurface.blit(bgrdInv, (bgrdInvX, bgrdY))

# =====================================================================================================================
def updateAll():
    global MeasuredFPS, Level

    # Draw prop door
    propDoor.update(c, False)

    # Update all objects
    if poolPlatform:
        poolPlatform.update()
    for f in foliage:
        f.draw()
    for i in range(0, len(p)):
        p[i].update((0, 0, ScreenWidth, ScreenHeight))
    for i in range(0, len(b)):
        b[i].update(keys)
    for enemy in Enemies:
        enemy.update(p, pygame.event.get(), AllMovableObjects, b, Enemies, c, poolPlatform)
    for spike in spikes:
        spike.update(p, [c] + mobs, b)
    c.update(p, pygame.event.get(), AllMovableObjects, b, Enemies, c, poolPlatform)
    for key in keys:
        key.update(c)

    # Draw temporary text
    drawTempText('Level ' + str(Level), mediumFont, white, (ScreenWidth - 150, 50), 8000)

    # Check for quit events
    checkForQuit()

    # Display developer mode info
    if DeveloperMode:
        videoInfo = pygame.display.Info()
        hardwareAccel = 'False'
        if videoInfo.hw:
            hardwareAccel = 'True'
        vram = 'Unknown'
        if videoInfo.video_mem != 0:
            vram = str(videoInfo.video_mem)
        printText('dx = ' + str(c.Vx), smallFont, white, (DevX, DevY))
        printText('dy = ' + str(c.Vy), smallFont, white, (DevX, DevY + DevSpacing))
        printText('fps = ' + str(round(MeasuredFPS, 1)) + (' (stable)' if StableFPS else ' (unstable)'), smallFont,
                  white, (DevX, DevY + 2 * DevSpacing))
        printText('vol = ' + str(100 * round(pygame.mixer.music.get_volume(), 2)) + '%', smallFont, white,
                  (DevX, DevY + 3 * DevSpacing))
        printText('onground = True' if c.onGround else 'onground = False', smallFont, white, (DevX, DevY +
                                                                                                    4 * DevSpacing))
        printText('hw accel = ' + hardwareAccel, smallFont, white, (DevX, DevY + 5 * DevSpacing))
        printText('vram (MB): ' + vram, smallFont, white, (DevX, DevY + 6 * DevSpacing))
        printText('esc to quit', smallFont, white, (DevX, DevY + 7 * DevSpacing))

    # Update screen and enforce maximum FPS
    handleFPS()

# =====================================================================================================================
def drawTitleScreen():
    global ShouldDisplayOptions, MouseX, MouseY, MouseX_Hover, MouseY_Hover, gameStart, c
    whichChar = 0

    # Check for quit events
    checkForQuit()
    for event in pygame.event.get():
        if event.type == MOUSEBUTTONDOWN:
            MouseX, MouseY = event.pos
        elif event.type == MOUSEMOTION:
            MouseX_Hover, MouseY_Hover = event.pos

    # Fill screen with background
    ScreenSurface.fill(black)
    ScreenSurface.blit(bgrdTitle, origin)

    # Print static text
    printText('Welcome to Exit Dash: Hyperion!', genericFont, white, (50, 50))
    printText('Choose a character to begin:', genericFont, white, (math.floor(ScreenWidth / 2) - 350, 150))

    # Draw three characters to choose from
    firstCharX = math.floor(ScreenWidth / 4) - 30
    secondCharX = 2 * firstCharX + 80
    thirdCharX = 3 * firstCharX + 190
    charY = math.floor(ScreenHeight / 2) - 50
    firstChar = PlayableCharacter(firstCharX, charY, 0, 0, 1)
    secondChar = PlayableCharacter(secondCharX, charY, 0, 0, 2)
    thirdChar = PlayableCharacter(thirdCharX, charY, 0, 0, 3)
    firstCharRect = pygame.Rect(firstChar.x, firstChar.y, firstChar.width, firstChar.height)
    secondCharRect = pygame.Rect(secondChar.x, secondChar.y, secondChar.width, secondChar.height)
    thirdCharRect = pygame.Rect(thirdChar.x, thirdChar.y, thirdChar.width, thirdChar.height)
    ScreenSurface.blit(firstChar.standingImage, (firstCharX, charY))
    ScreenSurface.blit(secondChar.standingImage, (secondCharX, charY))
    ScreenSurface.blit(thirdChar.standingImage, (thirdCharX, charY))
    if firstCharRect.collidepoint(MouseX_Hover, MouseY_Hover):
        pygame.draw.rect(ScreenSurface, white, firstCharRect, 3)
        printText('Flight Commander Alex', mediumFont, yellow, (firstCharX - 95, charY + firstChar.height + 15))
    else:
        printText('Flight Commander Alex', mediumFont, white, (firstCharX - 95, charY + firstChar.height + 15))
    if secondCharRect.collidepoint(MouseX_Hover, MouseY_Hover):
        pygame.draw.rect(ScreenSurface, white, secondCharRect, 3)
        printText('Astronaut Allan', mediumFont, yellow, (secondCharX - 55, charY + secondChar.height + 15))
    else:
        printText('Astronaut Allan', mediumFont, white, (secondCharX - 55, charY + secondChar.height + 15))
    if thirdCharRect.collidepoint(MouseX_Hover, MouseY_Hover):
        pygame.draw.rect(ScreenSurface, white, thirdCharRect, 3)
        printText('Medical Specialist Lisa', mediumFont, yellow, (thirdCharX - 95, charY + thirdChar.height + 15))
    else:
        printText('Medical Specialist Lisa', mediumFont, white, (thirdCharX - 95, charY + thirdChar.height + 15))
    firstCharacterChosen = firstCharRect.collidepoint(MouseX, MouseY)
    secondCharacterChosen = secondCharRect.collidepoint(MouseX, MouseY)
    thirdCharacterChosen = thirdCharRect.collidepoint(MouseX, MouseY)
    if firstCharacterChosen:
        whichChar = 1
    elif secondCharacterChosen:
        whichChar = 2
    elif thirdCharacterChosen:
        whichChar = 3

    # Draw quit button
    quitRect = printText('Quit', genericFont, white,
                         (int(ScreenWidth / 2) - 25, ScreenHeight - 200))
    if quitRect.collidepoint(MouseX, MouseY):
        pygame.quit()
        sys.exit()
    if quitRect.collidepoint(MouseX_Hover, MouseY_Hover):
        printText('Quit', genericFont, yellow, (int(ScreenWidth / 2) - 25, ScreenHeight - 200))

    # Draw settings button
    settingsRect = printText('Options', genericFont, white, (int(ScreenWidth / 2) - 60, ScreenHeight - 100))
    if settingsRect.collidepoint(MouseX, MouseY):
        ShouldDisplayOptions = True
    if settingsRect.collidepoint(MouseX_Hover, MouseY_Hover):
        printText('Options', genericFont, yellow, (int(ScreenWidth / 2) - 60, ScreenHeight - 100))
    while ShouldDisplayOptions:
        drawOptionsMenu()

    # Enter game if a character is chosen
    if firstCharacterChosen or secondCharacterChosen or thirdCharacterChosen:
        c = PlayableCharacter(0, 0, 0, 0, whichChar)
        return True

    return False

# =====================================================================================================================
def drawTempText(text, font, colour, coords, time):
    global textTimer

    # Set the timer
    timeElapsed = pygame.time.get_ticks()
    if textTimer == 0:
        textTimer = timeElapsed

    # Draw text if applicable
    if timeElapsed - textTimer < time:
        printText(text, font, colour, coords)
        return True
    else:
        return False

# =====================================================================================================================
def handleFPS():
    global MeasuredFPS, FPS
    pygame.display.update(pygame.Rect(0, 0, ScreenWidth, ScreenHeight))
    if StableFPS:
        FPSClock.tick_busy_loop(FPS)
    else:
        FPSClock.tick(FPS)
    MeasuredFPS = FPSClock.get_fps()

# =====================================================================================================================
def showGameOverScreen(won):
    ScreenSurface.blit(bgrdTitle, origin)
    outcome = 'win' if won else 'lose'
    printText('Game Over! You ' + outcome + '.', genericFont, white, (50, 50))
    printText(str(c.coins) + ' coins', mediumFont, white, (50, 100))
    printText(str(c.lives) + ' lives left', mediumFont, white, (50, 150))
    printText(str(int(pygame.time.get_ticks() / 1000)) + ' seconds', mediumFont, white, (50, 200))
    printText('TOTAL SCORE: ' + str(int(c.coins + 100 * c.lives - 0.1 * pygame.time.get_ticks() / 1000)), mediumFont,
              white, (50, 250))
    printText('Esc to Quit', mediumFont, white, (50, 300))
    keys = pygame.key.get_pressed()
    while not keys[K_ESCAPE]:
        keys = pygame.key.get_pressed()
        handleFPS()
    pygame.quit()
    sys.exit()

# =====================================================================================================================
def drawToggle(name, coords, mousepos, mousehoverpos, on=True):
    # Draw the text for the toggle and save the rects
    mainText = printText(name, mediumFont, white, coords)
    onText = printText('ON', smallFont, white, (mainText.right + 50, coords[1] + 10))
    slash = printText(' / ', smallFont, white, (onText.right + 5, coords[1] + 10))
    offText = printText('OFF', smallFont, white, (slash.right + 5, coords[1] + 10))

    # Make the ON/OFF text yellow if it is the selected option or if the mouse hovers over it
    if onText.collidepoint(mousehoverpos[0], mousehoverpos[1]) or on:
        onText = printText('ON', smallFont, yellow, (mainText.right + 50, coords[1] + 10))
    if offText.collidepoint(mousehoverpos[0], mousehoverpos[1]) or not on:
        offText = printText('OFF', smallFont, yellow, (slash.right + 5, coords[1] + 10))

    # Return a toggle output
    if onText.collidepoint(mousepos[0], mousepos[1]):
        return True
    elif offText.collidepoint(mousepos[0], mousepos[1]):
        return False
    return DefaultValue

# =====================================================================================================================
def drawOptionsMenu():
    global MeasuredFPS, DeveloperMode, ShouldDisplayOptions, MouseX, MouseY, MouseX_Hover, MouseY_Hover, Antialiasing, \
            StableFPS, Decorations
    ShouldDisplayOptions = True

    # Fill screen with background
    ScreenSurface.fill(black)
    ScreenSurface.blit(bgrdTitle, origin)

    # Get mouse status
    for event in pygame.event.get():
        if event.type == MOUSEBUTTONDOWN:
            MouseX, MouseY = event.pos
        elif event.type == MOUSEMOTION:
            MouseX_Hover, MouseY_Hover = event.pos

    # Draw title
    printText('Exit Dash: Hyperion | Options Menu', genericFont, white, (int(ScreenWidth / 2) - 420, 50))

    # Draw toggles
    devModeToggle = drawToggle('Debug Info', (math.ceil(0.25 * ScreenWidth), 150), (MouseX, MouseY),
                           (MouseX_Hover, MouseY_Hover), DeveloperMode)
    aaToggle = drawToggle('Anti-aliasing', (math.ceil(0.25 * ScreenWidth), 200), (MouseX, MouseY), (MouseX_Hover,
            MouseY_Hover), Antialiasing)
    sFPSToggle = drawToggle('Stabilize Framerate', (math.ceil(0.5 * ScreenWidth), 150), (MouseX, MouseY), (MouseX_Hover,
            MouseY_Hover), StableFPS)
    decorationToggle = drawToggle('Visual Details', (math.ceil(0.5 * ScreenWidth), 200), (MouseX, MouseY),
                                  (MouseX_Hover, MouseY_Hover), Decorations)

    # Update global variables with the values from the toggles
    if devModeToggle != DefaultValue:
        DeveloperMode = devModeToggle
    if aaToggle != DefaultValue:
        Antialiasing = aaToggle
    if sFPSToggle != DefaultValue:
        StableFPS = sFPSToggle
    if decorationToggle != DefaultValue:
        Decorations = decorationToggle

    # Draw quit button
    quitRect = printText('Return to Menu', genericFont, white, (int(ScreenWidth / 2) - 185, ScreenHeight - 150))
    if quitRect.collidepoint(MouseX_Hover, MouseY_Hover):
        quitRect = printText('Return to Menu', genericFont, yellow, (int(ScreenWidth / 2) - 185, ScreenHeight - 150))
    if quitRect.collidepoint(MouseX, MouseY):
        ShouldDisplayOptions = False

    # Update display
    handleFPS()

# =====================================================================================================================
def main():
    global FPSClock, Level, MeasuredFPS, door, c, gameStart, textTimer
    ld = LevelData()
    textTimer = 0
    gameStart = False
    pygame.mixer.music.load('music' + os.sep + 'disconnected_jukeri12.ogg')
    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.play(-1)

    while Level == 0:
        if drawTitleScreen():
            ld.generateRandomLevel('stone', 10, 1)
            pygame.mixer.music.load('music' + os.sep + 'artblock_jan125.ogg')
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
            Level = 1

        pygame.display.update()
        handleFPS()

    while Level == 1:
        ScreenSurface.fill(white)
        drawBgrd('castle')
        shouldAdvanceLevel = door.update(c)
        updateAll()
        if shouldAdvanceLevel:
            printText('Loading Level ' + str(Level + 1), mediumFont, white, (50, ScreenHeight - 50))
            Level += 1
            pygame.time.wait(TimeBetweenLevels)
            ld.generateRandomLevel('stone', 20, 2)

    while Level == 2:
        ScreenSurface.fill(white)
        drawBgrd('castle')
        shouldAdvanceLevel = door.update(c)
        updateAll()
        if shouldAdvanceLevel:
            printText('Loading Level ' + str(Level + 1), mediumFont, white, (50, ScreenHeight - 50))
            Level += 1
            pygame.time.wait(TimeBetweenLevels)
            ld.generateRandomLevel('stone', 25, 3)

# =====================================================================================================================
if __name__ == '__main__':
    main()
        

    
        
    




