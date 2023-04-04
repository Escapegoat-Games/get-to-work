import collections
import pygame
import vec2

WIDTH = 600
HEIGHT = 400

BACKGROUND = (0, 0, 0)

GRAVITY_ACC = (0, 0.2)
DRAG = 0.2
PLAYER_SPEED = 3
JUMP_SPEED = 5
SCREEN_CENTER = (300, 200)


def argmin(args):
    best_min = None
    idx = -1
    for i, x in enumerate(args):
        if best_min == None:
            best_min = x
            idx = i
        elif x < best_min:
            best_min = x
            idx = i
    return idx


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


class Block(pygame.sprite.Sprite):
    def __init__(self, position, size):
        super().__init__()
        self.image = pygame.Surface(size)
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect()
        self.rect.center = position


class Player(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__()
        self.image = pygame.Surface([10, 10])
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.velocity = (0, 0)
        self._last_jumped = 0
        self._is_grounded = False
        self._is_collide_bottom_history = collections.deque(maxlen=10)

    def update(self, blocks_list):
        is_colide_bottom = False

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
                left_dist = abs(self.rect.center[0] - hit_block.rect.left)
                right_dist = abs(self.rect.center[0] - hit_block.rect.right)
                top_dist = abs(self.rect.center[1] - hit_block.rect.top)
                bottom_dist = abs(self.rect.center[1] - hit_block.rect.bottom)
                min_idx = argmin(
                    [left_dist, right_dist, top_dist, bottom_dist]
                )
                if min_idx == 0:
                    self.rect.right = hit_block.rect.left
                    self.velocity = (0, self.velocity[1])
                elif min_idx == 1:
                    self.rect.left = hit_block.rect.right
                    self.velocity = (0, self.velocity[1])
                elif min_idx == 2:
                    self.rect.bottom = hit_block.rect.top
                    self.velocity = (self.velocity[0], 0)
                    is_colide_bottom = True
                else:
                    self.rect.top = hit_block.rect.bottom
                    self.velocity = (self.velocity[0], 0)

        self._is_collide_bottom_history.append(is_colide_bottom)
        self._is_grounded = len([
            x for x in self._is_collide_bottom_history if x
        ]) > 0

    def move_right(self):
        self.velocity = (PLAYER_SPEED, self.velocity[1])

    def move_left(self):
        self.velocity = (-PLAYER_SPEED, self.velocity[1])

    def jump(self):
        now = pygame.time.get_ticks()
        if self._is_grounded and now - self._last_jumped >= 10:
            self._last_jumped = pygame.time.get_ticks()
            self.velocity = vec2.add(self.velocity, (0, -JUMP_SPEED))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    player = Player(position=(0, 0))
    players_list = pygame.sprite.Group()
    players_list.add(player)

    cam = Camera(player, (100, 50))

    blocks = [
        Block(position=(0, 300), size=(50, 50)),
        Block(position=(300, 300), size=(300, 50)),
        Block(position=(300, 200), size=(50, 150)),
    ]
    blocks_list = pygame.sprite.Group()
    for b in blocks:
        blocks_list.add(b)

    is_k_left_down = False
    is_k_right_down = False
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    is_k_left_down = True
                if event.key == pygame.K_RIGHT:
                    is_k_right_down = True
                if event.key == pygame.K_UP:
                    player.jump()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    is_k_left_down = False
                if event.key == pygame.K_RIGHT:
                    is_k_right_down = False

        if is_k_left_down:
            player.move_left()
        if is_k_right_down:
            player.move_right()

        players_list.update(blocks_list)
        blocks_list.update()

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
        for b in blocks:
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
