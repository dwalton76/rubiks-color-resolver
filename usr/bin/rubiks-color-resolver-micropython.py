#!/usr/bin/env micropython

from rubikscolorresolver import resolve_colors
import logging
import sys


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(None)

resolve_colors(sys.argv)
