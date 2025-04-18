#!/usr/bin/env python
""" pygame.examples.aliens

Shows a mini game where you have to defend against aliens.

What does it show you about pygame?

* pg.sprite, the difference between Sprite and Group.
* dirty rectangle optimization for processing for speed.
* music with pg.mixer.music, including fadeout
* sound effects with pg.Sound
* event processing, keyboard handling, self.esci handling.
* a main loop frame limited with a game clock from pg.time.Clock
* fullscreen switching.


Controls
--------

* Left and right arrows to move.
* Space bar to shoot
* f key to toggle between fullscreen.

"""

import os
import math
import random
import asyncio
from typing import List
# import basic pygame modules
import pygame as pg
# see if we can load more than standard BMP
if not pg.image.get_extended():
    raise SystemExit("Sorry, extended image module required")


# game constants
schermox = 1400
schermoy = 770
SCREENRECT = pg.Rect(0, 0, schermox, schermoy)
main_dir = os.path.split(os.path.abspath(__file__))[0]
IDLE = 0
RUNNING = 1
JUMPING = 2
WALKING = 3
ATTACKING = 4
DYING = 5
HURT = 6
RUN_ATTACK = 7
atomic = [JUMPING, ATTACKING, DYING, HURT, RUN_ATTACK]

def load_image(file):
    """loads an image, prepares it for play"""
    file = os.path.join(main_dir, "data", file)
    try:
        surface = pg.image.load(file)
    except pg.error:
        raise SystemExit(f'Could not load image "{file}" {pg.get_error()}')
    return surface.convert_alpha()


def load_sound(file):
    """because pygame can be compiled without mixer."""
    if not pg.mixer:
        return None
    file = os.path.join(main_dir, "data", file)
    try:
        sound = pg.mixer.Sound(file)
        return sound
    except pg.error:
        print(f"Warning, unable to load, {file}")
    return None

def get_image(sheet, startx, starty, frame_size):
    image = pg.Surface.subsurface(sheet,pg.Rect(startx + 4, starty, frame_size - 4, frame_size))
    return image


# Each type of game object gets an init and an update function.
# The update function is called once per frame, and it is when each object should
# change its current position and state.
#
# The Player object actually gets a "move" function instead of update,
# since it is passed extra information about the keyboard.


class Character(pg.sprite.Sprite):
    """Representing the player1 as a moon buggy type car."""
    
    def __init__(self, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        self.image = self.images[0]
        self.rect = self.image.get_rect(x = 400, y = 400)
        self.current_image = 0
        self.directionx = 0
        self.y = 400
        self.mode = IDLE
        self.facing = False
        self.frame = 0
        self.health = 100
        self.lasthealth = self.health
        self.dead = False
        self.running_time = 0

    def update(self, keystate, player1, enemies):
        self.input(keystate, player1)
        self.move()
        self.next_frame()
    def move(self):

        if self.mode == DYING:
            self.die()
        elif self.mode == HURT:
            self.hurt()
        elif self.mode == JUMPING:
            self.jump()
        elif self.mode == ATTACKING:
            self.attack()
        elif self.mode == RUNNING:
            self.run()
        elif self.mode == WALKING:
            self.walk()
        elif self.mode == RUN_ATTACK:
            self.run_attack()
        else:
            self.idle()

        self.lasthealth = self.health

        self.rect.bottom = min(max(self.rect.bottom, 440),726)
        self.rect.left = min(max(self.rect.left, 0),1000)

        if self.mode == RUNNING:
            self.running_time += 1
        else:
            self.running_time = 0
    def run (self):

        self.rect[0] += self.velx * self.directionx
        self.rect[1] += self.vely * self.directiony

        self.facing = self.directionx < 0

    def idle (self):
        pass
    
    def jump(self):
            if self.current_image > self.frames[JUMPING] + 4 and self.current_image < self.frames[JUMPING] + 8:
                if self.facing:
                    self.rect[0] += self.velx
                else:
                    self.rect[0] -= self.velx

    def walk(self):
        self.rect[1] += self.vely * self.directiony
        self.rect[0] += self.velx * self.directionx / 2

    def attack(self):
        pass

    def die(self):
        pass

    def hurt(self):
        pass

    def run_attack(self):
        if self.facing == 0:
            dir = 1.3
        else:
            dir = -1.3
        self.rect[0] += self.velx * dir

    def input(self, keystate, player):
        
        if self.mode == DYING and self.current_image == self.frames[self.mode]:        
            self.dead = True
    
        if self.health <= 0:
            next = DYING
        elif self.lasthealth > self.health:
            next = HURT
        else:
            next = self.choose_move(keystate, player)

        if self.mode != next and ((self.mode not in atomic or (self.mode in atomic and self.current_image == self.frames[self.mode])) or next == DYING or next == HURT):
            self.mode = next
            self.current_image = self.frames[next]
            self.frame = 0

    def next_frame (self):
        if self.frame % self.anim_speed[self.mode] == 0:
            self.frame = 0
            self.image = self.images[self.current_image]
            self.current_image += 1
            if self.current_image >= self.frames[self.mode + 1]:
                self.current_image = self.frames[self.mode]

            if self.facing:
                self.image = pg.transform.flip(self.image, 1, 0)

        self.frame += 1

    def collides(self, player):
        collide = False

        if ( player.mode != HURT and player.mode != DYING and
            (self.mode == ATTACKING and self.current_image - self.frames[self.mode] in self.att_times or
            self.mode == RUN_ATTACK and self.current_image - self.frames[self.mode] in self.run_att_times)):
            if not self.facing:
                collide = player.rect[0] - self.rect[0] > 0 and abs(player.rect[0] - self.rect[0] - self.att_range) <= 15
            else:
                collide = player.rect[0] - self.rect[0] < 0 and abs(player.rect[0] - self.rect[0] + self.att_range) <= 15
        return collide
    
def player_init(classe):
    classe.images = []
    frame_size = 128
    animation = 0
    for y in classe.sprites_names:
        frameno_sum = 0
        for i in y:
            ninjas_idle_sheet = load_image(classe.sprites_directory + i)
            frameno = math.floor(ninjas_idle_sheet.get_width() / frame_size)
            frameno_sum += frameno
            for x in range(0, frameno):
                classe.images.append(pg.transform.scale_by((get_image(ninjas_idle_sheet, x * frame_size, 0, frame_size)), 2))
        classe.frames[animation + 1] = classe.frames[animation] + frameno_sum
        animation += 1

class Player(Character):
    anim_speed = [7, 4, 4, 3, 3, 10, 20, 5]
    frames = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    sprites_names = [["Idle.png"], ["Run.png"], ["Jump.png"], ["Walk.png"], ["Attack_1.png", "Attack_2.png"], ["Dead.png"], ["Hurt.png"], []]
    sprites_directory = "ninjas/Kunoichi/"
    velx = 15
    vely = 7
    att_range = 70
    att_times = [2, 6]
    damage = 10

    def update(self, keystate, player, enemies):
        super().update(keystate, player, enemies)
        for x in enemies:
            if self.collides(x):
                x.health -= self.damage

    def choose_move(self, keystate, player1):
        self.directionx = (keystate[pg.K_d] - keystate[pg.K_a])
        self.directiony = (keystate[pg.K_s] - keystate[pg.K_w])

        if keystate[pg.K_k] == 1:
            next = JUMPING
        elif keystate[pg.K_l] == 1:
            next = ATTACKING
        elif self.directionx != 0:
            next = RUNNING
        elif self.directiony != 0:
            next = WALKING
        else:
            next = IDLE

        return next

class Enemy(Character):

    def update(self, keystate, player, enemies):
        super().update(keystate, player, enemies)
        if self.collides(player):
            player.health -= self.damage
class Skeleton1(Enemy):
    anim_speed = [7, 5, 0, 8, 3, 10, 10, 5]
    frames = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    sprites_names = [["Idle.png"], ["Run.png"], [], ["Walk.png"], ["Attack_1.png", "Attack_2.png", "Attack_3.png"], ["Dead.png"], ["Hurt.png"], []]
    sprites_directory = "scheletri/Skeleton_Warrior/"
    velx = 7
    vely = 3
    att_range = 70
    att_times = [2, 6]
    damage = 10
    def __init__(self, *groups):
        super().__init__(*groups)
        self.idle_frame = 0

    def choose_move(self, keystate, player):
        side = self.rect[0] < player.rect[0]
        if side:
            side = -1
        else:
            side = 1
        distx = abs(player.rect[0] - self.rect[0] + 70 * side)
        disty = abs(player.rect[1] - self.rect[1])
        if distx > 600:
            self.idle_frame += 1
            if self.idle_frame < 60:
                next = IDLE
            elif self.idle_frame < 90:
                next = WALKING
                self.directionx = 1
                self.directiony = 0
                self.facing = False
            elif self.idle_frame < 150:
                next = IDLE  
            elif self.idle_frame < 180:
                next = WALKING
                self.directionx = -1
                self.directiony = 0
                self.facing = True
            else:
                next = IDLE
                self.idle_frame = 0

        elif distx <= 10 and disty <= 10:
            if self.mode != ATTACKING:
                self.facing = side == 1
            next = ATTACKING
        else:
            next = RUNNING
            self.directiony = 0
            if distx > 10:
                if self.rect[0] < player.rect[0] + 70 * side:
                    self.directionx = 1
                else:
                    self.directionx = -1
            else:
                self.directionx = 0
            if disty > 10:
                if self.rect[1] < player.rect[1]:
                    self.directiony = 1
                else:
                    self.directiony = -1
            else:
                self.directiony = 0
        return next

class Skeleton2(Enemy):
    anim_speed = [7, 5, 0, 8, 3, 10, 10, 5]
    frames = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    sprites_names = [["Idle.png"], ["Run.png"], [], ["Walk.png"], ["Attack_1.png", "Attack_2.png"], ["Dead.png"], ["Hurt.png"], ["Run+attack.png"]]
    sprites_directory = "scheletri/Skeleton_Spearman/"
    velx = 10
    vely = 5
    att_range = 70
    att_times = [2, 6]
    run_att_times = [1, 2, 3]
    damage = 10

    def __init__(self, *groups):
        super().__init__(*groups)
        self.idle_frame = 0

    def choose_move(self, keystate, player):
        side = self.rect[0] < player.rect[0]
        if side:
            side = -1
        else:
            side = 1
        distx = abs(player.rect[0] - self.rect[0] + 70 * side)
        disty = abs(player.rect[1] - self.rect[1])
        if distx > 600:
            self.idle_frame += 1
            if self.idle_frame < 60:
                next = IDLE
            elif self.idle_frame < 90:
                next = WALKING
                self.directionx = 1
                self.directiony = 0
                self.facing = False
            elif self.idle_frame < 150:
                next = IDLE  
            elif self.idle_frame < 180:
                next = WALKING
                self.directionx = -1
                self.directiony = 0
                self.facing = True
            else:
                next = IDLE
                self.idle_frame = 0
        elif distx <= 120 and disty <= 10 and (self.mode == RUNNING or self.mode == RUN_ATTACK) and self.running_time > 30:
            next = RUN_ATTACK
        elif distx <= 10 and disty <= 10:
            if self.mode != ATTACKING:
                self.facing = side == 1
            next = ATTACKING
        else:
            next = RUNNING
            self.directiony = 0
            if distx > 10:
                if self.rect[0] < player.rect[0] + 70 * side:
                    self.directionx = 1
                else:
                    self.directionx = -1
            else:
                self.directionx = 0
            if disty > 10:
                if self.rect[1] < player.rect[1]:
                    self.directiony = 1
                else:
                    self.directiony = -1
            else:
                self.directiony = 0
        return next
class Sfondo(pg.sprite.Sprite):
    """to keep track of the score."""

    def __init__(self, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        self.image = self.images[0]
        self.rect = self.image.get_rect(x = 0, y = 0)

class YAwareGroup(pg.sprite.Group):
    def by_y(self, spr):
        return spr.rect[1]

    def draw(self, surface):
        sprites = self.sprites()
        surface_blit = surface.blit
        for spr in sorted(sprites, key=self.by_y):
            self.spritedict[spr] = surface_blit(spr.image, spr.rect)
        self.lostsprites = []

async def main(winstyle=0):
    # Initialize pygame
    if pg.get_sdl_version()[0] == 2:
        pg.mixer.pre_init(44100, 32, 2, 1024)
    pg.init()
    if pg.mixer and not pg.mixer.get_init():
        print("Warning, no sound")
        pg.mixer = None

    fullscreen = False
    # Set the display mode
    winstyle = 0  # |FULLSCREEN
    bestdepth = pg.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pg.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    # Load images, assign to sprite classes
    # (do this before the classes are used, after screen setup)
    sfondo_image = load_image("sfondi/PNG/Battleground2/Bright/Battleground2.png")
    Sfondo.images = [pg.transform.scale_by(sfondo_image, 0.72)]

    player_init(Player)
    player_init(Skeleton1)
    player_init(Skeleton2)

    # decorate the game window
    pg.mouse.set_visible(0)

    # Initialize Game Groups
    #all = pg.sprite.RenderUpdates()
    all = YAwareGroup()    
    enemies = pg.sprite.Group()

    # Create Some Starting Values
    clock = pg.time.Clock()

    # initialize our starting sprites
    sfondo = Sfondo(all)
    player1 = Player(all)
    scheletro = Skeleton2(all, enemies)
    scheletro.rect[0] = 600
    scheletro2 = Skeleton1(all, enemies)
    scheletro2.rect[0] = 800

    # Run our main loop whilst the player1 is alive.
    screen_backup = screen.copy()
    screen = pg.display.set_mode(SCREENRECT.size, winstyle | pg.FULLSCREEN, bestdepth)
    screen.blit(screen_backup, (0, 0))
    pg.display.flip()

    while player1.alive and player1.dead == False:
        # get input
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return

                
        keystate = pg.key.get_pressed()
        
        # clear/erase the last drawn sprites
        all.update(keystate, player1, enemies)
        
        background = pg.Surface(SCREENRECT.size)
        all.clear(screen, background)

        # update all the sprites
        # handle player1 input
        #player1.input(coins, meteoriti, keystate, 0, all)

        # draw the scene
        dirty = all.draw(screen)
        #pg.draw.rect(screen, (255, 0, 0), player1.rect, width = 1)
        #pg.display.update(dirty)
        pg.display.flip()


        # cap the framerate at 40fps. Also called 40HZ or 40 times per second.
        clock.tick(40)
        await asyncio.sleep(0)
    

# call the "main" function if mode this script
if __name__ == "__main__":
    asyncio.run(main())
    pg.quit()
