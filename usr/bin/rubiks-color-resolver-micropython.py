#!/usr/bin/env micropython

from rubikscolorresolver import resolve_colors, print_mem_stats
#import logging
import sys

#logging.basicConfig(level=logging.INFO)

resolve_colors(sys.argv)
