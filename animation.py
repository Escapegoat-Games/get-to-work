import os
import pygame
import utils


class Animation:
    def __init__(self, path):
        with open(os.path.join(utils.get_resource_path(), path), "r") as f:
            text = f.read()
        header_data, data = utils.parse_dat(text)
        self.is_loop = header_data["is_loop"] == "1"

        self.frame_idx = 0
        self.frames = []
        for l in data:
            d = l.split(":")
            self.frames.append({
                "tile_idx": int(d[0]),
                "delay_ms": int(d[1]),
            })
        self.last_ms = None
        self.frame_idx = 0
        self.acc_ms = 0

    def reset(self):
        self.last_ms = pygame.time.get_ticks()
        self.acc_ms = 0

    def update(self):
        now = pygame.time.get_ticks()
        if self.last_ms == None:
            self.last_ms = now
        self.acc_ms += now - self.last_ms
        self.last_ms = now

        frame = self.frames[self.frame_idx]
        while self.acc_ms > frame["delay_ms"]:
            self.acc_ms -= frame["delay_ms"]
            if self.is_loop:
                self.frame_idx = (self.frame_idx + 1) % len(self.frames)
            else:
                self.frame_idx = len(self.frames) - 1

    def get_current_tile_idx(self):
        frame = self.frames[self.frame_idx]
        return frame["tile_idx"]
