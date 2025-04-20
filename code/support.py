import pygame

from settings import *


# without multiple_files argument u provide path for one file and amount of rows
# with multiple_files argument u can provide multiple files , and it merges it into one dictionary () - tuple with path and length

def tile_importer(cols, rows, size, file_paths, multiple_files=False):
    if not multiple_files:
        frames = []
        surf = pygame.image.load(file_paths).convert_alpha()
        cutout_width = surf.width / cols
        cutout_height = surf.height / rows
        row_frames_1 = []
        for row in range(rows):
            row_frames = []
            for col in range(cols):
                cutout_surf = pygame.Surface((cutout_width, cutout_height), pygame.SRCALPHA)
                cutout_rect = pygame.FRect(cutout_width * col, cutout_height * row, cutout_width, cutout_height)
                cutout_surf.blit(surf, (0, 0), cutout_rect)
                cutout_surf_scaled = pygame.transform.scale(cutout_surf, size)
                if rows == 1:
                    row_frames_1.append(cutout_surf_scaled)
                else:
                    row_frames.append(cutout_surf_scaled)
            frames.append(row_frames)

        if rows == 1:
            return row_frames_1
        else:
            return frames
    else:
        frames = []
        for path, length in file_paths:
            file_frames = []
            surf = pygame.image.load(path).convert_alpha()
            cutout_width = surf.width / length
            for col in range(cols):
                cutout_surf = pygame.Surface((cutout_width, surf.height), pygame.SRCALPHA)
                cutout_rect = pygame.FRect(cutout_width * col, 0, cutout_width, surf.height)
                cutout_surf.blit(surf, (0, 0), cutout_rect)
                cutout_surf_scaled = pygame.transform.scale(cutout_surf, size)
                file_frames.append(cutout_surf_scaled)
            frames.append(file_frames)
        return frames
