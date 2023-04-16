import pygame


class Textbox:
    def __init__(self):
        self.font_size = 8
        self.font = pygame.font.Font(
            "assets/fonts/Grand9K Pixel.ttf", self.font_size)
        self.char_idx = 0
        self.line_idx = 0
        self.dialogue = []
        self.last_ms = None
        self.acc_ms = 0
        self.delay_ms = 30
        self.textbox_img = pygame.image.load("assets/images/textbox.png")
        self.is_visible = False
        self.callback = None

    def update(self):
        now = pygame.time.get_ticks()
        if self.last_ms == None:
            self.last_ms = now
        self.acc_ms += now - self.last_ms
        self.last_ms = now
        if self.acc_ms > self.delay_ms:
            self.acc_ms = 0
            if self.line_idx < len(self.dialogue):
                dialogue_line = self.dialogue[self.line_idx]
                if self.char_idx < len(dialogue_line["text"]):
                    self.char_idx += 1

    def has_next_line(self):
        return self.line_idx + 1 < len(self.dialogue)

    def move_next_line(self):
        self.line_idx += 1
        self.char_idx = 0

    def load(self, dialogue, callback):
        self.char_idx = 0
        self.line_idx = 0
        self.dialogue = dialogue
        self.callback = callback

    def get_image(self):
        img = self.textbox_img.copy()
        if len(self.dialogue) > 0:
            speaker_img = self.font.render(
                self.dialogue[self.line_idx]["speaker"],
                False,
                (0, 0, 0),
            )
            img.blit(speaker_img, (24, 19))

            texts = self.dialogue[self.line_idx]["text"][:self.char_idx].split(
                "\n")
            for idx, text in enumerate(texts):
                text_img = self.font.render(
                    text,
                    False,
                    (0, 0, 0),
                )
                img.blit(text_img, (24, 40 + self.font_size*idx))

        return img
