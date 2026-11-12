from pathlib import Path

import pygame

from Config import WINDOW_HEIGHT, WINDOW_WIDTH


class MainMenu:
    def __init__(self, uiPath, backgroundPath, levelCount):
        if levelCount < 1:
            raise ValueError("The main menu requires at least one level")
        self.uiPath = Path(uiPath) / "png@0.5x"
        self.levelCount = levelCount
        self.screen = "main"
        self.selectedLevel = 0
        self.mainSelection = 0
        self.mainActions = ("start", "levels", "quit")
        self.mainLabels = ("PLAY", "SELECT LEVEL", "QUIT")

        root = Path(__file__).resolve().parent
        self.background = pygame.transform.scale(
            pygame.image.load(str(backgroundPath)).convert(),
            (WINDOW_WIDTH, WINDOW_HEIGHT),
        )
        self.titleFont = pygame.font.Font(
            str(root / "PyGameDev-main" / "Assets" / "Fonts" / "IMMORTAL.ttf"),
            62,
        )
        self.buttonFont = pygame.font.Font(
            str(root / "PyGameDev-main" / "Assets" / "Fonts" / "IMMORTAL.ttf"),
            24,
        )
        self.hintFont = pygame.font.Font(None, 24)

        self.buttonImages = {
            "default": self._loadImage("Button/Rect/Default@0.5x.png"),
            "hover": self._loadImage("Button/Rect/Hover@0.5x.png"),
            "level": self._loadImage(
                "Buttons/Square/Levels/Default@0.5x.png"
            ),
            "level_hover": self._loadImage(
                "Buttons/Square/Levels/Hover@0.5x.png"
            ),
            "home": self._loadImage(
                "Buttons/Square/Home/Default@0.5x.png"
            ),
            "home_hover": self._loadImage(
                "Buttons/Square/Home/Hover@0.5x.png"
            ),
        }
        self.mainButtonRects = [
            pygame.Rect(WINDOW_WIDTH // 2 - 150, 260 + index * 72, 300, 58)
            for index in range(len(self.mainActions))
        ]
        cardWidth = min(220, (WINDOW_WIDTH - 100) // max(levelCount, 1))
        cardGap = 24
        cardsWidth = levelCount * cardWidth + max(0, levelCount - 1) * cardGap
        firstCardLeft = (WINDOW_WIDTH - cardsWidth) // 2
        self.levelButtonRects = [
            pygame.Rect(
                firstCardLeft + index * (cardWidth + cardGap),
                220,
                cardWidth,
                190,
            )
            for index in range(levelCount)
        ]
        self.backButtonRect = pygame.Rect(28, 28, 52, 52)

    def _loadImage(self, relativePath):
        path = self.uiPath / relativePath
        return pygame.image.load(str(path)).convert_alpha()

    def handleEvent(self, event):
        if event.type == pygame.KEYDOWN:
            if self.screen == "main":
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.mainSelection = (
                        self.mainSelection - 1
                    ) % len(self.mainActions)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.mainSelection = (
                        self.mainSelection + 1
                    ) % len(self.mainActions)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    return self._activateMainAction()
                elif event.key == pygame.K_ESCAPE:
                    return "quit"
            else:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.selectedLevel = (
                        self.selectedLevel - 1
                    ) % self.levelCount
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.selectedLevel = (
                        self.selectedLevel + 1
                    ) % self.levelCount
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    return "start", self.selectedLevel
                elif event.key == pygame.K_ESCAPE:
                    self.screen = "main"
            return None

        if event.type != pygame.MOUSEBUTTONUP or event.button != 1:
            return None

        if self.screen == "main":
            for index, rect in enumerate(self.mainButtonRects):
                if rect.collidepoint(event.pos):
                    self.mainSelection = index
                    return self._activateMainAction()
        else:
            if self.backButtonRect.collidepoint(event.pos):
                self.screen = "main"
                return None
            for index, rect in enumerate(self.levelButtonRects):
                if rect.collidepoint(event.pos):
                    self.selectedLevel = index
                    return "start", index
        return None

    def _activateMainAction(self):
        action = self.mainActions[self.mainSelection]
        if action == "levels":
            self.screen = "levels"
            return None
        if action == "start":
            return "start", self.selectedLevel
        return action

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 24, 19, 150))
        surface.blit(overlay, (0, 0))

        self._blitText(
            surface,
            self.titleFont,
            "MAGICAL FOREST",
            (255, 239, 190),
            center=(WINDOW_WIDTH // 2, 145),
        )

        if self.screen == "main":
            self._drawMainMenu(surface)
        else:
            self._drawLevelSelect(surface)

    def _drawMainMenu(self, surface):
        mousePosition = self._getMousePosition()
        for index, (rect, label) in enumerate(
            zip(self.mainButtonRects, self.mainLabels)
        ):
            hovered = rect.collidepoint(mousePosition)
            selected = index == self.mainSelection
            imageKey = (
                "hover"
                if hovered or selected
                else "default"
            )
            image = pygame.transform.smoothscale(
                self.buttonImages[imageKey], rect.size
            )
            surface.blit(image, rect)
            self._blitText(
                surface,
                self.buttonFont,
                label,
                (255, 239, 190),
                center=rect.center,
            )
        self._drawHint(
            surface,
            "MOVE: A / D OR ARROWS  •  JUMP: W / UP  •  ATTACK: SPACE",
            500,
        )

    def _drawLevelSelect(self, surface):
        self._blitText(
            surface,
            self.buttonFont,
            "CHOOSE YOUR LEVEL",
            (255, 239, 190),
            center=(WINDOW_WIDTH // 2, 195),
        )
        mousePosition = self._getMousePosition()
        for index, rect in enumerate(self.levelButtonRects):
            hovered = rect.collidepoint(mousePosition)
            selected = index == self.selectedLevel
            imageKey = "level_hover" if hovered or selected else "level"
            image = pygame.transform.scale(
                self.buttonImages[imageKey],
                (min(88, rect.width - 24), 92),
            )
            imageRect = image.get_rect(center=(rect.centerx, rect.centery - 20))
            surface.blit(image, imageRect)
            if selected or hovered:
                pygame.draw.rect(
                    surface,
                    (255, 239, 190),
                    imageRect.inflate(6, 6),
                    2,
                    border_radius=8,
                )
            color = (
                (255, 239, 190)
                if selected or hovered
                else (230, 222, 188)
            )
            self._blitText(
                surface,
                self.buttonFont,
                f"LEVEL {index + 1}",
                color,
                center=(rect.centerx, rect.bottom - 22),
            )
        backImage = self.buttonImages[
            "home_hover"
            if self.backButtonRect.collidepoint(mousePosition)
            else "home"
        ]
        surface.blit(
            pygame.transform.smoothscale(backImage, self.backButtonRect.size),
            self.backButtonRect,
        )
        self._drawHint(surface, "CLICK A LEVEL OR USE LEFT / RIGHT + ENTER", 470)

    def _drawHint(self, surface, message, yPosition):
        self._blitText(
            surface,
            self.hintFont,
            message,
            (235, 230, 203),
            center=(WINDOW_WIDTH // 2, yPosition),
        )

    def _blitText(self, surface, font, message, color, **alignment):
        shadow = font.render(message, True, (0, 0, 0))
        shadowRect = shadow.get_rect(**alignment).move(2, 2)
        surface.blit(shadow, shadowRect)
        text = font.render(message, True, color)
        surface.blit(text, text.get_rect(**alignment))

    def _getMousePosition(self):
        display = pygame.display.get_surface()
        if display is None:
            return pygame.mouse.get_pos()
        displayWidth, displayHeight = display.get_size()
        scale = min(
            displayWidth / WINDOW_WIDTH,
            displayHeight / WINDOW_HEIGHT,
        )
        viewportWidth = round(WINDOW_WIDTH * scale)
        viewportHeight = round(WINDOW_HEIGHT * scale)
        viewportLeft = (displayWidth - viewportWidth) // 2
        viewportTop = (displayHeight - viewportHeight) // 2
        mouseX, mouseY = pygame.mouse.get_pos()
        return (
            round((mouseX - viewportLeft) * WINDOW_WIDTH / viewportWidth),
            round((mouseY - viewportTop) * WINDOW_HEIGHT / viewportHeight),
        )
