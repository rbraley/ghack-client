#!/usr/bin/env python

# Copyright 2010, 2011 The ghack Authors. All rights reserved.
# Use of this source code is governed by the GNU General Public License
# version 3 (or any later version). See the file COPYING for details.

import struct

from proto import protocol_pb2 as ghack_pb2
import states
import netclient
import messages
from debug import debug

"""
Client:
    Holds a client connection to the game server. 
"""

class Client(object):
    def __init__(self, name):
        self.name = name
        self.conn = None
        self.handler = None
        self.version = 1
        self.entities = {} # id -> entity

    def run(self):
        """Start the client connection"""
        self.connect()


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

        def close():
            self.conn.close()
        self.conn.call_later(0.1, close)

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

        login = messages.login(client.name)
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

        wait_time = 10
        print "Cool, we're connected! Disconnecting in %d seconds" % wait_time
        def dc():
            client.disconnect()
        client.conn.call_later(wait_time, dc)


class GameHandler(Handler):
    handlers = {
            ghack_pb2.Message.ADDENTITY: lambda h: h.handle_add,
        }
    def handle_add(self, client, add):
        if add.id in client.entities:
            print "Error: Added the same entity id (%d) twice" % add.id
        client.entities[add.id] = states.Entity(add.id, add.name)
        print "Entity list expanded:", [
                e.name for e in client.entities.values()]

