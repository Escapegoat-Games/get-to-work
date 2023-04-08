import pygame
import spritesheet


class Block(pygame.sprite.Sprite):
    def __init__(self, position, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = position


class Level:
    def __init__(self, path):
        with open(path, "r") as f:
            data = f.read().split("\n")
        header_data = data[0].split(",")
        ss_path = header_data[0]
        self.ss = spritesheet.Spritesheet(ss_path)

        offset_x = int(header_data[1])
        offset_y = int(header_data[2])
        curr_x = offset_x
        curr_y = offset_y
        self.blocks = []
        for line in data[1:]:
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
