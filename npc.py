import pygame
from spritesheet import Spritesheet


class NPC(pygame.sprite.Sprite):
    def __init__(self, position, dialogue):
        super().__init__()
        self.ss = Spritesheet(
            "assets/spritesheets/player.dat")
        self.image = self.ss.image_at(0)
        self.rect = pygame.Rect(
            (0, 0), (self.ss.tile_w, self.ss.tile_h))
        self.rect.center = position
        self.dialogue = dialogue

    def talk(self, textbox):
        textbox.is_visible = True
        textbox.load(self.dialogue)
