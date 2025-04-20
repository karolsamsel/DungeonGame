import pygame.font
from pygame import FRect, Vector2

from settings import *


class Ui:
    def __init__(self, player):
        self.screen = pygame.display.get_surface()
        self.player = player
        self.wave = 1
        self.container = FRect((50, 50), (250, 150))
        self.wave_multiplier = 0
        self.direction_up = True
        self.size = 31
        self.play_the_animation = False

    def menu(self):
        # stats
        self.display_stats()
        # current wave
        self.render_wave()

    def display_stats(self):
        # profile
        avatar_image = pygame.transform.scale(
            pygame.image.load(join('..\\', 'static', 'images', 'Soldier', 'avatar.png')).convert_alpha(),
            (110, 110))
        avatar_rect = avatar_image.get_frect(topleft=self.container.topleft + Vector2(-13, -5))
        self.screen.blit(avatar_image, avatar_rect)

        # level
        level_font = pygame.font.Font(join('..\\', 'static', 'fonts', 'UncialAntiqua-Regular.ttf'), 22)
        level_text = level_font.render(f"Level: {self.player.level}", True, '#90EE90')
        level_rect = level_text.get_frect(midright=self.container.midright + Vector2(-40, 10))
        self.screen.blit(level_text, level_rect)

        # health_bar
        outer_color = '#2E2E2E'
        inner_color = '#4B4B4B'

        health_rect = FRect(self.container.midleft + Vector2(40, 30), (180, 35))
        health_ratio = (health_rect.width - 23) / self.player.max_health
        progress_bar = FRect(health_rect.left + 15, health_rect.top + 5,
                             self.player.health * health_ratio,
                             health_rect.height - 10)
        pygame.draw.rect(self.screen, '#8B0000', progress_bar)
        pygame.draw.rect(self.screen, outer_color, health_rect, 8, 7)

        inner_border_offset = 6
        inner_border = FRect(health_rect.left + inner_border_offset, health_rect.top + inner_border_offset,
                             health_rect.width - inner_border_offset * 2,
                             health_rect.height - inner_border_offset * 2)
        pygame.draw.rect(self.screen, inner_color, inner_border, 3, 7)

        # heart image
        heart_image = pygame.transform.scale(
            pygame.image.load(join('..\\', 'static', 'images', 'Heart', 'heart.png')).convert_alpha(), (50, 50))
        heart_offset = Vector2(-24, -10)
        heart_rect = heart_image.get_frect(topleft=health_rect.topleft + heart_offset)

        heart_border = pygame.transform.scale(
            pygame.image.load(join('..\\', 'static', 'images', 'Heart', 'border-charcoal.png')).convert_alpha(),
            (50, 50))
        heart_border_rect = heart_border.get_frect(topleft=health_rect.topleft + heart_offset)

        self.screen.blit(heart_image, heart_rect)
        self.screen.blit(heart_border, heart_border_rect)

    def render_wave(self):
        # its fucking hardcoded don't ask how it works
        if self.play_the_animation and self.direction_up:
            self.wave_multiplier += 1

        if self.wave_multiplier == 45 and self.direction_up:
            self.direction_up = False

        if not self.direction_up and self.wave_multiplier > 0:
            self.wave_multiplier -= 1

        if self.wave_multiplier == 0 and not self.direction_up:
            self.wave_multiplier = 0

        size = self.size + self.wave_multiplier
        font = pygame.font.Font(join('..\\', 'static', 'fonts', 'UncialAntiqua-Regular.ttf'), size)
        text = font.render(f"Wave: {self.wave}", True, '#C4A000')
        text_rect = text.get_frect(center=(WINDOW_WIDTH / 2, 50))
        self.screen.blit(text, text_rect)

    def draw(self):
        self.menu()
