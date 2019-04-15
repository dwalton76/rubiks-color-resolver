#!/usr/bin/env python3

import sys
sys.path.append("/home/dwalton/rubiks-cube/rubiks-color-resolver")

from rubikscolorresolver import resolve_colors
import logging


# logging.basicConfig(filename='rubiks-rgb-solver.log',
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)7s: %(message)s')

resolve_colors(sys.argv)
