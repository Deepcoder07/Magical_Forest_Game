import math

import pygame


class Collectible(pygame.sprite.Sprite):
    def __init__(self, position, image, itemType):
        super().__init__()
        if image is None:
            raise ValueError(f"Missing TMX image for collectible: {itemType}")

        self.image = image
        self.rect = self.image.get_rect(topleft=position)
        self.itemType = itemType
        self.baseY = self.rect.y
        self.elapsed = 0.0

    def update(self, deltaTime):
        self.elapsed += deltaTime
        self.rect.y = self.baseY + round(math.sin(self.elapsed * 4) * 3)
