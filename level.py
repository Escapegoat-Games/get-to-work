import pygame
import spritesheet
import utils


class Block(pygame.sprite.Sprite):
    def __init__(self, position, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = position


class Level:
    def __init__(self, path):
        with open(path, "r") as f:
            text = f.read()
        header_data, data = utils.parse_dat(text)
        ss_path = header_data["ss_path"]
        self.ss = spritesheet.Spritesheet(ss_path)

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
                    # TODO: this only takes values from 0-9. make it more flexible
                    tile_idx = ord(c) - ord('0')
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
