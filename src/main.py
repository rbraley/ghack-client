#!/usr/bin/env python

# Copyright 2010, 2011 The ghack Authors. All rights reserved.
# Use of this source code is governed by the GNU General Public License
# version 3 (or any later version). See the file COPYING for details.

import sys
import os
import time
from optparse import OptionParser
import subprocess
import curses
import atexit

from twisted.internet import reactor

# It's bad form to put code before an import, unless it has to go there:
def generate_protoc():
    """Regenerate the protoc python code (call before importing)"""
    path = os.path.dirname(os.path.realpath(__file__))
    parent = os.path.dirname(path)
    proto_dir = os.path.join(parent, 'protocol')
    proto_file = os.path.join(proto_dir, 'protocol.proto')
    output_dir = os.path.join(path, 'proto')
    if os.path.exists(proto_file):
        cmd = "protoc --proto_path=%(proto_dir)s --python_out=%(output_dir)s %(proto_file)s" % locals()

        subprocess.call(cmd, shell=True)
try:
    generate_protoc()
except:
    print "Failed to generate protobuf file -- is protoc installed?"
    sys.exit(1)


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
    
def cleanup():
    curses.nocbreak();
    #stdscr.keypad(0); 
    curses.echo()
    curses.endwin()


def main(options, args):
    debug.verbose = options.verbose
    #(run,options.host,int(options.port),options.name)
    run(options.host, int(options.port), options.name)

if __name__ == '__main__':
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
    
    atexit.register(cleanup)

    options, args = parser.parse_args()
    reactor.callWhenRunning(main, options, args)
    reactor.run()
    sys.exit(0)
