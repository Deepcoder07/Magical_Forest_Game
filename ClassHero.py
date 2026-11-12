from pathlib import Path

import pygame

from ClassBee import Bee
from ClassSpriteSheet import SpriteSheet
from Config import *

HERO_FOOTSTEP_DISTANCE = 48


def gridSprites(
    columns,
    rows,
    frameWidth=128,
    frameHeight=64,
    frameCount=None,
):
    frameCount = columns * rows if frameCount is None else frameCount
    return [
        (
            (frame % columns) * frameWidth,
            (frame // columns) * frameHeight,
            frameWidth,
            frameHeight,
        )
        for frame in range(frameCount)
    ]

class Hero(pygame.sprite.Sprite):
    ACTION_STATES = {
        'ATTACK',
        'AIR_ATTACK',
        'CROUCH_ATTACK',
        'ROLL',
        'SLIDE',
    }

    def __init__(self, position, faceRight):
        super().__init__()

        if pygame.mixer.get_init() is None:
            pygame.mixer.init()
        jumpSoundPath = (
            Path(__file__).resolve().parent
            / "PyGameDev-main"
            / "Assets"
            / "Sound"
            / "SoundFX"
            / "KronBits"
            / "Retro Jump Classic 08.wav"
        )
        self.jumpSound = pygame.mixer.Sound(str(jumpSoundPath))
        soundEffectsPath = (
            Path(__file__).resolve().parent
            / "PyGameDev-main"
            / "Assets"
            / "Sound"
            / "SoundFX"
            / "KronBits"
        )
        self.footstepSound = pygame.mixer.Sound(
            str(soundEffectsPath / "step grass.flac")
        )
        self.attackSound = pygame.mixer.Sound(str(soundEffectsPath / "metal sword hit.wav"))
        self.waveSound = pygame.mixer.Sound(str(soundEffectsPath / "fast sword whoosh.wav"))
        self.gameOverMusicPath = (
            Path(__file__).resolve().parent
            / "PyGameDev-main"
            / "Assets"
            / "Sound"
            / "Music"
            / "Alexander Ehlers"
            / "game-lose.mp3"
        )

        knightPath = Path(SPRITESHEET_PATH) / "Character" / "Knight"
        animationSpecs = {
            "AIR_ATTACK": ("Attack_air/attack_from_air.png", 2, 4, 8),
            "CLIMB": ("Climb/Climb.png", 2, 3, 6),
            "CROUCH_ATTACK": ("Crouch_attack/crouch_attacks.png", 2, 4, 7),
            "CROUCH_IDLE": ("Crouch_idle/crouch_idle.png", 2, 4, 8),
            "DIE": ("Death/Death.png", 2, 2, 4),
            "HANGING": ("Hanging/Hanging.png", 2, 4, 8),
            "HEALTH": ("Health/Health.png", 2, 4, 8),
            "HURT": ("Hurt/Hurt.png", 2, 2, 3),
            "IDLE": ("Idle/Idle.png", 2, 4, 8),
            "JUMP": ("Jump/Jump.png", 2, 4, 8),
            "PRAY": ("Pray/Pray.png", 4, 3, 12),
            "ROLL": ("Roll/Roll.png", 2, 2, 4),
            "RUN": ("Run/Run.png", 2, 4, 8),
            "SLIDE": ("Slide/Slide.png", 4, 3, 10),
        }
        self.spriteSheets = {
            state: SpriteSheet(
                str(knightPath / relativePath),
                gridSprites(columns, rows, frameCount=frameCount),
            )
            for state, (relativePath, columns, rows, frameCount)
            in animationSpecs.items()
        }
        attackPath = str(knightPath / "Attack" / "Attacks.png")
        self.attackSpriteSheets = [
            SpriteSheet(
                attackPath,
                [
                    (column * 128, row * 64, 128, 64)
                    for column in range(8)
                ],
            )
            for row in range(5)
        ]
        self.spriteSheets.update(
            {
                f"ATTACK_{index + 1}": spriteSheet
                for index, spriteSheet in enumerate(self.attackSpriteSheets)
            }
        )
        self.attackVariant = -1

        self.animationIndex = 0
        self.facingRight = faceRight
        self.currentState = 'IDLE'
        self.previousState = 'IDLE'
        self.xDir = 0
        self.jumpWasPressed = False
        self.attackWasPressed = False
        self.rollWasPressed = False
        self.actionDirection = 0
        self.footstepDistance = 0.0
        self.jumpsUsed = 0
        self.speed = SPEED_HERO
        self.xPos = position[0]
        self.yPos = position[1]
        self.yVelocity = 0
        self.onGround = True
        self.invulnerabilityTimer = 0.0
        self.invulnerabilityElapsed = 0.0
        self.deathFlashElapsed = None
        self.deathAnimationFinished = False
        self.glowSurface = pygame.Surface((96, 96), pygame.SRCALPHA)
        pygame.draw.circle(self.glowSurface, (255, 220, 70, 24), (48, 48), 46)
        pygame.draw.circle(self.glowSurface, (255, 220, 70, 34), (48, 48), 34)
        pygame.draw.circle(self.glowSurface, (255, 244, 170, 45), (48, 48), 22)
        self.image = self.getSprites()[0]
        self.rect = pygame.Rect(0, 0, 44, 52)
        self.rect.midbottom = (round(self.xPos), round(self.yPos))


    def update(self, level, deltaTime=1 / 60):
        frameScale = deltaTime * 60
        if self.currentState == 'DIE' and self.deathAnimationFinished:
            self.deathFlashElapsed += deltaTime

        if self.invulnerabilityTimer > 0:
            self.invulnerabilityTimer = max(
                0, self.invulnerabilityTimer - deltaTime
            )
            self.invulnerabilityElapsed += deltaTime

        self.previousState = self.currentState
        self.xDir = 0

        keys = pygame.key.get_pressed()
        jumpPressed = keys[pygame.K_UP] or keys[pygame.K_w]
        movingLeft = keys[pygame.K_LEFT] or keys[pygame.K_a]
        movingRight = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        crouchPressed = keys[pygame.K_DOWN] or keys[pygame.K_s]
        attackPressed = keys[pygame.K_SPACE]
        rollPressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        jumpStarted = jumpPressed and not self.jumpWasPressed
        attackStarted = attackPressed and not self.attackWasPressed
        rollStarted = rollPressed and not self.rollWasPressed
        self.jumpWasPressed = jumpPressed
        self.attackWasPressed = attackPressed
        self.rollWasPressed = rollPressed

        if self.currentState == 'DIE':
            self.xDir = 0
        elif self.currentState in self.ACTION_STATES:
            if self.currentState == 'ROLL':
                self.xDir = self.actionDirection
            elif self.currentState == 'SLIDE':
                self.xDir = self.actionDirection
            elif self.currentState == 'AIR_ATTACK':
                self.xDir = (
                    -1 if movingLeft
                    else 1 if movingRight
                    else 0
                )
                if self.xDir:
                    self.facingRight = self.xDir > 0
        else:
            if jumpStarted:
                if self.onGround:
                    self.yVelocity = -JUMP_STRENGTH_HERO
                    self.onGround = False
                    self.jumpsUsed = 1
                    self.jumpSound.play()
                elif self.jumpsUsed < 2:
                    self.yVelocity = -JUMP_STRENGTH_HERO
                    self.jumpsUsed = 2
                    self.jumpSound.play()

            crouching = self.onGround and crouchPressed
            if attackStarted:
                if crouching:
                    self.currentState = 'CROUCH_ATTACK'
                elif self.onGround:
                    self.currentState = 'ATTACK'
                    self.attackVariant = (
                        self.attackVariant + 1
                    ) % len(self.attackSpriteSheets)
                else:
                    self.currentState = 'AIR_ATTACK'
                self.waveSound.play()
            elif rollStarted and self.onGround:
                self.currentState = 'ROLL'
                self.actionDirection = (
                    -1 if movingLeft
                    else 1 if movingRight
                    else 1 if self.facingRight
                    else -1
                )
                self.xDir = self.actionDirection
            elif crouching and (movingLeft or movingRight):
                self.currentState = 'SLIDE'
                self.actionDirection = -1 if movingLeft else 1
                self.facingRight = self.actionDirection > 0
                self.xDir = self.actionDirection
            elif crouching:
                self.currentState = 'CROUCH_IDLE'
            elif movingLeft:
                self.xDir = -1
                self.facingRight = False
                self.currentState = 'RUN' if self.onGround else 'JUMP'
            elif movingRight:
                self.xDir = 1
                self.facingRight = True
                self.currentState = 'RUN' if self.onGround else 'JUMP'
            elif not self.onGround:
                self.currentState = 'JUMP'
            else:
                self.currentState = 'IDLE'

        self.selectAnimation()
        if self.previousState != self.currentState:
            self.animationIndex = 0

        self.image = self.currentAnimation[int(self.animationIndex)]
        hitboxSizes = {
            'ATTACK': (88, 64),
            'AIR_ATTACK': (88, 64),
            'CROUCH_ATTACK': (88, 64),
            'CROUCH_IDLE': (44, 40),
            'DIE': (64, 56),
            'IDLE': (44, 52),
            'JUMP': (40, 48),
            'RUN': (40, 48),
            'ROLL': (40, 40),
            'SLIDE': (48, 32),
        }
        self.rect.size = hitboxSizes.get(self.currentState, (44, 52))
        self.rect.midbottom = (round(self.xPos), round(self.yPos))

        actionFinished = False
        self.animationIndex += self.animationSpeed * frameScale
        if self.animationIndex >= len(self.currentAnimation):
            if self.currentState == 'DIE':
                self.animationIndex = len(self.currentAnimation) - 1
                self.deathAnimationFinished = True
            elif self.currentState == 'JUMP':
                self.animationIndex = len(self.currentAnimation) - 1
            elif self.currentState in ('IDLE', 'RUN', 'CROUCH_IDLE'):
                self.animationIndex = 0
            else:
                self.animationIndex = 0
                actionFinished = True

        self.moveHorizontal(level, frameScale)
        self.moveVertical(level, frameScale)

        if self.invulnerabilityTimer <= 0:
            self.checkEnemyCollisions(level.enemies)
        if actionFinished and self.currentState in self.ACTION_STATES:
            self.currentState = 'IDLE'
            self.actionDirection = 0

    def selectAnimation(self):
        self.animationSpeed = ANIMSPEED_HERO_DEFAULT
        if self.currentState in ('IDLE', 'CROUCH_IDLE'):
            self.animationSpeed = ANIMSPEED_HERO_IDLE

        if self.currentState == 'ATTACK':
            spriteSheet = self.attackSpriteSheets[self.attackVariant]
            self.currentAnimation = spriteSheet.getSprites(
                flipped=not self.facingRight
            )
        else:
            self.currentAnimation = self.getSprites(
                flipped=not self.facingRight
            )

    def getSprites(self, flipped=False):
        spriteSheet = self.spriteSheets[self.currentState]
        return spriteSheet.getSprites(flipped=flipped)

    def moveHorizontal(self, level, frameScale=1):
        speed = self.speed
        if self.currentState == 'ROLL':
            speed *= 1.8
        elif self.currentState == 'SLIDE':
            speed *= 1.4
        previousX = self.xPos
        self.xPos += self.xDir * speed * frameScale
        self.rect.centerx = round(self.xPos)

        if self.rect.left < 0:
            self.rect.left = 0
            self.xPos = self.rect.centerx
        elif self.rect.right > level.worldWidth:
            self.rect.right = level.worldWidth
            self.xPos = self.rect.centerx

        if self.currentState == 'RUN' and self.onGround and self.xDir:
            self.footstepDistance += abs(self.xPos - previousX)
            if self.footstepDistance >= HERO_FOOTSTEP_DISTANCE:
                self.footstepSound.play()
                self.footstepDistance %= HERO_FOOTSTEP_DISTANCE
        else:
            self.footstepDistance = 0.0

    def moveVertical(self, level, frameScale=1):
        if self.onGround and not level.hasPlatformAt(self.rect.centerx, self.yPos):
            self.onGround = False

        if not self.onGround:
            previousY = self.yPos
            self.yVelocity += GRAVITY * frameScale
            self.yPos += self.yVelocity * frameScale
            platform = level.getLandingPlatform(
                self.rect.centerx, previousY, self.yPos
            )
            if platform is not None:
                self.yPos = platform.top
                self.yVelocity = 0
                self.onGround = True
                self.jumpsUsed = 0

        self.rect.bottom = int(self.yPos)
        if self.currentState != 'DIE' and self.yPos >= level.mapHeight:
            self.die()

    def die(self):
        if self.currentState != 'DIE':
            self.currentState = 'DIE'
            self.animationIndex = 0
            self.deathFlashElapsed = 0.0
            self.deathAnimationFinished = False
            self.actionDirection = 0
            self.selectAnimation()
            self.image = self.currentAnimation[0]

    def revive(self, position):
        self.currentState = 'IDLE'
        self.animationIndex = 0
        self.xPos, self.yPos = position
        self.yVelocity = 0
        self.xDir = 0
        self.footstepDistance = 0.0
        self.onGround = True
        self.jumpWasPressed = False
        self.attackWasPressed = False
        self.rollWasPressed = False
        self.actionDirection = 0
        self.jumpsUsed = 0
        self.invulnerabilityTimer = HERO_RESPAWN_FLASH_DURATION
        self.invulnerabilityElapsed = 0.0
        self.deathFlashElapsed = None
        self.deathAnimationFinished = False
        self.image = self.getSprites(flipped=not self.facingRight)[0]
        self.rect = pygame.Rect(0, 0, 44, 52)
        self.rect.midbottom = (round(self.xPos), round(self.yPos))

    def draw(self, surface, cameraX=0, cameraY=0):
        drawRect = self.image.get_rect(midbottom=self.rect.midbottom).move(
            -cameraX, -cameraY
        )
        if self.currentState == 'DIE':
            if not self.deathAnimationFinished:
                surface.blit(self.image, drawRect)
                return
            if self.deathFlashElapsed >= HERO_DEATH_FLASH_DURATION:
                return
            if int(self.deathFlashElapsed * 12) % 2:
                return
            surface.blit(self.image, drawRect)
            return

        if self.invulnerabilityTimer > 0:
            glowRect = self.glowSurface.get_rect(center=drawRect.center)
            surface.blit(self.glowSurface, glowRect)
            if int(self.invulnerabilityElapsed * 10) % 2 == 0:
                flashingImage = self.image.copy()
                flashingImage.set_alpha(90)
                surface.blit(flashingImage, drawRect)
                return
        surface.blit(self.image, drawRect)

    def checkEnemyCollisions(self, enemies):
        collidedSprites = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in collidedSprites:
            if self.currentState in ('ATTACK', 'AIR_ATTACK', 'CROUCH_ATTACK'):
                enemyIsInFront = (
                    enemy.rect.centerx > self.xPos
                    if self.facingRight
                    else enemy.rect.centerx < self.xPos
                )
                if enemy.currentState != 'DYING' and enemyIsInFront:
                    self.attackSound.play()
                    enemy.die()
            elif enemy.currentState == 'ATTACK':
                if isinstance(enemy, Bee) or self.onGround:
                    self.die()
