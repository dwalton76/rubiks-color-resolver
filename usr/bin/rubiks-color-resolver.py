#!/usr/bin/env micropython

import sys
sys.path.append("/home/dwalton/rubiks-cube/rubiks-color-resolver")

try:
    from json import dumps as json_dumps
    from json import loads as json_loads
except ImportError:
    from ujson import dumps as json_dumps
    from ujson import loads as json_loads

from math import sqrt
from rubikscolorresolver import RubiksColorSolverGeneric

import logging


# logging.basicConfig(filename='rubiks-rgb-solver.log',
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)7s: %(message)s')
log = logging.getLogger(__name__)


# Handle command line args without argparse
help_string = """usage: rubiks-color-resolver.py [-h] [-j] [--filename FILENAME] [--rgb RGB]

optional arguments:
  -h, --help           show this help message and exit
  -j, --json           Print json results
  --filename FILENAME  Print json results
  --rgb RGB            RGB json
"""
filename = None
rgb = None
use_json = False
argv_index = 1

while argv_index < len(sys.argv):

    if sys.argv[argv_index] == "--help":
        print(help_string)
        sys.exit(0)

    elif sys.argv[argv_index] == "--filename":
        filename = sys.argv[argv_index + 1]
        argv_index += 2

    elif sys.argv[argv_index] == "--rgb":
        rgb = sys.argv[argv_index + 1]
        argv_index += 2

    elif sys.argv[argv_index] == "--json" or sys.argv[argv_index] == "-j":
        use_json = True
        argv_index += 1

    else:
        print(help_string)
        sys.exit(1)

if filename:
    file_as_string = []
    with open(filename, 'r') as fh:
        rgb = ''.join(fh.readlines())
elif rgb:
    pass
else:
    print("ERROR: Neither --filename or --rgb was specified")
    sys.exit(1)

scan_data_str_keys = json_loads(rgb)
scan_data = {}

for (key, value) in scan_data_str_keys.items():
    scan_data[int(key)] = value

square_count = len(list(scan_data.keys()))
square_count_per_side = int(square_count/6)
width = int(sqrt(square_count_per_side))

cube = RubiksColorSolverGeneric(width)
cube.enter_scan_data(scan_data)
cube.crunch_colors()

if use_json:
    print(json_dumps(cube.cube_for_json(), indent=4, sort_keys=True))
else:
    print(''.join(cube.cube_for_kociemba_strict()))
