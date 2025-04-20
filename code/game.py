from settings import *
from groups import AllSprites
from support import tile_importer
from ui import Ui
from pytmx import load_pygame
from sprites import Sprite, CollisionSprite
from player import Player
from enemies import *
import json


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.player_sprites = pygame.sprite.Group()
        self.player_attack_sprites = pygame.sprite.Group()
        self.necromancer_lasers = pygame.sprite.Group()
        self.wave_enemies = pygame.sprite.Group()

        self.ground_locations = []
        self.load_assets()
        self.setup()
        self.game_music = pygame.mixer.Sound(join('..\\', 'static', 'audio', 'game-music.wav'))
        self.game_music.set_volume(0.1)
        self.game_music.play(-1)

        # ui
        self.ui = Ui(self.player)

        # gameplay
        self.current_wave = 1
        self.game_started = False
        with open(join('..\\', 'static', 'data', 'waves_info.json')) as json_file:
            self.json_data = json.load(json_file)

    def load_assets(self):
        # 2nd argument is animation length
        # player
        player_frames = tile_importer(9, 7, (260, 260), join('..\\', 'static', 'images', 'Soldier', 'Soldier.png'))
        self.player_frames = {
            'idle': [player_frames[0], 6],
            'walk': [player_frames[1], 8],
            'basic-attack': [player_frames[2], 6],
            'heavy-attack': [player_frames[3], 6],
            'ranged-attack': [player_frames[4], 9],
            'hurt': [player_frames[5], 4],
            'death': [player_frames[6], 4]
        }
        # player attacks
        player_attack_frames = tile_importer(6, 1, (400, 400),
                                             (
                                                 (join('..\\', 'static', 'images', 'Soldier', 'basic_effect.png'), 6),
                                                 (join('..\\', 'static', 'images', 'Soldier', 'heavy_effect.png'), 6),
                                                 (join('..\\', 'static', 'images', 'Soldier', 'ranged_effect.png'), 6)
                                             ), multiple_files=True)
        self.player_attack_frames = {
            'basic-effect': [player_attack_frames[0][3], player_attack_frames[0][4]],
            'heavy-effect': [player_attack_frames[1][3], player_attack_frames[1][4]],
            'ranged-effect': [player_frames[2][4], player_attack_frames[2][5]]
        }
        # skeleton frames
        skeleton_frames = tile_importer(13, 5, (170, 170), join('..\\', 'static', 'images', 'Skeleton', 'skeleton.png'))
        self.skeleton_frames = {
            'attack': [skeleton_frames[0], 13],
            'death': [skeleton_frames[1], 13],
            'walk': [skeleton_frames[2], 12],
            'idle': [skeleton_frames[3], 4],
            'hurt': [skeleton_frames[4], 3]
        }
        # small skeleton
        small_skeleton_frames = tile_importer(8, 1, (125, 125), (
            (join('..\\', 'static', 'images', 'Small_Skeleton',
                  'Attack.png'), 8),
            (join('..\\', 'static', 'images', 'Small_Skeleton',
                  'Death.png'), 4),
            (join('..\\', 'static', 'images', 'Small_Skeleton',
                  'Idle.png'), 4),
            (join('..\\', 'static', 'images', 'Small_Skeleton',
                  'Shield.png'), 4),
            (join('..\\', 'static', 'images', 'Small_Skeleton',
                  'Hurt.png'), 4),
            (join('..\\', 'static', 'images', 'Small_Skeleton',
                  'Walk.png'), 4)
        ),
                                              multiple_files=True)
        self.small_skeleton_frames = {
            'attack': [small_skeleton_frames[0], 8],
            'death': [small_skeleton_frames[1], 4],
            'idle': [small_skeleton_frames[2], 4],
            'shield': [small_skeleton_frames[3], 4],
            'hurt': [small_skeleton_frames[4], 4],
            'walk': [small_skeleton_frames[5], 4]
        }
        # night borne
        night_borne_frames = tile_importer(23, 5, (170, 170),
                                           join('..\\', 'static', 'images', 'NightBorn', 'NightBorne.png'))
        self.night_borne_frames = {
            'idle': [night_borne_frames[0], 9],
            'walk': [night_borne_frames[1], 6],
            'attack': [night_borne_frames[2], 12],
            'hurt': [night_borne_frames[3], 5],
            'death': [night_borne_frames[4], 23],
            'teleport': [[night_borne_frames[2][2], night_borne_frames[4][13], night_borne_frames[4][14],
                          night_borne_frames[4][15], night_borne_frames[4][16]], 5]
        }
        # necromancer
        necromancer_frames = tile_importer(17, 7, (170, 170), join('..\\', 'static', 'images', 'Necromancer',
                                                                   'necromancer.png'))
        self.necromancer_frames = {
            'idle': [necromancer_frames[0], 8],
            'walk': [necromancer_frames[1], 8],
            'attack-1': [necromancer_frames[2], 13],
            'attack-2': [necromancer_frames[3], 13],
            'attack-3': [necromancer_frames[4], 17],
            'hurt': [necromancer_frames[5], 5],
            'death': [necromancer_frames[6], 10]
        }
        # goblin
        goblin_frames = tile_importer(8, 1, (150, 150), (
            (join('..\\', 'static', 'images', 'Goblin', 'Attack.png'), 8),
            (join('..\\', 'static', 'images', 'Goblin', 'Death.png'), 4),
            (join('..\\', 'static', 'images', 'Goblin', 'Idle.png'), 4),
            (join('..\\', 'static', 'images', 'Goblin', 'Run.png'), 8),
            (join('..\\', 'static', 'images', 'Goblin', 'Hurt.png'), 4)
        ), multiple_files=True)
        self.goblin_frames = {
            'attack': [goblin_frames[0], 8],
            'death': [goblin_frames[1], 4],
            'idle': [goblin_frames[2], 4],
            'walk': [goblin_frames[3], 8],
            'hurt': [goblin_frames[4], 4]
        }
        # evil eye
        evil_eye_frames = tile_importer(8, 1, (169, 169), (
            (join('..\\', 'static', 'images', 'Evil eye', 'Attack.png'), 8),
            (join('..\\', 'static', 'images', 'Evil eye', 'Death.png'), 4),
            (join('..\\', 'static', 'images', 'Evil eye', 'Flight.png'), 8),
            (join('..\\', 'static', 'images', 'Evil eye', 'Hurt.png'), 4)
        ), multiple_files=True)
        self.evil_eye_frames = {
            'attack': [evil_eye_frames[0], 8],
            'death': [evil_eye_frames[1], 4],
            'walk': [evil_eye_frames[2], 8],
            'hurt': [evil_eye_frames[3], 4]
        }
        # demon slime
        demon_slime_frames = tile_importer(22, 5, (300, 300),
                                           join('..\\', 'static', 'images', 'DemonSlimeBoss', 'demon_king.png'))
        self.demon_slime_frames = {
            'idle': [demon_slime_frames[0], 6],
            'walk': [demon_slime_frames[1], 12],
            'attack': [demon_slime_frames[2], 15],
            'hurt': [demon_slime_frames[3], 5],
            'death': [demon_slime_frames[4], 22]
        }

    def setup(self):
        map = load_pygame(join('..\\', 'static', 'data', 'map.tmx'))
        x_offset, y_offset = 150, 50

        # ground
        scaled_value = 48
        for x, y, image in map.get_layer_by_name('Ground').tiles():
            image = pygame.transform.scale(image, (scaled_value, scaled_value))
            Sprite(image, ((x * TILE_SIZE) + x_offset, (y * TILE_SIZE) + y_offset), self.all_sprites)

        # walls
        for x, y, image in map.get_layer_by_name('Walls').tiles():
            image = pygame.transform.scale(image, (scaled_value, scaled_value))
            CollisionSprite(image, ((x * TILE_SIZE) + x_offset, (y * TILE_SIZE) + y_offset),
                            (self.all_sprites, self.collision_sprites))

        for x, y, image in map.get_layer_by_name('Arena').tiles():
            self.ground_locations.append(
                (x * TILE_SIZE + x_offset + random.randint(15, 35), y * TILE_SIZE + y_offset + random.randint(15, 35)))

        for player_spawn in map.get_layer_by_name('Player'):
            self.player = Player((4368 + x_offset, 816 + y_offset), self.player_frames,
                                 self.player_attack_frames,
                                 self.collision_sprites,
                                 self.enemy_sprites, self.player_attack_sprites,
                                 (self.all_sprites, self.player_sprites))

    def spawn(self, entity, frames):
        pos = choice(self.ground_locations)
        if entity == Necromancer:
            return Necromancer(pos, frames, self.player, self.player_sprites, pos, self.collision_sprites,
                               (self.all_sprites, self.enemy_sprites), self.necromancer_lasers,
                               self.small_skeleton_frames)
        elif entity == SmallSkeleton:
            return SmallSkeleton(pos, frames, self.player, self.player_sprites, self.collision_sprites,
                                 (self.all_sprites, self.enemy_sprites), False)
        else:
            return entity(pos, frames, self.player, self.player_sprites,
                          self.collision_sprites, (self.all_sprites, self.enemy_sprites))

    def play_the_wave(self):
        self.ui.wave_multiplier = 0
        self.ui.direction_up = True
        self.ui.play_the_animation = True

        for enemy in self.json_data['waves-data'][self.current_wave - 1]['data']:
            enemy_class = globals().get(enemy)
            enemy_frames = None
            match enemy:
                case "Goblin":
                    enemy_frames = self.goblin_frames
                case "SmallSkeleton":
                    enemy_frames = self.small_skeleton_frames
                case "Necromancer":
                    enemy_frames = self.necromancer_frames
                case "Skeleton":
                    enemy_frames = self.skeleton_frames
                case "EvilEye":
                    enemy_frames = self.evil_eye_frames
                case "NightBorne":
                    enemy_frames = self.night_borne_frames
                case "DemonSlime":
                    enemy_frames = self.demon_slime_frames

            spawned_enemy = self.spawn(enemy_class, enemy_frames)
            self.wave_enemies.add(spawned_enemy)

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # update
            self.all_sprites.update(dt)
            if self.player.rect.centerx < 2910 + 150 and not self.game_started:
                self.play_the_wave()
                self.game_started = True
            if not self.wave_enemies and self.game_started:
                self.current_wave += 1
                self.ui.wave += 1
                self.play_the_wave()

            # draw
            self.screen.fill(color='black')
            self.all_sprites.draw(self.player.rect.center)
            self.ui.draw()
            pygame.display.update()
        pygame.quit()
