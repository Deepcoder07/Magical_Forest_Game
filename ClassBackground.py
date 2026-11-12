import pygame
from Config import *


class Background:

    

    def __init__(self, imagePath=None):
        if imagePath is None:
            imagePath = SPRITESHEET_PATH + "Background/Background.png"
        self.skyImage = pygame.image.load(str(imagePath)).convert()
        self.skyImage = pygame.transform.scale(self.skyImage, (WINDOW_WIDTH, WINDOW_HEIGHT))

    def draw(self, displaySurface):
        displaySurface.blit(self.skyImage, (0, 0))