import pygame


class NPC(pygame.sprite.Sprite):
    def __init__(self, ss, tile_idx, position, rect=None, anim=None, is_single_talk=False, dialogue=[], dialogue_callback=None):
        super().__init__()
        self.ss = ss
        self.tile_idx = tile_idx
        if rect:
            self.rect = rect
        else:
            self.rect = pygame.Rect(
                (0, 0), (self.ss.tile_w, self.ss.tile_h))
        self.rect.topleft = position
        self.image = self._get_image()
        self.anim = anim
        self.dialogue = dialogue
        self.is_single_talk = is_single_talk
        self.is_talked_once = False
        self.is_talking = False

        def dialogue_callback_wrapper():
            self.is_talking = False
            self.is_talked_once = True
            if dialogue_callback:
                dialogue_callback()

        self.dialogue_callback = dialogue_callback_wrapper

    def can_talk(self):
        if self.is_talking:
            return False
        elif self.is_single_talk:
            return not self.is_talked_once
        else:
            return True

    def talk(self, textbox):
        self.is_talking = True
        textbox.is_visible = True
        textbox.load(
            self.dialogue,
            self.dialogue_callback,
        )

    def update(self):
        self.image = self._get_image()

    def _get_image(self):
        if self.tile_idx == -1:
            # TODO: remove image after debug
            img = pygame.Surface(self.rect.size)
            img.fill((255, 0, 255))
            return img
        else:
            return self.ss.image_at(self.tile_idx)
