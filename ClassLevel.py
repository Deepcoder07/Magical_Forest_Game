from pathlib import Path

import pygame
from pytmx.util_pygame import load_pygame
from Config import *
from ClassHero import Hero
from ClassBee import Bee
from ClassBoar import Boar
from ClassSnail import Snail
from ClassBackground import Background
from ClassCollectible import Collectible
from ClassHUD import HUD


BACKGROUND_MUSIC_TRACKS = (
    ("Warped", "Alexander Ehlers - Warped.mp3"),
    ("Fantasy Adventure", "alex-morgan-fantasy-adventure-quest-537478.mp3"),
    ("Fun Retro Game", "desifreemusic-fun-retro-game-background-music-587956.mp3"),
    ("RPG Battle", "nickpanek-rpg-battle-chiptune-video-game-music-346666.mp3"),
    ("Treasure Hunt", "nickpanek-treasure-hunt-8-bit-chiptune-adventure-music-357568.mp3"),
    ("Arcade Neon", "slimeyfox-arcade-games-neon-munch-480827.mp3"),
    ("Last Credit", "slimeyfox-last-credit-remaining-485095.mp3"),
)

class Level():
    def __init__(
        self,
        displaySurface,
        levelPath=LEVEL1_PATH,
        hudIcons=None,
        coinsCollected=0,
        extraLives=0,
        audioMuted=False,
        backgroundMusicPlaying=True,
        backgroundMusicIndex=0,
        backgroundPath=None,
    ):
        levelPath = Path(__file__).resolve().parent / levelPath
        self.levelData = load_pygame(str(levelPath))
        self.worldWidth = self.levelData.width * self.levelData.tilewidth
        self.mapHeight = self.levelData.height * self.levelData.tileheight
        self.cameraX = 0
        self.platformRects = [
            pygame.Rect(
                x * self.levelData.tilewidth,
                y * self.levelData.tileheight,
                self.levelData.tilewidth,
                self.levelData.tileheight,
            )
            for x, y, _ in self.levelData.get_layer_by_name("Platforms").tiles()
        ]

        mapSize = (self.worldWidth, self.mapHeight)
        self.mapBackground = pygame.Surface(mapSize, pygame.SRCALPHA)
        self.mapForeground = pygame.Surface(mapSize, pygame.SRCALPHA)
        for layerName in (
            "Background4",
            "Background3",
            "Background2",
            "Background1",
            "Platforms",
        ):
            self.drawMapLayer(
                self.mapBackground, self.getMapLayer(layerName)
            )
        self.drawMapLayer(
            self.mapForeground, self.getMapLayer("Foreground")
        )
        self.background = Background(backgroundPath)

        musicDirectory = (
            Path(__file__).resolve().parent
            / "PyGameDev-main"
            / "Assets"
            / "Sound"
            / "Music"
            / "Alexander Ehlers"
        )
        self.backgroundMusicTracks = tuple(
            (name, musicDirectory / fileName)
            for name, fileName in BACKGROUND_MUSIC_TRACKS
        )
        if not 0 <= backgroundMusicIndex < len(self.backgroundMusicTracks):
            raise ValueError("backgroundMusicIndex is outside the available tracks")
        self.backgroundMusicIndex = backgroundMusicIndex
        self.backgroundMusicPath = self.backgroundMusicTracks[
            self.backgroundMusicIndex
        ][1]
        coinCollectSoundPath = (
            Path(__file__).resolve().parent
            / "PyGameDev-main"
            / "Assets"
            / "Sound"
            / "SoundFX"
            / "KronBits"
            / "Retro PickUp Coin 07.wav"
        )
        self.coinCollectSound = pygame.mixer.Sound(str(coinCollectSoundPath))

        self.paused = False
        self.audioMuted = audioMuted
        self.backgroundMusicPlaying = backgroundMusicPlaying
        if hudIcons is None:
            coinObject = next(
                (obj for obj in self.levelData.objects if obj.name == "Coin"),
                None,
            )
            potionObject = next(
                (obj for obj in self.levelData.objects if obj.name == "Potion"),
                None,
            )
            if coinObject is None or potionObject is None:
                raise ValueError(
                    "TMX level must include coin and potion objects for the HUD"
                )
            hudIcons = (coinObject.image, potionObject.image)
        self.hud = HUD(
            *hudIcons,
            musicTrackNames=tuple(
                name for name, _ in self.backgroundMusicTracks
            ),
        )
        self.reset()
        self.coinsCollected = coinsCollected
        self.extraLives = extraLives

        self.displaySurface = displaySurface
        fontPath = (
            Path(__file__).resolve().parent
            / "PyGameDev-main"
            / "Assets"
            / "Fonts"
            / "IMMORTAL.ttf"
        )
        self.gameOverFont = pygame.font.Font(str(fontPath), 72)
        self.gameOverHintFont = pygame.font.Font(None, 28)
        buttonWidth = 150
        buttonGap = 16
        buttonLeft = (WINDOW_WIDTH - buttonWidth * 2 - buttonGap) // 2
        buttonTop = WINDOW_HEIGHT // 2 + 70
        self.gameOverRestartButton = pygame.Rect(
            buttonLeft, buttonTop, buttonWidth, 48
        )
        self.gameOverQuitButton = pygame.Rect(
            buttonLeft + buttonWidth + buttonGap,
            buttonTop,
            buttonWidth,
            48,
        )

    def reset(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self.cameraX = 0
        self.hero = pygame.sprite.GroupSingle()
        self.bees = pygame.sprite.Group()
        self.boars = pygame.sprite.Group()
        self.snails = pygame.sprite.Group()
        self.collectibles = pygame.sprite.Group()
        self.animatedEnemies = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.coinsCollected = 0
        self.extraLives = 0
        self.gameOverMusicPlaying = False
        self.respawnTimer = None

        playerSpawn = next(
            (obj for obj in self.levelData.objects if obj.name == "PlayerRight"),
            None,
        )
        if playerSpawn is None:
            raise ValueError("TMX level is missing a PlayerRight spawn object")

        heroX = playerSpawn.x + playerSpawn.width / 2
        heroGroundY = self.findGroundY(
            heroX, playerSpawn.y + playerSpawn.height
        )
        self.playerSpawnPosition = (heroX, heroGroundY)
        self.hero.add(Hero((heroX, heroGroundY), faceRight=True))
        self._applyAudioSetting()

        for obj in self.levelData.objects:
            if obj.name in ("Coin", "Potion"):
                self.collectibles.add(
                    Collectible(
                        (round(obj.x), round(obj.y)),
                        obj.image,
                        obj.name,
                    )
                )
            elif obj.name in ("BeeRight", "BeeLeft"):
                self.bees.add(
                    Bee(
                        (obj.x, obj.y + obj.height),
                        moveRight=obj.name == "BeeRight",
                    )
                )
            elif obj.name in ("BoarRight", "BoarLeft"):
                boarX = obj.x + obj.width / 2
                boarGroundY = self.findGroundY(
                    boarX, obj.y + obj.height
                )
                self.boars.add(
                    Boar(
                        (obj.x, boarGroundY),
                        moveRight=obj.name == "BoarRight",
                    )
                )
            elif obj.name in ("SnailRight", "SnailLeft") and len(self.snails) < 2:
                snailX = obj.x + obj.width / 2
                platformLeft, platformRight, snailGroundY = self.findPlatformSegment(
                    snailX, obj.y + obj.height
                )
                edgeMargin = 4
                snailX = max(
                    platformLeft + edgeMargin,
                    min(snailX, platformRight - edgeMargin),
                )
                self.snails.add(
                    Snail(
                        (snailX - 24, snailGroundY),
                        moveRight=obj.name == "SnailRight",
                    )
                )

        self.enemies.add(
            *self.bees.sprites(),
            *self.boars.sprites(),
            *self.snails.sprites(),
            *self.animatedEnemies.sprites(),
        )
        self.paused = False
        pygame.mixer.music.load(str(self.backgroundMusicPath))
        pygame.mixer.music.play(-1)
        self._applyAudioSetting()

    def handleEvent(self, event):
        if event.type == pygame.KEYDOWN:
            if self.isGameOver():
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return "quit"
                if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.reset()
                return None
            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                self._togglePause()
            elif event.key == pygame.K_r:
                self.reset()
            return None

        if (
            event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
            and self.isGameOver()
        ):
            if self.gameOverRestartButton.collidepoint(event.pos):
                self.reset()
                return None
            if self.gameOverQuitButton.collidepoint(event.pos):
                return "quit"

        action = self.hud.handleEvent(event)
        if action == "pause":
            if not self.isGameOver():
                self._togglePause()
        elif action == "restart":
            self.reset()
        elif action == "audio":
            self.audioMuted = not self.audioMuted
            self._applyAudioSetting()
        elif action == "music":
            self.backgroundMusicPlaying = not self.backgroundMusicPlaying
            self._syncBackgroundMusic()
        elif action == "previous_music":
            self._selectBackgroundMusic(
                (self.backgroundMusicIndex - 1)
                % len(self.backgroundMusicTracks)
            )
        elif action == "next_music":
            self._selectBackgroundMusic(
                (self.backgroundMusicIndex + 1)
                % len(self.backgroundMusicTracks)
            )
        elif isinstance(action, tuple) and action[0] == "select_music":
            self._selectBackgroundMusic(action[1])
        elif action == "home":
            return "home"
        elif action == "quit":
            return "quit"

    def isGameOver(self):
        return (
            self.hero.sprite.currentState == "DIE"
            and self.respawnTimer is None
            and self.extraLives == 0
        )

    def _togglePause(self):
        self.paused = not self.paused
        self._syncBackgroundMusic()

    def _syncBackgroundMusic(self):
        if self.paused or not self.backgroundMusicPlaying:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()

    def _selectBackgroundMusic(self, trackIndex):
        if trackIndex == self.backgroundMusicIndex:
            return
        self.backgroundMusicIndex = trackIndex
        self.backgroundMusicPath = self.backgroundMusicTracks[trackIndex][1]
        pygame.mixer.music.load(str(self.backgroundMusicPath))
        pygame.mixer.music.play(-1)
        self._applyAudioSetting()

    def _applyAudioSetting(self):
        volume = 0.0 if self.audioMuted else 1.0
        pygame.mixer.music.set_volume(volume)
        if hasattr(self, "hero") and self.hero.sprite is not None:
            for sound in (
                self.hero.sprite.jumpSound,
                self.hero.sprite.footstepSound,
                self.hero.sprite.attackSound,
                self.hero.sprite.waveSound,
                self.coinCollectSound,
            ):
                sound.set_volume(volume)
        self._syncBackgroundMusic()

    def update(self, deltaTime):
        self.hero.update(self, deltaTime)
        self.bees.update(self)
        self.boars.update(self, deltaTime)
        self.snails.update(self, deltaTime)
        self.collectibles.update(deltaTime)

        hero = self.hero.sprite
        collectedItems = (
            pygame.sprite.spritecollide(hero, self.collectibles, dokill=True)
            if hero.currentState != "DIE"
            else []
        )
        for item in collectedItems:
            if item.itemType == "Coin":
                self.coinsCollected += 1
                self.coinCollectSound.play()
            elif item.itemType == "Potion":
                self.extraLives += 1

        hero = self.hero.sprite
        if hero.currentState == "DIE":
            if self.respawnTimer is not None:
                self.respawnTimer = max(
                    0, self.respawnTimer - deltaTime
                )
                if self.respawnTimer <= 1e-6:
                    hero.revive(self.playerSpawnPosition)
                    self.respawnTimer = None
                    self.cameraX = 0
            elif self.extraLives > 0:
                self.extraLives -= 1
                self.respawnTimer = max(
                    0, HERO_RESPAWN_DELAY - deltaTime
                )
            elif not self.gameOverMusicPlaying:
                pygame.mixer.music.load(str(hero.gameOverMusicPath))
                pygame.mixer.music.play()
                self._applyAudioSetting()
                self.gameOverMusicPlaying = True

        self.cameraX = max(
            0,
            min(
                hero.rect.centerx - WINDOW_WIDTH // 2,
                self.worldWidth - WINDOW_WIDTH,
            ),
        )
        if hero.currentState != "DIE" and hero.rect.right >= self.worldWidth:
            return "next_level"
        return None

    def getMapLayer(self, layerName):
        layerAliases = {
            "Background4": ("Background4", "Background 4"),
            "Background3": ("Background3", "Background 3", "Baclground 3"),
            "Background2": ("Background2", "Background 2"),
            "Background1": ("Background1", "Background 1"),
            "Platforms": ("Platforms", "Platform"),
            "Foreground": ("Foreground",),
        }
        for candidate in layerAliases.get(layerName, (layerName,)):
            for layer in self.levelData.layers:
                if layer.name == candidate:
                    return layer
        raise ValueError(f"TMX level is missing the {layerName} layer")

    def drawMapLayer(self, target, layer):
        for x, y, image in layer.tiles():
            target.blit(
                image,
                (x * self.levelData.tilewidth, y * self.levelData.tileheight),
            )

    def findGroundY(self, xPosition, referenceY):
        groundHeights = [
            platform.top
            for platform in self.platformRects
            if platform.left <= xPosition < platform.right
            and abs(platform.top - referenceY) <= self.levelData.tileheight * 2
        ]
        if not groundHeights:
            raise ValueError(
                f"No platform found near map spawn at x={xPosition}, y={referenceY}"
            )
        return min(groundHeights, key=lambda height: abs(height - referenceY))

    def findPlatformSegment(self, xPosition, referenceY):
        platformsByHeight = {}
        for platform in self.platformRects:
            platformsByHeight.setdefault(platform.top, []).append(platform)

        segments = []
        for platformTop, platforms in platformsByHeight.items():
            platforms.sort(key=lambda platform: platform.left)
            segmentLeft = platforms[0].left
            segmentRight = platforms[0].right
            for platform in platforms[1:]:
                if platform.left <= segmentRight:
                    segmentRight = max(segmentRight, platform.right)
                else:
                    if segmentRight - segmentLeft >= 12:
                        segments.append((segmentLeft, segmentRight, platformTop))
                    segmentLeft = platform.left
                    segmentRight = platform.right
            if segmentRight - segmentLeft >= 12:
                segments.append((segmentLeft, segmentRight, platformTop))

        if not segments:
            raise ValueError(
                "TMX level has no platform wide enough for a snail patrol"
            )

        def spawnDistance(segment):
            left, right, top = segment
            safeLeft = left + 40
            safeRight = right - 40
            horizontalDistance = max(
                safeLeft - xPosition, 0, xPosition - safeRight
            )
            verticalDistance = top - referenceY
            return horizontalDistance**2 + verticalDistance**2

        return min(
            segments,
            key=spawnDistance,
        )

    def hasPlatformAt(self, xPosition, groundY):
        return any(
            platform.left <= xPosition < platform.right
            and platform.top == round(groundY)
            for platform in self.platformRects
        )

    def getPlatformSegmentAt(self, xPosition, groundY):
        platformTop = round(groundY)
        platforms = sorted(
            (platform for platform in self.platformRects if platform.top == platformTop),
            key=lambda platform: platform.left,
        )
        if not platforms:
            return None

        segmentLeft = platforms[0].left
        segmentRight = platforms[0].right
        for platform in platforms[1:]:
            if platform.left <= segmentRight:
                segmentRight = max(segmentRight, platform.right)
            else:
                if segmentLeft <= xPosition < segmentRight:
                    return segmentLeft, segmentRight, platformTop
                segmentLeft = platform.left
                segmentRight = platform.right

        if segmentLeft <= xPosition < segmentRight:
            return segmentLeft, segmentRight, platformTop
        return None

    def areOnSamePlatform(self, firstX, firstY, secondX, secondY):
        firstSegment = self.getPlatformSegmentAt(firstX, firstY)
        return (
            firstSegment is not None
            and firstSegment == self.getPlatformSegmentAt(secondX, secondY)
        )

    def getLandingPlatform(self, xPosition, previousY, currentY):
        if currentY < previousY:
            return None
        landingPlatforms = [
            platform
            for platform in self.platformRects
            if platform.left <= xPosition < platform.right
            and previousY <= platform.top <= currentY
        ]
        return min(landingPlatforms, key=lambda platform: platform.top, default=None)

    def draw(self):
        mapArea = pygame.Rect(self.cameraX, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.background.draw(self.displaySurface)
        self.displaySurface.blit(self.mapBackground, (0, 0), mapArea)
        for item in self.collectibles.sprites():
            self.displaySurface.blit(
                item.image, item.rect.move(-self.cameraX, 0)
            )
        self.hero.sprite.draw(self.displaySurface, self.cameraX)
        for group in (self.bees, self.boars, self.snails):
            for sprite in group.sprites():
                self.displaySurface.blit(
                    sprite.image, sprite.rect.move(-self.cameraX, 0)
                )
        self.displaySurface.blit(self.mapForeground, (0, 0), mapArea)
        if self.paused:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            self.displaySurface.blit(overlay, (0, 0))
            self._blitText(
                self.displaySurface,
                self.gameOverHintFont,
                "PAUSED",
                (255, 255, 255),
                center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2),
            )
        if self.isGameOver():
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.displaySurface.blit(overlay, (0, 0))

            self._blitText(
                self.displaySurface,
                self.gameOverFont,
                "GAME OVER",
                (220, 40, 40),
                center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 55),
            )
            self._blitText(
                self.displaySurface,
                self.gameOverHintFont,
                "Restart or quit",
                (255, 255, 255),
                center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10),
            )
            self._drawGameOverButton(self.gameOverRestartButton, "RESTART")
            self._drawGameOverButton(self.gameOverQuitButton, "QUIT")
        self.hud.draw(
            self.displaySurface,
            self.paused,
            self.coinsCollected,
            self.extraLives,
            self.audioMuted,
            self.backgroundMusicPlaying,
            self.backgroundMusicIndex,
        )

    def _drawGameOverButton(self, rect, label):
        pygame.draw.rect(
            self.displaySurface, (26, 34, 29), rect, border_radius=6
        )
        pygame.draw.rect(
            self.displaySurface,
            (222, 204, 151),
            rect,
            2,
            border_radius=6,
        )
        self._blitText(
            self.displaySurface,
            self.gameOverHintFont,
            label,
            (255, 239, 190),
            center=rect.center,
        )

    def _blitText(self, surface, font, message, color, **alignment):
        shadow = font.render(message, True, (0, 0, 0))
        shadowRect = shadow.get_rect(**alignment).move(2, 2)
        surface.blit(shadow, shadowRect)
        text = font.render(message, True, color)
        surface.blit(text, text.get_rect(**alignment))


    def run(self, deltaTime):
        action = None
        if not self.paused:
            action = self.update(deltaTime)
        self.draw()     
        return action