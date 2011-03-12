#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2010, 2011 The ghack Authors. All rights reserved.
# Use of this source code is governed by the GNU General Public License
# version 3 (or any later version). See the file COPYING for details.

"""
A game class, which renders game state for the player and handles
player input. All input state changes are sent to an external service,
which is responsible for updating the game's state in response, and
implementing the actual gameplay logic
"""

import curses
import sys
import os

from debug import debug
from objects import Entity, Vector

class Game(object):
    def __init__(self, name):
        #set up curses
        self.scr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        self.scr.keypad(1)
        
        
        self.name = name
        self.entities = {}
        self.direction = Vector()

        # also temporary: instead of taking input,
        # the game just pretends the character is
        # moving in a circle
        self.progress = 0
        self.dir_idx = 0

        # temporary; remove when curses gets added
        #fd = sys.stdin.fileno()
        #fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        #fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        self.create()
        
    def create(self):        
        curses.curs_set(0)
        self.scr.nodelay(1)	# Make getch() non-blocking
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLUE)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLUE)
        
    def update(self, elapsed_seconds):
        """Runs every frame"""
        self.progress += elapsed_seconds
        if self.progress > 1:
            circle_map = [ (1 , 0), (0 , 1), (-1, 0), (0 , -1) ]
            d = circle_map[self.dir_idx]
            self.move(*d)
            self.progress -= 1
            self.dir_idx = (self.dir_idx + 1) % 4

            self.running = True
            self.redraw()

    def add_entity(self, id, name=None):
        if id in self.entities:
            debug("Entity id %d added twice" % id)
        self.entities[id] = Entity(id, name)
        self.redraw()

    def remove_entity(self, id, name=None):
        if id not in self.entities:
            debug("Entity id %d removed without being added" % id)
            return
        del self.entities[id]
        self.redraw()

    def update_entity(self, id, state_id, value=None):
        if id not in self.entities:
            debug("Entity id %d updated without being added" % id)
            return
        self.entities[id].set_state(state_id, value)
        self.redraw()
        self._handle_input()

    

    def redraw(self):
        #print "%d Entities:" % len(self.entities)
        self.scr.erase()
        def in_bounds(x,y):
            by,bx = self.scr.getbegyx()
            my,mx = self.scr.getmaxyx()
            return bx<x<mx and by<y<my
        
        for entity in self.entities.values():
            #print(entity.name, entity.states)
            if entity.states.has_key('Position'):
                pos = entity.states['Position']
                if entity.states.has_key('Asset'):
                    asset = entity.states['Asset']
                    #sddelf.scr.addstr(int(pos.y),int(pos.x), '⩕⎈☸⨳⩕⩖⩕@', curses.color_pair(2))
                    if in_bounds(pos.x,pos.y):
                        self.scr.addstr(int(pos.y),int(pos.x), asset, curses.color_pair(2))
        self.scr.refresh()

    def _handle_input(self):
        ch = self.scr.getch()
        if ch == curses.KEY_UP:
            self.move(0,-1)
        elif ch == curses.KEY_DOWN:
            self.move(0,1)
        elif ch == curses.KEY_LEFT:
            self.move(-1,0)
        elif ch == curses.KEY_RIGHT:
            self.move(1,0)
        
    def move(self, x, y):
        """Sending commands is weird. For now, just save it somewhere for
        the network to pick up
        """

        self.direction = Vector(x, y)
