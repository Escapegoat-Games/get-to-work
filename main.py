import collections
import pygame
import spritesheet
import level
import vec2
import utils

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
SCREEN_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

BACKGROUND = (0, 0, 0)

GRAVITY_ACC = (0, 0.2)
DRAG = 0.2
PLAYER_SPEED = 3
JUMP_COOLDOWN = 100


def time_diff_to_strength(time_diff):
    return min(max(3, 0.06*time_diff), 8)


class Camera:
    def __init__(self, player, size):
        self.player = player
        self.position = player.rect.center
        self.size = size

    def update(self):
        w, h = self.size
        x, y = self.position
        player_x, player_y = self.player.rect.center
        if player_x > x + w:
            self.position = (player_x - w, self.position[1])
        if player_x < x - w:
            self.position = (player_x + w, self.position[1])
        if player_y > y + h:
            self.position = (self.position[0], player_y - h)
        if player_y < y - h:
            self.position = (self.position[0], player_y + h)


class Player(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__()
        player_ss = spritesheet.Spritesheet("assets/spritesheets/player.dat")
        self.image = player_ss.image_at(0)
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.velocity = (0, 0)
        self._last_jumped = 0
        self._is_grounded = False
        self._is_collide_bottom_history = collections.deque(maxlen=3)

    def update(self, blocks_list):
        is_collide_bottom = False

        self.velocity = vec2.add(self.velocity, GRAVITY_ACC)

        if abs(self.velocity[0]) > 0:
            drag_v = (-DRAG if self.velocity[0] > 0 else DRAG, 0)
            self.velocity = vec2.add(self.velocity, drag_v)

        self.rect.center = vec2.add(self.rect.center, self.velocity)

        # Collide player with ground
        blocks_hit_list = pygame.sprite.spritecollide(
            self, blocks_list, False)
        if blocks_hit_list:
            for hit_block in blocks_hit_list:
                # Make sure player is always outside of block
                left_dist = abs(self.rect.right - hit_block.rect.left)
                right_dist = abs(self.rect.left - hit_block.rect.right)
                top_dist = abs(self.rect.bottom - hit_block.rect.top)
                bottom_dist = abs(self.rect.top - hit_block.rect.bottom)
                min_idx = utils.argmin(
                    [top_dist, bottom_dist, left_dist, right_dist]
                )
                if min_idx == 0:
                    self.rect.bottom = hit_block.rect.top
                    self.velocity = (self.velocity[0], 0)
                    is_collide_bottom = True
                elif min_idx == 1:
                    self.rect.top = hit_block.rect.bottom
                    self.velocity = (self.velocity[0], 0)
                elif min_idx == 2:
                    pass
                    self.rect.right = hit_block.rect.left
                    self.velocity = (0, self.velocity[1])
                elif min_idx == 3:
                    pass
                    self.rect.left = hit_block.rect.right
                    self.velocity = (0, self.velocity[1])

        self._is_collide_bottom_history.append(is_collide_bottom)
        self._is_grounded = len([
            x for x in self._is_collide_bottom_history if x
        ]) > 0

    def move_right(self):
        self.velocity = (PLAYER_SPEED, self.velocity[1])

    def move_left(self):
        self.velocity = (-PLAYER_SPEED, self.velocity[1])

    def jump(self, strength):
        now = pygame.time.get_ticks()
        time_diff = now - self._last_jumped
        if self._is_grounded and time_diff >= JUMP_COOLDOWN:
            self._last_jumped = pygame.time.get_ticks()
            self.velocity = vec2.add(self.velocity, (0, -strength))


def main():
    pygame.init()
    screen = pygame.display.set_mode(
        SCREEN_SIZE, pygame.SCALED | pygame.RESIZABLE
    )
    clock = pygame.time.Clock()

    player = Player(position=(0, 0))
    players_list = pygame.sprite.Group()
    players_list.add(player)

    cam = Camera(player, (100, 50))

    lvl = level.Level("assets/levels/level01.dat")

    is_k_left_down = False
    is_k_right_down = False
    is_k_up_down = False
    jump_start_time = 0
    running = True
    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    is_k_left_down = True
                if event.key == pygame.K_RIGHT:
                    is_k_right_down = True
                if event.key == pygame.K_UP:
                    jump_start_time = pygame.time.get_ticks()
                    is_k_up_down = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    is_k_left_down = False
                if event.key == pygame.K_RIGHT:
                    is_k_right_down = False
                if event.key == pygame.K_UP:
                    is_k_up_down = False
                    time_diff = now - jump_start_time
                    strength = time_diff_to_strength(time_diff)
                    player.jump(strength)

        if is_k_left_down:
            player.move_left()
        if is_k_right_down:
            player.move_right()

        time_diff = now - jump_start_time
        if is_k_up_down and time_diff >= JUMP_COOLDOWN:
            strength = time_diff_to_strength(time_diff)
            player.jump(strength)

        players_list.update(lvl.blocks_list)
        lvl.blocks_list.update()

        cam.update()

        screen.fill(BACKGROUND)
        # players_list.draw(screen)
        # blocks_list.draw(screen)

        screen.blit(player.image, vec2.add(
            vec2.add(
                player.rect.topleft, vec2.scale(cam.position, -1)
            ),
            SCREEN_CENTER,
        ))
        for b in lvl.blocks:
            screen.blit(b.image, vec2.add(
                vec2.add(
                    b.rect.topleft, vec2.scale(cam.position, -1)
                ),
                SCREEN_CENTER,
            ))

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
