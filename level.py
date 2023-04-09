import pygame
from spritesheet import Spritesheet
import utils


class Block(pygame.sprite.Sprite):
    def __init__(self, position, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = position


CHAR_LOOKUP = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def char2idx(c):
    return CHAR_LOOKUP.find(c)


class Level:
    def __init__(self, path):
        with open(path, "r") as f:
            text = f.read()
        header_data, data = utils.parse_dat(text)
        ss_path = header_data["ss_path"]
        self.ss = Spritesheet(ss_path)

        offset_x = int(header_data["offset_x"])
        offset_y = int(header_data["offset_y"])
        collidable_blocks = set([c for c in header_data["collidable_blocks"]])
        curr_x = offset_x
        curr_y = offset_y
        self.collidable_blocks = []
        self.noncollidable_blocks = []
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
                    if c in collidable_blocks:
                        self.collidable_blocks.append(b)
                    else:
                        self.noncollidable_blocks.append(b)
                curr_x += self.ss.tile_w
            curr_x = offset_x
            curr_y += self.ss.tile_h

        self.collidable_blocks_list = pygame.sprite.Group()
        for b in self.collidable_blocks:
            self.collidable_blocks_list.add(b)
