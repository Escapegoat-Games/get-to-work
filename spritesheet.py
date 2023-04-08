import pygame
import utils


class Spritesheet:
    def __init__(self, path):
        with open(path, "r") as f:
            text = f.read()
        header_data, _ = utils.parse_dat(text)
        img_path = header_data["img_path"]
        self.sheet_img = pygame.image.load(img_path)
        self.tile_w = int(header_data["tile_w"])
        self.tile_h = int(header_data["tile_h"])
        self.columns = int(header_data["columns"])

    def image_at(self, tile_idx):
        x = tile_idx % self.columns * self.tile_w
        y = tile_idx // self.columns * self.tile_h
        size = (self.tile_w, self.tile_h)
        sprite_img = pygame.Surface(size, pygame.SRCALPHA)
        sprite_img.blit(
            self.sheet_img,
            (0, 0),
            (x, y, x + self.tile_w, y + self.tile_h),
        )
        return sprite_img
