#!/usr/bin/env python

# Copyright 2010, 2011 The ghack Authors. All rights reserved.
# Use of this source code is governed by the GNU General Public License
# version 3 (or any later version). See the file COPYING for details.

"""
ClientState is a class that keeps data in sync with the server for
"""

import sys
import time
import struct

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.protocol import Protocol, ClientFactory

from proto import protocol_pb2 as ghack_pb2
from states import Entity

def connect(host, port, on_connected):
    """Create a GhackProtocol connection and fire on_connected"""

    point = TCP4ClientEndpoint(reactor, host, port)
    d = point.connect(GhackClientFactory())
    if on_connected:
        d.addCallback(on_connected)
    def on_error(err):
        print "Error connecting"
        print err.getTraceback()
        if reactor.running:
            reactor.stop()
    d.addErrback(on_error)


class GhackClientFactory(ClientFactory):
    def buildProtocol(self, addr):
        return GhackProtocol()

class GhackProtocol(Protocol):
    def __init__(self):
        self._buffer = ''
        self.callback = None

    def dataReceived(self, data):
        self._buffer += data

        # flush the buffer of messages to send
        while self.callback:
            msg = self.get_message()
            if not msg:
                return
            try:
                self.callback(msg)
            except:
                self.close()
                raise

    def call_later(self, time, fn):
        reactor.callLater(time, fn)

    def get_message(self):
        "Dispatches the next message from the server (non-blocking)"
        if len(self._buffer) <= 2:
            return None

        msg_len = struct.unpack('H', self._buffer[:2])[0]
        if len(self._buffer) < 2 + msg_len:
            return None

        msg = ghack_pb2.Message()
        msg.ParseFromString(self._buffer[2:msg_len + 2])

        self._buffer = self._buffer[2 + msg_len:]

        return msg

    def send_bytes(self, byte_buffer):
        self.transport.write(byte_buffer)

    def close(self):
        reactor.stop()


