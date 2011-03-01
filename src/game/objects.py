#!/usr/bin/env python

# Copyright 2010, 2011 The ghack Authors. All rights reserved.
# Use of this source code is governed by the GNU General Public License
# version 3 (or any later version). See the file COPYING for details.

"""
Basic entity and state types
"""

class Entity(object):
    def __init__(self, id, name, **states):
        self.id = id
        self.name = name
        self.states = states

    def set_state(self, state_id, val):
        self.states[state_id] = val

    def __unicode__(self):
        return self.name

    def __repr__(self):
        name = self.name
        if len(name) > 8:
            name = name[:6] + '...'
        return "<Entity id=%d, name='%s'>" % (self.id, name)

class Vector(object):
    """A simple vector structure"""
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def len_squared(self):
        return (self.x * self.x +
            self.y * self.y +
            self.z * self.z)
