import os
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
    GAME_OVER = 2


class GameManager:
    def __init__(self, game_state):
        self.game_state = game_state
        self.office_clothes_flag = False
        self.left_home_flag = False


class Fader(pygame.sprite.Sprite):
    def __init__(self,  color=(0, 0, 0), delta=5):
        super().__init__()
        self.rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.image.fill(color)
        self.alpha = 255
        self.image.set_alpha(self.alpha)
        self.target_alpha = self.alpha
        self.delta = delta

    def fade_in(self):
        self.target_alpha = 0

    def fade_out(self):
        self.target_alpha = 255

    def update(self):
        if self.alpha < self.target_alpha:
            self.alpha += self.delta
        elif self.alpha > self.target_alpha:
            self.alpha -= self.delta
        self.image.set_alpha(self.alpha)


class EndingScreen(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.font = pygame.font.Font(os.path.join(
            utils.get_resource_path(), "assets/fonts/Grand9K Pixel.ttf"), 10)
        self.rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.ending_text = "THE END"
        self.start_ms = -1
        self.is_playing = False
        self.callback = None

    def play(self, ending_text, callback=None):
        self.start_ms = pygame.time.get_ticks()
        self.is_playing = True
        self.ending_text = ending_text
        self.callback = callback

    def update(self):
        if self.is_playing:
            now = pygame.time.get_ticks()
            self.image = pygame.Surface(self.rect.size)
            self.image.fill((0, 0, 0))
            lines = self.ending_text.split("\n")
            for idx, text in enumerate(lines):
                text_img = self.font.render(
                    text,
                    False,
                    (255, 255, 255),
                )
                text_img_rect = text_img.get_rect()
                self.image.blit(text_img, (SCREEN_WIDTH // 2 - text_img_rect.width //
                                           2, SCREEN_HEIGHT // 2 - text_img_rect.height // 2 + 10*idx))
            if now - self.start_ms > 100:
                if self.callback:
                    self.callback()


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


def time_diff_to_strength(time_diff):
    return min(max(3, 0.06*time_diff), 5)


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

    game_manager = GameManager(GameState.PLAYER_CONTROL)

    textbox = Textbox()
    fader = Fader(color=(0, 0, 0))
    fader.fade_in()

    ending_screen = EndingScreen()

    player = Player(position=(-48, 0))
    player_group = pygame.sprite.Group()
    player_group.add(player)

    npcs = []
    autotalk_npcs = []

    def start_pre():
        fader.fade_in()

    start_npc = NPC(
        ss=tiles_ss,
        tile_idx=-1,
        position=(-48, 0),
        rect=pygame.Rect(0, 0, 16, 16),
        is_single_talk=True,
        dialogue=[
            {
                "speaker": "Ada",
                "text": "Ow...My head hurts.",
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
                "text": "Yeah no idea.",
            },
            {
                "speaker": "Ada",
                "text": "The time is.........9AM!? I'm going to be late!",
            },
            {
                "speaker": "Ada",
                "text": "At least I put my suit on the drawer.\n\nAll I need to do is walk over to it and press (Z) to put it on.",
            },
        ],
        pre_dialogue=start_pre,
    )
    autotalk_npcs.append(start_npc)

    def clothes_npc_post():
        clothes_npc.tile_idx = -1
        player.ss = player_office_ss
        game_manager.office_clothes_flag = True

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
            "text": "Never again after Harold and that HR fiasco last year.",
        },
    ], post_dialogue=clothes_npc_post)
    npcs.append(clothes_npc)

    def leave_house_post():
        game_manager.left_home_flag = True

    leave_house_npc = NPC(
        ss=tiles_ss,
        tile_idx=-1,
        position=(368, -32),
        rect=pygame.Rect(0, 0, 16, 48),
        is_single_talk=True,
        dialogue=[
            {
                "speaker": "Ada",
                "text": "Dang what happened? The ground's floating.",
            },
            {
                "speaker": "Ada",
                "text": "What a pain in the ass. Making me jump with the arrow pad.",
            },
        ],
        post_dialogue=leave_house_post,
    )
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

    sign3_npc = NPC(ss=tiles_ss, tile_idx=47, position=(944, 0), dialogue=[
        {
            "speaker": "Ada",
            "text": "There's something pinned to the sign...",
        },
        {
            "speaker": "???",
            "text": "May 6th, 2023",
        },
        {
            "speaker": "???",
            "text": "I did not build it. I did not build it. I did not build it. I did not build it.\n\nI am not responsible. I am not responsible. I am not responsible.",
        },
        {
            "speaker": "Ada",
            "text": "...the rest of it is missing.",
        },
    ])
    npcs.append(sign3_npc)

    sign4_npc = NPC(ss=tiles_ss, tile_idx=47, position=(1712, -32), dialogue=[
        {
            "speaker": "Sign",
            "text": "Having a bad day? Is your world falling apart?",
        },
        {
            "speaker": "Sign",
            "text": "Come and take a break at Franz's Coffee!\n\nYou can find us just down this ledge!",
        },
        {
            "speaker": "Sign",
            "text": "We're pet friendly too :3",
        },
    ])
    npcs.append(sign4_npc)

    sign5_npc = NPC(ss=tiles_ss, tile_idx=47, position=(1600, -176), dialogue=[
        {
            "speaker": "Ada",
            "text": "There's something pinned to the sign...",
        },
        {
            "speaker": "???",
            "text": "Jan 2nd, 2023",
        },
        {
            "speaker": "???",
            "text": "Small-scale graviton tests were a success. Observations were\n\nwithin 2 microns of predictions theorized by the Weiss-Sakae\n\nconjecture.",
        },
        {
            "speaker": "???",
            "text": "Tomorrow we will begin our first practical field tests.\n\nTeam is apprehensive. They say it's too risky. They say\n\nwe are playing God.",
        },
        {
            "speaker": "???",
            "text": "However, it is too late to stop.\n\nWe must march on whether we like it or not.",
        },
        {
            "speaker": "Ada",
            "text": "...the rest of it is missing.",
        },
    ])
    npcs.append(sign5_npc)

    sign6_npc = NPC(ss=tiles_ss, tile_idx=47, position=(2464, 208), dialogue=[
        {
            "speaker": "Sign",
            "text": "Franz's Coffee\n\nHome of the best macchiato in the Aether!",
        },
    ])
    npcs.append(sign6_npc)

    sign7_npc = NPC(ss=tiles_ss, tile_idx=47, position=(2800, 32), dialogue=[
        {
            "speaker": "Ada",
            "text": "There's something pinned to the sign...",
        },
        {
            "speaker": "???",
            "text": "Mar 12th, 2023",
        },
        {
            "speaker": "???",
            "text": "Empirical tests are not looking good. Numbers are off from\n\nprediction by 2-6 microns.",
        },
        {
            "speaker": "???",
            "text": "The machine needs to change, but the engineers say it's too\n\nlate to modify spec.",
        },
        {
            "speaker": "???",
            "text": "Higher-ups are adamant we continue with what we have.",
        },
        {
            "speaker": "???",
            "text": "We can only hope that these mistakes do not blossom into\n\n irreversible catastrophe.",
        },
        {
            "speaker": "Ada",
            "text": "...the rest of it is missing.",
        },
    ])
    npcs.append(sign7_npc)

    # TODO: add more npcs...

    def office_ender_post():
        fader.fade_out()
        if game_manager.left_home_flag and game_manager.office_clothes_flag:
            def ending_cb():
                game_manager.game_state = GameState.GAME_OVER
                ending_screen.play("THE END\n\nOFFICE")

            game_manager.game_state = GameState.TEXTBOX_CONTROL
            textbox.is_visible = True
            textbox.load([
                {
                    "speaker": "???",
                    "text": "...and so in the end, Ada made it to the office.",
                },
                {
                    "speaker": "???",
                    "text": "Although she was late (like really fucking late), no one noticed.",
                },
                {
                    "speaker": "???",
                    "text": "Ada worked a full 8 hours that day, and slipped out\n\njust before 6.",
                },
                {
                    "speaker": "???",
                    "text": "Walking down the street hop in step, a crazy thought\n\nsuddenly entered her head.",
                },
                {
                    "speaker": "???",
                    "text": "However, it was a trifle matter, soon lost to time like many\n\nothers.",
                },
            ], ending_cb)
        elif game_manager.left_home_flag and not game_manager.office_clothes_flag:
            def ending_cb():
                game_manager.game_state = GameState.GAME_OVER
                ending_screen.play("THE END\n\nPAJAMAS")

            game_manager.game_state = GameState.TEXTBOX_CONTROL
            textbox.is_visible = True
            textbox.load([
                {
                    "speaker": "???",
                    "text": "...and so in the end, Ada made it to the office.",
                },
                {
                    "speaker": "???",
                    "text": "Although, in her haste she had forgotten to change out of her\n\npajamas.",
                },
                {
                    "speaker": "???",
                    "text": "Thankfully, it was Wear Your Pajamas to Work Day.",
                },
            ], ending_cb)
        else:
            def ending_cb():
                game_manager.game_state = GameState.GAME_OVER
                ending_screen.play("THE END\n\n???")

            game_manager.game_state = GameState.TEXTBOX_CONTROL
            textbox.is_visible = True
            textbox.load([
                {
                    "speaker": "???",
                    "text": "Somehow, Ada made it to the office without leaving her house.",
                },
                {
                    "speaker": "???",
                    "text": "Even Ada herself was confused as to how she did it.",
                },
                {
                    "speaker": "???",
                    "text": "...",
                },
                {
                    "speaker": "???",
                    "text": "What? I don't know how you did it either.\n\nMaybe file a bug or something...",
                },
                {
                    "speaker": "???",
                    "text": "Anyways.",
                },
                {
                    "speaker": "???",
                    "text": "Narrator out. Peace.",
                },
            ], ending_cb)

    office_ender_npc = NPC(
        ss=tiles_ss,
        tile_idx=-1,
        position=(4912, 16),
        rect=pygame.Rect(0, 0, 16, 64),
        is_single_talk=True,
        dialogue=[
            {
                "speaker": "Ada",
                "text": "Finally! I made it!",
            },
        ],
        post_dialogue=office_ender_post,
    )
    autotalk_npcs.append(office_ender_npc)

    def pit_ender_post():
        fader.fade_out()

        def ending_cb():
            game_manager.game_state = GameState.GAME_OVER
            ending_screen.play("THE END\n\nPIT")

        game_manager.game_state = GameState.TEXTBOX_CONTROL
        textbox.is_visible = True
        textbox.load([
            {
                "speaker": "???",
                "text": "Ada was found 6 hours later by a passing jogger.",
            },
            {
                "speaker": "???",
                "text": "No one, not even her close friends and family, had a clue as to\n\nwhy she would have jumped in the first place.",
            },
            {
                "speaker": "???",
                "text": "Perhaps she had merely lost her footing in an accident.",
            },
            {
                "speaker": "???",
                "text": "Whatever the case, the Earth continued to spin\n\nand life moved on.",
            },
        ], ending_cb)

    pit_ender_npc = NPC(
        ss=tiles_ss,
        tile_idx=-1,
        position=(0, 512),
        rect=pygame.Rect(0, 0, 5000, 32),
        is_single_talk=True,
        post_dialogue=pit_ender_post
    )
    autotalk_npcs.append(pit_ender_npc)

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
                    if game_manager.game_state == GameState.PLAYER_CONTROL:
                        hit_npcs = pygame.sprite.spritecollide(
                            player, npc_group, False)
                        if hit_npcs:
                            hit_npc = hit_npcs[0]
                            if hit_npc.can_talk():
                                hit_npc.talk(textbox)
                                if hit_npc.is_talking:
                                    game_manager.game_state = GameState.TEXTBOX_CONTROL
                                elif textbox.callback:
                                    textbox.callback()
                    elif game_manager.game_state == GameState.TEXTBOX_CONTROL:
                        if textbox.has_next_line():
                            textbox.move_next_line()
                        else:
                            game_manager.game_state = GameState.PLAYER_CONTROL
                            textbox.is_visible = False
                            textbox.callback()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    is_k_left_down = False
                if event.key == pygame.K_RIGHT:
                    is_k_right_down = False
                if event.key == pygame.K_UP:
                    is_k_up_down = False
                    if game_manager.game_state == GameState.PLAYER_CONTROL:
                        time_diff = now - jump_start_time
                        strength = time_diff_to_strength(time_diff)
                        player.jump(strength)

        hit_npcs = pygame.sprite.spritecollide(
            player, autotalk_npcs, False)
        if hit_npcs:
            hit_npc = hit_npcs[0]
            if hit_npc.can_talk():
                hit_npc.talk(textbox)
                if hit_npc.is_talking:
                    game_manager.game_state = GameState.TEXTBOX_CONTROL
                elif textbox.callback:
                    textbox.callback()

        # Update
        if game_manager.game_state == GameState.PLAYER_CONTROL:
            if is_k_left_down:
                player.move_left()
            if is_k_right_down:
                player.move_right()
            time_diff = now - jump_start_time
            if is_k_up_down and time_diff >= JUMP_COOLDOWN:
                strength = time_diff_to_strength(time_diff)
                player.jump(strength)
        elif game_manager.game_state == GameState.TEXTBOX_CONTROL:
            textbox.update()
        player_group.update(lvl.collidable_block_group)
        lvl.collidable_block_group.update()
        npc_group.update()
        autotalk_npc_group.update()
        cam.update()
        fader.update()
        ending_screen.update()

        # Render
        screen.fill(BACKGROUND)
        for layer in lvl.layers:
            for b in layer["collidable_blocks"]:
                if is_block_on_screen(b, cam):
                    screen.blit(b.image, to_screen_coords(
                        b.rect.topleft, cam))
            for b in layer["noncollidable_blocks"]:
                if is_block_on_screen(b, cam):
                    screen.blit(b.image, to_screen_coords(
                        b.rect.topleft, cam))
        for npc in npcs:
            screen.blit(npc.image, to_screen_coords(npc.rect.topleft, cam))
        for npc in autotalk_npcs:
            screen.blit(npc.image, to_screen_coords(npc.rect.topleft, cam))
        screen.blit(player.image, to_screen_coords(
            player.rect.topleft, cam))
        screen.blit(fader.image, (0, 0))
        screen.blit(ending_screen.image, (0, 0))
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
