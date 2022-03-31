#!/usr/bin/env python3

# standard libraries
import logging
import sys

# rubiks cube libraries
from rubikscolorresolver.solver import resolve_colors

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)7s: %(message)s")

resolve_colors(sys.argv)
