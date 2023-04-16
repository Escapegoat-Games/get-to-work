import enum
import collections
import pygame
from spritesheet import Spritesheet
from level import Level
from animation import Animation
from textbox import Textbox
from npc import NPC
import vec2
import utils

SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
SCREEN_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

BACKGROUND = (255, 255, 255)

GRAVITY_ACC = (0, 0.2)
DRAG = 0.2
PLAYER_SPEED = 2
JUMP_COOLDOWN = 100

tiles_ss = Spritesheet("assets/spritesheets/tiles.dat")
player_office_ss = Spritesheet("assets/spritesheets/player_office.dat")
player_pjs_ss = Spritesheet("assets/spritesheets/player_pjs.dat")

player_walk_anim = Animation("assets/animations/player_walk.dat")


class GameState(enum.Enum):
    PLAYER_CONTROL = 0
    TEXTBOX_CONTROL = 1


def time_diff_to_strength(time_diff):
    return min(max(3, 0.06*time_diff), 5)


def to_screen_coords(position, camera):
    return vec2.add(
        vec2.add(
            position, vec2.scale(camera.position, -1)
        ),
        SCREEN_CENTER,
    )


def is_block_on_screen(block, camera):
    coords = to_screen_coords(block.rect.topleft, camera)
    img_rect = block.image.get_rect()
    return coords[0] + img_rect.width >= 0 and coords[0] < SCREEN_WIDTH and coords[1] + img_rect.height >= 0 and coords[1] < SCREEN_HEIGHT


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


class PlayerState(enum.Enum):
    STANDING = 0
    WALKING = 1
    JUMPING = 2


class Player(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__()
        self.ss = player_pjs_ss
        self.image = self.ss.image_at(0)
        self.rect = pygame.Rect(
            (0, 0), (self.ss.tile_w, self.ss.tile_h))
        self.rect.topleft = position
        self.velocity = (0, 0)
        self._last_jumped = 0
        self._is_grounded = True
        self._is_collide_bottom_history = collections.deque(maxlen=5)
        self.walk_anim = player_walk_anim
        self.is_flipped = False
        self.state = PlayerState.STANDING

    def update(self, blocks_list):
        if self.state == PlayerState.STANDING:
            self.image = self.ss.image_at(0)
        elif self.state == PlayerState.WALKING:
            self.walk_anim.update()
            self.image = self.ss.image_at(
                self.walk_anim.get_current_tile_idx())
        if self.state == PlayerState.JUMPING:
            self.image = self.ss.image_at(1)

        if self.is_flipped:
            self.image = pygame.transform.flip(self.image, True, False)

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
                    self.state = PlayerState.STANDING
                elif min_idx == 1:
                    self.rect.top = hit_block.rect.bottom
                    self.velocity = (self.velocity[0], 0)
                elif min_idx == 2:
                    self.rect.right = hit_block.rect.left
                    self.velocity = (0, self.velocity[1])
                elif min_idx == 3:
                    self.rect.left = hit_block.rect.right
                    self.velocity = (0, self.velocity[1])

        self._is_collide_bottom_history.append(is_collide_bottom)
        self._is_grounded = len([
            x for x in self._is_collide_bottom_history if x
        ]) > 0
        if not self._is_grounded:
            self.state = PlayerState.JUMPING

    def move_right(self):
        self.is_flipped = False
        if self.state != PlayerState.JUMPING:
            self.state = PlayerState.WALKING
        self.velocity = (PLAYER_SPEED, self.velocity[1])

    def move_left(self):
        self.is_flipped = True
        if self.state != PlayerState.JUMPING:
            self.state = PlayerState.WALKING
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

    game_state = GameState.PLAYER_CONTROL

    textbox = Textbox()

    player = Player(position=(-48, 0))
    player_group = pygame.sprite.Group()
    player_group.add(player)

    npcs = []
    autotalk_npcs = []

    start_npc = NPC(ss=tiles_ss, tile_idx=-1, position=(-48, 0), rect=pygame.Rect(0, 0, 16, 16), is_single_talk=True, dialogue=[
        {
            "speaker": "Ada",
            "text": "Ugh...My head hurts.",
        },
        {
            "speaker": "Ada",
            "text": "What was I even doing last night?",
        },
        {
            "speaker": "Ada",
            "text": "I remember falling asleep and then...",
        },
        {
            "speaker": "Ada",
            "text": "...",
        },
        {
            "speaker": "Ada",
            "text": "Yeah nah. No idea.",
        },
        {
            "speaker": "Ada",
            "text": "The time is.........9AM!? I'm going to be late!\n\nWhere did I put my suit?!",
        },
    ])
    autotalk_npcs.append(start_npc)

    def clothes_npc_cb():
        clothes_npc.tile_idx = -1
        player.ss = player_office_ss

    clothes_npc = NPC(ss=tiles_ss, tile_idx=43, position=(32, -16), is_single_talk=True, dialogue=[
        {
            "speaker": "Ada",
            "text": "God I hate this suit.\n\nI wish it was Wear Your Pajamas to Work Day.",
        },
        {
            "speaker": "Ada",
            "text": "Actually.......................nah.",
        },
        {
            "speaker": "Ada",
            "text": "Nope nope nope.\n\nNot again after Harold and that HR fiasco last year.",
        },
    ], dialogue_callback=clothes_npc_cb)
    npcs.append(clothes_npc)

    leave_house_npc = NPC(ss=tiles_ss, tile_idx=-1, position=(368, -32), rect=pygame.Rect(0, 0, 16, 48), is_single_talk=True, dialogue=[
        {
            "speaker": "Ada",
            "text": "Dang. The ground's gone.",
        },
        {
            "speaker": "Ada",
            "text": "What a pain in the ass. Making me jump.",
        },
    ])
    autotalk_npcs.append(leave_house_npc)

    sign1_npc = NPC(ss=tiles_ss, tile_idx=47, position=(400, 0), dialogue=[
        {
            "speaker": "Sign",
            "text": "Endless pit of death ahead",
        },
        {
            "speaker": "Ada",
            "text": "(I guess I better not fall...)",
        },
    ])
    npcs.append(sign1_npc)

    sign2_npc = NPC(ss=tiles_ss, tile_idx=47, position=(1328, 208), dialogue=[
        {
            "speaker": "Sign",
            "text": "Endless pit of death ahead (seriously)",
        },
    ])
    npcs.append(sign2_npc)

    npc_group = pygame.sprite.Group()
    npc_group.add(npcs)
    autotalk_npc_group = pygame.sprite.Group()
    autotalk_npc_group.add(autotalk_npcs)

    cam = Camera(player, (20, 20))

    lvl = Level("assets/levels/level01.dat")

    is_k_left_down = False
    is_k_right_down = False
    is_k_up_down = False
    jump_start_time = 0
    running = True
    while running:
        now = pygame.time.get_ticks()

        # Events
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
                if event.key == pygame.K_z:
                    if game_state == GameState.PLAYER_CONTROL:
                        hit_npcs = pygame.sprite.spritecollide(
                            player, npc_group, False)
                        if hit_npcs:
                            hit_npc = hit_npcs[0]
                            if hit_npc.can_talk():
                                game_state = GameState.TEXTBOX_CONTROL
                                hit_npc.talk(textbox)
                    elif game_state == GameState.TEXTBOX_CONTROL:
                        if textbox.has_next_line():
                            textbox.move_next_line()
                        else:
                            textbox.is_visible = False
                            textbox.callback()
                            game_state = GameState.PLAYER_CONTROL
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    is_k_left_down = False
                if event.key == pygame.K_RIGHT:
                    is_k_right_down = False
                if event.key == pygame.K_UP:
                    is_k_up_down = False
                    if game_state == GameState.PLAYER_CONTROL:
                        time_diff = now - jump_start_time
                        strength = time_diff_to_strength(time_diff)
                        player.jump(strength)

        hit_npcs = pygame.sprite.spritecollide(
            player, autotalk_npcs, False)
        if hit_npcs:
            hit_npc = hit_npcs[0]
            if hit_npc.can_talk():
                game_state = GameState.TEXTBOX_CONTROL
                hit_npc.talk(textbox)

        # Update
        if game_state == GameState.PLAYER_CONTROL:
            if is_k_left_down:
                player.move_left()
            if is_k_right_down:
                player.move_right()
            time_diff = now - jump_start_time
            if is_k_up_down and time_diff >= JUMP_COOLDOWN:
                strength = time_diff_to_strength(time_diff)
                player.jump(strength)
        elif game_state == GameState.TEXTBOX_CONTROL:
            textbox.update()
        player_group.update(lvl.collidable_block_group)
        lvl.collidable_block_group.update()
        npc_group.update()
        autotalk_npc_group.update()
        cam.update()

        # Render
        screen.fill(BACKGROUND)
        for layer in lvl.layers:
            for b in layer["collidable_blocks"]:
                if is_block_on_screen(b, cam):
                    screen.blit(b.image, to_screen_coords(b.rect.topleft, cam))
            for b in layer["noncollidable_blocks"]:
                if is_block_on_screen(b, cam):
                    screen.blit(b.image, to_screen_coords(b.rect.topleft, cam))
        for npc in npcs:
            screen.blit(npc.image, to_screen_coords(npc.rect.topleft, cam))
        for npc in autotalk_npcs:
            screen.blit(npc.image, to_screen_coords(npc.rect.topleft, cam))
        screen.blit(player.image, to_screen_coords(player.rect.topleft, cam))
        if textbox.is_visible:
            textbox_img = textbox.get_image()
            screen.blit(
                textbox_img,
                (0, SCREEN_HEIGHT - textbox_img.get_height() - 8),
            )

        debug_text = f"DEBUG:\nplayer_position:{player.rect.topleft}"
        debug_font = textbox.font
        debug_font_size = textbox.font_size
        for idx, line in enumerate(debug_text.split("\n")):
            debug_img = debug_font.render(
                line,
                False,
                (0, 0, 0),
            )
            screen.blit(debug_img, (8, 8+debug_font_size*idx))

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
