from pathlib import Path

import pygame

from Config import SPRITESHEET_PATH, WINDOW_HEIGHT, WINDOW_WIDTH


class HUD:
    def __init__(self, coinIcon, potionIcon, musicTrackNames=()):
        self.buttonSize = 32
        self.margin = 7
        self.musicTrackNames = tuple(musicTrackNames)
        self.settingsOpen = False
        self.musicDropdownOpen = False
        self.uiPath = Path(SPRITESHEET_PATH) / "UI" / "png@0.5x"
        self.counterFont = pygame.font.SysFont("arial", 16, bold=True)
        self.musicDropdownFont = pygame.font.SysFont("arial", 12, bold=True)
        self.counterIconSizes = {"coin": 22, "potion": 16}
        self.counterIcons = {
            "coin": pygame.transform.scale(
                coinIcon, (self.counterIconSizes["coin"], self.counterIconSizes["coin"])
            ),
            "potion": pygame.transform.scale(
                potionIcon,
                (self.counterIconSizes["potion"], self.counterIconSizes["potion"]),
            ),
        }
        self.buttonBackgrounds = {
            "default": self._loadUIButton("Button/Square/Default@0.5x.png"),
            "hover": self._loadUIButton("Button/Square/Hover@0.5x.png"),
        }
        self.buttonIconSprites = {
            name: self._loadUIButtonIcon(f"Button/Icon/{asset}@0.5x.png")
            for name, asset in (
                ("pause", "Pause"),
                ("play", "Play"),
                ("restart", "Replay"),
                ("home", "Home"),
                ("settings", "Levels"),
                ("audio", "SoundOn"),
                ("muted", "SoundOff"),
            )
        }
        self.arrowSprites = {
            "previous": self._loadUIButtonIcon(
                "Button/Icon/ArrowLeft-Bold@0.5x.png"
            ),
            "next": self._loadUIButtonIcon(
                "Button/Icon/ArrowRight-Bold@0.5x.png"
            ),
        }
        self.pauseButton = pygame.Rect(
            WINDOW_WIDTH - self.margin - self.buttonSize,
            self.margin,
            self.buttonSize,
            self.buttonSize,
        )
        self.restartButton = pygame.Rect(
            self.pauseButton.left - 6 - self.buttonSize,
            self.margin,
            self.buttonSize,
            self.buttonSize,
        )
        self.quitButton = pygame.Rect(
            self.restartButton.left - 6 - self.buttonSize,
            self.margin,
            self.buttonSize,
            self.buttonSize,
        )
        self.settingsButton = pygame.Rect(
            self.quitButton.left - 6 - self.buttonSize,
            self.margin,
            self.buttonSize,
            self.buttonSize,
        )
        self.homeButton = pygame.Rect(
            self.settingsButton.left - 6 - self.buttonSize,
            self.margin,
            self.buttonSize,
            self.buttonSize,
        )
        panelWidth = 230
        panelLeft = WINDOW_WIDTH - self.margin - panelWidth
        panelTop = self.margin + self.buttonSize + 5
        self.settingsPanelRect = pygame.Rect(
            panelLeft, panelTop, panelWidth, 72
        )
        self.audioButton = pygame.Rect(panelLeft + 8, panelTop + 7, 24, 24)
        self.musicButton = pygame.Rect(panelLeft + 116, panelTop + 7, 24, 24)
        self.musicPreviousButton = pygame.Rect(
            panelLeft + 7, panelTop + 39, 24, 24
        )
        self.musicDropdownButton = pygame.Rect(
            panelLeft + 36, panelTop + 40, 156, 22
        )
        self.musicNextButton = pygame.Rect(
            panelLeft + 199, panelTop + 39, 24, 24
        )
        self.musicOptionRects = tuple(
            pygame.Rect(
                self.musicDropdownButton.left,
                self.musicDropdownButton.bottom + index * 20,
                self.musicDropdownButton.width,
                20,
            )
            for index in range(len(self.musicTrackNames))
        )

    def _loadUIButton(self, relativePath):
        return pygame.image.load(str(self.uiPath / relativePath)).convert_alpha()

    def _loadUIButtonIcon(self, relativePath):
        image = self._loadUIButton(relativePath)
        image.fill((0, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
        return image

    def handleEvent(self, event):
        if event.type != pygame.MOUSEBUTTONUP or event.button != 1:
            return None
        if self.settingsOpen and self.musicDropdownOpen:
            for index, optionRect in enumerate(self.musicOptionRects):
                if optionRect.collidepoint(event.pos):
                    self.musicDropdownOpen = False
                    return "select_music", index
            if not self.musicDropdownButton.collidepoint(event.pos):
                self.musicDropdownOpen = False
        if self.settingsButton.collidepoint(event.pos):
            self.settingsOpen = not self.settingsOpen
            self.musicDropdownOpen = False
            return None
        if self.settingsOpen:
            if self.musicDropdownButton.collidepoint(event.pos):
                self.musicDropdownOpen = not self.musicDropdownOpen
                return None
            if self.settingsPanelRect.collidepoint(event.pos):
                if self.audioButton.collidepoint(event.pos):
                    return "audio"
                if self.musicButton.collidepoint(event.pos):
                    return "music"
                if self.musicPreviousButton.collidepoint(event.pos):
                    return "previous_music"
                if self.musicNextButton.collidepoint(event.pos):
                    return "next_music"
                return None
            self.settingsOpen = False
            self.musicDropdownOpen = False
        if self.homeButton.collidepoint(event.pos):
            return "home"
        if self.pauseButton.collidepoint(event.pos):
            return "pause"
        if self.restartButton.collidepoint(event.pos):
            return "restart"
        if self.quitButton.collidepoint(event.pos):
            return "quit"
        return None

    def draw(
        self,
        surface,
        paused,
        coinsCollected=0,
        potionsCollected=0,
        audioMuted=False,
        backgroundMusicPlaying=True,
        musicTrackIndex=0,
    ):
        self._drawCounter(
            surface,
            "coin",
            coinsCollected,
            (
                self.margin,
                self.margin + self.counterIconSizes["coin"] // 2,
            ),
        )
        self._drawCounter(
            surface,
            "potion",
            potionsCollected,
            (
                self.margin + 76,
                self.margin + self.counterIconSizes["potion"] // 2,
            ),
        )

        displaySize = pygame.display.get_surface().get_size()
        scale = min(
            displaySize[0] / WINDOW_WIDTH,
            displaySize[1] / WINDOW_HEIGHT,
        )
        viewportWidth = round(WINDOW_WIDTH * scale)
        viewportHeight = round(WINDOW_HEIGHT * scale)
        viewportLeft = (displaySize[0] - viewportWidth) // 2
        viewportTop = (displaySize[1] - viewportHeight) // 2
        mouseX, mouseY = pygame.mouse.get_pos()
        mousePosition = (
            round((mouseX - viewportLeft) * WINDOW_WIDTH / viewportWidth),
            round((mouseY - viewportTop) * WINDOW_HEIGHT / viewportHeight),
        )
        self._drawHudButton(surface, self.homeButton, mousePosition, "home")
        self._drawHudButton(surface, self.restartButton, mousePosition, "restart")
        self._drawHudButton(surface, self.quitButton, mousePosition, "quit")
        self._drawHudButton(surface, self.settingsButton, mousePosition, "settings")
        self._drawHudButton(
            surface,
            self.pauseButton,
            mousePosition,
            "play" if paused else "pause",
        )
        if self.settingsOpen:
            panelHeight = (
                72 + len(self.musicOptionRects) * 20
                if self.musicDropdownOpen
                else 72
            )
            panel = self.settingsPanelRect.copy()
            panel.height = panelHeight
            pygame.draw.rect(
                surface, (26, 34, 29), panel, border_radius=6
            )
            pygame.draw.rect(
                surface, (222, 204, 151), panel, 1, border_radius=6
            )
            self._drawHudButton(
                surface,
                self.audioButton,
                mousePosition,
                "muted" if audioMuted else "audio",
            )
            self._drawHudButton(
                surface,
                self.musicButton,
                mousePosition,
                "music" if backgroundMusicPlaying else "music_off",
            )
            self._drawSettingLabel(surface, "Audio", self.audioButton)
            self._drawSettingLabel(surface, "Music", self.musicButton)
            self._drawHudButton(
                surface, self.musicPreviousButton, mousePosition, "previous"
            )
            self._drawHudButton(
                surface, self.musicNextButton, mousePosition, "next"
            )
            self._drawMusicDropdown(surface, mousePosition, musicTrackIndex)

    def _drawSettingLabel(self, surface, label, buttonRect):
        self._blitText(
            surface,
            self.musicDropdownFont,
            label,
            (255, 255, 255),
            midleft=(buttonRect.right + 5, buttonRect.centery),
        )

    def _drawMusicDropdown(self, surface, mousePosition, musicTrackIndex):
        if not self.musicTrackNames:
            return

        selectedTrack = self.musicTrackNames[musicTrackIndex]
        buttonHovered = self.musicDropdownButton.collidepoint(mousePosition)
        buttonFill = (43, 53, 45) if buttonHovered else (26, 34, 29)
        pygame.draw.rect(
            surface, buttonFill, self.musicDropdownButton, border_radius=6
        )
        pygame.draw.rect(
            surface,
            (222, 204, 151),
            self.musicDropdownButton,
            1,
            border_radius=6,
        )
        self._blitText(
            surface,
            self.musicDropdownFont,
            f"Music: {selectedTrack}",
            (255, 255, 255),
            midleft=(
                self.musicDropdownButton.left + 6,
                self.musicDropdownButton.centery,
            ),
        )
        arrowX = self.musicDropdownButton.right - 11
        arrowY = self.musicDropdownButton.centery
        pygame.draw.polygon(
            surface,
            (255, 255, 255),
            (
                (arrowX - 4, arrowY - 2),
                (arrowX + 4, arrowY - 2),
                (arrowX, arrowY + 3),
            ),
        )

        if not self.musicDropdownOpen:
            return
        for index, (trackName, optionRect) in enumerate(
            zip(self.musicTrackNames, self.musicOptionRects)
        ):
            isSelected = index == musicTrackIndex
            isHovered = optionRect.collidepoint(mousePosition)
            fill = (
                (75, 88, 69)
                if isSelected or isHovered
                else (26, 34, 29)
            )
            pygame.draw.rect(surface, fill, optionRect)
            pygame.draw.rect(surface, (222, 204, 151), optionRect, 1)
            self._blitText(
                surface,
                self.musicDropdownFont,
                trackName,
                (255, 255, 255),
                midleft=(optionRect.left + 6, optionRect.centery),
            )

    def _drawCounter(self, surface, itemType, count, position):
        icon = self.counterIcons[itemType]
        iconRect = icon.get_rect(midleft=position)
        surface.blit(icon, iconRect)
        self._blitText(
            surface,
            self.counterFont,
            str(count),
            (255, 255, 255),
            midleft=(iconRect.right + 5, iconRect.centery),
        )

    def _blitText(self, surface, font, message, color, **alignment):
        shadow = font.render(message, True, (0, 0, 0))
        shadowRect = shadow.get_rect(**alignment).move(1, 1)
        surface.blit(shadow, shadowRect)
        text = font.render(message, True, color)
        surface.blit(text, text.get_rect(**alignment))

    def _drawHudButton(self, surface, rect, mousePosition, icon):
        hovered = rect.collidepoint(mousePosition)
        background = self.buttonBackgrounds[
            "hover" if hovered else "default"
        ]
        self._blitButtonImage(surface, background, rect)
        centerX, centerY = rect.center
        iconColor = (0, 0, 0)
        if icon in self.buttonIconSprites:
            iconImage = self.buttonIconSprites[icon]
            iconSize = min(16, rect.width - 12, rect.height - 12)
            iconRect = pygame.Rect(0, 0, iconSize, iconSize)
            iconRect.center = rect.center
            iconRect = iconImage.get_rect().fit(iconRect)
            surface.blit(
                pygame.transform.smoothscale(iconImage, iconRect.size),
                iconRect,
            )
        elif icon == "quit":
            pygame.draw.line(
                surface,
                iconColor,
                (centerX - 4, centerY - 4),
                (centerX + 4, centerY + 4),
                2,
            )
            pygame.draw.line(
                surface,
                iconColor,
                (centerX + 4, centerY - 4),
                (centerX - 4, centerY + 4),
                2,
            )
        elif icon in self.arrowSprites:
            arrow = pygame.transform.smoothscale(
                self.arrowSprites[icon], (9, 14)
            )
            surface.blit(arrow, arrow.get_rect(center=rect.center))
        elif icon in ("music", "music_off"):
            pygame.draw.line(
                surface,
                iconColor,
                (centerX + 2, centerY - 6),
                (centerX + 2, centerY + 2),
                2,
            )
            pygame.draw.line(
                surface,
                iconColor,
                (centerX + 2, centerY - 6),
                (centerX + 6, centerY - 7),
                2,
            )
            pygame.draw.ellipse(
                surface,
                iconColor,
                (centerX - 4, centerY + 1, 6, 4),
            )
            pygame.draw.ellipse(
                surface,
                iconColor,
                (centerX + 1, centerY - 8, 6, 4),
            )
            if icon == "music_off":
                pygame.draw.line(
                    surface,
                    iconColor,
                    (centerX - 7, centerY - 7),
                    (centerX + 7, centerY + 7),
                    2,
                )

    def _blitButtonImage(self, surface, image, rect):
        scaledImage = pygame.transform.smoothscale(image, rect.size)
        shadow = scaledImage.copy()
        shadow.fill((0, 0, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(shadow, rect.move(0, 2))
        surface.blit(scaledImage, rect)
