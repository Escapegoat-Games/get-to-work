import pygame


class Spritesheet:
    def __init__(self, path):
        with open(path, "r") as f:
            raw_data = f.read()
        data = raw_data.split(",")
        sheet_img_path = data[0]
        self.sheet_img = pygame.image.load(sheet_img_path)
        self.tile_w = int(data[1])
        self.tile_h = int(data[2])
        self.columns = int(data[3])

    def image_at(self, tile_idx):
        x = tile_idx % self.columns * self.tile_w
        y = tile_idx // self.columns * self.tile_h
        size = (self.tile_w, self.tile_h)
        sprite_img = pygame.Surface(size)
        sprite_img.blit(
            self.sheet_img,
            (0, 0),
            (x, y, x + self.tile_w, y + self.tile_h),
        )
        return sprite_img
