#!/usr/bin/env python2

from rubikscolorresolver import RubiksColorSolverGeneric
from math import sqrt
import argparse
import json
import logging
import sys

parser = argparse.ArgumentParser()
parser.add_argument('rgb', help='RGB json', default=None)
parser.add_argument('-j', '--json', help='Print json results', action='store_true')
args = parser.parse_args()

# logging.basicConfig(filename='rubiks-rgb-solver.log',
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)7s: %(message)s')
log = logging.getLogger(__name__)

# Color the errors and warnings in red
logging.addLevelName(logging.ERROR, "\033[91m  %s\033[0m" % logging.getLevelName(logging.ERROR))
logging.addLevelName(logging.WARNING, "\033[91m%s\033[0m" % logging.getLevelName(logging.WARNING))

try:
    scan_data_str_keys = json.loads(args.rgb)
    scan_data = {}

    for (key, value) in scan_data_str_keys.items():
        scan_data[int(key)] = value

    square_count = len(scan_data.keys())
    square_count_per_side = int(square_count/6)
    width = int(sqrt(square_count_per_side))

    cube = RubiksColorSolverGeneric(width)
    cube.enter_scan_data(scan_data)
    cube.crunch_colors()

    if args.json:
        print(json.dumps(cube.cube_for_json(), indent=4, sort_keys=True))
    else:
        print(''.join(cube.cube_for_kociemba_strict()))

except Exception as e:
    log.exception(e)
    sys.exit(1)
