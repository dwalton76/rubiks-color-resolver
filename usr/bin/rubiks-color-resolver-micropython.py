#!/usr/bin/env micropython

import sys
sys.path.append("/home/dwalton/rubiks-cube/rubiks-color-resolver")

from rubikscolorresolver import resolve_colors
import logging


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(None)

resolve_colors(sys.argv)
