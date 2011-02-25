#!/usr/bin/env python

# Copyright 2010, 2011 The ghack Authors. All rights reserved.
# Use of this source code is governed by the GNU General Public License
# version 3 (or any later version). See the file COPYING for details.

import sys
from optparse import OptionParser

from client import netclient
from client.client import Client # redundaaaant
import debug

def run(host, port, name):
    client = Client(name)

    def on_connected(protocol):
        protocol.callback = lambda msg: client.handle(msg)
        client.conn = protocol
        client.run()

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
    main()
    sys.exit(0)
