import pygame
from Config import *


class SpriteSheet():

    def __init__(self, spritSheetPath, spritePositions):
        image = pygame.image.load(spritSheetPath).convert_alpha()
        self.sprites = []
        self.spritesFlipped = []
        for position in spritePositions:
            sprite = image.subsurface(pygame.Rect(position))
            self.sprites.append(sprite)
            sprite = pygame.transform.flip(sprite, True, False)
            self.spritesFlipped.append(sprite)



    def getSprites(self, flipped):
        if flipped  == True:
            return self.spritesFlipped
        else:
            return self.sprites
