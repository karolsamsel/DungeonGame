import random

import pygame.draw
from pygame import Vector2, FRect

from settings import *
from timers import Timer

from random import choice, uniform


# noinspection PyTypeChecker

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, frames, player, player_sprites, collision_sprites, groups):
        super().__init__(groups)
        # general
        self.screen = pygame.display.get_surface()
        self.frames, self.frame_index = frames, 0
        self.state = 'walk'
        self.walls = collision_sprites

        # image
        self.image = self.frames[self.state][0][self.frame_index]
        self.rect = self.image.get_frect(center=pos)

        # animations
        self.animation_speed = 5
        self.animation_length = frames[self.state][1]
        self.flip = False

        # combat
        self.player = player
        self.player_sprites = player_sprites

        self.max_health = 50
        self.health = None
        self.damage = 1

        self.dodge = False
        self.is_dead = False
        self.is_out = False

        self.death_timer = Timer(2000, func=lambda: self.kill())

    def deal_damage(self):
        self.player.health -= self.damage
        self.player.state = 'hurt'
        self.player.onetap_animation_running = True
        self.player.frame_index = 0

    def animate_state(self, looped=False, func=None):
        self.animation_length = self.frames[self.state][1]

        if looped:
            self.image = pygame.transform.flip(
                self.frames[self.state][0][int(self.frame_index % self.animation_length)], self.flip, False)
        else:
            self.image = pygame.transform.flip(
                self.frames[self.state][0][int(self.frame_index)], self.flip, False)
            if self.frame_index > self.animation_length - 0.4 and func:
                func()

    def check_for_death(self):
        if self.health <= 0:
            self.is_dead = True
            self.state = 'death'
            self.moving = False
            return True

    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        self.image = self.frames[self.state][0][int(self.frame_index) % self.animation_length]

    def check_for_flip(self):
        if self.direction.x > 0:
            self.flip = False
        elif self.direction.x < 0:
            self.flip = True

    def collisions(self, direction, rect):
        for wall in self.walls:
            if wall.rect.colliderect(rect):
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        rect.right = wall.rect.left
                    elif self.direction.x < 0:
                        rect.left = wall.rect.right
                if direction == 'vertical':
                    if self.direction.y > 0:
                        rect.bottom = wall.rect.top
                    elif self.direction.y < 0:
                        rect.top = wall.rect.bottom

    def update(self, dt):
        self.animate(dt)


class Skeleton(Enemy):
    def __init__(self, pos, frames, player, player_sprites, collision_sprites, groups):
        super().__init__(pos, frames, player, player_sprites, collision_sprites, groups)
        # override values
        self.animation_speed = 10
        self.max_health = 130
        self.health = self.max_health
        self.damage = 55
        self.hitbox_value = (-100, -100)
        self.hitbox_rect = self.rect.inflate(self.hitbox_value)

        self.speed = 200
        self.direction = Vector2()
        self.moving = True
        self.can_attack = True
        self.can_hit = True
        self.range = 70
        self.attack_frames_values = [4, 10]

        # timers
        self.damage_cooldown_timer = Timer(500, func=lambda: setattr(self, 'can_hit', True))
        self.attack_cooldown_timer = Timer(1, func=lambda: (
            setattr(self, 'can_attack', True), setattr(self, 'moving', True)))

    def check_if_in_range(self):
        if self.rect.y > self.player.rect.y:
            if (((0 < self.rect.centerx - self.player.rect.centerx < self.range) and self.can_attack) or (
                    (0 > self.rect.centerx - self.player.rect.centerx > -self.range) and self.can_attack)) \
                    and self.rect.y - self.player.rect.y < self.range:
                return True

    def check_for_state(self):
        # check if he is walking
        if self.direction and self.moving:
            self.state = 'walk'

        # check if he is attacking
        if self.check_if_in_range():
            self.frame_index = 0
            self.state = 'attack'
            self.moving = False
            self.can_attack = False
        if int(self.frame_index) > self.animation_length:
            self.frame_index = 0
            self.attack_cooldown_timer.activate()

        # check if player got hit and apply damage
        if pygame.sprite.spritecollide(self, self.player_sprites, False,
                                       pygame.sprite.collide_mask) and self.can_hit and self.state == 'attack' and (
                self.attack_frames_values[1] > self.frame_index > self.attack_frames_values[0]):
            self.deal_damage()
            self.can_hit = False
            self.damage_cooldown_timer.activate()

    def move(self, dt):
        player_pos = Vector2(self.player.rect.center)
        enemy_pos = Vector2(self.rect.center)
        self.direction = (player_pos - enemy_pos)
        self.direction = self.direction.normalize() if self.direction else self.direction

        if self.moving:
            self.hitbox_rect.centerx += self.direction.x * self.speed * dt
            self.collisions('horizontal', self.hitbox_rect)
            self.hitbox_rect.centery += self.direction.y * self.speed * dt
            self.collisions('vertical', self.hitbox_rect)
            self.rect.center = self.hitbox_rect.center

        if self.direction.x < 0:
            self.flip = True
        else:
            self.flip = False

    def animate(self, dt):
        def animation_speeds():
            match self.state:
                case 'attack':
                    self.animation_speed = 9
                case 'idle' | 'walk':
                    self.animation_speed = 10
                case 'hurt':
                    self.animation_speed = 5

        animation_speeds()
        self.frame_index += self.animation_speed * dt

        if self.state == 'hurt':
            if self.dodge:
                self.state = 'attack'
            else:
                self.animate_state()
                if self.frame_index > self.animation_length:
                    self.frame_index = 0
                    self.attack_cooldown_timer.activate()
            self.check_for_death()

        elif self.state == 'walk' or self.state == 'idle':
            self.animate_state(looped=True)

        elif self.state == 'attack':
            self.animate_state(func=lambda: setattr(self, 'state', 'walk'))

        elif self.state == 'death':
            self.animate_state(func=lambda: setattr(self, 'frame_index', 12))

    def update(self, dt):
        if not self.player.is_dead and not self.is_dead:
            self.attack_cooldown_timer.update()
            self.damage_cooldown_timer.update()
            self.check_for_state()
            self.move(dt)

        self.state = 'idle' if (self.frame_index > self.animation_length and self.player.is_dead) else self.state

        self.death_timer.update() if self.is_dead else self.death_timer

        self.animate(dt)
        self.hitbox_rect = self.rect.inflate(self.hitbox_value)


class SmallSkeleton(Skeleton):
    def __init__(self, pos, frames, player, player_sprites, collision_sprites, groups,
                 is_spawned_by_necromancer):
        super().__init__(pos, frames, player, player_sprites, collision_sprites, groups)
        self.health = 60
        self.range = 50
        self.damage = 30
        self.hitbox_value = (-60, -60)
        self.attack_frames_values = [6, 7]
        self.attack_hitbox = self.rect.inflate(50, 70)
        self.sleep = is_spawned_by_necromancer
        self.sleep_timer = Timer(2000, func=lambda: setattr(self, 'sleep', False), autostart=True)

    def check_if_in_range(self):
        if self.attack_hitbox.y > self.player.rect.y:
            if (((0 < self.attack_hitbox.centerx - self.player.rect.centerx < self.range) and self.can_attack) or (
                    (0 > self.attack_hitbox.centerx - self.player.rect.centerx > -self.range) and self.can_attack)) \
                    and self.attack_hitbox.y - self.player.rect.y < self.range:
                return True

    def animate(self, dt):
        def animation_speeds():
            match self.state:
                case 'attack':
                    self.animation_speed = 9
                case 'idle' | 'walk':
                    self.animation_speed = 10
                case 'hurt':
                    self.animation_speed = 5

        animation_speeds()
        self.frame_index += self.animation_speed * dt

        if self.state == 'hurt':
            if self.dodge:
                self.state = 'attack'
            else:
                self.animate_state(looped=False, func=lambda: setattr(self, 'state', 'walk'))
                if self.frame_index > self.animation_length:
                    self.frame_index = 0
                    self.attack_cooldown_timer.activate()
            self.check_for_death()

        elif self.state == 'walk' or self.state == 'idle':
            self.animate_state(looped=True)

        elif self.state == 'attack':
            self.animate_state(func=lambda: setattr(self, 'state', 'walk'))

        elif self.state == 'death':
            self.animate_state(func=lambda: setattr(self, 'frame_index', 3))

    def update(self, dt):
        if not self.sleep:
            if not self.player.is_dead and not self.is_dead:
                self.attack_cooldown_timer.update()
                self.damage_cooldown_timer.update()
                self.check_for_state()
                self.move(dt)

            self.state = 'idle' if (self.frame_index > self.animation_length and self.player.is_dead) else self.state

            self.death_timer.update() if self.is_dead else self.death_timer

            self.animate(dt)
            self.hitbox_rect = self.rect.inflate(self.hitbox_value)
            self.attack_hitbox = self.rect.inflate(50, 70)
        else:
            self.sleep_timer.update()
            mask = pygame.mask.from_surface(self.frames['idle'][0][0]).to_surface()
            mask.set_colorkey('black')
            self.image = mask


class NightBorne(Enemy):
    def __init__(self, pos, frames, player, player_sprites, starting_pos, collision_sprites, groups):
        super().__init__(pos, frames, player, player_sprites, collision_sprites, groups)
        self.max_health = 100
        self.health = self.max_health
        self.camera_x = 1
        self.camera_y = 1

        # movement
        self.speed = 250
        self.direction = Vector2(choice([-1, 1]), 0)
        self.starting_pos = starting_pos
        self.hitbox_rect = self.rect.inflate(-100, -100)
        self.moving = True

        # combat
        self.damage = 50
        self.is_in_movement_area = True
        self.can_teleport = True
        self.can_attack = True
        self.can_damage = False

        # draw teleportation line
        self.can_draw_line = True
        self.activate_line_timer = True
        self.teleporting = False
        self.teleport_cooldown = False

        self.can_turn_in_area = True
        self.can_turn_in_area_timer = Timer(100, func=lambda: setattr(self, 'can_turn_in_area', True))
        self.attack_cooldown_timer = Timer(1, func=lambda: setattr(self, 'can_attack', True))
        self.damage_cooldown_timer = Timer(700, func=lambda: setattr(self, 'can_damage', True))
        self.teleportation_damage_timer = Timer(100, func=lambda: setattr(self, 'can_damage', True))
        self.line_draw_timer = Timer(100, func=lambda: setattr(self, 'can_draw_line', False))
        self.teleport_cooldown_timer = Timer(200,
                                             func=lambda: (self.teleport(), setattr(self, 'teleport_cooldown', False)))

    def teleport(self):
        self.frame_index = 0
        self.teleporting = True
        self.can_teleport = False
        self.is_in_movement_area = False

        if self.player.flip:
            self.moving = False
            self.rect.x = self.player.hitbox_rect.right - 50
            self.rect.y = self.player.hitbox_rect.centery - 100

        else:
            self.moving = False
            self.rect.x = self.player.hitbox_rect.left - 125
            self.rect.y = self.player.hitbox_rect.centery - 100

        self.teleportation_damage_timer.activate()

    def initiate_attack(self):
        def check_for_range():
            distance = 60
            if self.rect.y > self.player.rect.y:
                if (((0 < self.rect.centerx - self.player.rect.centerx < distance) and self.can_attack) or (
                        (0 > self.rect.centerx - self.player.rect.centerx > -distance) and self.can_attack)) \
                        and self.rect.y - self.player.rect.y < distance:
                    return True

        if self.can_teleport:
            range_rect_pos = (self.rect.left - 450, self.rect.top - 250)
            range_rect = pygame.Rect(range_rect_pos, (1000, 700))
            if range_rect.contains(self.player.hitbox_rect):
                self.teleport_cooldown = True
                self.teleport_cooldown_timer.activate()

        if not self.is_in_movement_area:
            enemy_pos = Vector2(self.rect.center)
            player_pos = Vector2(self.player.rect.center) + Vector2(0, -20)
            self.direction = (player_pos - enemy_pos)
            self.direction = self.direction.normalize() if self.direction else self.direction

        if check_for_range() and self.can_attack and not self.teleporting:
            self.frame_index = 0
            self.state = 'attack'
            self.can_attack = False
            self.moving = False

        if pygame.sprite.spritecollide(self, self.player_sprites, False,
                                       pygame.sprite.collide_mask) and self.can_damage and self.state == 'attack' and (
                11 > self.frame_index > 9):
            # 9 and 10
            self.deal_damage()
            self.can_damage = False
            self.damage_cooldown_timer.activate()

    def movement(self, dt):
        self.camera_x = self.player.rect.centerx - WINDOW_WIDTH // 2
        self.camera_y = self.player.rect.centery - WINDOW_HEIGHT // 2
        area_pos = (self.starting_pos[0] - 200, self.starting_pos[1] - 80)
        area_rect = pygame.Rect(area_pos, (400, 200))

        if self.can_turn_in_area and self.is_in_movement_area:
            if not area_rect.contains(self.hitbox_rect):
                self.direction.x *= -1
                self.can_turn_in_area = False
                self.can_turn_in_area_timer.activate()

        if self.moving:
            self.hitbox_rect.x += self.direction.x * self.speed * dt
            self.collisions('horizontal', self.hitbox_rect)
            self.hitbox_rect.y += self.direction.y * self.speed * dt
            self.collisions('vertical', self.hitbox_rect)
            self.rect.center = self.hitbox_rect.center

    def animate(self, dt):
        if self.direction.x < 0:
            self.flip = True
        elif self.direction.x > 0:
            self.flip = False

        if self.teleporting:
            self.state = 'teleport'

        if self.direction and self.moving and not self.teleporting and not self.teleport_cooldown:
            self.state = 'walk'

        def animation_speeds():
            match self.state:
                case 'idle' | 'walk':
                    self.animation_speed = 10
                case 'attack':
                    self.animation_speed = 15
                case 'hurt':
                    self.animation_speed = 15
                case 'teleport':
                    self.animation_speed = 8
                case 'death':
                    self.animation_speed = 12

        animation_speeds()
        self.frame_index += self.animation_speed * dt

        match self.state:
            case 'idle' | 'walk':
                self.animate_state(looped=True)
            case 'hurt':
                self.animate_state(looped=False,
                                   func=lambda: (setattr(self, 'moving', True), setattr(self, 'can_attack', True),
                                                 self.check_for_death()))
            case 'attack':
                self.animate_state(looped=False,
                                   func=lambda: (setattr(self, 'moving', True), self.attack_cooldown_timer.activate()))
            case 'death':
                self.animate_state(looped=False, func=self.kill)
            case 'teleport':
                self.animate_state(looped=False,
                                   func=lambda: (setattr(self, 'teleporting', False), setattr(self, 'moving', True)))

    def draw_teleportation_line(self):
        camera_x = self.player.rect.centerx - WINDOW_WIDTH // 2
        camera_y = self.player.rect.centery - WINDOW_HEIGHT // 2
        color = 'darkviolet'

        if self.can_teleport:
            self.start_p = (self.rect.centerx - camera_x, self.rect.centery - camera_y)

        if not self.can_teleport and self.can_draw_line:
            end_p = (self.rect.centerx - camera_x, self.rect.centery - camera_y + 15)
            pygame.draw.line(self.screen, color, self.start_p, end_p, 3)
            pygame.draw.circle(self.screen, color, self.start_p, 1)
            pygame.draw.circle(self.screen, color, end_p, 1)
            if self.activate_line_timer:
                self.line_draw_timer.activate()
                self.activate_line_timer = False

    def update(self, dt):
        self.teleport_cooldown_timer.update()

        if not self.player.is_dead and not self.teleport_cooldown:
            self.teleportation_damage_timer.update()
            if self.can_draw_line:
                self.line_draw_timer.update()
            if not self.can_damage:
                self.damage_cooldown_timer.update()
            if not self.can_turn_in_area:
                self.can_turn_in_area_timer.update()
            if not self.can_attack:
                self.attack_cooldown_timer.update()
            if not self.is_dead:
                self.movement(dt)
                self.initiate_attack()
        else:
            self.state = 'idle' if self.frame_index > self.animation_length else 1

        self.hitbox_rect = self.rect.inflate(-100, -100)
        self.animate(dt)


class Necromancer(Enemy):
    def __init__(self, pos, frames, player, player_sprites, starting_pos, collision_sprites, groups,
                 lasers, skeleton_frames):
        super().__init__(pos, frames, player, player_sprites, collision_sprites, groups)
        self.groups = groups
        self.all_sprites = groups[0]
        self.health = 80
        self.direction = Vector2(uniform(0, 1), uniform(0, 1))
        self.speed = 100
        self.hitbox_rect = self.rect.inflate(-110, -50)
        self.starting_pos = starting_pos
        self.collision_sprites = collision_sprites

        self.can_change_direction = True
        self.can_attack = True
        self.change_direction_timer = Timer(2100, func=lambda: setattr(self, 'can_change_direction', True))
        self.attack_cooldown_timer = Timer(2000, func=lambda: setattr(self, 'can_attack', True))
        self.moving = True
        self.laser_damage = 40
        self.can_create_laser = True
        self.laser_creation_timer = Timer(200, func=lambda: setattr(self, 'can_create_laser', True))
        self.lasers = lasers

        self.can_spawn_skeletons = True
        self.skeleton_summoning_timer = Timer(200, func=lambda: setattr(self, 'can_spawn_skeletons', True))

        self.skeleton_frames = skeleton_frames

    def skeleton_spell(self):
        self.frame_index = 0
        self.state = 'attack-1'
        self.moving = False
        self.attack_cooldown_timer.activate()

    def summon_skeletons(self):
        offset = 50
        for i in range(1):
            pos = self.rect.center + Vector2(random.randint(-offset - 20, offset), random.randint(-offset - 20, offset))
            SmallSkeleton(pos, self.skeleton_frames, self.player,
                          self.player_sprites, self.collision_sprites, self.groups, True)

    def attack(self):
        self.frame_index = 0
        self.state = 'attack-3'
        self.moving = False
        self.attack_cooldown_timer.activate()

    def movement(self, dt):
        # flip
        if self.direction.x > 0:
            self.flip = False
        elif self.direction.x < 0:
            self.flip = True

        # range rect
        range_rect_size = (900, 700)
        range_rect_offset = Vector2(-380, -230)
        self.range_rect = FRect((self.rect.left, self.rect.top) + range_rect_offset,
                                range_rect_size)

        # area rect
        area_rect_size = (850, 600)
        area_rect_offset = Vector2(-430, - 250)
        self.area_rect = FRect((self.starting_pos[0], self.starting_pos[1]) + area_rect_offset,
                               area_rect_size)

        # movement
        self.direction = self.direction.normalize() if self.direction else self.direction
        if self.moving:
            self.hitbox_rect.centerx += self.direction.x * self.speed * dt
            self.collisions('horizontal', self.hitbox_rect)
            self.hitbox_rect.centery += self.direction.y * self.speed * dt
            self.collisions('vertical', self.hitbox_rect)
            self.rect.center = self.hitbox_rect.center

        # change the direction ever few second
        if self.can_change_direction:
            if self.area_rect.contains(self.hitbox_rect):
                self.direction = Vector2(uniform(-1, 1), uniform(-1, 1))
            else:
                self.direction.y *= -1
                self.direction.x *= -1
            self.can_change_direction = False
            self.change_direction_timer.activate()

        # attack if player is in range
        skeleton_spell_chance = 10  # chance is in percentages
        if self.range_rect.contains(self.player.hitbox_rect) and self.can_attack:
            if random.randint(0, 100) <= skeleton_spell_chance:
                self.skeleton_spell()
            else:
                self.attack()
            self.can_attack = False

    def animate(self, dt):
        def animation_speeds():
            match self.state:
                case 'idle':
                    self.animation_speed = 8
                case 'walk':
                    self.animation_speed = 8
                case 'attack-3':
                    self.animation_speed = 12
                case 'attack-1':
                    self.animation_speed = 6
                case 'hurt':
                    self.animation_speed = 12
                case 'death':
                    self.animation_speed = 8

        animation_speeds()
        self.frame_index += self.animation_speed * dt

        if self.direction and self.moving:
            self.state = 'walk'

        match self.state:
            case 'idle' | 'walk':
                self.animate_state(looped=True)
            case 'hurt':
                self.animate_state(looped=False, func=lambda: setattr(self, 'state', 'walk'))
                self.check_for_death()
            case 'attack-3':
                self.animate_state(looped=False,
                                   func=lambda: (setattr(self, 'frame_index', 0), setattr(self, 'moving', True)))

                if (14 > self.frame_index > 11) and self.can_create_laser:
                    NecromancerLaser(self.rect.topright + Vector2(-120, 75), self.player, self.player_sprites,
                                     self.laser_damage, self.collision_sprites,
                                     (self.all_sprites, self.lasers))
                    self.can_create_laser = False
                    self.laser_creation_timer.activate()
            case 'attack-1':
                self.animate_state(looped=False,
                                   func=lambda: (setattr(self, 'frame_index', 0), setattr(self, 'moving', True)))
                if (9 > self.frame_index > 8) and self.can_spawn_skeletons:
                    self.summon_skeletons()
                    self.can_spawn_skeletons = False
                    self.skeleton_summoning_timer.activate()

            case 'death':
                self.animate_state(looped=False, func=lambda: self.kill())

    def update(self, dt):
        if not self.is_dead:
            if not self.can_create_laser:
                self.laser_creation_timer.update()
            if not self.can_spawn_skeletons:
                self.skeleton_summoning_timer.update()

            if self.moving:
                self.change_direction_timer.update()
            if not self.can_attack:
                self.attack_cooldown_timer.update()
            self.movement(dt)
            self.hitbox_rect = self.rect.inflate(-110, -35) if self.direction.y > 0 else self.hitbox_rect
            self.hitbox_rect = self.rect.inflate(-110, -150) if self.direction.y < 0 else self.hitbox_rect

        self.animate(dt)


class NecromancerLaser(pygame.sprite.Sprite):
    def __init__(self, pos, player, player_sprites, damage, collision_sprites, groups):
        super().__init__(groups)
        self.image = pygame.transform.scale(
            pygame.image.load(join('..\\', 'static', 'images', 'Necromancer', 'laser.png')).convert_alpha(), (100, 100))
        self.rect = self.image.get_frect(topleft=pos)

        # movement
        self.player = player
        self.player_pos = Vector2(self.player.rect.center)
        self.laser_pos = Vector2(self.rect.center)
        self.direction = (self.player_pos - self.laser_pos)
        self.direction = self.direction.normalize() if self.direction else self.direction

        # flip
        self.flip = False
        if self.direction.x > 0:
            self.flip = False
        elif self.direction.x < 0:
            self.flip = True

        self.image = pygame.transform.flip(pygame.transform.scale(
            pygame.image.load(join('..\\', 'static', 'images', 'Necromancer', 'laser.png')), (100, 100)), self.flip,
            False)

        # others
        self.player_sprites = player_sprites
        self.speed = 500
        self.damage = damage
        self.can_damage_the_player = True
        self.collision_sprites = collision_sprites

        # lifetime
        self.lifetime = 2000  # 2s
        self.death_timer = Timer(self.lifetime, func=lambda: self.kill(), autostart=True)

    def move(self, dt):
        self.rect.center += self.direction * self.speed * dt

    def check_for_player_collision(self):
        if pygame.sprite.spritecollide(self, self.player_sprites, False,
                                       pygame.sprite.collide_mask) and self.can_damage_the_player:
            self.player.health -= self.damage
            self.player.state = 'hurt'
            self.player.onetap_animation_running = True
            self.player.frame_index = 0
            self.can_damage_the_player = False
            self.kill()

    def update(self, dt):
        self.death_timer.update()
        self.move(dt)
        self.check_for_player_collision()


class Goblin(Enemy):
    def __init__(self, pos, frames, player, player_sprites, collision_sprites, groups):
        super().__init__(pos, frames, player, player_sprites, collision_sprites, groups)
        self.hitbox_rect = self.rect.inflate(-102, -102)

        # movement
        self.direction = Vector2()
        self.speed = 160
        self.moving = True

        # animations
        self.animation_speed = 8

        # combat
        self.health = 60
        self.damage = 3
        self.can_attack = True

        self.death_timer = Timer(2000, func=lambda: self.kill())

    def move(self, dt):
        self.direction.x = self.player.rect.centerx - self.rect.centerx
        self.direction.y = self.player.rect.centery - self.rect.centery
        self.direction = self.direction.normalize() if self.direction else self.direction

        if self.moving:
            self.hitbox_rect.centerx += self.direction.x * self.speed * dt
            self.collisions('horizontal', self.hitbox_rect)
            self.hitbox_rect.centery += self.direction.y * self.speed * dt
            self.collisions('vertical', self.hitbox_rect)
            self.rect.center = self.hitbox_rect.center

    def attack(self):
        range_rect_pos = (self.rect.centerx, self.rect.centery) + Vector2(-20, 5)
        range_rect_size = (40, 10)
        range_rect = FRect(range_rect_pos, range_rect_size)

        # check if player is in range
        if range_rect.colliderect(self.player.hitbox_rect) and self.can_attack:
            self.frame_index = 0
            self.state = 'attack'
            self.moving = False
            self.can_attack = False

    def animate(self, dt):
        def animation_speeds():
            match self.state:
                case 'idle' | 'walk':
                    self.animation_speed = 10

        self.check_for_flip()
        animation_speeds()
        self.frame_index += self.animation_speed * dt

        match self.state:
            case 'idle' | 'walk':
                self.animate_state(looped=True)
            case 'hurt':
                if self.check_for_death():
                    self.death_timer.activate()
                self.moving = False
                self.animate_state(looped=False, func=lambda: setattr(self, 'moving', True))
            case 'death':
                self.animate_state(looped=False, func=lambda: (setattr(self, 'frame_index', 3)))
            case 'attack':
                if not self.is_dead:
                    self.animate_state(looped=False,
                                       func=lambda: (setattr(self, 'moving', True), setattr(self, 'can_attack', True)))
                    if pygame.sprite.spritecollide(self, self.player_sprites, False, pygame.sprite.collide_mask):
                        if 6 < self.frame_index < 7:
                            self.deal_damage()

        if self.direction and self.moving:
            self.state = 'walk'

    def update(self, dt):
        if not self.is_dead and not self.player.is_dead:
            self.move(dt)
            self.attack()
        else:
            self.death_timer.update()
        self.animate(dt)
        self.hitbox_rect = self.rect.inflate(-100, -100)

        if self.player.is_dead:
            self.state = 'idle'
            self.player.state = 'death'


class EvilEye(Enemy):
    def __init__(self, pos, frames, player, player_sprites, collision_sprites, groups):
        super().__init__(pos, frames, player, player_sprites, collision_sprites, groups)
        self.hitbox_rect = self.rect.inflate(-100, -100)

        # movement
        self.direction = Vector2()
        self.speed = 160
        self.moving = True

        # animations
        self.animation_speed = 8

        # combat
        self.health = 60
        self.damage = 40
        self.can_attack = True
        self.can_damage = True

        self.death_timer = Timer(10000, func=lambda: self.kill())
        self.can_damage_timer = Timer(100, func=lambda: setattr(self, 'can_damage', True))

    def move(self, dt):
        self.direction.x = self.player.rect.centerx - self.rect.centerx
        self.direction.y = self.player.rect.centery - self.rect.centery
        self.direction = self.direction.normalize() if self.direction else self.direction

        if self.moving:
            self.hitbox_rect.centerx += self.direction.x * self.speed * dt
            self.collisions('horizontal', self.hitbox_rect)
            self.hitbox_rect.centery += self.direction.y * self.speed * dt
            self.collisions('vertical', self.hitbox_rect)
            self.rect.center = self.hitbox_rect.center

    def attack(self):
        range_rect_pos = (self.rect.centerx, self.rect.centery) + Vector2(-20, 5)
        range_rect_size = (40, 10)
        range_rect = FRect(range_rect_pos, range_rect_size)

        # check if player is in range
        if range_rect.colliderect(self.player.hitbox_rect) and self.can_attack:
            self.frame_index = 0
            self.state = 'attack'
            self.moving = False
            self.can_attack = False

    def animate(self, dt):
        def animation_speeds():
            match self.state:
                case 'walk':
                    self.animation_speed = 10

        self.check_for_flip()
        animation_speeds()
        self.frame_index += self.animation_speed * dt

        match self.state:
            case 'walk':
                self.animate_state(looped=True)
            case 'hurt':
                if self.check_for_death():
                    self.death_timer.activate()
                self.moving = False
                self.animate_state(looped=False, func=lambda: setattr(self, 'moving', True))
            case 'death':
                self.animate_state(looped=False, func=lambda: (setattr(self, 'frame_index', 3)))
            case 'attack':
                if not self.is_dead:
                    self.animate_state(looped=False,
                                       func=lambda: (setattr(self, 'moving', True), setattr(self, 'can_attack', True)))
                    if pygame.sprite.spritecollide(self, self.player_sprites, False, pygame.sprite.collide_mask):
                        if (6 < self.frame_index < 7) and self.can_damage:
                            self.deal_damage()
                            self.can_damage = False
                            self.can_damage_timer.activate()

        if self.direction and self.moving:
            self.state = 'walk'

    def update(self, dt):
        if not self.is_dead and not self.player.is_dead:
            if not self.can_damage:
                self.can_damage_timer.update()
            self.move(dt)
            self.attack()
        else:
            self.death_timer.update()
        self.animate(dt)
        self.hitbox_rect = self.rect.inflate(-100, -100)


class DemonSlime(Enemy):
    def __init__(self, pos, frames, player, player_sprites, collision_sprites, groups):
        super().__init__(pos, frames, player, player_sprites, collision_sprites, groups)
        self.hitbox_rect = self.rect.inflate(-140, -130)

        # movement
        self.direction = Vector2()
        self.speed = 160
        self.moving = True

        # animations
        self.animation_speed = 8

        # combat
        self.health = 1000
        self.damage = 35
        self.can_attack = True
        self.can_damage = True

        self.death_timer = Timer(10000, func=lambda: self.kill())
        self.can_damage_timer = Timer(100, func=lambda: setattr(self, 'can_damage', True))

    def move(self, dt):
        player_pos = Vector2(self.player.rect.center) + Vector2(0, -70)
        enemy_pos = Vector2(self.rect.center)

        self.direction = (player_pos - enemy_pos)
        self.direction = self.direction.normalize() if self.direction else self.direction

        if self.moving:
            self.hitbox_rect.centerx += self.direction.x * self.speed * dt
            self.collisions('horizontal', self.hitbox_rect)
            self.hitbox_rect.centery += self.direction.y * self.speed * dt
            self.collisions('vertical', self.hitbox_rect)
            self.rect.center = self.hitbox_rect.center

    def attack(self):
        camera_x = self.player.rect.centerx - WINDOW_WIDTH // 2
        camera_y = self.player.rect.centery - WINDOW_HEIGHT // 2

        range_rect_pos = (self.rect.centerx, self.rect.centery) + Vector2(-15, 60)
        range_rect_size = (40, 10)
        range_rect = FRect(range_rect_pos, range_rect_size)
        pygame.draw.rect(self.screen, 'black', range_rect, 10)

        # check if player is in range
        if range_rect.colliderect(self.player.hitbox_rect) and self.can_attack:
            self.frame_index = 0
            self.state = 'attack'
            self.moving = False
            self.can_attack = False

    def animate(self, dt):
        def animation_speeds():
            match self.state:
                case 'walk':
                    self.animation_speed = 10

        if self.direction.x > 0:
            self.flip = True
        elif self.direction.x < 0:
            self.flip = False

        animation_speeds()
        self.frame_index += self.animation_speed * dt

        match self.state:
            case 'walk':
                self.animate_state(looped=True)
            case 'death':
                self.animate_state(looped=False, func=lambda: self.kill())
            case 'attack':
                if not self.is_dead:
                    self.animate_state(looped=False,
                                       func=lambda: (setattr(self, 'moving', True), setattr(self, 'can_attack', True)))
                    if pygame.sprite.spritecollide(self, self.player_sprites, False, pygame.sprite.collide_mask):
                        if (9 < self.frame_index < 12) and self.can_damage:
                            self.can_damage = False
                            self.can_damage_timer.activate()

        if self.direction and self.moving:
            self.state = 'walk'

    def update(self, dt):
        if self.check_for_death():
            self.death_timer.activate()
        if not self.is_dead and not self.player.is_dead:
            if not self.can_damage:
                self.can_damage_timer.update()
            self.move(dt)
            self.attack()
        else:
            self.death_timer.update()
        self.animate(dt)
        self.hitbox_rect = self.rect.inflate(-140, -150)
        print(self.health)
