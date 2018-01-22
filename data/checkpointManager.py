# coding=utf-8
import pygame

class CheckpointManager(object):

    def __init__(self, platforms, blocks, character):
        # Initialize lists for the co-ordinates for every checkpoint and the direction needed to get there
        self.checkpointsLeft, self.checkpointsRight = [] * 2
        self.checkpointDirectionsL, self.checkpointDirectionsR = [] * 2
        self.indexLevel(platforms, blocks, character)

    def indexLevel(self, platforms, blocks, char):
        # This method obtains all of the level information necessary to pathfind

        # Gather information about the character
        maxW = char.maxJumpLength
        maxH = char.maxJumpWidth
        charRect = pygame.Rect(char.x, char.y, char.width, char.height)
        charW = char.width

        # Fill in the checkpoint coordinates and directions
        for platform in platforms:
            self.checkpointsLeft.append(platform.x + 5)
            self.checkpointsRight.append(platform.x + platform.width - charW - 5)
