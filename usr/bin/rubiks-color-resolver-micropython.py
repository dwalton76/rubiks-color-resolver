#!/usr/bin/env micropython

# standard libraries
import sys

# rubiks cube libraries
from rubikscolorresolver.solver import resolve_colors

resolve_colors(sys.argv)
