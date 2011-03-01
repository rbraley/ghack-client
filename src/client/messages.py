#!/usr/bin/env python

# Copyright 2010, 2011 The ghack Authors. All rights reserved.
# Use of this source code is governed by the GNU General Public License
# version 3 (or any later version). See the file COPYING for details.

from proto import protocol_pb2 as ghack_pb2

from game.objects import Vector

"""
Contains convenience functions to create the various protocol buffer messages
"""

def unwrap(msg):
    """Unwraps a Message"""
    return getattr(msg, MESSAGE_TYPES[msg.type])

def unwrap_state(state):
    """Unwraps a Message"""
    if state.type == ghack_pb2.StateValue.ARRAY:
        return [unwrap_state(s) for s in state.array_val]
    val = getattr(state, STATE_TYPES[state.type])
    if state.type in STATE_MAPPERS:
        return STATE_MAPPERS[state.type](val)
    return val

def login(name, authtoken='', permissions=0):
    msg = ghack_pb2.Message()
    msg.type = ghack_pb2.Message.LOGIN
    msg.login.name = name
    msg.login.authtoken = authtoken
    msg.login.permissions = permissions
    return msg

def connect(version):
    msg = ghack_pb2.Message()
    msg.type = ghack_pb2.Message.CONNECT
    msg.connect.version = version
    return msg

def disconnect(reason, reason_str=''):
    msg = ghack_pb2.Message()
    msg.type = ghack_pb2.Message.DISCONNECT
    msg.disconnect.reason = reason
    if reason_str:
        msg.disconnect.reason_str = reason_str
    return msg

def move(direction):
    """This is weird, at least for now. Pass it something of the form:
    %(sign)s%(direction)s -- such as +x or -y.
    """
    msg = ghack_pb2.Message()
    msg.type = ghack_pb2.Message.MOVE
    msg.move.direction.x = direction.x
    msg.move.direction.y = direction.y
    msg.move.direction.z = direction.z
    return msg

MESSAGE_TYPES = {
        ghack_pb2.Message.CONNECT: 'connect',
        ghack_pb2.Message.DISCONNECT: 'disconnect',
        ghack_pb2.Message.LOGIN: 'login',
        ghack_pb2.Message.LOGINRESULT: 'login_result',
        ghack_pb2.Message.ADDENTITY: 'add_entity',
        ghack_pb2.Message.REMOVEENTITY: 'remove_entity',
        ghack_pb2.Message.UPDATESTATE: 'update_state',
        ghack_pb2.Message.MOVE: 'move',
    }

STATE_TYPES = {
        ghack_pb2.StateValue.BOOL: 'bool_val',
        ghack_pb2.StateValue.INT: 'int_val',
        ghack_pb2.StateValue.FLOAT: 'float_val',
        ghack_pb2.StateValue.STRING: 'string_val',
        ghack_pb2.StateValue.VECTOR3: 'vector3_val',
    }

STATE_MAPPERS = {
        ghack_pb2.StateValue.VECTOR3: lambda v: Vector(v.x, v.y, v.z),
    }
