from timeit import repeat

import pygame.sprite
from pygame import K_d, K_a, K_w, K_s, K_SPACE, K_f, K_e, Vector2

from timers import Timer
from settings import *
from random import choice
from enemies import Skeleton, Goblin, DemonSlime


# noinspection PyTypeChecker

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, frames, attack_effect_frames, collision_sprites, enemy_sprites,
                 attack_sprites, groups):
        super().__init__(groups)
        # general setup
        self.screen = pygame.display.get_surface()
        self.groups = groups
        self.frames, self.frame_index, self.state, = frames, 0, 'idle'
        self.image = frames[self.state][0][self.frame_index]
        self.rect = self.image.get_rect(center=pos)

        # frames for player sword and bow
        self.player_attack_effects = attack_effect_frames
        # group to manage player sword frames
        self.attack_sprites = attack_sprites

        # group containing every enemy in the game
        self.enemy_sprites = enemy_sprites

        # movement
        self.direction = pygame.Vector2()
        self.speed = 750
        self.flip = False

        # animations
        self.animation_speed = 8
        self.onetap_animation_running = False
        self.is_dead = False

        # attack
        self.can_attack = {
            'basic': True,
            'heavy': True,
            'ranged': True
        }
        self.damage = 30

        # stats
        self.max_health = 200
        self.health = self.max_health
        self.level = 1

        # collisions and hitbox
        self.collision_sprites = collision_sprites
        self.x_inflate, self.y_inflate = -230, -220
        self.hitbox_rect = self.rect.inflate(self.x_inflate, self.y_inflate)

        # timers
        self.attack_timers = {
            'basic': Timer(400, func=lambda: self.allow_attack('basic')),
            'heavy': Timer(1500, func=lambda: self.allow_attack('heavy')),
            'ranged': Timer(1500, func=lambda: self.allow_attack('ranged'))
        }

    def allow_attack(self, attack_type):
        self.can_attack[attack_type] = True

    def animate(self, dt):
        # walk and idle checker
        self.state = 'walk' if self.direction and not self.onetap_animation_running else self.state
        self.state = 'idle' if not self.direction and not self.onetap_animation_running else self.state

        # methods
        def animate_state(looped=False, func=None):
            self.image = pygame.transform.flip(
                self.frames[self.state][0][int(self.frame_index % self.frames[self.state][1])], self.flip, False)
            if not looped and func:
                if self.frame_index > self.frames[self.state][1] - 0.1:
                    func()

        def animation_speeds():
            match self.state:
                case 'idle' | 'walk':
                    self.animation_speed = 11
                case 'basic-attack':
                    self.animation_speed = 20
                case 'heavy-attack':
                    self.animation_speed = 12

        # general
        animation_speeds()
        self.frame_index += self.animation_speed * dt
        match self.state:
            case 'idle' | 'walk':
                animate_state(looped=True)
            case 'basic-attack' | 'heavy-attack' | 'ranged-attack':
                animate_state(func=lambda: setattr(self, "onetap_animation_running", False))
            case 'hurt':
                if not self.is_dead:
                    self.check_for_death()
                    animate_state(func=lambda: setattr(self, "onetap_animation_running", False))
            case 'death':
                animate_state(func=lambda: setattr(self, "frame_index", 3))

    def input(self):
        # movement
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[K_d]) - int(keys[K_a])
        self.direction.y = int(keys[K_s]) - int(keys[K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction

        # attack
        def attack(type):
            self.state = f'{type}-attack'
            self.onetap_animation_running = True
            self.can_attack[type] = False
            self.frame_index = 0

            def create_effect(offset, attack_type):
                PlayerAttackEffect(self.player_attack_effects[attack_type], self.rect.center + offset, offset, self,
                                   self.enemy_sprites, self.attack_sprites, (self.groups[0], self.attack_sprites))

            if type == 'basic':
                offset = Vector2(-201, -210)
                create_effect(offset, 'basic-effect')
                self.attack_timers[type].activate()
            elif type == 'heavy':
                offset = Vector2(-200, -207)
                create_effect(offset, 'heavy-effect')
                self.attack_timers[type].activate()
            elif type == 'ranged':
                self.attack_timers[type].activate()

        if keys[K_SPACE] and self.can_attack['basic'] and not self.onetap_animation_running:
            attack('basic')
        if keys[K_f] and self.can_attack['heavy'] and not self.onetap_animation_running:
            attack('heavy')
        if keys[K_e] and self.can_attack['ranged'] and not self.onetap_animation_running:
            attack('ranged')

    def move(self, dt):
        if self.direction.x < 0:
            self.flip = True
        elif self.direction.x > 0:
            self.flip = False

        self.hitbox_rect.x += round(self.direction.x * self.speed * dt)
        self.collisions('horizontal')
        self.hitbox_rect.y += round(self.direction.y * self.speed * dt)
        self.collisions('vertical')
        self.rect.center = self.hitbox_rect.center

    def collisions(self, movement):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if movement == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0:
                        self.hitbox_rect.left = sprite.rect.right
                if movement == 'vertical':
                    if self.direction.y > 0:
                        self.hitbox_rect.bottom = sprite.rect.top
                    if self.direction.y < 0:
                        self.hitbox_rect.top = sprite.rect.bottom

    def check_for_death(self):
        if self.health <= 0:
            self.is_dead = True
            self.state = 'death'

    def update(self, dt):
        if not self.is_dead:
            self.hitbox_rect = self.rect.inflate(self.x_inflate, self.y_inflate)
            for timer in self.attack_timers.values():
                timer.update()

            self.input()
            self.move(dt)

        self.animate(dt)


class PlayerAttackEffect(pygame.sprite.Sprite):
    def __init__(self, frames, pos, offset, player, enemy_sprites, attack_sprites, groups):
        super().__init__(groups)
        self.player = player
        self.frames, self.frame_index = frames, 0
        self.image = pygame.transform.flip(self.frames[self.frame_index], self.player.flip, False)
        self.rect = self.image.get_frect(topleft=pos)
        self.enemy_sprites = enemy_sprites
        self.attack_sprites = attack_sprites
        self.can_hit = True
        self.attack_cooldown_timer = Timer(500, func=self.allow_attack)
        self.pos = pos
        self.offset = offset

    def animate(self, dt):
        animation_speed = 9
        if self.player.state == 'heavy-attack':
            animation_speed = 8

        self.frame_index += animation_speed * dt
        self.image = pygame.transform.flip(self.frames[int(self.frame_index)], self.player.flip, False)
        if self.frame_index > 1.4:
            self.kill()

        self.rect.topleft = self.player.rect.center + self.offset

    def collisions(self):
        for sprite in self.enemy_sprites:
            if sprite.is_dead and not sprite.is_out:
                sprite.death_timer.activate()
                sprite.is_out = True

            if pygame.sprite.spritecollide(sprite, self.attack_sprites, False,
                                           pygame.sprite.collide_mask) and self.can_hit:
                if not sprite.is_dead:
                    self.attack(sprite)
                    self.can_hit = False
                    self.attack_cooldown_timer.activate()

    def attack(self, target):
        if not type(target) == DemonSlime:
            target.state = 'hurt'
            target.frame_index = 0

        dodge = choice([0, 0, 0, 0, 1])
        target.dodge = dodge

        if dodge == 1 and type(target) == Skeleton:
            print('dodged')
        else:
            target.health -= self.player.damage

    def allow_attack(self):
        self.can_hit = True

    def update(self, dt):
        self.attack_cooldown_timer.update()
        self.animate(dt)
        self.collisions()
