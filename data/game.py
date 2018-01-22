# coding=utf-8
import sys, math, pygame, os.path, keymap as k, random as r
from pygame.locals import *
from data.aicharacter import AICharacter
from data.background import Background
from data.backgroundfoliage import BackgroundFoliage
from data.block import Block
from data.checkpoint import Checkpoint
from data.door import Door
from data.key import Key
from data.platform import Platform
from data.playablecharacter import PlayableCharacter
from data.pool import Pool
from data.spike import FallingSpike
from data.torch import Torch

# Colour constants
white = (255, 255, 255)
grey = (185, 185, 185)
black = (0, 0, 0)
red = (155, 0, 0)
brightred = (175, 20, 20)
green = (0, 155, 0)
brightgreen = (20, 175, 20)
blue = (0, 0, 155)
brightblue = (20, 20, 175)
yellow = (255, 255, 0)

# FPS constants
SLOWFPS = 25
VSYNCFPS = 60
SMOOTHFPS = 65
UNLIMITEDFPS = 800


class Game(object):

    def __init__(self, fps=65, fullscreen=True, numlevels=10):
        pygame.init()
    
        # Initialize control variables for the game instance
        self.developerMode = True
        self.antialiasing = True
        self.stableFPS = True
        self.decorations = True
        self.fpsClock = pygame.time.Clock()
        self.desiredFPS = fps
        self.fps, self.measuredFPS = self.desiredFPS, self.desiredFPS
        self.screenW = pygame.display.list_modes()[0][0]
        self.screenH = pygame.display.list_modes()[0][1]
        self.originalDimensions = [self.screenW, self.screenH]
        self.caption = 'Exit Dash - Hyperion'
        self.fullscreen = fullscreen
        self.flags = None
        self.displaysurf = None
        self.updateDisplayState()
        self.resDict = self.getResolutionDict()
        self.allMovableObjects, self.enemies = [], []
        self.defaultValue = -999
        self.levelDelay = 50
        self.devInfoX = self.screenW - 350
        self.devInfoY = 50
        self.devSpacing = 19
        self.mousex, self.mousey, self.mousex_hover, self.mousey_hover = 0, 0, 0, 0
        self.currLevel = 0
        self.doPlayMusic = True
        self.volume = 0.5
        self.autoscroll = False
        self.topmostPlatform, self.lowestPlatform, self.shortestPlatform, self.longestPlatform, \
            self.farthestPlatform = 0, 0, 0, 0, 0
        self.seed = None
        self.allowKillBonus = False
        self.receivingKillBonus = False
        self.firstCharX = 100
        self.secondCharX = self.screenW // 2 - 10
        self.thirdCharX = self.screenW - 220
        self.charY = math.floor(self.screenH / 2) - 50
        self.firstChar = PlayableCharacter(self.firstCharX, self.charY)
        self.secondChar = PlayableCharacter(self.secondCharX, self.charY, whichChar=2)
        self.thirdChar = PlayableCharacter(self.thirdCharX, self.charY, whichChar=3)
        self.clicking = False
        self.editorResult = False
        self.currentResolution = str(self.screenH) + 'p'
        self.recentKeyboardKeys = ''
        self.keyPressEvent = KEYDOWN
        self.maxKeyMemoryLength = 15
        self.levelDark = False
        self.levelHint = ''
        self.torches = []
        self.overwriteLevels = True
        self.numLevels = numlevels

        # Get game directory size
        self.totalSize = self.getGameDirSize()

        # Other file vars
        self.configExtension = '.cfg'
        self.levelExtension = '.dat'

        # Load settings from file
        self.loadGameSettings()

        # Game objects
        self.mainChar, self.platforms, self.pool, self.blocks, self.keys, self.door, self.fakedoor, self.icicles, \
                self.foliage, self.mobs, self.enemies, self.gameStart, self.fences = [None] * 13
        self.textTimers = [0] * 10

        # Music
        self.themeSong = 'music'+os.sep+'waking_devil.mp3'
        self.mainMusic = 'music'+os.sep+'char1_3.ogg'
        self.gameOverMusic = 'music'+os.sep+'gameover.mp3'
    
        # Fonts
        self.genericFont = pygame.font.Font('fonts'+os.sep+'2lines.ttf', 48)
        self.medFont = pygame.font.Font('fonts'+os.sep+'jetset.ttf', 24)
        self.smlFont = pygame.font.Font('fonts'+os.sep+'atari.ttf', 16)
        self.smoothFont = pygame.font.Font('fonts'+os.sep+'source.otf', 18)

        # Level theme
        self.theme = 'stone'
        self.backgroundTheme = 'castle'
    
        # Backgrounds
        self.origin = (0, 0)
        self.bgrdTitle = pygame.image.load('backgrounds'+os.sep+'main'+os.sep+'title_bgrd_compressed.png').convert()
        self.bgrdGloomy = pygame.image.load('backgrounds'+os.sep+'main'+os.sep+'red_sky.jpg').convert()
        self.bgrdYellowSky = pygame.image.load('backgrounds'+os.sep+'main'+os.sep+'yellow-sky.jpg').convert()
        self.bgrdCastle = pygame.image.load('backgrounds'+os.sep+'main'+os.sep+'bg_castle.png').convert()
        self.bgrdCastle = pygame.transform.smoothscale(self.bgrdCastle, (3 * pygame.Surface.get_width(self.bgrdCastle),
                                                               3 * pygame.Surface.get_height(self.bgrdCastle)))
        self.bgrdDesert = pygame.image.load('backgrounds'+os.sep+'main'+os.sep+'bg_desert.png').convert()
        self.bgrd = None
        self.activeBackground = None

        # Cursor
        self.prevCursorVisibleState = pygame.mouse.set_visible(False)   # Hide existing cursor
        self.cursorImage = pygame.image.load('hud'+os.sep+'pointer.png').convert_alpha()
        self.cursorImage = pygame.transform.scale2x(self.cursorImage)
        self.cursorClickedImage = pygame.image.load('hud'+os.sep+'pointerClicked.png').convert_alpha()
        self.cursorClickedImage = pygame.transform.scale2x(self.cursorClickedImage)

        # Options UI Images
        self.slider = pygame.image.load('ui'+os.sep+'grey_sliderHorizontal.png').convert_alpha()
        self.sliderPointer = pygame.image.load('ui'+os.sep+'grey_sliderDown.png').convert_alpha()

    # --------------------------------------------------------------------------------------------------------------

    def reinit(self):
        """ Performs a reinitialization of position-sensitive calculations. Can be called anytime after init. """
        self.devInfoX = self.screenW - 350
        self.secondCharX = self.screenW // 2 - 10
        self.thirdCharX = self.screenW - 220
        self.charY = math.floor(self.screenH / 2) - 50
        self.firstChar = PlayableCharacter(self.firstCharX, self.charY, 0, 0, 1)
        self.secondChar = PlayableCharacter(self.secondCharX, self.charY, 0, 0, 2)
        self.thirdChar = PlayableCharacter(self.thirdCharX, self.charY, 0, 0, 3)

    # --------------------------------------------------------------------------------------------------------------

    def refreshDisplay(self):
        pygame.display.init()
        self.displaysurf = pygame.display.set_mode((self.screenW, self.screenH), self.flags, 0)
        pygame.display.set_caption(self.caption)

    # --------------------------------------------------------------------------------------------------------------

    @staticmethod
    def quitGame():
        pygame.quit()
        print('Game closing...')
        sys.exit()

    # --------------------------------------------------------------------------------------------------------------

    @staticmethod
    def toBool(x):
        return 'True' in x

    # --------------------------------------------------------------------------------------------------------------

    def getGameDirSize(self):
        parentDirectory = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        return self.getSize(parentDirectory)

    # --------------------------------------------------------------------------------------------------------------

    @staticmethod
    def getSize(startPath='.'):
        size = 0
        bytesInMegabyte = 1048576.0
        for dirpath, dirnames, filenames in os.walk(startPath):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                size += os.path.getsize(fp)
        size /= bytesInMegabyte
        return round(size, 2)

    # --------------------------------------------------------------------------------------------------------------

    def updateDisplayState(self, windowedConstant=0.82):
        """ Updates the fullscreen status of the display surface

        Args:
            windowedConstant (float, optional): Ratio between windows screen dimensions and fullscreen dimensions

        """
        if self.fullscreen:
            self.flags = FULLSCREEN | HWACCEL | ASYNCBLIT
            self.screenW, self.screenH = self.originalDimensions
        else:
            self.flags = HWACCEL | ASYNCBLIT
            self.screenW = int(windowedConstant * self.originalDimensions[0])
            self.screenH = int(windowedConstant * self.originalDimensions[1])
        self.refreshDisplay()

    # --------------------------------------------------------------------------------------------------------------

    def getRecentKeys(self, events, restrictToAlphabet=True):
        for event in events:
            if event.type == self.keyPressEvent and (len(pygame.key.name(event.key)) == 1 or not restrictToAlphabet):
                self.recentKeyboardKeys += pygame.key.name(event.key)
        while len(self.recentKeyboardKeys) > self.maxKeyMemoryLength:
            self.recentKeyboardKeys = self.recentKeyboardKeys[1:]

    # --------------------------------------------------------------------------------------------------------------

    def printText(self, text, font, colour, coords, center=False):
        """ Prints the input string onto the display surface with the given settings

        Args:
            text (str): String to display on screen
            font (pygame.font.Font): Cached font to use for the text
            colour (tuple of int): RGB constant for the desired text colour
            coords (tuple of int): X and y coordinates for text display
            center (bool, optional): Whether the given coords act as the center or top left of the displayed text

        Returns:
            pygame.Rect object representing the rectangle boundaries of the text

        """

        textSurf = font.render(text, self.antialiasing, colour)
        textRect = textSurf.get_rect()
        if center:
            textRect.center = coords
        else:
            textRect.topleft = coords
        self.displaysurf.blit(textSurf, textRect)
        return textRect

    # --------------------------------------------------------------------------------------------------------------

    @staticmethod
    def getAngle(pointA, pointB):
        # Determines the angle between a line (defined by points A and B) and the positive x-axis
        Ax, Ay = pointA
        Bx, By = pointB
        return math.atan2(By - Ay, Bx - Ax) * (180 / math.pi)

    # --------------------------------------------------------------------------------------------------------------

    def checkForQuit(self):
        keys = pygame.key.get_pressed()
        if keys[k.EXIT]:
            self.quitGame()
    
    # --------------------------------------------------------------------------------------------------------------

    @staticmethod
    def distance(p0, p1):
        return math.sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)
    
    # --------------------------------------------------------------------------------------------------------------

    def drawTempText(self, text, font, colour, coords, time, index, events):
        # Set timer
        if self.textTimers[index] == 0:
            pygame.time.set_timer(USEREVENT + index, time)
            self.textTimers[index] = 1

        # Reset timer once finished
        for event in events:
            if event.type == USEREVENT + index:
                self.textTimers[index] = 2

        # Display text if the timer is working
        if self.textTimers[index] == 1:
            self.printText(text, font, colour, coords)
            return True
        return False

    # --------------------------------------------------------------------------------------------------------------

    def drawCursor(self):
        if not pygame.mouse.get_pressed()[0]:
            self.displaysurf.blit(self.cursorImage, (self.mousex_hover, self.mousey_hover))
        else:
            self.displaysurf.blit(self.cursorClickedImage, (self.mousex, self.mousey))
    
    # --------------------------------------------------------------------------------------------------------------

    def redrawAndProceedTick(self, mousex, mousey, mouseRegionUpdating=False):
        self.drawCursor()
        if mouseRegionUpdating:
            pygame.display.update(pygame.Rect(mousex - 300, mousey - 300, 600, 600))
        pygame.display.update()
        fpsTolerance = 4
        if self.measuredFPS < self.desiredFPS - fpsTolerance and self.fps < 2 * self.desiredFPS:
            self.fps += 0.1
        elif self.measuredFPS > self.desiredFPS + fpsTolerance and self.fps > 0:
            self.fps -= 0.1
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
        self.printText(str(self.mainChar.coins) + ' coins', self.medFont, white, (50, 100))
        self.printText(str(self.mainChar.lives) + ' lives left', self.medFont, white, (50, 150))
        self.printText(str(int(pygame.time.get_ticks() / 1000)) + ' seconds', self.medFont, white, (50, 200))
        self.printText('TOTAL SCORE: ' + str(int(self.mainChar.coins +
                                                 100 * self.mainChar.lives - 0.1 * pygame.time.get_ticks() / 1000)),
                       self.medFont, white, (50, 250))
        self.printText('Esc to Quit', self.medFont, white, (50, 300))
        keys = pygame.key.get_pressed()
        while not keys[k.EXIT]:
            keys = pygame.key.get_pressed()
            self.redrawAndProceedTick(self.mousex_hover, self.mousey_hover)
            pygame.event.get()
        self.quitGame()

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
        if onText.collidepoint(mousepos[0], mousepos[1]) and self.clicking:
            return True
        elif offText.collidepoint(mousepos[0], mousepos[1]) and self.clicking:
            return False
        return self.defaultValue

    # --------------------------------------------------------------------------------------------------------------

    def drawSlider(self, label, coords, value, valueMax, unlockCondition=True):
        # Draw a title for the slider
        text = self.printText(label, self.medFont, white, coords)

        # Determine the coordinates relevant to the actual slider
        separation = 40
        startX = text.right + separation
        length = pygame.Surface.get_width(self.slider)

        # Draw the slider
        self.displaysurf.blit(self.slider, [startX, coords[1] + 10])

        # Determine the slider pointer position
        pointerX = startX + length * value / valueMax
        pointerWidth = pygame.Surface.get_width(self.sliderPointer)
        pointerHeight = pygame.Surface.get_height(self.sliderPointer)
        sliderRect = pygame.Rect(pointerX, coords[1], pointerWidth, pointerHeight)
        collisionBorder = 100
        collisionRect = pygame.Rect(pointerX - collisionBorder, coords[1], pointerWidth +
                                                                           2 * collisionBorder, pointerHeight)

        # Move the slider pointer
        if collisionRect.collidepoint(self.mousex, self.mousey) and pygame.mouse.get_pressed()[0] and unlockCondition:
            pointerX = self.mousex - 0.5 * sliderRect.width

        # Ensure that the pointer is within bounds
        if pointerX + 0.5 * sliderRect.width >= startX + length:
            pointerX = startX + length - 0.5 * sliderRect.width
        if pointerX < startX:
            pointerX = startX

        # Draw the slider
        self.displaysurf.blit(self.sliderPointer, [pointerX, coords[1]])

        # Return the new value determined by the slider pointer position
        return valueMax * (pointerX - startX) / length

    # --------------------------------------------------------------------------------------------------------------

    @staticmethod
    def getDisplayResolutions():
        pygame.display.init()
        result = [pygame.display.list_modes()[0]]
        acceptableHeights = [2160, 1440, 1200, 1080, 900, 720, 600]
        for mode in pygame.display.list_modes():
            if mode[1] in acceptableHeights and len(result) < 5 and not mode in result:
                result.append(mode)
        return result

    # --------------------------------------------------------------------------------------------------------------

    def getResolutionDict(self):
        modes = self.getDisplayResolutions()
        result = {}
        for mode in modes:
            result[str(mode[1]) + 'p'] = mode
        return result

    # --------------------------------------------------------------------------------------------------------------

    def saveGameSettings(self):
        # Open file for writing
        fileName = 'settings' + self.configExtension
        permissions = 'w'
        dataFile = open(fileName, permissions)

        # Add a warning to the data file
        dataFile.write('Game Settings Configuration - DO NOT MODIFY THIS FILE! Change settings in-game!\n')

        # Save settings
        dataFile.write(str(self.developerMode) + '\n' + str(self.antialiasing) + '\n' + str(self.stableFPS) + '\n' +
                       str(self.decorations) + '\n' + str(self.doPlayMusic) + '\n' + str(self.fullscreen) + '\n' +
                       str(self.volume) + '\n' + str(self.currentResolution))

        dataFile.close()

    # --------------------------------------------------------------------------------------------------------------

    def loadGameSettings(self):
        # Collect information
        fileName = 'settings' + self.configExtension
        if not os.path.isfile(fileName):
            return
        permissions = 'r'
        dataFile = open(fileName, permissions)
        uselessWarning = dataFile.readline()
        print uselessWarning

        # Read settings
        self.developerMode = self.toBool(dataFile.readline())
        self.antialiasing = self.toBool(dataFile.readline())
        self.stableFPS = self.toBool(dataFile.readline())
        self.decorations = self.toBool(dataFile.readline())
        self.doPlayMusic = self.toBool(dataFile.readline())
        self.fullscreen = self.toBool(dataFile.readline())
        self.volume = float(dataFile.readline())
        self.currentResolution = dataFile.readline()

        # Make sure that the resolution setting is valid
        if not self.currentResolution in self.resDict.keys():
            self.currentResolution = str(self.getDisplayResolutions()[0][1]) + 'p'

        dataFile.close()

    # --------------------------------------------------------------------------------------------------------------

    def drawOptionsMenu(self):
        while True:

            # Fill screen with background
            self.displaysurf.fill(black)
            self.displaysurf.blit(self.bgrdTitle, self.origin)

            # Get mouse status
            self.getMousePos()

            # Draw title
            self.printText('Exit Dash: Hyperion | Options Menu', self.genericFont, white, [self.screenW // 2, 50], True)

            # Draw toggles
            devModeToggle = self.drawToggle('Debug Info', (math.ceil(0.2 * self.screenW), 150),
                                            (self.mousex, self.mousey), (self.mousex_hover, self.mousey_hover),
                                            self.developerMode)
            aaToggle = self.drawToggle('Anti-aliasing', (math.ceil(0.2 * self.screenW), 200), (self.mousex,
                                                                                               self.mousey),
                                       (self.mousex_hover, self.mousey_hover), self.antialiasing)
            sFPSToggle = self.drawToggle('Stabilize Framerate', (math.ceil(0.55 * self.screenW), 150),
                                         (self.mousex, self.mousey), (self.mousex_hover, self.mousey_hover),
                                         self.stableFPS)
            decorationToggle = self.drawToggle('Visual Details', (math.ceil(0.55 * self.screenW), 200),
                                               (self.mousex, self.mousey), (self.mousex_hover, self.mousey_hover),
                                               self.decorations)
            musicToggle = self.drawToggle('Game Music', (math.ceil(0.2 * self.screenW), 250),
                                          (self.mousex, self.mousey),
                                                         (self.mousex_hover, self.mousey_hover), self.doPlayMusic)
            fullscrToggle = self.drawToggle('Fullscreen', (math.ceil(0.55 * self.screenW), 250),
                                            (self.mousex, self.mousey),
                                            (self.mousex_hover, self.mousey_hover), self.fullscreen)

            # Draw volume slider
            self.volume = self.drawSlider('Music Volume', [math.ceil(0.2 * self.screenW), 300],
                                          self.volume, 1.0, self.doPlayMusic)

            # Draw resolution panel
            self.printText('Display Resolution:', self.medFont, white, [0.2 * self.screenW, 350])
            self.currentResolution = self.drawSelectionPanel([0.2 * self.screenW, 400], self.currentResolution,
                                                             *self.resDict.keys())
            if self.screenH != int(self.resDict[self.currentResolution][1]):
                self.screenW, self.screenH = self.resDict[self.currentResolution]
                self.refreshDisplay()
                self.reinit()

            # Update game vars with the values from the toggles
            if devModeToggle != self.defaultValue:
                self.developerMode = devModeToggle
            if aaToggle != self.defaultValue:
                self.antialiasing = aaToggle
            if sFPSToggle != self.defaultValue:
                self.stableFPS = sFPSToggle
            if decorationToggle != self.defaultValue:
                self.decorations = decorationToggle
            if musicToggle != self.defaultValue:
                self.doPlayMusic = musicToggle
                # Set volume as necessary
                if self.doPlayMusic and self.volume == 0.0:
                    self.volume = 1.0
                elif not self.doPlayMusic:
                    self.volume = 0.0
            if fullscrToggle != self.defaultValue:
                self.fullscreen = fullscrToggle
                self.updateDisplayState()
                self.reinit()

            # Update volume
            pygame.mixer.music.set_volume(self.volume)

            # Draw quit button
            if self.drawButton('Return to Menu', [self.screenW // 2, self.screenH - 100]):
                self.saveGameSettings()
                break

            # Update display
            self.redrawAndProceedTick(self.mousex_hover, self.mousey_hover)

    # --------------------------------------------------------------------------------------------------------------

    def getMousePos(self):
        self.clicking = False
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                self.mousex, self.mousey = event.pos
                self.clicking = True
            elif event.type == MOUSEMOTION:
                self.mousex, self.mousey = event.pos
                self.mousex_hover, self.mousey_hover = event.pos

    # --------------------------------------------------------------------------------------------------------------

    @staticmethod
    def leftmostPlatform(platforms):
        result = platforms[0]
        for platform in platforms:
            if platform.x <= result.x:
                result = platform
        return result

    # --------------------------------------------------------------------------------------------------------------

    @staticmethod
    def rightmostPlatform(platforms):
        result = platforms[0]
        for platform in platforms:
            if platform.x >= result.x:
                result = platform
        return result

    # --------------------------------------------------------------------------------------------------------------

    def drawChevron(self, x, y, targetX, targetY, thickness=6):
        # Create a new surface object with the size of the chevron
        length = 20
        height = 40
        colour = black
        chevronsurf = pygame.Surface([2 * length, height], SRCALPHA)
        # Draw two lines representing a chevron arrow
        if self.antialiasing:
            pygame.draw.aaline(chevronsurf, colour, [0, height], [length, 0])
            pygame.draw.aaline(chevronsurf, colour, [length, 0], [2 * length, height])
        else:
            pygame.draw.line(chevronsurf, colour, [0, height], [length, 0], thickness)
            pygame.draw.line(chevronsurf, colour, [length, 0], [2 * length, height], thickness)
        # Start the chevron facing the positive x-axis
        chevronsurf = pygame.transform.rotate(chevronsurf, -90)
        # Determine the angle the chevron needs to be
        angle = self.getAngle([targetX, y], [x, targetY]) - 180
        chevronsurf = pygame.transform.rotate(chevronsurf, angle)
        # Blit the chevron
        self.displaysurf.blit(chevronsurf, [x, y])

    # --------------------------------------------------------------------------------------------------------------

    def launchLevelEditor(self, theme='stone'):
        # Initialize editor variables
        movableObjects = []
        currentItem = 'Left platform'
        currentState = 'Platforms'

        # Platform variables
        numPlatforms = 25
        platformDataSize = 3
        currentPlatformIndex = 0
        platforms = []
        platformCoords = [[self.defaultValue] * platformDataSize for x in xrange(numPlatforms)]
        platformSample = Platform(self.defaultValue, self.defaultValue, 0, 0, 0, theme)

        # Block variables
        blockSample = Block(self.defaultValue, self.defaultValue, 'coin')
        numBlocks = 25
        blockDataSize = 3
        currentBlockIndex = 0
        blocks = []
        blockCoords = [[self.defaultValue] * blockDataSize for x in xrange(numBlocks)]
        key = Key(self.defaultValue, self.defaultValue, 'blue')
        coinID = 0
        mysteryID = 1

        # Pool variables
        poolDefWidth = 490
        poolDefHeight = 180
        poolSample = Pool(self.defaultValue, self.defaultValue, poolDefWidth, poolDefHeight, theme)
        poolSurf = pygame.Surface([0, 0], SRCALPHA)
        poolSample.draw(poolSurf)
        poolDataSize = 4
        poolCoords = [self.defaultValue] * poolDataSize
        pool = None

        # Design constants
        selPanelCoords = [self.screenW - 225, 30]

        while True:
            # Draw background
            self.activeBackground.update(self.displaysurf)

            # Get mouse position and state
            self.checkForQuit()
            self.getMousePos()

            # Define the current item using the current state
            if currentState != 'Platforms' and currentState != 'Pool':
                currentItem = currentState.lower()
            elif currentItem != 'Right platform' and currentState == 'Platforms':
                currentItem = 'Left platform'
            elif currentItem != 'Right pool edge' and currentState == 'Pool':
                currentItem = 'Left pool edge'

            # Allow horizontal motion
            keys = pygame.key.get_pressed()
            movementSpeed = 10
            if keys[k.RIGHT] or keys[k.RIGHT2]:
                self.activeBackground.x -= movementSpeed
                self.activeBackground.invertedX -= movementSpeed
                if movableObjects:
                    for obj in movableObjects:
                        obj.x -= movementSpeed
            elif keys[k.LEFT] or keys[k.LEFT2]:
                self.activeBackground.x += movementSpeed
                self.activeBackground.invertedX += movementSpeed
                if movableObjects:
                    for obj in movableObjects:
                        obj.x += movementSpeed

            # Allow vertical motion
            if keys[k.ACTION]:
                if movableObjects:
                    for obj in movableObjects:
                        obj.y += movementSpeed
            elif keys[k.DUCK] or keys[k.DUCK2]:
                if movableObjects:
                    for obj in movableObjects:
                        obj.y -= movementSpeed

            # Draw platforms
            for platform in platforms:
                platform.draw(self.displaysurf)

            # Draw pool
            if pool:
                pool.draw(self.displaysurf)

            # Draw blocks
            for block in blocks:
                block.draw([key], self.displaysurf)

            # Prevent excessive platforms or blocks
            if currentItem == 'Left platform' and currentPlatformIndex >= numPlatforms:
                currentItem = 'coin block'
            if (currentItem == 'coin block' or currentItem == 'mystery block') and currentBlockIndex >= numBlocks:
                currentItem = 'pool'

            # Display the current item next to the cursor and allow placement of any item
            mouseOnScreen = self.mousex < selPanelCoords[0]
            if currentItem == 'Left platform' and mouseOnScreen:
                self.displaysurf.blit(platformSample.leftImage, (self.mousex_hover - platformSample.tileWidth,
                                                                 self.mousey_hover - platformSample.tileWidth))
                if self.clicking:
                    platformCoords[currentPlatformIndex][0] = self.mousex_hover - platformSample.tileWidth
                    platformCoords[currentPlatformIndex][2] = self.mousey_hover - platformSample.tileWidth
                    currentItem = 'Right platform'
            elif currentItem == 'Right platform' and mouseOnScreen:
                self.displaysurf.blit(platformSample.rightImage, (self.mousex_hover - platformSample.tileWidth,
                                                                 self.mousey_hover - platformSample.tileWidth))
                self.displaysurf.blit(platformSample.leftImage, (platformCoords[currentPlatformIndex][0],
                                                                 platformCoords[currentPlatformIndex][2]))
                for x in xrange(platformCoords[currentPlatformIndex][0] + platformSample.tileWidth, self.mousex_hover -
                        2 * platformSample.tileWidth, platformSample.tileWidth):
                    self.displaysurf.blit(platformSample.image, (x, platformCoords[currentPlatformIndex][2]))
                if self.clicking:
                    platformCoords[currentPlatformIndex][1] = self.mousex_hover - platformSample.tileWidth
                    platform = Platform(platformCoords[currentPlatformIndex][0],
                                        platformCoords[currentPlatformIndex][2], 0, 0,
                                        platformCoords[currentPlatformIndex][1] -
                                        platformCoords[currentPlatformIndex][0], theme)
                    platforms.append(platform)
                    movableObjects.append(platform)
                    currentItem = 'Left platform'
                    currentPlatformIndex += 1
            elif currentItem == 'coin block' and mouseOnScreen:
                self.displaysurf.blit(blockSample.coinBlockImage, (self.mousex_hover - blockSample.width,
                                                                 self.mousey_hover - blockSample.width))
                if self.clicking:
                    blockCoords[currentBlockIndex][0] = self.mousex_hover - blockSample.width
                    blockCoords[currentBlockIndex][1] = self.mousey_hover - blockSample.width
                    blockCoords[currentBlockIndex][2] = coinID
                    block = Block(blockCoords[currentBlockIndex][0], blockCoords[currentBlockIndex][1], 'coin')
                    blocks.append(block)
                    movableObjects.append(block)
                    currentBlockIndex += 1
            elif currentItem == 'mystery block' and mouseOnScreen:
                self.displaysurf.blit(blockSample.regularImage, (self.mousex_hover - blockSample.width,
                                                                 self.mousey_hover - blockSample.width))
                if self.clicking:
                    blockCoords[currentBlockIndex][0] = self.mousex_hover - blockSample.width
                    blockCoords[currentBlockIndex][1] = self.mousey_hover - blockSample.width
                    blockCoords[currentBlockIndex][2] = mysteryID
                    block = Block(blockCoords[currentBlockIndex][0], blockCoords[currentBlockIndex][1], 'regular')
                    blocks.append(block)
                    movableObjects.append(block)
                    currentBlockIndex += 1
            elif currentItem == 'Left pool edge' and mouseOnScreen:
                poolSample = Pool(self.mousex_hover - poolSample.width, self.mousey_hover - poolSample.height,
                                  poolDefWidth, poolDefHeight, theme)
                poolSample.draw(self.displaysurf)
                if self.clicking:
                    poolCoords[0] = self.mousex_hover - poolSample.width
                    poolCoords[1] = self.mousey_hover - poolSample.height
                    currentItem = 'Right pool edge'
            elif currentItem == 'Right pool edge' and mouseOnScreen:
                pool = Pool(poolCoords[0], poolCoords[1], self.mousex_hover - poolCoords[0],
                            self.mousey_hover - poolCoords[1], theme)
                pool.draw(self.displaysurf)
                if self.clicking:
                    poolCoords[2] = self.mousex_hover - poolCoords[0]
                    poolCoords[3] = self.mousey_hover - poolCoords[1]
                    movableObjects.append(pool)
                    currentState = 'Platforms'
            elif currentItem == 'save and quit' and platforms:
                self.platforms = platforms
                self.blocks = blocks
                self.pool = pool
                self.door = Door(self.rightmostPlatform(self.platforms)[2] - 70,
                                 self.rightmostPlatform(self.platforms)[1])
                self.fakedoor = Door(self.leftmostPlatform(platforms)[0] + 70, self.leftmostPlatform(platforms)[1])
                self.saveLevel('custom')
                self.seed = 0
                return 1
            elif currentItem == 'save and quit':
                currentState = 'Platforms'

            # Check for quit
            if keys[k.EXIT2]:
                return 0

            # Print instructions
            self.printText('Left-click to place item, Q to exit without saving', self.medFont, white, (50, 50))
            self.printText('Platforms remaining: ' + str(numPlatforms - currentPlatformIndex),
                           self.medFont, white, (50, 100))
            self.printText('Blocks remaining: ' + str(numBlocks - currentBlockIndex), self.medFont, white, (50, 150))

            # Draw chevron
            if platforms and (platforms[0][0] not in range(0, self.screenW) or
                                      platforms[0][1] not in range(0, self.screenH)):
                self.drawChevron(self.screenW // 2, 50, platforms[0].x, platforms[0].y)

            # Draw right section separator
            if self.antialiasing:
                pygame.draw.aaline(self.displaysurf, black, [selPanelCoords[0], 0], [selPanelCoords[0],
                                                                                     self.screenH])
            else:
                pygame.draw.line(self.displaysurf, black, [selPanelCoords[0], 0], [selPanelCoords[0], self.screenH])

            # Allow the user to select which mode they want to be in
            currentState = self.drawSelectionPanel([selPanelCoords[0] + 25, selPanelCoords[1]], currentState,
                                                   'Platforms', 'Coin Block', 'Mystery Block', 'Pool', 'SAVE AND QUIT')

            self.redrawAndProceedTick(self.mousex, self.mousey)

    # --------------------------------------------------------------------------------------------------------------

    def initializeLevel(self):
        self.textTimers = [0] * 10
        self.mobs, self.allMovableObjects, self.enemies, self.icicles, self.platforms = [], [], [], [], []
        self.blocks, self.keys, self.torches = [], [], []
        self.pool = None
        if not type(self.mainChar) is PlayableCharacter:
            self.mainChar = PlayableCharacter(int(0.5 * self.screenW), int(0.5 * self.screenH))
        self.mainChar.longestPlatform = None
        self.mainChar.respawnPoint = None
        self.mousex_hover, self.mousey_hover = self.defaultValue, self.defaultValue
        self.mainChar.hasKey, self.autoscroll = False, False
        self.measuredFPS, self.fps = self.desiredFPS, self.desiredFPS

    # --------------------------------------------------------------------------------------------------------------

    def finalizeBlocks(self):
        for block in self.blocks:
            if block.form == 'regular' and not self.keys and not block.yieldsStar:
                key = Key(block[0][0], block[0][1] - 80, 'blue')
                self.keys.append(key)
                self.allMovableObjects.append(key)
            elif block.form == 'regular' and r.randint(0, 2) == 0:
                block.willExplode = True
            elif block.form == 'regular':
                block.yieldsStar = True
            self.allMovableObjects.append(block)

    # --------------------------------------------------------------------------------------------------------------

    @staticmethod
    def illuminate(targetSurf, x, y):
        x, y = int(x), int(y)
        rad = r.randint(215, 245)
        transp = 255
        delta = 3
        clr = 0
        defclr = 0
        while rad > 50:
            pygame.draw.circle(targetSurf, (clr, clr, defclr, transp), (x, y), rad)
            rad -= delta; transp -= delta; clr += delta
        pygame.draw.circle(targetSurf, (clr, clr, defclr, transp), (x, y), rad)

    # --------------------------------------------------------------------------------------------------------------

    def darken(self, surface, value):
        dark = pygame.Surface(surface.get_size(), 32)
        dark.set_alpha(value, pygame.RLEACCEL)
        for torch in self.torches:
            if torch.burning:
                self.illuminate(dark, torch.x + 0.5 * torch.width, torch.y + 5)
        surface.blit(dark, (0, 0))

    # --------------------------------------------------------------------------------------------------------------

    @staticmethod
    def interpretHintString(hint):
        try:
            hint = str(hint)
        except TypeError:
            return ''
        if hint == 'None':
            return ''
        openingBrace = '{'
        closingBrace = '}'
        if not openingBrace in hint:
            return hint
        keymap = k.SUMMARY
        startSlice = 0
        endSlice = 0
        for letterIndex in range(len(hint)):
            if hint[letterIndex] == openingBrace:
                startSlice = letterIndex + 1
        for letterIndex in range(startSlice, len(hint)):
            if hint[letterIndex] == closingBrace:
                endSlice = letterIndex
        return hint[:startSlice - 1] + '"' + pygame.key.name(keymap[hint[startSlice:endSlice]]) + '"' + \
               hint[endSlice + 1:]

    # --------------------------------------------------------------------------------------------------------------

    def isPlatformCollision(self, obj):
        try:
            testrect = obj.getRect()
        except AttributeError:
            testrect = pygame.Surface.get_rect(obj.image)
        for platform in self.platforms:
            platrect = platform.getRect()
            if testrect.colliderect(platrect):
                return True
        return False

    # --------------------------------------------------------------------------------------------------------------

    def generateMobs(self, longestPlatform, farthestPlatform):
        quantityMobs = len(self.platforms) - 1
        mainMobType = 'slime'
        sampleMob = AICharacter(0, 0, 0, 0, (mainMobType, -1, -1))
        self.mobs = []
        for i in range(0, quantityMobs):
            whichPlatform = r.randint(1, len(self.platforms) - 1)
            while self.platforms[whichPlatform][0] == longestPlatform[0]:
                whichPlatform = r.randint(1, len(self.platforms) - 1)
            if r.randint(0, 1) == 0:
                self.mobs.append(AICharacter(r.randint(self.platforms[whichPlatform][0],
                                                     self.platforms[whichPlatform][2]),
                                             self.platforms[whichPlatform][3] - sampleMob.height,
                                             int(0.7 * self.mainChar.runSpeed), 0, (mainMobType, -1, -1)))
            else:
                self.mobs.append(AICharacter(r.randint(self.platforms[whichPlatform][0],
                                                     self.platforms[whichPlatform][2]),
                                             self.platforms[whichPlatform][3] - sampleMob.height,
                                             int(0.7 * self.mainChar.runSpeed), 0, ('snail', -1, -1)))
        self.mobs.append(AICharacter(70, self.platforms[0][1] - 750, 5, 0, ('fly', self.platforms[0][0],
                                                                            farthestPlatform[2])))
        if self.pool:
            self.mobs.append(AICharacter(self.pool.poolStartX + self.pool.tileWidth, self.pool.y +
                    self.pool.tileWidth, 5, 0, ('fish', -1, -1)))
        self.enemies.extend(self.mobs)
        self.allMovableObjects.extend(self.mobs)

    # --------------------------------------------------------------------------------------------------------------

    def generateFences(self):
        sampleFence = Checkpoint(self.defaultValue, self.defaultValue)
        self.fences = []
        for platformIndex in xrange(1, len(self.platforms), 5):
            if self.platforms[platformIndex].width >= 2 * sampleFence.width and not self.autoscroll:
                fenceX = self.platforms[platformIndex][0] + 20
                fenceY = self.platforms[platformIndex][1] - sampleFence.height
                self.fences.append(Checkpoint(fenceX, fenceY))
        self.allMovableObjects.extend(self.fences)

    # --------------------------------------------------------------------------------------------------------------

    def generateFoliage(self):
        self.foliage = []
        for platform in self.platforms:
            for x in xrange(int(platform.x), int(platform.x + platform.width - 100), 100):
                if r.randint(0, 10) == 0 and self.decorations:
                    decoration = BackgroundFoliage(x, platform.y)
                    decoration.y -= decoration.height
                    self.allMovableObjects.append(decoration)
                    self.foliage.append(decoration)

    # --------------------------------------------------------------------------------------------------------------

    def generateTorches(self):
        if not self.levelDark:
            return
        for block in self.blocks:
            newTorch = Torch(block.x, block.y - self.firstChar.height - 25)
            if not self.isPlatformCollision(newTorch) and newTorch.x <= self.farthestPlatform[2]:
                self.torches.append(newTorch)
        maxDistBwTorches = 490
        for torch1 in self.torches:
            for torch2 in self.torches:
                if self.distance([torch1.x, torch1.y], [torch2.x, torch2.y]) < maxDistBwTorches:
                    self.torches.remove(torch2)
        self.allMovableObjects.extend(self.torches)

    # --------------------------------------------------------------------------------------------------------------

    def finalizeLevel(self, farthestPlatform):
        for key in self.keys:
            key.visible = False
        if not self.keys or self.autoscroll:
            key = Key(int(0.5 * (farthestPlatform[0] + farthestPlatform[2])), farthestPlatform[1] - 80, 'blue')
            key.visible = True
            self.keys.append(key)
            self.allMovableObjects.append(key)
        self.mainChar.x = self.platforms[0][0] + 20
        self.mainChar.y = self.platforms[0][1] - self.mainChar.height
        self.mainChar.Vx = 5
        self.mainChar.cpuControlled = True
        for c in [self.mainChar] + self.mobs:
            c.platformInit(self.platforms)
        self.mainChar.setMapObjX(self.enemies, self.allMovableObjects, self.platforms, self.screenW - 100)
        self.allMovableObjects.append(self.activeBackground)
        self.decideDark()
        self.generateTorches()

    # --------------------------------------------------------------------------------------------------------------

    def decideDark(self):
        self.levelDark = False
        if (r.randint(0, 2) == 0 and self.currLevel > 2) or self.currLevel == 2:
            self.levelDark = True

    # --------------------------------------------------------------------------------------------------------------

    def gatherPlatformInfo(self):
        self.topmostPlatform, self.lowestPlatform, self.shortestPlatform, self.longestPlatform, \
            self.farthestPlatform = self.platforms[1], self.platforms[1], self.platforms[1], \
                                    self.platforms[1], self.platforms[1]
        for platform in self.platforms:
            if platform[1] < self.topmostPlatform[1]:
                self.topmostPlatform = platform
            if platform[1] > self.lowestPlatform[1]:
                self.lowestPlatform = platform
            if platform.width > self.longestPlatform.width and platform[0] != self.platforms[0][0]:
                self.longestPlatform = platform
            if platform[2] - platform[0] < self.shortestPlatform[2] - self.shortestPlatform[0]:
                self.shortestPlatform = platform
            if platform[2] > self.farthestPlatform[2]:
                self.farthestPlatform = platform

    # --------------------------------------------------------------------------------------------------------------

    def generateRandomLevel(self, theme, numberofplatforms, lvl, levelSeed=None):

        # Step 0: Clear all data from the previous level and initialize the random number generator
        self.initializeLevel()
        r.seed(levelSeed)

        # Step 1: Generate the necessary number of platforms using an iterative strategy
        firstPlatform = Platform(r.randint(-300, 500), r.randint(self.screenH - 200, self.screenH - 50),
                                 0, 0, r.randint(800, 1500), theme)
        overlap = True
        attempts = 3 * numberofplatforms                   # Reduce number of attempts for slower computers
        maxHeightDifference = self.mainChar.maxJumpHeight - 10
        maxWidthDifference = self.mainChar.maxJumpLength * 2
        while overlap and attempts >= 0:
            overlap = False
            attempts -= 1
            self.platforms = [firstPlatform]
            for i in range(1, numberofplatforms):
                randomDirection = [1, r.randint(0, 1)]
                platformWidth = r.randint(400, 2000)
                prevPlatform = self.platforms[i - 1]
                if randomDirection[0] == 0 and randomDirection[1] == 0:
                    platformRight = prevPlatform[0] - r.randint(int(0.5 * maxWidthDifference), maxWidthDifference)
                    platformLeft = platformRight - platformWidth
                    platformTop = prevPlatform[1] + r.randint(int(0.75 * maxHeightDifference), maxHeightDifference)
                elif randomDirection[0] == 0 and randomDirection[1] == 1:
                    platformRight = prevPlatform[0] - r.randint(int(0.5 * maxWidthDifference), maxWidthDifference)
                    platformLeft = platformRight - platformWidth
                    platformTop = prevPlatform[1] - r.randint(int(0.75 * maxHeightDifference), maxHeightDifference)
                elif randomDirection[0] == 1 and randomDirection[1] == 1:
                    platformLeft = prevPlatform[2] + r.randint(int(0.5 * maxWidthDifference), maxWidthDifference)
                    platformTop = prevPlatform[1] - r.randint(int(0.75 * maxHeightDifference), maxHeightDifference)
                else:
                    platformLeft = prevPlatform[2] + r.randint(int(1.2 * self.mainChar.width), maxWidthDifference)
                    platformTop = prevPlatform[1] + r.randint(int(0.5 * maxHeightDifference), int(0.4 * self.screenH))
                self.platforms.append(Platform(platformLeft, platformTop, 0, 0, platformWidth, theme))
                overlap = self.isPlatformCollision(self.platforms[i])
        for platform in self.platforms:
            self.allMovableObjects.append(platform)

        # Step 2: Gather platform info
        self.gatherPlatformInfo()
        focusHeight = self.longestPlatform[1] - 324

        # Step 3: Generate rare pool platform
        self.pool = None
        if r.randint(0, 2) == 0 or self.currLevel <= 1:
            poolX = self.farthestPlatform[2] + int(0.9 * self.mainChar.maxJumpLength)
            poolY = self.farthestPlatform[1]
            poolWidth = r.randint(700, 900)
            poolHeight = 4 * self.mainChar.height
            self.pool = Pool(poolX, poolY, poolWidth, poolHeight, theme)
            self.allMovableObjects.append(self.pool)
        elif r.randint(0, 1) == 0:
            self.autoscroll = True

        # Step 4: Generate blocks
        quantityBlocks = numberofplatforms
        sampleBlock = Block(0, 0, 'bonus')
        blockHeight = math.floor(1.3 * self.mainChar.height + sampleBlock.height)
        self.blocks = [Block(r.randint(self.platforms[0][0] + 50, self.platforms[0][2] - 50),
                             self.platforms[0][1] - blockHeight, 'coin')]
        blockplatform = [0]
        self.keys = []
        for i in range(1, quantityBlocks):
            y = self.platforms[i][1] - blockHeight
            if self.platforms[i].x != self.longestPlatform.x and r.randint(0, 3) != 0:
                x = 0.5 * self.platforms[i][0] + 0.5 * self.platforms[i][2] + r.randint\
                    (int(-0.4 * self.platforms[i].width), int(0.4 * self.platforms[i].width))
                self.blocks.append(Block(x, y, 'coin'))
                blockplatform.append(i)
            elif self.platforms[i].x != self.longestPlatform.x and not self.keys:
                x = 0.5 * self.platforms[i][0] + 0.5 * self.platforms[i][2] + \
                    r.randint(int(-0.4 * self.platforms[i].width), int(0.4 * self.platforms[i].width))
                self.blocks.append(Block(x, y, 'regular'))
                blockplatform.append(i)
        # Check for block-platform collisions
        for block in self.blocks:
            blockRect = block.getRect()
            for platform in self.platforms:
                platformRect = platform.getRect()
                if blockRect.colliderect(platformRect):
                    block.x += 550
        # Add a block to the pool platform if present
        if self.pool:
            poolBlock = Block(self.pool.poolStartX + self.pool.tileWidth,
                              self.pool.y + self.pool.height - blockHeight, 'regular')
            poolBlock.yieldsStar = True
            poolBlock.willExplode = False
            self.blocks.append(poolBlock)
        r.shuffle(self.blocks)
        # Add all blocks to the movable objects list
        self.finalizeBlocks()

        # Step 5: Generate icicles if necessary by first creating a platform to use as a ledge
        self.icicles = []
        shouldCreateLedge = self.longestPlatform.y != self.platforms[0].y and (lvl == 1 or r.randint(0, 1) == 0)
        if shouldCreateLedge:
            ledge = Platform(self.longestPlatform[0], focusHeight, 0, 0, self.longestPlatform.width, 'snow')
            # Move the ledge out of the visible area if it overlaps with another platform
            for platform in self.platforms:
                if platform.getRect().colliderect(ledge.getRect()):
                    ledge.x, ledge.y = self.defaultValue, self.defaultValue
            self.platforms.append(ledge), self.allMovableObjects.append(ledge)
            for i in range(ledge[0] + ledge.tileWidth * 2, ledge[2] - ledge.tileWidth * 2, 40):
                self.icicles.append(FallingSpike(i, ledge[3]))
            self.allMovableObjects.extend(self.icicles)

        # Step 6: Add foliage to enhance the atmosphere
        self.generateFoliage()

        # Step 7: Generate mobs
        self.generateMobs(self.longestPlatform, self.farthestPlatform)

        # Step 8: Place a door
        doorX = self.farthestPlatform[2] - 100
        doorY = self.farthestPlatform[1]
        self.door = Door(doorX, doorY)
        self.allMovableObjects.append(self.door)
        self.fakedoor = Door(self.platforms[0].x + 10, self.platforms[0].y)
        self.allMovableObjects.append(self.fakedoor)

        # Step 9: Place fences as respawn points
        self.generateFences()

        # Step 10: Finalize level details and set player and camera position
        self.loadLevelHint(lvl)
        self.finalizeLevel(self.farthestPlatform)

        # Step 11: Save level to disk
        self.saveLevel(lvl)
        
    # --------------------------------------------------------------------------------------------------------------

    def setupBgrd(self, environment):
        if environment == 'gloomy':
            self.bgrd = self.bgrdGloomy
        elif environment == 'yellow':
            self.bgrd = self.bgrdYellowSky
        elif environment == 'castle':
            self.bgrd = self.bgrdCastle
        elif environment == 'desert':
            self.bgrd = self.bgrdDesert
        self.activeBackground = Background(self.bgrd, self.screenW, self.screenH)

    # --------------------------------------------------------------------------------------------------------------

    def drawButton(self, text, coords, center=True):
        btnRect = self.printText(text, self.genericFont, white, coords, center)
        if btnRect.collidepoint(self.mousex, self.mousey) and self.clicking:
            return True
        if btnRect.collidepoint(self.mousex_hover, self.mousey_hover):
            self.printText(text, self.genericFont, yellow, coords, center)
        return False

    # --------------------------------------------------------------------------------------------------------------

    def drawSelectionPanel(self, topLeftCoords, currentlySelected, *args):
        for index in range(len(args)):
            buttonRect = self.printText(args[index], self.medFont, white, (topLeftCoords[0], topLeftCoords[1] +
                                                                                                 60 * index))
            hovering = buttonRect.collidepoint(self.mousex_hover, self.mousey_hover)
            clickingThis = pygame.mouse.get_pressed()[0] and buttonRect.collidepoint(self.mousex, self.mousey)
            selected = args[index] == currentlySelected
            if hovering or clickingThis or selected:
                self.printText(args[index], self.medFont, yellow, (topLeftCoords[0], topLeftCoords[1] + 60 * index))
            if clickingThis:
                currentlySelected = args[index]
        return currentlySelected

    # --------------------------------------------------------------------------------------------------------------

    def drawTitleScreen(self):
        whichChar = 0

        # Check for quit events
        self.checkForQuit()
        self.getMousePos()

        # Fill screen with background
        self.displaysurf.blit(self.bgrdTitle, self.origin)

        # Print static text
        self.printText('Stranded in a monster-infested space centre on the moon HYPERION. One goal: Find an exit.',
                       self.medFont, white, (self.screenW // 2, 120), True)
        self.printText('Welcome to Exit Dash: Hyperion!', self.genericFont, white, (self.screenW // 2, 50), True)
        self.printText('Choose a character to begin:', self.genericFont, white, (self.screenW // 2, 250), True)

        # Draw three characters to choose from
        firstCharRect = pygame.Rect(self.firstChar.x, self.firstChar.y, self.firstChar.width, self.firstChar.height)
        secondCharRect = pygame.Rect(self.secondChar.x, self.secondChar.y, self.secondChar.width,
                                     self.secondChar.height)
        thirdCharRect = pygame.Rect(self.thirdChar.x, self.thirdChar.y, self.thirdChar.width, self.thirdChar.height)
        self.displaysurf.blit(self.firstChar.standingImage, (self.firstCharX, self.charY))
        self.displaysurf.blit(self.secondChar.standingImage, (self.secondCharX, self.charY))
        self.displaysurf.blit(self.thirdChar.standingImage, (self.thirdCharX, self.charY))
        if firstCharRect.collidepoint(self.mousex_hover, self.mousey_hover):
            pygame.draw.rect(self.displaysurf, white, firstCharRect, 3)
            self.printText('Flight Commander ALEX', self.medFont, yellow, (self.firstCharX - 95, self.charY +
                                                                                            self.firstChar.height + 15))
        else:
            self.printText('Flight Commander ALEX', self.medFont, white, (self.firstCharX - 95, self.charY +
                                                                                           self.firstChar.height + 15))
        if secondCharRect.collidepoint(self.mousex_hover, self.mousey_hover):
            pygame.draw.rect(self.displaysurf, white, secondCharRect, 3)
            self.printText('Astronaut ALLAN', self.medFont, yellow, (self.secondCharX - 70,
                                                                     self.charY + self.secondChar.height + 15))
        else:
            self.printText('Astronaut ALLAN', self.medFont, white, (self.secondCharX - 70,
                                                                    self.charY + self.secondChar.height + 15))
        if thirdCharRect.collidepoint(self.mousex_hover, self.mousey_hover):
            pygame.draw.rect(self.displaysurf, white, thirdCharRect, 3)
            self.printText('Medical Specialist LISA', self.medFont, yellow, (self.thirdCharX - 95,
                                                                             self.charY + self.thirdChar.height + 15))
        else:
            self.printText('Medical Specialist LISA', self.medFont, white, (self.thirdCharX - 95,
                                                                            self.charY + self.thirdChar.height + 15))
        firstCharacterChosen = firstCharRect.collidepoint(self.mousex, self.mousey) and self.clicking
        secondCharacterChosen = secondCharRect.collidepoint(self.mousex, self.mousey) and self.clicking
        thirdCharacterChosen = thirdCharRect.collidepoint(self.mousex, self.mousey) and self.clicking
        if firstCharacterChosen:
            whichChar = 1
        elif secondCharacterChosen:
            whichChar = 2
        elif thirdCharacterChosen:
            whichChar = 3

        # Draw quit button
        if self.drawButton('Exit', [self.screenW // 2, self.screenH - 50]):
            self.quitGame()

        # Draw editor button
        if self.drawButton('Editor', [self.screenW // 2, self.screenH - 230]):
            self.editorResult = self.launchLevelEditor()
        if self.editorResult:
            self.printText('Level saved to levels'+os.sep+'lvl_custom' + self.levelExtension +
                           '. Change name to lvl_{desiredLevelNum}' + self.levelExtension + 'to replace existing level',
                           self.smoothFont, white, [20, self.screenH - 25])

        # Draw settings button
        if self.drawButton('Options', [self.screenW // 2, self.screenH - 140]):
            self.editorResult = False
            self.drawOptionsMenu()

        # Enter game if a character is chosen
        if firstCharacterChosen or secondCharacterChosen or thirdCharacterChosen:
            self.mainChar = PlayableCharacter(0, 0, 0, 0, whichChar)
            self.currLevel = 1
            self.seed = pygame.time.get_ticks() % 1000000
            if self.overwriteLevels:
                self.generateRandomLevel('stone', 10, 1, self.seed)
            else:
                self.loadLevel(self.currLevel, self.theme)
            pygame.mixer.music.load(self.mainMusic)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)

        self.redrawAndProceedTick(self.mousex_hover, self.mousey_hover, True)

    # --------------------------------------------------------------------------------------------------------------

    def updateAll(self):

        # Draw background
        self.activeBackground.update(self.displaysurf)

        # Draw prop door
        self.fakedoor.update(self.mainChar, self.displaysurf, False)

        # Let player control the main character when ready
        if self.mainChar.x >= self.platforms[0][0] + 0.5 * self.platforms[0].width:
            self.mainChar.Vx = 0
            self.mainChar.cpuControlled = False

        # Handle events
        events = pygame.event.get()

        # Get recent key presses
        self.getRecentKeys(events)

        # Blit and update all objects
        result = self.door.update(self.mainChar, self.displaysurf)
        if self.pool:
            self.pool.update(self.displaysurf)
        if self.fences:
            for fence in self.fences:
                fence.draw(self.displaysurf)
        for f in self.foliage:
            f.draw(self.displaysurf)
        for torch in self.torches:
            torch.draw(self.displaysurf)
        for i in range(0, len(self.platforms)):
            self.platforms[i].update((0, 0, self.screenW, self.screenH), self.displaysurf)
        for i in range(0, len(self.blocks)):
            self.blocks[i].update(self.keys, self.displaysurf)
        for enemy in self.enemies:
            enemy.update(self.platforms, events, self.allMovableObjects, self.blocks, self.enemies,
                         self.mainChar, self.pool, self.displaysurf,
                         self.measuredFPS)
        for spike in self.icicles:
            spike.update(self.platforms, [self.mainChar], self.blocks, self.displaysurf)
        if not self.mainChar.update(self.platforms, events, self.allMovableObjects, self.blocks,
                                    self.enemies, self.mainChar, self.pool, self.displaysurf,
                                    self.screenW, self.screenH, int(self.measuredFPS), self.autoscroll, self.fences,
                                    self.torches):
            self.showGameOverScreen(False)
        for key in self.keys:
            key.update(self.mainChar, self.displaysurf)

        # Give the player a multi-kill bonus
        if self.mainChar.mobJumping and self.allowKillBonus:
            self.allowKillBonus = False
            self.mainChar.coins += 2
            self.receivingKillBonus = True
        elif not self.mainChar.mobJumping:
            self.allowKillBonus = True
        if self.receivingKillBonus:
            self.receivingKillBonus = self.drawTempText('Kill Bonus! +2 Coins',
                                                       self.medFont, white, (self.screenW / 2 - 50, 50), 4000, 1, events)

        # Draw level numer and hint
        self.drawTempText('Level ' + str(self.currLevel), self.medFont, white, (self.screenW - 150, 50),
                          15000, 0, events)
        self.drawTempText(self.levelHint, self.smlFont, white, (250, 200), 13000, 3, events)

        # Check for quit events
        self.checkForQuit()

        # Display developer mode info
        if self.developerMode:
            videoInfo = pygame.display.Info()
            hardwareAccel = 'True' if videoInfo.hw else 'False'
            vram = str(videoInfo.video_mem) if videoInfo.video_mem != 0 else 'Unknown'

            self.printText('x = ' + str(round(self.mainChar.x, 2)), self.smoothFont, white, (self.devInfoX,
                                                                                          self.devInfoY))
            self.printText('y = ' + str(round(self.mainChar.y, 2)), self.smoothFont, white,
                           (self.devInfoX, self.devInfoY + self.devSpacing))
            self.printText('dx = ' + str(round(self.mainChar.Vx, 2)), self.smoothFont, white,
                           (self.devInfoX, self.devInfoY + 2 * self.devSpacing))
            self.printText('dy = ' + str(round(self.mainChar.Vy, 2)), self.smoothFont, white,
                           (self.devInfoX, self.devInfoY + 3 * self.devSpacing))
            self.printText('fps = ' + str(round(self.measuredFPS, 2)) +
                           (' (stable)' if self.stableFPS else ' (unstable)'),
                           self.smoothFont, white, (self.devInfoX, self.devInfoY + 4 * self.devSpacing))
            self.printText('vol = ' + str(100 * round(pygame.mixer.music.get_volume(), 2)) + '%', self.smoothFont, white,
                      (self.devInfoX, self.devInfoY + 5 * self.devSpacing))
            self.printText('onground = True' if self.mainChar.onGround else 'onground = False', self.smoothFont, white,
                           (self.devInfoX, self.devInfoY + 6 * self.devSpacing))
            self.printText('hw accel = ' + hardwareAccel, self.smoothFont, white, (self.devInfoX, self.devInfoY +
                                                                                               7 * self.devSpacing))
            self.printText('vram (MB) = ' + vram, self.smoothFont, white, (self.devInfoX, self.devInfoY + 8 *
                                                                                      self.devSpacing))
            self.printText('health = ' + str(self.mainChar.health), self.smoothFont, white,
                           (self.devInfoX, self.devInfoY + 9 * self.devSpacing))
            self.printText('seed = ' + str(int(self.seed)), self.smoothFont, white,
                           (self.devInfoX, self.devInfoY + 10 * self.devSpacing))
            self.printText('dirsize = ' + str(self.totalSize) + ' MB', self.smoothFont, white,
                           (self.devInfoX, self.devInfoY + 11 * self.devSpacing))
            self.printText('recent keys = ' + self.recentKeyboardKeys, self.smoothFont, white,
                           (self.devInfoX, self.devInfoY + 12 * self.devSpacing))
            self.printText('esc to quit', self.smoothFont, white, (self.devInfoX, self.devInfoY + 13 * self.devSpacing))

        # Darken level if necessary
        if self.levelDark:
            self.darken(self.displaysurf, 130)

        # Update screen and enforce maximum fps
        self.redrawAndProceedTick(self.mousex_hover, self.mousey_hover)

        return result

    # --------------------------------------------------------------------------------------------------------------

    def loadLevelHint(self, level):
        fileName = 'levels'+os.sep+'lvlhints' + self.levelExtension
        if not os.path.isfile(fileName):
            self.levelHint = self.interpretHintString('None')
        permissions = 'r'
        dataFile = open(fileName, permissions)
        data = []
        for ln in dataFile:
            data.append(ln)
        try:
            self.levelHint = self.interpretHintString(data[level - 1])
        except IndexError:
            self.levelHint = self.interpretHintString('None')

    # --------------------------------------------------------------------------------------------------------------

    def loadLevel(self, level, theme):
        # Collect information from the level data file
        fileName = 'levels/lvl_' + str(level) + self.levelExtension
        if not os.path.isfile(fileName) or self.overwriteLevels:
            # If the data file does not exist, generate a new random level instead
            self.seed = pygame.time.get_ticks() % 1000000
            self.generateRandomLevel(theme, 5 + 5 * level, level, self.seed)
            return
        permissions = 'r'
        dataFile = open(fileName, permissions)
        uselessWarning = dataFile.readline()
        print uselessWarning
        data = []
        line = 0
        for ln in dataFile:
            try:
                data.append(float(ln))
            except ValueError:
                data.append(ln)

        # Clear previous level cache
        self.initializeLevel()

        # Set up platforms
        maxNumPlatforms = 25
        platformDataSize = 3
        for i in xrange(line, platformDataSize * (maxNumPlatforms - 1) + 1, platformDataSize):
            if data[i] != self.defaultValue:
                self.platforms.append(Platform(data[i], data[i + 1], 0, 0, data[i + 2], theme))
            line += platformDataSize
        self.allMovableObjects.extend(self.platforms)
        self.gatherPlatformInfo()

        # Set up pool platform
        poolDataSize = 4
        if data[line] != self.defaultValue:
            self.pool = Pool(data[line], data[line + 1], data[line + 2], data[line + 3], theme)
            self.allMovableObjects.append(self.pool)
        line += poolDataSize

        # Set up bonus blocks
        maxNumBlocks = 25
        blockDataSize = 3
        for i in xrange(line, line + (blockDataSize * (maxNumBlocks - 1) + 1), blockDataSize):
            if data[i] != self.defaultValue and data[i + 2] == 0:
                self.blocks.append(Block(data[i], data[i + 1], 'coin'))
            elif data[i] != self.defaultValue:
                self.blocks.append(Block(data[i], data[i + 1], 'regular'))
            line += blockDataSize
        self.finalizeBlocks()

        # Initialize ledge and icicles
        ledgeDataSize = 3
        if data[line] != self.defaultValue:
            ledge = Platform(data[line], data[line + 1], 0, 0, data[line + 2], 'snow')
            self.platforms.append(ledge)
            self.allMovableObjects.append(ledge)
            for i in xrange(int(ledge[0] + ledge.tileWidth * 2), int(ledge[2] - ledge.tileWidth * 2), 40):
                self.icicles.append(FallingSpike(i, ledge[3]))
            self.allMovableObjects.extend(self.icicles)
        line += ledgeDataSize

        # Set up random mobs
        self.generateMobs(self.longestPlatform, self.farthestPlatform)

        # Place door
        doorDataSize = 2
        self.door = Door(data[line], data[line + 1])
        line += doorDataSize
        self.allMovableObjects.append(self.door)
        self.fakedoor = Door(self.platforms[0][0] + 10, self.platforms[0][1])
        self.allMovableObjects.append(self.fakedoor)

        # Generate fences
        if data[line] != 0:
            self.generateFences()
            self.autoscroll = False
        elif r.randint(0, 3) == 0:
            self.autoscroll = True
        line += 1

        # Generate foliage
        if data[line] != 0:
            self.generateFoliage()
        line += 1

        # Obtain the seed used to generate the saved level
        self.seed = data[line]

        # Load the level hint
        self.loadLevelHint(level)

        # Finalize the level details
        self.finalizeLevel(self.farthestPlatform)

    # --------------------------------------------------------------------------------------------------------------

    def saveLevel(self, level):
        # Open file for writing
        fileName = 'levels/lvl_' + str(level) + self.levelExtension
        permissions = 'w'
        dataFile = open(fileName, permissions)

        # Add a warning to the data file
        dataFile.write('Position Data For Level ' + str(level) + ' - DO NOT MODIFY THIS FILE!\n')

        # Save data in the same order as the "loadLevel" method reads it
        blankLine = str(self.defaultValue) + '\n'
        maxNumPlatforms = 25
        platformDataSize = 3
        for i in xrange(maxNumPlatforms):
            if i < len(self.platforms):
                dataFile.write(str(self.platforms[i].x) + '\n' + str(self.platforms[i].y) + '\n' +
                               str(self.platforms[i].width) + '\n')
            else:
                dataFile.write(blankLine * platformDataSize)
        poolDataSize = 4
        if self.pool:
            dataFile.write(str(self.pool.x) + '\n' + str(self.pool.y) + '\n' + str(self.pool.width) +
                           '\n' + str(self.pool.height) + '\n')
        else:
            dataFile.write(blankLine * poolDataSize)
        maxNumBlocks = 25
        blockDataSize = 3
        for i in xrange(maxNumBlocks):
            if i < len(self.blocks):
                dataFile.write(str(self.blocks[i].x) + '\n' + str(self.blocks[i].y) + '\n')
                if self.blocks[i].form == 'coin':
                    dataFile.write('0\n')
                else:
                    dataFile.write('1\n')
            else:
                dataFile.write(blankLine * blockDataSize)
        if self.icicles:
            dataFile.write(str(self.platforms[len(self.platforms) - 1].x) + '\n' +
                           str(self.platforms[len(self.platforms) - 1].y) + '\n' +
                           str(self.platforms[len(self.platforms) - 1].width) + '\n')
        else:
            dataFile.write(blankLine * 3)
        dataFile.write(str(self.door.x) + '\n' + str(self.door.y + self.door.height + self.door.topBlankSpace) + '\n')
        if self.autoscroll:
            dataFile.write('0\n')
        else:
            dataFile.write('1\n')
        dataFile.write('1\n' + str(self.seed))

    # --------------------------------------------------------------------------------------------------------------

    def loopThroughLevel(self, lvl=0):
        if lvl == 0:
            self.gameStart = False
            pygame.mixer.music.load(self.themeSong)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)
            self.setupBgrd(self.backgroundTheme)
            while self.currLevel == 0:
                self.drawTitleScreen()
        else:
            while self.currLevel == lvl:
                shouldAdvanceLevel = self.updateAll()
                if shouldAdvanceLevel:
                    self.printText('Loading Level ' + str(self.currLevel + 1), self.medFont, white,
                                   (50, self.screenH - 50))
                    self.currLevel += 1
                    self.redrawAndProceedTick(self.mousex_hover, self.mousey_hover)
                    pygame.time.wait(self.levelDelay)
                    self.loadLevel(self.currLevel, self.theme)

    # --------------------------------------------------------------------------------------------------------------

    def executeLevels(self, finalLevel=2):
        for level in xrange(finalLevel + 1):
            self.loopThroughLevel(level)

    # --------------------------------------------------------------------------------------------------------------

    def executeGameLoop(self):
        self.executeLevels(self.numLevels)
