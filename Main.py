from pathlib import Path

import pygame 
from Config import *
from ClassLevel import Level
from ClassMainMenu import MainMenu

UIpath = Path(__file__).resolve().parent / "PyGameDev-main" / "Assets" / "SpriteSheets" / "Legacy-Fantasy - High Forest 2.3" / "UI"

level1bgpath = Path(__file__).resolve().parent / "PyGameDev-main" / "Assets" / "SpriteSheets" / "Legacy-Fantasy - High Forest 2.3" / "Background" / "b6.png"
level2bgpath = Path(__file__).resolve().parent / "PyGameDev-main" / "Assets" / "SpriteSheets" / "Legacy-Fantasy - High Forest 2.3" / "Background" / "b1.png"

def getViewport(displaySize):
    scale = min(
        displaySize[0] / WINDOW_WIDTH,  
        displaySize[1] / WINDOW_HEIGHT,
    )
    viewportSize = (
        round(WINDOW_WIDTH * scale),
        round(WINDOW_HEIGHT * scale),
    )
    viewport = pygame.Rect((0, 0), viewportSize)
    viewport.center = (displaySize[0] // 2, displaySize[1] // 2)
    return viewport


def toGamePosition(position, viewport):
    if not viewport.collidepoint(position):
        return (-1, -1)
    return (
        (position[0] - viewport.left) * WINDOW_WIDTH // viewport.width,
        (position[1] - viewport.top) * WINDOW_HEIGHT // viewport.height,
    )


# Init
pygame.init()
clock = pygame.time.Clock()

# Open fullscreen display and render the game at its original resolution.
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("MagicalForest")
displaySurface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
viewport = getViewport(screen.get_size())


levelBackgroundPaths = (level1bgpath, level2bgpath)
menu = MainMenu(UIpath, level1bgpath, len(LEVEL_PATHS))
levelIndex = 0
level = None

 
isGameRunning = True
while isGameRunning:
    deltaTime = clock.tick(60) / 1000.0

    #Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            isGameRunning = False
            continue
        if event.type == pygame.MOUSEBUTTONUP:
            eventData = event.dict.copy()
            eventData["pos"] = toGamePosition(event.pos, viewport)
            event = pygame.event.Event(event.type, eventData)
        if level is None:
            menuAction = menu.handleEvent(event)
            if menuAction == "quit":
                isGameRunning = False
            elif isinstance(menuAction, tuple) and menuAction[0] == "start":
                levelIndex = menuAction[1]
                level = Level(
                    displaySurface,
                    LEVEL_PATHS[levelIndex],
                    backgroundPath=levelBackgroundPaths[levelIndex],
                )
            continue
        levelAction = level.handleEvent(event)
        if levelAction == "quit":
            isGameRunning = False
        elif levelAction == "home":
            pygame.mixer.music.stop()
            menu.screen = "main"
            menu.mainSelection = 0
            level = None
    if not isGameRunning:
        break
    if level is None:
        menu.draw(displaySurface)
    else:
        levelAction = level.run(deltaTime)
        if levelAction == "next_level" and levelIndex + 1 < len(LEVEL_PATHS):
            previousLevel = level
            levelIndex += 1
            level = Level(
                displaySurface,
                LEVEL_PATHS[levelIndex],
                hudIcons=(
                    previousLevel.hud.counterIcons["coin"],
                    previousLevel.hud.counterIcons["potion"],
                ),
                coinsCollected=previousLevel.coinsCollected,
                extraLives=previousLevel.extraLives,
                audioMuted=previousLevel.audioMuted,
                backgroundMusicPlaying=previousLevel.backgroundMusicPlaying,
                backgroundMusicIndex=previousLevel.backgroundMusicIndex,
                backgroundPath=levelBackgroundPaths[levelIndex],
            )
            level.run(0)

    screen.fill((0, 0, 0))
    screen.blit(pygame.transform.scale(displaySurface, viewport.size), viewport)
    pygame.display.flip()

# Close pygame
pygame.quit()