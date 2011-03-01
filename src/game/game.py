#!/usr/bin/env python

# Copyright 2010, 2011 The ghack Authors. All rights reserved.
# Use of this source code is governed by the GNU General Public License
# version 3 (or any later version). See the file COPYING for details.

"""
A game class, which renders game state for the player and handles
player input. All input state changes are sent to an external service,
which is responsible for updating the game's state in response, and
implementing the actual gameplay logic
"""

import fcntl
import sys
import os

from debug import debug
from objects import Entity, Vector

class Game(object):
    def __init__(self, name):
        self.name = name
        self.entities = {}
        self.direction = Vector()

        # also temporary: instead of taking input,
        # the game just pretends the character is
        # moving in a circle
        self.progress = 0
        self.dir_idx = 0

        # temporary; remove when curses gets added
        fd = sys.stdin.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def update(self, elapsed_seconds):
        """Runs every frame"""
        self.progress += elapsed_seconds
        if self.progress > 1:
            circle_map = [ (1 , 0), (0 , 1), (-1, 0), (0 , -1) ]
            d = circle_map[self.dir_idx]
            self.move(*d)
            self.progress -= 1
            self.dir_idx = (self.dir_idx + 1) % 4

        try:
            ch = sys.stdin.read(1)
        except IOError:
            pass
        else:
            # do stuff with ch here?
            self.running = False

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

    def redraw(self):
        print "%d Entities:" % len(self.entities)
        for entity in self.entities.values():
            print "== %s ==" % entity.name
            try: # not sure how good an idea this is ;)
                print " at %d, %d" % (entity.states['PositionX'],
                        entity.states['PositionY'])
            except KeyError:
                pass

    def move(self, x, y):
        """Sending commands is weird. For now, just save it somewhere for
        the network to pick up
        """

        self.direction = Vector(x, y)
