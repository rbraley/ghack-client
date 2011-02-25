#!/usr/bin/env python

import sys
import time
import socket
import struct
from optparse import OptionParser
from collections import defaultdict

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.protocol import Protocol, ClientFactory

from proto import protocol_pb2 as ghack_pb2

class Entity(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __unicode__(self):
        return self.name

class GhackClientFactory(ClientFactory):
    def buildProtocol(self, addr):
        return GhackProtocol()

class GhackProtocol(Protocol):
    def __init__(self):
        self._buffer = ''
        self.client = None

    def dataReceived(self, data):
        self._buffer += data

        # flush the buffer of messages to send
        while self.client != None:
            msg = self.get_message()
            if not msg:
                return
            self.dispatch(msg)

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

    def dispatch(self, msg):
        self.client.handle(msg)

    def send_bytes(self, byte_buffer):
        self.transport.write(byte_buffer)

    def close(self):
        reactor.stop()

LOGIN_FAILS = defaultdict(lambda: "Unknown reason")
LOGIN_FAILS[ghack_pb2.LoginResult.ACCESS_DENIED] = "Access denied"
LOGIN_FAILS[ghack_pb2.LoginResult.BANNED] = "Banned from server"
LOGIN_FAILS[ghack_pb2.LoginResult.SERVER_FULL] = "Server full"

CONNECT_WAIT = 0
LOGINRESULT_WAIT = 1
CONNECTED = 2

class Client(object):
    def __init__(self, name):
        self.name = name
        self.conn = None
        self.state = None
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
        if self.state == CONNECT_WAIT:
            self.handle_connect(msg.connect)
        elif self.state == LOGINRESULT_WAIT:
            self.handle_login_result(msg.login_result)
        elif self.state == CONNECTED:
            self.handle_normal_message(msg)
        else:
            print "Unexpected message:", msg


    def handle_connect(self, connect):
        if connect.version != self.version:
            sys.stderr.write("Version strings do not match\n")
            self.conn.close()

        login = ghack_pb2.Message()
        login.type = ghack_pb2.Message.LOGIN
        login.login.name = self.name
        login.login.authtoken = "passwordHash"
        login.login.permissions = 0
        self.state = LOGINRESULT_WAIT
        self.send(login)

    def handle_login_result(self, login_result):
        if not login_result.succeeded:
            sys.stderr.write("Login failed: " +
                    LOGIN_FAILS[login_result.reason])
            self.conn.close()
        self.state = CONNECTED

        wait_time = 10
        print "Cool, we're connected! Disconnecting in %d seconds" % wait_time
        def dc():
            self.disconnect()
        reactor.callLater(wait_time, dc)

    def handle_normal_message(self, msg):
        if msg.type == ghack_pb2.Message.ADDENTITY:
            add = msg.add_entity
            if add.id in self.entities:
                print "Error: Added the same entity id (%d) twice" % add.id
            self.entities[add.id] = Entity(add.id, add.name)
            print "Entity list expanded:", [
                    e.name for e in self.entities.values()]
        else:
            print "Unexpected message:", msg

    def connect(self):
        """Do the client-server handshake"""
        connect = ghack_pb2.Message()
        connect.connect.version = self.version
        connect.type = ghack_pb2.Message.CONNECT
        self.state = CONNECT_WAIT
        self.send(connect)


    def disconnect(self):
        "Disconnect from the server"
        disconnect = ghack_pb2.Message()
        disconnect.type = ghack_pb2.Message.DISCONNECT
        disconnect.disconnect.reason = ghack_pb2.Disconnect.QUIT
        disconnect.disconnect.reason_str = "Client disconnected"
        self.send(disconnect)
        self.conn.close()

    def send(self, msg):
        "Send a message to the server"
        debug(">>", msg)
        msg_bytes = msg.SerializeToString()
        self.conn.send_bytes(struct.pack('H', len(msg_bytes)) + msg_bytes)

def run(host, port, name):
    client = Client(name)

    def on_connect(protocol):
        protocol.client = client
        client.conn = protocol
        client.run()

    point = TCP4ClientEndpoint(reactor, host, port)
    d = point.connect(GhackClientFactory())
    d.addCallback(on_connect)
    reactor.run()

DEBUG = False
def debug(*args):
    if DEBUG:
        print ' '.join(args)
def main():
    global DEBUG
    parser = OptionParser()
    parser.add_option('-s', '--host',
            help='Server hostname',
            default='localhost')
    parser.add_option('-p', '--port',
            help='Server port',
            default='9190')
    parser.add_option('-n', '--name',
            help='Player name',
            default='pyClient')
    parser.add_option('-v', '--verbose',
            help='Player name',
            action='store_true',
            default=False)

    options, args = parser.parse_args()
    DEBUG = options.verbose

    run(options.host, int(options.port), options.name)

if __name__ == '__main__':
    main()
    sys.exit(0)
