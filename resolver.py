#!/usr/bin/env python3

from rubikscolorresolver import RubiksColorSolverGeneric, RubiksColorSolver2x2x2, RubiksColorSolver3x3x3
from math import sqrt
import argparse
import json
import logging
import sys

parser = argparse.ArgumentParser()
parser.add_argument('rgb', help='RGB json', default=None)
args = parser.parse_args()

# logging.basicConfig(filename='rubiks-rgb-solver.log',
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)5s: %(message)s')
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

    if width == 2:
        cube = RubiksColorSolver2x2x2()
    elif width == 3:
        cube = RubiksColorSolver3x3x3()
    else:
        cube = RubiksColorSolverGeneric(width)

    cube.enter_scan_data(scan_data)
    cube.crunch_colors()
    # print(json.dumps(cube.cube_for_json()))
    print(''.join(cube.cube_for_kociemba_strict()))

except Exception as e:
    log.exception(e)
    sys.exit(1)
