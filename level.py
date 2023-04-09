import pygame
from spritesheet import Spritesheet
import utils


class Block(pygame.sprite.Sprite):
    def __init__(self, position, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = position


def char2idx(c):
    v = ord(c)
    if v >= ord("0") and v <= ord("9"):
        return v - ord("0")
    elif v >= ord("A") and v <= ord("Z"):
        return v - ord("A") + 10
    elif v >= ord("a") and v <= ord("z"):
        return v - ord("a") + 36


class Level:
    def __init__(self, path):
        with open(path, "r") as f:
            text = f.read()
        header_data, data = utils.parse_dat(text)
        ss_path = header_data["ss_path"]
        self.ss = Spritesheet(ss_path)

        offset_x = int(header_data["offset_x"])
        offset_y = int(header_data["offset_y"])
        curr_x = offset_x
        curr_y = offset_y
        self.blocks = []
        for line in data:
            for c in line:
                if c == "-":
                    pass
                else:
                    tile_idx = char2idx(c)
                    b = Block(
                        position=(curr_x, curr_y),
                        image=self.ss.image_at(tile_idx),
                    )
                    self.blocks.append(b)
                curr_x += self.ss.tile_w
            curr_x = offset_x
            curr_y += self.ss.tile_h

        self.blocks_list = pygame.sprite.Group()
        for b in self.blocks:
            self.blocks_list.add(b)
