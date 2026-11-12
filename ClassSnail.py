import pygame

from Config import *
from ClassSpriteSheet import SpriteSheet


snailWalkSprites = [(frame * 48, 0, 48, 32) for frame in range(8)]
snailHideSprites = [(frame * 48, 0, 48, 32) for frame in range(8)]
snailDeadSprites = [(frame * 48, 0, 48, 32) for frame in range(8)]


class Snail(pygame.sprite.Sprite):
    def __init__(self, position, moveRight):
        super().__init__()

        self.walkSpriteSheet = SpriteSheet(
            SPRITESHEET_PATH + "Mob/Snail/walk-Sheet.png", snailWalkSprites
        )
        self.hideSpriteSheet = SpriteSheet(
            SPRITESHEET_PATH + "Mob/Snail/Hide-Sheet.png", snailHideSprites
        )
        self.deadSpriteSheet = SpriteSheet(
            SPRITESHEET_PATH + "Mob/Snail/Dead-Sheet.png", snailDeadSprites
        )

        self.movingRight = moveRight
        self.currentState = "HIDE"
        self.animationIndex = 0
        self.animationSpeed = ANIMSPEED_SNAIL_HIDE
        self.currentAnimation = self.hideSpriteSheet.getSprites(
            flipped=moveRight
        )
        self.image = self.currentAnimation[0]
        self.rect = self.image.get_rect(bottomleft=position)
        self.xPosition = float(self.rect.x)
        self.isChasing = False

    def update(self, level, deltaTime=1 / 60):
        frameScale = deltaTime * 60
        hero = level.hero.sprite
        distanceToHero = hero.rect.centerx - self.rect.centerx

        if self.currentState == "DYING":
            self.selectAnimation()
            self.animationIndex += self.animationSpeed * frameScale
            if self.animationIndex >= len(self.currentAnimation):
                self.kill()
                return
            self.image = self.currentAnimation[int(self.animationIndex)]
            return

        if self.currentState == "HIDE":
            if (
                hero.onGround
                and level.areOnSamePlatform(
                    hero.rect.centerx,
                    hero.yPos,
                    self.rect.centerx,
                    self.rect.bottom,
                )
                and
                abs(distanceToHero) <= SNAIL_WAKE_RANGE
                and abs(hero.rect.centery - self.rect.centery) <= SNAIL_WAKE_RANGE
            ):
                self.isChasing = True
                self.currentState = "RUN"
                self.animationIndex = 0
            else:
                self.animationIndex = min(
                    self.animationIndex + self.animationSpeed * frameScale,
                    len(self.currentAnimation) - 1,
                )
                self.image = self.currentAnimation[int(self.animationIndex)]
                return

        if hero.currentState == "DIE":
            self.currentState = "RUN"
            speed = SPEED_SNAIL_CHASE
        else:
            if self.isChasing:
                if distanceToHero != 0:
                    self.movingRight = distanceToHero > 0
                self.currentState = (
                    "ATTACK" if abs(distanceToHero) <= 42 else "RUN"
                )
                speed = SPEED_SNAIL_CHASE
            else:
                self.currentState = "WALK"
                speed = SPEED_SNAIL_WALK

        leadingFootX = self.rect.right if self.movingRight else self.rect.left - 1
        if not level.hasPlatformAt(leadingFootX, self.rect.bottom):
            self.movingRight = not self.movingRight

        direction = 1 if self.movingRight else -1
        self.xPosition += direction * speed * frameScale
        self.rect.x = round(self.xPosition)
        if self.rect.left <= 0:
            self.rect.left = 0
            self.xPosition = float(self.rect.x)
            self.movingRight = True
        elif self.rect.right >= level.worldWidth:
            self.rect.right = level.worldWidth
            self.xPosition = float(self.rect.x)
            self.movingRight = False

        self.selectAnimation()
        self.animationIndex += self.animationSpeed * frameScale
        if self.animationIndex >= len(self.currentAnimation):
            self.animationIndex = 0
        self.image = self.currentAnimation[int(self.animationIndex)]

    def selectAnimation(self):
        if self.currentState == "DYING":
            self.currentAnimation = self.deadSpriteSheet.getSprites(
                flipped=self.movingRight
            )
            self.animationSpeed = ANIMSPEED_SNAIL_DEAD
        elif self.currentState == "HIDE":
            self.currentAnimation = self.hideSpriteSheet.getSprites(
                flipped=self.movingRight
            )
            self.animationSpeed = ANIMSPEED_SNAIL_HIDE
        else:
            self.currentAnimation = self.walkSpriteSheet.getSprites(
                flipped=self.movingRight
            )
            self.animationSpeed = ANIMSPEED_SNAIL_WALK

    def die(self):
        if self.currentState != "DYING":
            self.currentState = "DYING"
            self.animationIndex = 0
