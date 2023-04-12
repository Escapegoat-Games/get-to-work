import pygame


class NPC(pygame.sprite.Sprite):
    def __init__(self, ss, tile_idx, position, anim=None, dialogue=[], dialogue_callback=None):
        super().__init__()
        self.ss = ss
        self.tile_idx = tile_idx
        self.image = self.ss.image_at(self.tile_idx)
        self.rect = pygame.Rect(
            (0, 0), (self.ss.tile_w, self.ss.tile_h))
        self.rect.center = position
        self.anim = anim
        self.dialogue = dialogue
        self.dialogue_callback = dialogue_callback

    def update(self):
        self.image = self.ss.image_at(self.tile_idx)
