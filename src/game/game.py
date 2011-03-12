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
        self.name = name
        self.entities = {}
        self.direction = Vector()

        self._init_curses()

    def _init_curses(self):
        self.scr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        self.scr.keypad(1)
        
        curses.curs_set(0)
        self.scr.nodelay(1)	# Make getch() non-blocking
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLUE)
        
    def update(self, elapsed_seconds):
        """Runs every frame"""
        self.running = True
        self.redraw()
        self._handle_input()

    def add_entity(self, id, name=None):
        if id in self.entities:
            debug("Entity id %d added twice" % id)
        self.entities[id] = Entity(id, name)

    def remove_entity(self, id, name=None):
        if id not in self.entities:
            debug("Entity id %d removed without being added" % id)
            return
        del self.entities[id]

    def update_entity(self, id, state_id, value=None):
        if id not in self.entities:
            debug("Entity id %d updated without being added" % id)
            return
        self.entities[id].set_state(state_id, value)
        self.redraw()

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
                    #self.scr.addstr(int(pos.y),int(pos.x), '⩕⎈☸⨳⩕⩖⩕@', curses.color_pair(2))
                    if in_bounds(pos.x,pos.y):
                        self.scr.addstr(int(pos.y),int(pos.x), asset, curses.color_pair(2))
        self.scr.border()
        try:
            self.scr.addstr(0,self.scr.getmaxyx()[1]/2-9,"GHack SpiderForest",curses.color_pair(1))
        except curses.error:
            print("oh no!")
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
