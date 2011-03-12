#!/usr/bin/env python

# Copyright 2010, 2011 The ghack Authors. All rights reserved.
# Use of this source code is governed by the GNU General Public License
# version 3 (or any later version). See the file COPYING for details.

import sys

verbose = False
def debug(*args):
    if verbose:
        print >> sys.stderr, ' '.join(map(str, args))
