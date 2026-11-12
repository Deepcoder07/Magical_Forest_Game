import pygame

from Config import *
from ClassSpriteSheet import SpriteSheet


boarIdleSprites = [(frame * 48, 0, 48, 32) for frame in range(4)]
boarWalkSprites = [(frame * 48, 0, 48, 32) for frame in range(6)]
boarRunSprites = [(frame * 48, 0, 48, 32) for frame in range(6)]
boarHitSprites = [(frame * 48, 0, 48, 32) for frame in range(4)]


class Boar(pygame.sprite.Sprite):
    def __init__(self, position, moveRight):
        super().__init__()

        self.idleSpriteSheet = SpriteSheet(
            SPRITESHEET_PATH + "Mob/Boar/Idle/Idle-Sheet.png", boarIdleSprites
        )
        self.walkSpriteSheet = SpriteSheet(
            SPRITESHEET_PATH + "Mob/Boar/Walk/Walk-Base-Sheet.png", boarWalkSprites
        )
        self.runSpriteSheet = SpriteSheet(
            SPRITESHEET_PATH + "Mob/Boar/Run/Run-Sheet.png", boarRunSprites
        )
        self.hitSpriteSheet = SpriteSheet(
            SPRITESHEET_PATH + "Mob/Boar/Hit-Vanish/Hit-Sheet.png", boarHitSprites
        )

        self.movingRight = moveRight
        self.currentState = "WALK"
        self.animationIndex = 0
        self.image = self.walkSpriteSheet.getSprites(moveRight)[0]
        self.rect = self.image.get_rect(bottomleft=position)
        self.speed = SPEED_BOAR_WALK
        self.isChasing = False

    def update(self, level, deltaTime=1 / 60):
        frameScale = deltaTime * 60
        hero = level.hero.sprite
        distanceToHero = hero.rect.centerx - self.rect.centerx
        seesHero = (
            hero.onGround
            and level.areOnSamePlatform(
                hero.rect.centerx,
                hero.yPos,
                self.rect.centerx,
                self.rect.bottom,
            )
            and
            abs(distanceToHero) <= BOAR_SIGHT_RANGE
            and abs(hero.rect.centery - self.rect.centery) <= BOAR_SIGHT_RANGE
        )

        if self.currentState == "DYING":
            self.selectAnimation()
            self.animationIndex += self.animationSpeed * frameScale
            if self.animationIndex >= len(self.currentAnimation):
                self.kill()
                return
            self.image = self.currentAnimation[int(self.animationIndex)]
            return

        if hero.currentState == "DIE":
            self.currentState = "RUN"
            self.speed = SPEED_BOAR_RUN
        else:
            if seesHero:
                self.isChasing = True

            if self.isChasing:
                if hero.onGround and distanceToHero != 0:
                    self.movingRight = distanceToHero > 0
                self.currentState = "ATTACK" if abs(distanceToHero) <= 42 else "RUN"
                self.speed = SPEED_BOAR_RUN
            else:
                self.currentState = "WALK"
                self.speed = SPEED_BOAR_WALK
                if self.rect.left <= 0:
                    self.movingRight = True
                elif self.rect.right >= level.worldWidth:
                    self.movingRight = False

        stepDistance = max(1, round(self.speed * frameScale))
        leadingFootX = (
            self.rect.right + stepDistance
            if self.movingRight
            else self.rect.left - stepDistance
        )
        if not level.hasPlatformAt(leadingFootX, self.rect.bottom):
            self.movingRight = not self.movingRight
            if self.isChasing:
                self.currentState = "WALK"
                self.speed = SPEED_BOAR_WALK

        direction = 1 if self.movingRight else -1
        self.rect.x += round(direction * self.speed * frameScale)
        if not self.movingRight and self.rect.left <= 0:
            self.rect.left = 0
            self.movingRight = True
        elif self.movingRight and self.rect.right >= level.worldWidth:
            self.rect.right = level.worldWidth
            self.movingRight = False
        self.selectAnimation()

        self.animationIndex += self.animationSpeed * frameScale
        if self.animationIndex >= len(self.currentAnimation):
            self.animationIndex = 0
        self.image = self.currentAnimation[int(self.animationIndex)]

    def selectAnimation(self):
        if self.currentState == "IDLE":
            self.currentAnimation = self.idleSpriteSheet.getSprites(
                flipped=self.movingRight
            )
            self.animationSpeed = ANIMSPEED_BOAR_IDLE
        elif self.currentState == "WALK":
            self.currentAnimation = self.walkSpriteSheet.getSprites(
                flipped=self.movingRight
            )
            self.animationSpeed = ANIMSPEED_BOAR_WALK
        elif self.currentState in ("RUN", "ATTACK"):
            self.currentAnimation = self.runSpriteSheet.getSprites(
                flipped=self.movingRight
            )
            self.animationSpeed = ANIMSPEED_BOAR_RUN
        else:
            self.currentAnimation = self.hitSpriteSheet.getSprites(
                flipped=self.movingRight
            )
            self.animationSpeed = ANIMSPEED_BOAR_HIT

    def die(self):
        if self.currentState != "DYING":
            self.currentState = "DYING"
            self.animationIndex = 0
