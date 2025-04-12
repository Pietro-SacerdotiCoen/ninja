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
RUNNING = 8
JUMPING = 16
WALKING = 24

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

def get_image(sheet, width, heigth, startx, starty):
    image = pg.Surface.subsurface(sheet,pg.Rect(startx, starty, 128, 128))
    return image


# Each type of game object gets an init and an update function.
# The update function is called once per frame, and it is when each object should
# change its current position and state.
#
# The Player object actually gets a "move" function instead of update,
# since it is passed extra information about the keyboard.


class Player(pg.sprite.Sprite):
    """Representing the player1 as a moon buggy type car."""

    def __init__(self, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        self.image = self.images[0]
        self.rect = self.image.get_rect(x = 400, y = 400)
        self.current_image = 0
        self.walk_frame = 0
        self.velx = 30
        self.vely = 15
        self.directionx = 0
        self.idle_frame = 0
        self.y = 400
        self.mode = IDLE
        self.facing = False


    def move(self, all):

        if self.mode == JUMPING:
            self.jump()
        elif self.mode == RUNNING:
            self.run()
        elif self.mode == WALKING:
            self.walk()
        else:
            self.idle()

        self.next_frame()

        if self.mode == JUMPING and self.current_image == self.mode:
            self.mode = IDLE

    def run (self):

        self.rect[0] += self.velx * self.directionx
        self.rect[1] += self.vely * self.directiony

        self.facing = self.directionx < 0
    
    def idle (self):
        pass
    
    def jump (self):
            if self.current_image > 18:
                if self.facing:
                    self.rect[0] += 30
                else:
                    self.rect[0] -= 30

    def walk (self):
        self.rect[1] += self.vely * self.directiony

    def input(self, keystate, all):
        self.directionx = (keystate[pg.K_d] - keystate[pg.K_a])
        self.directiony = (keystate[pg.K_s] - keystate[pg.K_w])

        if keystate[pg.K_SPACE] == 1:
            next = JUMPING
        elif self.directionx != 0:
            next = RUNNING
        elif self.directiony != 0:
            next = WALKING
        else:
            next = IDLE

        if self.mode != next and self.mode != JUMPING:
            self.mode = next
            self.current_image = next

        


    def next_frame (self):
        self.image = self.images[self.current_image]
        self.current_image += 1
        if self.current_image >= self.mode + 8:
            self.current_image = self.mode

        if self.facing:
            self.image = pg.transform.flip(self.image, 1, 0)

class Sfondo(pg.sprite.Sprite):
    """to keep track of the score."""

    def __init__(self, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        self.image = self.images[0]
        self.rect = self.image.get_rect(x = 0, y = 0)


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
    sfondo_image = pg.image.load("sfondi/PNG/Battleground2/Bright/Battleground2.png")
    Sfondo.images = [pg.transform.scale_by(sfondo_image, 0.72)]

    Player.images = []
    for y in ["Idle.png", "Run.png", "Jump.png", "Walk.png"]:
        ninjas_idle_sheet = pg.image.load("ninjas/Kunoichi/" + y)
        for x in range(0, 8):
            Player.images.append(pg.transform.scale_by((get_image(ninjas_idle_sheet, 128, 128, x * 128, 0)), 2))


    # decorate the game window
    pg.mouse.set_visible(0)

    # Initialize Game Groups
    all = pg.sprite.RenderUpdates()
    

    # Create Some Starting Values
    clock = pg.time.Clock()

    # initialize our starting sprites
    sfondo = Sfondo(all)
    player1 = Player(all)


    # Run our main loop whilst the player1 is alive.
    screen_backup = screen.copy()
    screen = pg.display.set_mode(SCREENRECT.size, winstyle | pg.FULLSCREEN, bestdepth)
    screen.blit(screen_backup, (0, 0))
    pg.display.flip()

    while player1.alive:
    
        # get input
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return

                
        keystate = pg.key.get_pressed()
        
        player1.input(keystate, all)
        player1.move(all)
        
        # clear/erase the last drawn sprites
        background = pg.Surface(SCREENRECT.size)
        all.clear(screen, background)

        # update all the sprites
        all.update()
        # handle player1 input
        
        #player1.input(coins, meteoriti, keystate, 0, all)

        # draw the scene
        dirty = all.draw(screen)
        #pg.draw.rect(screen, (255, 0, 0), player1.rect, width = 1)
        pg.display.update(dirty)



        # cap the framerate at 40fps. Also called 40HZ or 40 times per second.
        clock.tick(40)
        await asyncio.sleep(0)
    

# call the "main" function if mode this script
if __name__ == "__main__":
    asyncio.run(main())
    pg.quit()
