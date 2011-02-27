#!/usr/bin/env python

# Copyright 2010, 2011 The ghack Authors. All rights reserved.
# Use of this source code is governed by the GNU General Public License
# version 3 (or any later version). See the file COPYING for details.

import sys
import time
from optparse import OptionParser

from twisted.internet import reactor

from client import netclient
from client.client import Client # redundaaaant
from game.game import Game
import debug

# sleep 100ms between updates
UPDATE_DELAY = 0.1

def gameloop(game, client):
    def inner(last_frame):
        if not game.running:
            client.disconnect()
            return
        this_frame = time.time()
        delta = this_frame - last_frame
        if client.connected:
            game.update(delta)
            client.update(delta)
        reactor.callLater(UPDATE_DELAY, inner, this_frame)

    last_frame = time.time() - UPDATE_DELAY
    game.running = True
    inner(last_frame)

def run(host, port, name):
    game = Game(name)
    client = Client(game)

    def on_connected(protocol):
        protocol.callback = lambda msg: client.handle(msg)
        client.conn = protocol
        client.run()
        gameloop(game, client)

    netclient.connect(host, port, on_connected)

def main():
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
    debug.verbose = options.verbose

    run(options.host, int(options.port), options.name)

if __name__ == '__main__':
    reactor.callWhenRunning(main)
    reactor.run()
    sys.exit(0)
