# coding=utf-8
from random import randint, shuffle
import pygame, sys, math
from pygame.locals import *
from aicharacter import AICharacter
from backgroundfoliage import BackgroundFoliage
from block import Block
from door import Door
from key import Key
from platform import Platform
from playablecharacter import PlayableCharacter
from pool import Pool
from spike import FallingSpike

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

c = None

class Game(object):

    def __init__(self):
        pygame.mixer.pre_init(48000, -16, 2, 4096)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(20)
        pygame.init()
    
        # Initialize control variables for the game
        self.developerMode = True
        self.antialiasing = True
        self.stableFPS = True
        self.decorations = True
        self.fpsClock = pygame.time.Clock()
        self.desiredFPS = 60
        self.fps, self.measuredFPS = self.desiredFPS, self.desiredFPS
        self.screenW = pygame.display.list_modes()[0][0]
        self.screenH = pygame.display.list_modes()[0][1]
        self.caption = 'Exit Dash - Hyperion'
        self.displaysurf = pygame.display.set_mode((self.screenW, self.screenH), pygame.FULLSCREEN | pygame.HWACCEL |
                    pygame.ASYNCBLIT | pygame.HWSURFACE | pygame.DOUBLEBUF)
        if pygame.display.mode_ok((self.screenW, self.screenH), pygame.FULLSCREEN | pygame.HWACCEL |
                pygame.ASYNCBLIT | pygame.HWSURFACE | pygame.DOUBLEBUF) == 0:
            self.displaysurf = pygame.display.set_mode((self.screenW, self.screenH), pygame.FULLSCREEN)
        pygame.display.set_caption(self.caption)
        self.displayingOptions = False
        self.allMovableObjects, self.mobs = [], []
        self.defaultValue = -999
        self.levelDelay = 50
        self.devInfoX = self.screenW - 350
        self.devInfoY = 50
        self.devSpacing = 32
        self.mousex, self.mousey, self.mousex_hover, self.mousey_hover = 0, 0, 0, 0
        self.currLevel = 0
    
        # Fonts
        self.genericFont = pygame.font.Font('fonts\\gamecuben.ttf', 32)
        self.medFont = pygame.font.Font('fonts\\jetset.ttf', 24)
        self.smlFont = pygame.font.Font('fonts\\atari.ttf', 16)
    
        # Backgrounds
        self.origin = (0, 0)
        self.bgrdTitle = pygame.image.load('backgrounds\\main\\aquatiled_jordan_irwin.png').convert()
        self.bgrdGloomy = pygame.image.load('backgrounds\\main\\red_sky.jpg').convert()
        self.bgrdGloomyInv = pygame.image.load('backgrounds\\main\\red_sky_inverted.jpg').convert()
        self.bgrdYellowSky = pygame.image.load('backgrounds\\main\\yellow-sky.jpg').convert()
        self.bgrdYellowSkyInv = pygame.image.load('backgrounds\\main\\yellow-sky-inverted.jpg').convert()
        self.bgrdCastle = pygame.image.load('backgrounds\\main\\bg_castle.png').convert()
        self.bgrdCastleInv = pygame.image.load('backgrounds\\main\\bg_castle_inv.png').convert()
        self.bgrdCastle = pygame.transform.smoothscale(self.bgrdCastle, (3 * pygame.Surface.get_width(self.bgrdCastle),
                                                               3 * pygame.Surface.get_height(self.bgrdCastle)))
        self.bgrdCastleInv = pygame.transform.smoothscale(self.bgrdCastleInv, (pygame.Surface.get_width
                                                                               (self.bgrdCastle),
                                                                     pygame.Surface.get_height(self.bgrdCastle)))
        self.bgrdDesert = pygame.image.load('backgrounds\\main\\bg_desert.png').convert()
        self.bgrdDesertInv = pygame.image.load('backgrounds\\main\\bg_desert_inv.png').convert()
        self.initialBgrdSetup = True
        self.bgrdX, self.bgrdY, self.bgrdInvX = 0, 0, 0

    # --------------------------------------------------------------------------------------------------------------

    def printText(self,text, font, colour, coords):
        textSurf = font.render(text, self.antialiasing, colour)
        textRect = textSurf.get_rect()
        textRect.topleft = coords
        self.displaysurf.blit(textSurf, textRect)
        return textRect

    # --------------------------------------------------------------------------------------------------------------

    def checkForQuit(self):
        keys = pygame.key.get_pressed()
        if keys[K_ESCAPE]:
            pygame.quit(), sys.exit()
    
    # --------------------------------------------------------------------------------------------------------------

    def distance(self, p0, p1):
        return math.sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)
    
    # --------------------------------------------------------------------------------------------------------------

    def drawTempText(self, text, font, colour, coords, time):
        global textTimer
    
        # Set the timer
        timeElapsed = pygame.time.get_ticks()
        if textTimer == 0:
            textTimer = timeElapsed
    
        # Draw text if applicable
        if timeElapsed - textTimer < time:
            self.printText(text, font, colour, coords)
            return True
        else:
            return False
    
    # --------------------------------------------------------------------------------------------------------------

    def handleFPS(self):
        pygame.display.flip()
        if self.stableFPS:
            self.fpsClock.tick_busy_loop(self.fps)
        else:
            self.fpsClock.tick(self.fps)
        self.measuredFPS = self.fpsClock.get_fps()
    
    # --------------------------------------------------------------------------------------------------------------

    def showGameOverScreen(self, won):
        self.displaysurf.blit(self.bgrdTitle, self.origin)
        outcome = 'win' if won else 'lose'
        self.printText('Game Over! You ' + outcome + '.', self.genericFont, white, (50, 50))
        self.printText(str(c.coins) + ' coins', self.medFont, white, (50, 100))
        self.printText(str(c.lives) + ' lives left', self.medFont, white, (50, 150))
        self.printText(str(int(pygame.time.get_ticks() / 1000)) + ' seconds', self.medFont, white, (50, 200))
        self.printText('TOTAL SCORE: ' + str(int(c.coins + 100 * c.lives - 0.1 * pygame.time.get_ticks() / 1000)), self.medFont,
                  white, (50, 250))
        self.printText('Esc to Quit', self.medFont, white, (50, 300))
        keys = pygame.key.get_pressed()
        while not keys[K_ESCAPE]:
            keys = pygame.key.get_pressed()
            self.handleFPS()
        pygame.quit()
        sys.exit()

    # --------------------------------------------------------------------------------------------------------------

    def drawToggle(self, name, coords, mousepos, mousehoverpos, on=True):
        # Draw the text for the toggle and save the rects
        mainText = self.printText(name, self.medFont, white, coords)
        onText = self.printText('ON', self.smlFont, white, (mainText.right + 50, coords[1] + 10))
        slash = self.printText(' / ', self.smlFont, white, (onText.right + 5, coords[1] + 10))
        offText = self.printText('OFF', self.smlFont, white, (slash.right + 5, coords[1] + 10))
    
        # Make the ON/OFF text yellow if it is the selected option or if the mouse hovers over it
        if onText.collidepoint(mousehoverpos[0], mousehoverpos[1]) or on:
            onText = self.printText('ON', self.smlFont, yellow, (mainText.right + 50, coords[1] + 10))
        if offText.collidepoint(mousehoverpos[0], mousehoverpos[1]) or not on:
            offText = self.printText('OFF', self.smlFont, yellow, (slash.right + 5, coords[1] + 10))
    
        # Return a toggle output
        if onText.collidepoint(mousepos[0], mousepos[1]):
            return True
        elif offText.collidepoint(mousepos[0], mousepos[1]):
            return False
        return self.defaultValue
    
    # --------------------------------------------------------------------------------------------------------------

    def drawOptionsMenu(self):
        global c

        self.displayingOptions = True
    
        # Fill screen with background
        self.displaysurf.fill(black)
        self.displaysurf.blit(self.bgrdTitle, self.origin)
    
        # Get mouse status
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                self.mousex, self.mousey = event.pos
            elif event.type == MOUSEMOTION:
                self.mousex_hover, self.mousey_hover = event.pos
    
        # Draw title
        self.printText('Exit Dash: Hyperion | Options Menu', self.genericFont, white, (int(self.screenW / 2) - 420, 50))
    
        # Draw toggles
        devModeToggle = self.drawToggle('Debug Info', (math.ceil(0.25 * self.screenW), 150), (self.mousex, self.mousey),
                               (self.mousex_hover, self.mousey_hover), self.developerMode)
        aaToggle = self.drawToggle('Anti-aliasing', (math.ceil(0.25 * self.screenW), 200), (self.mousex, self.mousey), (self.mousex_hover,
                self.mousey_hover), self.antialiasing)
        sFPSToggle = self.drawToggle('Stabilize Framerate', (math.ceil(0.5 * self.screenW), 150), (self.mousex, self.mousey), (self.mousex_hover,
                self.mousey_hover), self.stableFPS)
        decorationToggle = self.drawToggle('Visual Details', (math.ceil(0.5 * self.screenW), 200), (self.mousex, self.mousey),
                                      (self.mousex_hover, self.mousey_hover), self.decorations)
    
        # Update global variables with the values from the toggles
        if devModeToggle != self.defaultValue:
            self.developerMode = devModeToggle
        if aaToggle != self.defaultValue:
            self.antialiasing = aaToggle
        if sFPSToggle != self.defaultValue:
            self.stableFPS = sFPSToggle
        if decorationToggle != self.defaultValue:
            self.decorations = decorationToggle
    
        # Draw quit button
        quitRect = self.printText('Return to Menu', self.genericFont, white, (int(self.screenW / 2) - 185, self.screenH - 150))
        if quitRect.collidepoint(self.mousex_hover, self.mousey_hover):
            quitRect = self.printText('Return to Menu', self.genericFont, yellow, (int(self.screenW / 2) - 185, self.screenH - 150))
        if quitRect.collidepoint(self.mousex, self.mousey):
            self.displayingOptions = False
    
        # Update display
        self.handleFPS()

    def generateRandomLevel(self, theme, numberofplatforms, lvl):
        global p, c, b, mobs, AllMovableObjects, Enemies, spikes, door, keys, propDoor, textTimer, \
            foliage, poolPlatform, MeasuredFPS, FPS

        # Step 0: Clear all data from the previous level
        mobs, AllMovableObjects, Enemies, spikes = [], [], [], []
        if not type(c) is PlayableCharacter:
            c = PlayableCharacter(self.defaultValue, self.defaultValue)
        self.initialBgrdSetup = True
        textTimer = 0
        c.hasKey = False
        MeasuredFPS, FPS = self.desiredFPS, self.desiredFPS

        # Step 1: Generate the necessary number of platforms using an iterative strategy
        firstPlatform = Platform(randint(-300, 500), randint(self.screenH - 200, self.screenH - 50),
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
                    platformTop = prevPlatform[1] + randint(int(0.5 * maxHeightDifference), int(0.4 * self.screenH))
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
        focusHeight = longestPlatform[1] - 0.3 * self.screenH

        # Step 3: Generate rare pool platform
        poolPlatform = None
        if randint(0, 2) == 0 or self.currLevel <= 1:
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
                if randint(0, 10) == 0 and self.decorations:
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

    def drawBgrd(self, environment):

        # Determine correct background
        if environment == 'gloomy':
            self.bgrd = self.bgrdGloomy
            self.bgrdInv = self.bgrdGloomyInv
        elif environment == 'yellow':
            self.bgrd = self.bgrdYellowSky
            self.bgrdInv = self.bgrdYellowSkyInv
        elif environment == 'castle':
            self.bgrd = self.bgrdCastle
            self.bgrdInv = self.bgrdCastleInv
        elif environment == 'desert':
            self.bgrd = self.bgrdDesert
            self.bgrdInv = self.bgrdDesertInv
        self.bgrdWidth = pygame.Surface.get_width(self.bgrd)
    
        # Swap background positions as needed
        if self.bgrdX < -self.bgrdWidth:
            self.bgrdX = self.bgrdWidth
        elif self.bgrdX > self.bgrdWidth:
            self.bgrdX = -self.bgrdWidth
        if self.bgrdInvX < -self.bgrdWidth:
            self.bgrdInvX = self.bgrdWidth
        elif self.bgrdInvX > self.bgrdWidth:
            self.bgrdInvX = -self.bgrdWidth
    
        # Verify corrent positioning of the backgrounds
        if self.bgrdX > self.bgrdInvX:
            self.bgrdX = self.bgrdInvX + self.bgrdWidth
        elif self.bgrdInvX > self.bgrdX:
            self.bgrdInvX = self.bgrdX + self.bgrdWidth
    
        # If necessary, perform initial setup
        if self.initialBgrdSetup:
            self.initialBgrdSetup = False
            self.bgrdX, self.bgrdY = 0, 0
            self.bgrdInvX = -self.bgrdWidth
        self.displaysurf.blit(self.bgrd, (self.bgrdX, self.bgrdY))
        self.displaysurf.blit(self.bgrdInv, (self.bgrdInvX, self.bgrdY))

    # -----------------------------------------------------------------------------------------------------------------

    def updateAll(self):
        global MeasuredFPS

        # Draw prop door
        propDoor.update(c, self.displaysurf, False)

        # Update all objects
        if poolPlatform:
            poolPlatform.update(self.displaysurf)
        for f in foliage:
            f.draw(self.displaysurf)
        for i in range(0, len(p)):
            p[i].update((0, 0, self.screenW, self.screenH), self.displaysurf)
        for i in range(0, len(b)):
            b[i].update(keys, self.displaysurf)
        for enemy in Enemies:
            enemy.update(p, pygame.event.get(), AllMovableObjects, b, Enemies, c, poolPlatform, self.displaysurf)
        for spike in spikes:
            spike.update(p, [c] + mobs, b, self.displaysurf)
        if not c.update(p, pygame.event.get(), AllMovableObjects, b, Enemies, c, poolPlatform, self.displaysurf,
                        self.bgrdX, self.bgrdInvX, self.screenW, self.screenH, int(MeasuredFPS)):
            self.showGameOverScreen(False)
        for key in keys:
            key.update(c, self.displaysurf)

        # Draw temporary text
        self.drawTempText('self.currLevel ' + str(self.currLevel), self.medFont, white, (self.screenW - 150, 50), 8000)

        # Check for quit events
        self.checkForQuit()

        # Display developer mode info
        if self.developerMode:
            videoInfo = pygame.display.Info()
            hardwareAccel = 'False'
            if videoInfo.hw:
                hardwareAccel = 'True'
            vram = 'Unknown'
            if videoInfo.video_mem != 0:
                vram = str(videoInfo.video_mem)
            self.printText('dx = ' + str(c.Vx), self.smlFont, white, (self.devInfoX, self.devInfoY))
            self.printText('dy = ' + str(c.Vy), self.smlFont, white, (self.devInfoX, self.devInfoY + self.devSpacing))
            self.printText('fps = ' + str(round(MeasuredFPS, 1)) + (' (stable)' if self.stableFPS else ' (unstable)'), 
                           self.smlFont, white, (self.devInfoX, self.devInfoY + 2 * self.devSpacing))
            self.printText('vol = ' + str(100 * round(pygame.mixer.music.get_volume(), 2)) + '%', self.smlFont, white,
                      (self.devInfoX, self.devInfoY + 3 * self.devSpacing))
            self.printText('onground = True' if c.onGround else 'onground = False', self.smlFont, white, 
                           (self.devInfoX, self.devInfoY + 4 * self.devSpacing))
            self.printText('hw accel = ' + hardwareAccel, self.smlFont, white, (self.devInfoX, self.devInfoY + 
                                                                                               5 * self.devSpacing))
            self.printText('vram (MB): ' + vram, self.smlFont, white, (self.devInfoX, self.devInfoY + 6 * 
                                                                                      self.devSpacing))
            self.printText('esc to quit', self.smlFont, white, (self.devInfoX, self.devInfoY + 7 * self.devSpacing))

        # Update screen and enforce maximum FPS
        self.handleFPS()

    # -----------------------------------------------------------------------------------------------------------------

    def drawTitleScreen(self):
        global gameStart, c
        whichChar = 0

        # Check for quit events
        self.checkForQuit()
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                self.mousex, self.mousey = event.pos
            elif event.type == MOUSEMOTION:
                self.mousex_hover, self.mousey_hover = event.pos

        # Fill screen with background
        self.displaysurf.fill(black)
        self.displaysurf.blit(self.bgrdTitle, self.origin)

        # Print static text
        self.printText('Welcome to Exit Dash: Hyperion!', self.genericFont, white, (50, 50))
        self.printText('Choose a character to begin:', self.genericFont, white, (math.floor(self.screenW / 2) - 350, 150))

        # Draw three characters to choose from
        firstCharX = math.floor(self.screenW / 4) - 30
        secondCharX = 2 * firstCharX + 80
        thirdCharX = 3 * firstCharX + 190
        charY = math.floor(self.screenH / 2) - 50
        firstChar = PlayableCharacter(firstCharX, charY, 0, 0, 1)
        secondChar = PlayableCharacter(secondCharX, charY, 0, 0, 2)
        thirdChar = PlayableCharacter(thirdCharX, charY, 0, 0, 3)
        firstCharRect = pygame.Rect(firstChar.x, firstChar.y, firstChar.width, firstChar.height)
        secondCharRect = pygame.Rect(secondChar.x, secondChar.y, secondChar.width, secondChar.height)
        thirdCharRect = pygame.Rect(thirdChar.x, thirdChar.y, thirdChar.width, thirdChar.height)
        self.displaysurf.blit(firstChar.standingImage, (firstCharX, charY))
        self.displaysurf.blit(secondChar.standingImage, (secondCharX, charY))
        self.displaysurf.blit(thirdChar.standingImage, (thirdCharX, charY))
        if firstCharRect.collidepoint(self.mousex_hover, self.mousey_hover):
            pygame.draw.rect(self.displaysurf, white, firstCharRect, 3)
            self.printText('Flight Commander Alex', self.medFont, yellow, (firstCharX - 95, charY +
                                                                                            firstChar.height + 15))
        else:
            self.printText('Flight Commander Alex', self.medFont, white, (firstCharX - 95, charY +
                                                                                           firstChar.height + 15))
        if secondCharRect.collidepoint(self.mousex_hover, self.mousey_hover):
            pygame.draw.rect(self.displaysurf, white, secondCharRect, 3)
            self.printText('Astronaut Allan', self.medFont, yellow, (secondCharX - 55, charY + secondChar.height + 15))
        else:
            self.printText('Astronaut Allan', self.medFont, white, (secondCharX - 55, charY + secondChar.height + 15))
        if thirdCharRect.collidepoint(self.mousex_hover, self.mousey_hover):
            pygame.draw.rect(self.displaysurf, white, thirdCharRect, 3)
            self.printText('Medical Specialist Lisa', self.medFont, yellow, (thirdCharX - 95, charY +
                                                                                              thirdChar.height + 15))
        else:
            self.printText('Medical Specialist Lisa', self.medFont, white, (thirdCharX - 95, charY +
                                                                                             thirdChar.height + 15))
        firstCharacterChosen = firstCharRect.collidepoint(self.mousex, self.mousey)
        secondCharacterChosen = secondCharRect.collidepoint(self.mousex, self.mousey)
        thirdCharacterChosen = thirdCharRect.collidepoint(self.mousex, self.mousey)
        if firstCharacterChosen:
            whichChar = 1
        elif secondCharacterChosen:
            whichChar = 2
        elif thirdCharacterChosen:
            whichChar = 3

        # Draw quit button
        quitRect = self.printText('Quit', self.genericFont, white,
                             (int(self.screenW / 2) - 25, self.screenH - 200))
        if quitRect.collidepoint(self.mousex, self.mousey):
            pygame.quit()
            sys.exit()
        if quitRect.collidepoint(self.mousex_hover, self.mousey_hover):
            self.printText('Quit', self.genericFont, yellow, (int(self.screenW / 2) - 25, self.screenH - 200))

        # Draw settings button
        settingsRect = self.printText('Options', self.genericFont, white, (int(self.screenW / 2) - 60, self.screenH - 100))
        if settingsRect.collidepoint(self.mousex, self.mousey):
            self.displayingOptions = True
        if settingsRect.collidepoint(self.mousex_hover, self.mousey_hover):
            self.printText('Options', self.genericFont, yellow, (int(self.screenW / 2) - 60, self.screenH - 100))
        while self.displayingOptions:
            self.drawOptionsMenu()

        # Enter game if a character is chosen
        if firstCharacterChosen or secondCharacterChosen or thirdCharacterChosen:
            c = PlayableCharacter(0, 0, 0, 0, whichChar)
            self.currLevel = 1
            self.generateRandomLevel('stone', 10, 1)
            pygame.mixer.music.load('music\\artblock_jan125.ogg')
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)

        self.handleFPS()

    # -----------------------------------------------------------------------------------------------------------------

    @staticmethod
    def loadLevel(self, level):
        fileName = 'levels/data_' + str(level[0]) + '_' + str(level[1]) + \
                   '.txt'
        data = open(fileName)

    # --------------------------------------------------------------------------------------------------------------

    def executeGameLoop(self):
        global door, c, gameStart, textTimer
        textTimer = 0
        gameStart = False
        pygame.mixer.music.load('music\\disconnected_jukeri12.ogg')
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play(-1)

        while self.currLevel == 0:
            self.drawTitleScreen()

        while self.currLevel == 1:
            self.displaysurf.fill(white)
            self.drawBgrd('castle')
            shouldAdvanceLevel = door.update(c, self.displaysurf)
            self.updateAll()
            if shouldAdvanceLevel:
                self.printText('Loading self.currLevel ' + str(self.currLevel + 1), self.medFont, white, (50, self.screenH - 50))
                self.currLevel += 1
                pygame.time.wait(self.levelDelay)
                self.generateRandomLevel('stone', 20, 2)

        while self.currLevel == 2:
            self.displaysurf.fill(white)
            self.drawBgrd('castle')
            shouldAdvanceLevel = door.update(c, self.displaysurf)
            self.updateAll()
            if shouldAdvanceLevel:
                self.printText('Loading self.currLevel ' + str(self.currLevel + 1), self.medFont, white, (50, self.screenH - 50))
                self.currLevel += 1
                pygame.time.wait(self.levelDelay)
                self.generateRandomLevel('stone', 25, 3)
