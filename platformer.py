import pygame
from pygame import mixer
import pickle
from os import path

#### OVA NE E SE MOE, DEL E OD JUTUBER, DEL E MOE ####

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 1000
screen_height = 1000

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Џoni Bravo')

# Define font
font = pygame.font.SysFont('Bauhaus 93', 70)
font_score = pygame.font.SysFont('Bauhaus 93', 30)

# Game variables
tile_size = 50
game_over = 0
main_menu = True
level = 1
max_levels = 6
score = 0
lives = 3

# Define colours
white = (255, 255, 255)
blue = (0, 0, 255)

# Loading images
bg_img = pygame.image.load('img/sky.png')
restart_img = pygame.image.load('img/reset.png')
start_img = pygame.image.load('img/start.png')
exit_img = pygame.image.load('img/exit.png')

## Load sounds ##
coin_fx = pygame.mixer.Sound('sounds/coin.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('sounds/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('sounds/gameover.wav')
game_over_fx.set_volume(2.5)
pygame.mixer.music.load('sounds/music.mp3')
pygame.mixer.music.play(-1, 0.0, 5000)
win_fx = pygame.mixer.Sound('sounds/win.wav')
win_fx.set_volume(0.5)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

#def draw_grid():
#    for line in range(0, 20):
#        pygame.draw.line(screen, (255, 255, 255), (0, line * tile_size), (screen_width, line * tile_size))
#        pygame.draw.line(screen, (255, 255, 255), (line * tile_size, 0), (line * tile_size, screen_height))

# Function to reset level
def reset_level(level):
    player.reset(100, screen_height - 173)
    blob_group.empty()
    lava_group.empty()
    exit_group.empty()

    # Load in level data and create world
    if path.exists(f'level{level}_data'):
        pickle_in = open(f'level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)
    world = World(world_data)

    return world

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False

        ## Get mouse position ##
        pos = pygame.mouse.get_pos()

        ## Check mouseover and clicked conditions ##
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        ## Draw button ##
        screen.blit(self.image, self.rect)

        return action

class Player():
    def __init__(self, x, y):
        self.reset(x, y)

    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 5
        col_thresh = 20

        if game_over == 0:
            ## Get key presses ##
            key = pygame.key.get_pressed()
            if key[pygame.K_UP] and self.jumped == False and self.in_air == False:
                jump_fx.play()
                self.vel_y = -15
                self.jumped = True
            if key[pygame.K_UP] == False:
                self.jumped = False
            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT]:
                dx += 5
                self.counter += 1
                self.direction = 1
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            ## Handle animation ##
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            ## Gravity ##
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            ## Check for collision ##
            self.in_air = True
            for tile in world.tile_list:
                ## Check for collision in x direction ##
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0

                ## Check for collision in y direction ##
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    ## Check if below the ground i.e. jumping ##
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    ## Check if above the ground i.e. falling ##
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            ## Player bounderies ##
            if player.rect.x < 0:
                player.rect.x = 0

            if player.rect.x > 960:
                player.rect.x = 960

            ## Check for collision with enemies ##
            if pygame.sprite.spritecollide(self, blob_group, False):
                game_over = -1
                game_over_fx.play()

            ## Check for collision with lava ##
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
                game_over_fx.play()

            ## Check for collision with gate ##
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

            ## Check for collision with trampoline ##
            #if pygame.sprite.spritecollide(self, trampoline_group, False):
            #    self.vel_y = -25
            #    jump_fx.play()

            for platform in trampoline_group:
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    ## Check if above trampoline ##
                    if abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.in_air = True
                        self.vel_y = -25
                        jump_fx.play()

            ## Check for collision with platforms ##
            for platform in platform_group:
                ## Collision in the x direction ##
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                ## Collision in the y direction ##
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    ## Check if below platform ##
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    ## Check if above platform ##
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    ## Move sideways with the platform ##
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction


            ## Update player coordinates ##
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER!', font, blue, (screen_width // 2) - 160, screen_height // 2 + 20)
            self.rect.y -= 5

        ## Draw player on the screen ##
        screen.blit(self.image, self.rect)

        return game_over

    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 9):
            img_right = pygame.image.load(f'player/R{num}.png')
            img_right = pygame.transform.scale(img_right, (40, 80))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_left.append(img_left)
            self.images_right.append(img_right)
        self.dead_image = pygame.image.load('img/ghost.png')
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True

blob_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
trampoline_group = pygame.sprite.Group()

class World():
    def __init__(self, data):
        self.tile_list = []

        # load images
        grass_img = pygame.image.load('img/grass.png')
        dirt_img = pygame.image.load('img/dirt.png')

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    blob = Enemy(col_count * tile_size, row_count * tile_size - 58)
                    blob_group.add(blob)
                if tile == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                if tile == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                if tile == 6:
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                if tile == 7:
                    coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                if tile == 9:
                    trampoline = Trampoline(col_count * tile_size, row_count * tile_size)
                    trampoline_group.add(trampoline)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('enemy\R1.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y + 40
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 100:
            self.move_direction *= -1
            self.image = pygame.transform.flip(self.image, True, False)
            self.move_counter *= -1

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img\platform.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_counter = 0
        self.move_direction = 1
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 100:
            self.move_direction *= -1
            self.move_counter *= -1


class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.images.append(pygame.image.load('img/lava1.png'))
        self.images.append(pygame.image.load('img/lava2.png'))
        self.images.append(pygame.image.load('img/lava3.png'))
        self.current_image = 0
        self.image = self.images[self.current_image]
        self.image = pygame.transform.scale(self.image, (tile_size , tile_size))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.current_image += 0.2
        if self.current_image >= len(self.images):
            self.current_image = 0
        self.image = self.images[int(self.current_image)]
        self.image = pygame.transform.scale(self.image, (tile_size , tile_size - 30))
        if level == 4:
            self.image = pygame.transform.scale(self.image, (tile_size, tile_size // 2))

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img\coin.png')
        self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class Trampoline(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/trampoline.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img\gate.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

player = Player(100, screen_height - 173)

## Dummy coin for showing the score ##
score_coin = Coin(tile_size // 2, tile_size // 2 - 7)
coin_group.add(score_coin)

## Load in level data and create world ##
if path.exists(f'level{level}_data'):
    pickle_in = open(f'level{level}_data', 'rb')
    world_data = pickle.load(pickle_in)
world = World(world_data)

## Create buttons ##
restart_button = Button(screen_width // 2 - 100, screen_height // 2 + 100, restart_img)
start_button = Button(screen_width // 2 + 100, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 - 300, screen_height // 2, exit_img)


run = True
while run:

    clock.tick(fps)
    screen.blit(bg_img, (0, 0))

    if main_menu == True:
        if start_button.draw():
            main_menu = False
        if exit_button.draw():
            run = False
    else:
        world.draw()

        if game_over == 0:
            blob_group.update()
            platform_group.update()
            lava_group.update()
            # Update score
            # Check if a coin has been collected
            if pygame.sprite.spritecollide(player, coin_group, True):
                score += 1
                coin_fx.play()
            draw_text('X ' + str(score), font_score, white, tile_size - 10, 10)
            draw_text('lives ' + str(lives), font_score, white, tile_size + 820, 10)



        blob_group.draw(screen)
        platform_group.draw(screen)
        lava_group.draw(screen)
        coin_group.draw(screen)
        exit_group.draw(screen)
        trampoline_group.draw(screen)

        game_over = player.update(game_over)

        # If player dies
        if game_over == -1:
            if lives > 1:
                if restart_button.draw():
                    game_over = 0
                    player = Player(100, screen_height - 173)

                    lives -= 1
            else:
                coin_group.empty()
                blob_group.empty()
                platform_group.empty()
                if restart_button.draw():
                    level = 1
                    # Reset level
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0
                    coin_group.add(score_coin)
                    lives = 3

        # If player completes the level
        if game_over == 1:
            # Reset game and go to next level
            platform_group.empty()
            level += 1
            if level <= max_levels:
                # Reset level
                world_data = []
                world = reset_level(level)
                game_over = 0
            else:
                draw_text('YOU WIN!', font, blue, (screen_width // 2) - 130, screen_height // 2)
                win_fx.play()
                pygame.mixer.music.stop()
                coin_group.empty()
                trampoline_group.empty()
                # Restart game
                if restart_button.draw():
                    level = 1
                    # Reset level
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0
                    platform_group.empty()
                    pygame.mixer.music.play(-1, 0.0, 5000)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()
