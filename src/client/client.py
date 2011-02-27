#!/usr/bin/env python

# Copyright 2010, 2011 The ghack Authors. All rights reserved.
# Use of this source code is governed by the GNU General Public License
# version 3 (or any later version). See the file COPYING for details.

import struct

from proto import protocol_pb2 as ghack_pb2
import netclient
import messages
from debug import debug

"""
Client:
    Holds a client connection to the game server. 
"""

class Client(object):
    def __init__(self, game):
        self.game = game
        self.conn = None
        self.handler = None
        self.version = 1
        self.connected = False
        self.last_move = [0, 0]

    def run(self):
        """Start the client connection"""
        self.connect()

    def update_move(self, idx, axis):
        game_dir = self.game.direction[idx]
        if game_dir == self.last_move[idx]:
            return
        
        sign_dir = game_dir
        if game_dir == 0:
            sign_dir = self.last_move[idx]
        sign = '+' if sign_dir > 0 else '-'
        self.send(messages.move(sign + axis, game_dir != 0))
        self.last_move[idx] = game_dir


    def update(self, elapsed_seconds):
        """Runs every frame"""
        self.update_move(0, 'x')
        self.update_move(1, 'y')

    def handle(self, msg):
        """
        Handle messages. Needs to be replaced with more generic handler
        objects for the various states, and soon
        """
        debug("<<", msg)
        if self.handler:
            self.handler.handle_msg(msg)
        else:
            debug("No handler for message, ignoring")


    def connect(self):
        """Do the client-server handshake"""
        connect = messages.connect(self.version)
        self.handler = ConnectHandler(self)
        self.send(connect)

    def disconnect(self):
        "Disconnect from the server"
        disconnect = messages.disconnect(ghack_pb2.Disconnect.QUIT,
                "Client disconnected")
        self.handler = None
        self.send(disconnect)

        self.conn.close()

    def send(self, msg):
        "Send a message to the server"
        debug(">>", msg)
        msg_bytes = msg.SerializeToString()
        self.conn.send_bytes(struct.pack('H', len(msg_bytes)))
        self.conn.send_bytes(msg_bytes)

class Handler(object):
    """
    Client state is implemented in message handlers.

    A complicated Handler defines a mapping of type -> function in
    handlers, which don't have to worry about unwrapping messages or
    splitting logic.

    Handlers can also define a list of expected message types that are
    passed (with the wrapping Message intact) to handle()
    """
    def __init__(self, client):
        self.client = client

    expected_types = []
    handlers = {}

    def handle_msg(self, msg):
        """Handle a message"""
        if msg.type in self.handlers:
            handler = self.handlers[msg.type](self)
            handler(self.client, messages.unwrap(msg))
        elif msg.type in self.expected_types:
            self.handle(self.client, msg)
        else:
            unexpected(msg)


    def unexpected(self, msg):
        """Handle an unexpected message"""
        print "Unexpected message:", msg

class ConnectHandler(Handler):
    """Handles the server's connect reply"""
    expected_types = [ghack_pb2.Message.CONNECT]
    def handle(self, client, msg):
        connect = msg.connect

        if connect.version != client.version:
            sys.stderr.write("Version strings do not match\n")
            client.close()

        login = messages.login(client.game.name)
        client.handler = LoginResultHandler(client)
        client.send(login)

class LoginResultHandler(Handler):
    expected_types = [ghack_pb2.Message.LOGINRESULT]
    def handle(self, client, msg):
        login_result = msg.login_result

        if not login_result.succeeded:
            sys.stderr.write("Login failed: " +
                    LOGIN_FAILS[login_result.reason])
            client.close()
        client.handler = GameHandler(client)
        client.connected = True

        print "Connection established"


class GameHandler(Handler):
    handlers = {
            ghack_pb2.Message.ADDENTITY: lambda h: h.handle_add,
            ghack_pb2.Message.REMOVEENTITY: lambda h: h.handle_remove,
            ghack_pb2.Message.UPDATESTATE: lambda h: h.handle_update,
        }
    def handle_add(self, client, add):
        args = {'id': add.id}
        if add.name:
            args['name'] = add.name
        client.game.add_entity(**args)

    def handle_remove(self, client, add):
        args = {'id': add.id}
        if add.name:
            args['name'] = add.name
        client.game.remove_entity(**args)

    def handle_update(self, client, add):
        args = {'id': add.id, 'state_id': add.state_id}
        if add.name:
            args['value'] = messages.unwrap_state(add.value)
        client.game.update_entity(**args)
