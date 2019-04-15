
from rubikscolorresolver.cube_444 import highlow_edge_values_444
from rubikscolorresolver.cube_555 import highlow_edge_values_555
from rubikscolorresolver.cube_666 import highlow_edge_values_666
from rubikscolorresolver.tsp_solver_greedy import solve_tsp

try:
    from collections import OrderedDict
    from json import dumps as json_dumps
    from json import loads as json_loads
    use_cie2000_cache = True
except ImportError:
    from ucollections import OrderedDict
    from ujson import dumps as json_dumps
    from ujson import loads as json_loads
    use_cie2000_cache = False

from math import atan2, ceil, cos, degrees, exp, radians, sin, sqrt

import array
import gc
import logging
import os
import sys

log = logging.getLogger(None)

LAB_DISTANCE_ALGORITHM = 'cie2000'
# LAB_DISTANCE_ALGORITHM = 'euclidean'
# LAB_DISTANCE_ALGORITHM = 'both'

cie2000_cache = {}

WHITE = (255, 255, 255)

html_color = {
    'Gr' : {'red' :   0, 'green' : 102, 'blue' : 0},
    'Bu' : {'red' :   0, 'green' :   0, 'blue' : 153},
    'OR' : {'red' : 255, 'green' : 102, 'blue' : 0},
    'Rd' : {'red' : 204, 'green' :   0, 'blue' : 0},
    'Wh' : {'red' : 255, 'green' : 255, 'blue' : 255},
    'Ye' : {'red' : 255, 'green' : 204, 'blue' : 0},
}

odd_cube_center_color_permutations = (
    ('Wh', 'OR', 'Gr', 'Rd', 'Bu', 'Ye'),
    ('Wh', 'Gr', 'Rd', 'Bu', 'OR', 'Ye'),
    ('Wh', 'Bu', 'OR', 'Gr', 'Rd', 'Ye'),
    ('Wh', 'Rd', 'Bu', 'OR', 'Gr', 'Ye'),

    ('Ye', 'Bu', 'Rd', 'Gr', 'OR', 'Wh'),
    ('Ye', 'Gr', 'OR', 'Bu', 'Rd', 'Wh'),
    ('Ye', 'Rd', 'Gr', 'OR', 'Bu', 'Wh'),
    ('Ye', 'OR', 'Bu', 'Rd', 'Gr', 'Wh'),

    ('OR', 'Ye', 'Gr', 'Wh', 'Bu', 'Rd'),
    ('OR', 'Wh', 'Bu', 'Ye', 'Gr', 'Rd'),
    ('OR', 'Gr', 'Wh', 'Bu', 'Ye', 'Rd'),
    ('OR', 'Bu', 'Ye', 'Gr', 'Wh', 'Rd'),

    ('Gr', 'Ye', 'Rd', 'Wh', 'OR', 'Bu'),
    ('Gr', 'Wh', 'OR', 'Ye', 'Rd', 'Bu'),
    ('Gr', 'Rd', 'Wh', 'OR', 'Ye', 'Bu'),
    ('Gr', 'OR', 'Ye', 'Rd', 'Wh', 'Bu'),

    ('Rd', 'Ye', 'Bu', 'Wh', 'Gr', 'OR'),
    ('Rd', 'Wh', 'Gr', 'Ye', 'Bu', 'OR'),
    ('Rd', 'Bu', 'Wh', 'Gr', 'Ye', 'OR'),
    ('Rd', 'Gr', 'Ye', 'Bu', 'Wh', 'OR'),

    ('Bu', 'Wh', 'Rd', 'Ye', 'OR', 'Gr'),
    ('Bu', 'Ye', 'OR', 'Wh', 'Rd', 'Gr'),
    ('Bu', 'Rd', 'Ye', 'OR', 'Wh', 'Gr'),
    ('Bu', 'OR', 'Wh', 'Rd', 'Ye', 'Gr'),
)

# from itertools import permutations
# from pprint import pprint
# even_cube_center_color_permutations = list(permutations(['Wh', 'Ye', 'OR', 'Rd', 'Gr', 'Bu']))
# even_cube_center_color_permutations.sort()
# pprint(even_cube_center_color_permutations)
even_cube_center_color_permutations = [
    ('Bu', 'Gr', 'OR', 'Rd', 'Wh', 'Ye'),
    ('Bu', 'Gr', 'OR', 'Rd', 'Ye', 'Wh'),
    ('Bu', 'Gr', 'OR', 'Wh', 'Rd', 'Ye'),
    ('Bu', 'Gr', 'OR', 'Wh', 'Ye', 'Rd'),
    ('Bu', 'Gr', 'OR', 'Ye', 'Rd', 'Wh'),
    ('Bu', 'Gr', 'OR', 'Ye', 'Wh', 'Rd'),
    ('Bu', 'Gr', 'Rd', 'OR', 'Wh', 'Ye'),
    ('Bu', 'Gr', 'Rd', 'OR', 'Ye', 'Wh'),
    ('Bu', 'Gr', 'Rd', 'Wh', 'OR', 'Ye'),
    ('Bu', 'Gr', 'Rd', 'Wh', 'Ye', 'OR'),
    ('Bu', 'Gr', 'Rd', 'Ye', 'OR', 'Wh'),
    ('Bu', 'Gr', 'Rd', 'Ye', 'Wh', 'OR'),
    ('Bu', 'Gr', 'Wh', 'OR', 'Rd', 'Ye'),
    ('Bu', 'Gr', 'Wh', 'OR', 'Ye', 'Rd'),
    ('Bu', 'Gr', 'Wh', 'Rd', 'OR', 'Ye'),
    ('Bu', 'Gr', 'Wh', 'Rd', 'Ye', 'OR'),
    ('Bu', 'Gr', 'Wh', 'Ye', 'OR', 'Rd'),
    ('Bu', 'Gr', 'Wh', 'Ye', 'Rd', 'OR'),
    ('Bu', 'Gr', 'Ye', 'OR', 'Rd', 'Wh'),
    ('Bu', 'Gr', 'Ye', 'OR', 'Wh', 'Rd'),
    ('Bu', 'Gr', 'Ye', 'Rd', 'OR', 'Wh'),
    ('Bu', 'Gr', 'Ye', 'Rd', 'Wh', 'OR'),
    ('Bu', 'Gr', 'Ye', 'Wh', 'OR', 'Rd'),
    ('Bu', 'Gr', 'Ye', 'Wh', 'Rd', 'OR'),
    ('Bu', 'OR', 'Gr', 'Rd', 'Wh', 'Ye'),
    ('Bu', 'OR', 'Gr', 'Rd', 'Ye', 'Wh'),
    ('Bu', 'OR', 'Gr', 'Wh', 'Rd', 'Ye'),
    ('Bu', 'OR', 'Gr', 'Wh', 'Ye', 'Rd'),
    ('Bu', 'OR', 'Gr', 'Ye', 'Rd', 'Wh'),
    ('Bu', 'OR', 'Gr', 'Ye', 'Wh', 'Rd'),
    ('Bu', 'OR', 'Rd', 'Gr', 'Wh', 'Ye'),
    ('Bu', 'OR', 'Rd', 'Gr', 'Ye', 'Wh'),
    ('Bu', 'OR', 'Rd', 'Wh', 'Gr', 'Ye'),
    ('Bu', 'OR', 'Rd', 'Wh', 'Ye', 'Gr'),
    ('Bu', 'OR', 'Rd', 'Ye', 'Gr', 'Wh'),
    ('Bu', 'OR', 'Rd', 'Ye', 'Wh', 'Gr'),
    ('Bu', 'OR', 'Wh', 'Gr', 'Rd', 'Ye'),
    ('Bu', 'OR', 'Wh', 'Gr', 'Ye', 'Rd'),
    ('Bu', 'OR', 'Wh', 'Rd', 'Gr', 'Ye'),
    ('Bu', 'OR', 'Wh', 'Rd', 'Ye', 'Gr'),
    ('Bu', 'OR', 'Wh', 'Ye', 'Gr', 'Rd'),
    ('Bu', 'OR', 'Wh', 'Ye', 'Rd', 'Gr'),
    ('Bu', 'OR', 'Ye', 'Gr', 'Rd', 'Wh'),
    ('Bu', 'OR', 'Ye', 'Gr', 'Wh', 'Rd'),
    ('Bu', 'OR', 'Ye', 'Rd', 'Gr', 'Wh'),
    ('Bu', 'OR', 'Ye', 'Rd', 'Wh', 'Gr'),
    ('Bu', 'OR', 'Ye', 'Wh', 'Gr', 'Rd'),
    ('Bu', 'OR', 'Ye', 'Wh', 'Rd', 'Gr'),
    ('Bu', 'Rd', 'Gr', 'OR', 'Wh', 'Ye'),
    ('Bu', 'Rd', 'Gr', 'OR', 'Ye', 'Wh'),
    ('Bu', 'Rd', 'Gr', 'Wh', 'OR', 'Ye'),
    ('Bu', 'Rd', 'Gr', 'Wh', 'Ye', 'OR'),
    ('Bu', 'Rd', 'Gr', 'Ye', 'OR', 'Wh'),
    ('Bu', 'Rd', 'Gr', 'Ye', 'Wh', 'OR'),
    ('Bu', 'Rd', 'OR', 'Gr', 'Wh', 'Ye'),
    ('Bu', 'Rd', 'OR', 'Gr', 'Ye', 'Wh'),
    ('Bu', 'Rd', 'OR', 'Wh', 'Gr', 'Ye'),
    ('Bu', 'Rd', 'OR', 'Wh', 'Ye', 'Gr'),
    ('Bu', 'Rd', 'OR', 'Ye', 'Gr', 'Wh'),
    ('Bu', 'Rd', 'OR', 'Ye', 'Wh', 'Gr'),
    ('Bu', 'Rd', 'Wh', 'Gr', 'OR', 'Ye'),
    ('Bu', 'Rd', 'Wh', 'Gr', 'Ye', 'OR'),
    ('Bu', 'Rd', 'Wh', 'OR', 'Gr', 'Ye'),
    ('Bu', 'Rd', 'Wh', 'OR', 'Ye', 'Gr'),
    ('Bu', 'Rd', 'Wh', 'Ye', 'Gr', 'OR'),
    ('Bu', 'Rd', 'Wh', 'Ye', 'OR', 'Gr'),
    ('Bu', 'Rd', 'Ye', 'Gr', 'OR', 'Wh'),
    ('Bu', 'Rd', 'Ye', 'Gr', 'Wh', 'OR'),
    ('Bu', 'Rd', 'Ye', 'OR', 'Gr', 'Wh'),
    ('Bu', 'Rd', 'Ye', 'OR', 'Wh', 'Gr'),
    ('Bu', 'Rd', 'Ye', 'Wh', 'Gr', 'OR'),
    ('Bu', 'Rd', 'Ye', 'Wh', 'OR', 'Gr'),
    ('Bu', 'Wh', 'Gr', 'OR', 'Rd', 'Ye'),
    ('Bu', 'Wh', 'Gr', 'OR', 'Ye', 'Rd'),
    ('Bu', 'Wh', 'Gr', 'Rd', 'OR', 'Ye'),
    ('Bu', 'Wh', 'Gr', 'Rd', 'Ye', 'OR'),
    ('Bu', 'Wh', 'Gr', 'Ye', 'OR', 'Rd'),
    ('Bu', 'Wh', 'Gr', 'Ye', 'Rd', 'OR'),
    ('Bu', 'Wh', 'OR', 'Gr', 'Rd', 'Ye'),
    ('Bu', 'Wh', 'OR', 'Gr', 'Ye', 'Rd'),
    ('Bu', 'Wh', 'OR', 'Rd', 'Gr', 'Ye'),
    ('Bu', 'Wh', 'OR', 'Rd', 'Ye', 'Gr'),
    ('Bu', 'Wh', 'OR', 'Ye', 'Gr', 'Rd'),
    ('Bu', 'Wh', 'OR', 'Ye', 'Rd', 'Gr'),
    ('Bu', 'Wh', 'Rd', 'Gr', 'OR', 'Ye'),
    ('Bu', 'Wh', 'Rd', 'Gr', 'Ye', 'OR'),
    ('Bu', 'Wh', 'Rd', 'OR', 'Gr', 'Ye'),
    ('Bu', 'Wh', 'Rd', 'OR', 'Ye', 'Gr'),
    ('Bu', 'Wh', 'Rd', 'Ye', 'Gr', 'OR'),
    ('Bu', 'Wh', 'Rd', 'Ye', 'OR', 'Gr'),
    ('Bu', 'Wh', 'Ye', 'Gr', 'OR', 'Rd'),
    ('Bu', 'Wh', 'Ye', 'Gr', 'Rd', 'OR'),
    ('Bu', 'Wh', 'Ye', 'OR', 'Gr', 'Rd'),
    ('Bu', 'Wh', 'Ye', 'OR', 'Rd', 'Gr'),
    ('Bu', 'Wh', 'Ye', 'Rd', 'Gr', 'OR'),
    ('Bu', 'Wh', 'Ye', 'Rd', 'OR', 'Gr'),
    ('Bu', 'Ye', 'Gr', 'OR', 'Rd', 'Wh'),
    ('Bu', 'Ye', 'Gr', 'OR', 'Wh', 'Rd'),
    ('Bu', 'Ye', 'Gr', 'Rd', 'OR', 'Wh'),
    ('Bu', 'Ye', 'Gr', 'Rd', 'Wh', 'OR'),
    ('Bu', 'Ye', 'Gr', 'Wh', 'OR', 'Rd'),
    ('Bu', 'Ye', 'Gr', 'Wh', 'Rd', 'OR'),
    ('Bu', 'Ye', 'OR', 'Gr', 'Rd', 'Wh'),
    ('Bu', 'Ye', 'OR', 'Gr', 'Wh', 'Rd'),
    ('Bu', 'Ye', 'OR', 'Rd', 'Gr', 'Wh'),
    ('Bu', 'Ye', 'OR', 'Rd', 'Wh', 'Gr'),
    ('Bu', 'Ye', 'OR', 'Wh', 'Gr', 'Rd'),
    ('Bu', 'Ye', 'OR', 'Wh', 'Rd', 'Gr'),
    ('Bu', 'Ye', 'Rd', 'Gr', 'OR', 'Wh'),
    ('Bu', 'Ye', 'Rd', 'Gr', 'Wh', 'OR'),
    ('Bu', 'Ye', 'Rd', 'OR', 'Gr', 'Wh'),
    ('Bu', 'Ye', 'Rd', 'OR', 'Wh', 'Gr'),
    ('Bu', 'Ye', 'Rd', 'Wh', 'Gr', 'OR'),
    ('Bu', 'Ye', 'Rd', 'Wh', 'OR', 'Gr'),
    ('Bu', 'Ye', 'Wh', 'Gr', 'OR', 'Rd'),
    ('Bu', 'Ye', 'Wh', 'Gr', 'Rd', 'OR'),
    ('Bu', 'Ye', 'Wh', 'OR', 'Gr', 'Rd'),
    ('Bu', 'Ye', 'Wh', 'OR', 'Rd', 'Gr'),
    ('Bu', 'Ye', 'Wh', 'Rd', 'Gr', 'OR'),
    ('Bu', 'Ye', 'Wh', 'Rd', 'OR', 'Gr'),
    ('Gr', 'Bu', 'OR', 'Rd', 'Wh', 'Ye'),
    ('Gr', 'Bu', 'OR', 'Rd', 'Ye', 'Wh'),
    ('Gr', 'Bu', 'OR', 'Wh', 'Rd', 'Ye'),
    ('Gr', 'Bu', 'OR', 'Wh', 'Ye', 'Rd'),
    ('Gr', 'Bu', 'OR', 'Ye', 'Rd', 'Wh'),
    ('Gr', 'Bu', 'OR', 'Ye', 'Wh', 'Rd'),
    ('Gr', 'Bu', 'Rd', 'OR', 'Wh', 'Ye'),
    ('Gr', 'Bu', 'Rd', 'OR', 'Ye', 'Wh'),
    ('Gr', 'Bu', 'Rd', 'Wh', 'OR', 'Ye'),
    ('Gr', 'Bu', 'Rd', 'Wh', 'Ye', 'OR'),
    ('Gr', 'Bu', 'Rd', 'Ye', 'OR', 'Wh'),
    ('Gr', 'Bu', 'Rd', 'Ye', 'Wh', 'OR'),
    ('Gr', 'Bu', 'Wh', 'OR', 'Rd', 'Ye'),
    ('Gr', 'Bu', 'Wh', 'OR', 'Ye', 'Rd'),
    ('Gr', 'Bu', 'Wh', 'Rd', 'OR', 'Ye'),
    ('Gr', 'Bu', 'Wh', 'Rd', 'Ye', 'OR'),
    ('Gr', 'Bu', 'Wh', 'Ye', 'OR', 'Rd'),
    ('Gr', 'Bu', 'Wh', 'Ye', 'Rd', 'OR'),
    ('Gr', 'Bu', 'Ye', 'OR', 'Rd', 'Wh'),
    ('Gr', 'Bu', 'Ye', 'OR', 'Wh', 'Rd'),
    ('Gr', 'Bu', 'Ye', 'Rd', 'OR', 'Wh'),
    ('Gr', 'Bu', 'Ye', 'Rd', 'Wh', 'OR'),
    ('Gr', 'Bu', 'Ye', 'Wh', 'OR', 'Rd'),
    ('Gr', 'Bu', 'Ye', 'Wh', 'Rd', 'OR'),
    ('Gr', 'OR', 'Bu', 'Rd', 'Wh', 'Ye'),
    ('Gr', 'OR', 'Bu', 'Rd', 'Ye', 'Wh'),
    ('Gr', 'OR', 'Bu', 'Wh', 'Rd', 'Ye'),
    ('Gr', 'OR', 'Bu', 'Wh', 'Ye', 'Rd'),
    ('Gr', 'OR', 'Bu', 'Ye', 'Rd', 'Wh'),
    ('Gr', 'OR', 'Bu', 'Ye', 'Wh', 'Rd'),
    ('Gr', 'OR', 'Rd', 'Bu', 'Wh', 'Ye'),
    ('Gr', 'OR', 'Rd', 'Bu', 'Ye', 'Wh'),
    ('Gr', 'OR', 'Rd', 'Wh', 'Bu', 'Ye'),
    ('Gr', 'OR', 'Rd', 'Wh', 'Ye', 'Bu'),
    ('Gr', 'OR', 'Rd', 'Ye', 'Bu', 'Wh'),
    ('Gr', 'OR', 'Rd', 'Ye', 'Wh', 'Bu'),
    ('Gr', 'OR', 'Wh', 'Bu', 'Rd', 'Ye'),
    ('Gr', 'OR', 'Wh', 'Bu', 'Ye', 'Rd'),
    ('Gr', 'OR', 'Wh', 'Rd', 'Bu', 'Ye'),
    ('Gr', 'OR', 'Wh', 'Rd', 'Ye', 'Bu'),
    ('Gr', 'OR', 'Wh', 'Ye', 'Bu', 'Rd'),
    ('Gr', 'OR', 'Wh', 'Ye', 'Rd', 'Bu'),
    ('Gr', 'OR', 'Ye', 'Bu', 'Rd', 'Wh'),
    ('Gr', 'OR', 'Ye', 'Bu', 'Wh', 'Rd'),
    ('Gr', 'OR', 'Ye', 'Rd', 'Bu', 'Wh'),
    ('Gr', 'OR', 'Ye', 'Rd', 'Wh', 'Bu'),
    ('Gr', 'OR', 'Ye', 'Wh', 'Bu', 'Rd'),
    ('Gr', 'OR', 'Ye', 'Wh', 'Rd', 'Bu'),
    ('Gr', 'Rd', 'Bu', 'OR', 'Wh', 'Ye'),
    ('Gr', 'Rd', 'Bu', 'OR', 'Ye', 'Wh'),
    ('Gr', 'Rd', 'Bu', 'Wh', 'OR', 'Ye'),
    ('Gr', 'Rd', 'Bu', 'Wh', 'Ye', 'OR'),
    ('Gr', 'Rd', 'Bu', 'Ye', 'OR', 'Wh'),
    ('Gr', 'Rd', 'Bu', 'Ye', 'Wh', 'OR'),
    ('Gr', 'Rd', 'OR', 'Bu', 'Wh', 'Ye'),
    ('Gr', 'Rd', 'OR', 'Bu', 'Ye', 'Wh'),
    ('Gr', 'Rd', 'OR', 'Wh', 'Bu', 'Ye'),
    ('Gr', 'Rd', 'OR', 'Wh', 'Ye', 'Bu'),
    ('Gr', 'Rd', 'OR', 'Ye', 'Bu', 'Wh'),
    ('Gr', 'Rd', 'OR', 'Ye', 'Wh', 'Bu'),
    ('Gr', 'Rd', 'Wh', 'Bu', 'OR', 'Ye'),
    ('Gr', 'Rd', 'Wh', 'Bu', 'Ye', 'OR'),
    ('Gr', 'Rd', 'Wh', 'OR', 'Bu', 'Ye'),
    ('Gr', 'Rd', 'Wh', 'OR', 'Ye', 'Bu'),
    ('Gr', 'Rd', 'Wh', 'Ye', 'Bu', 'OR'),
    ('Gr', 'Rd', 'Wh', 'Ye', 'OR', 'Bu'),
    ('Gr', 'Rd', 'Ye', 'Bu', 'OR', 'Wh'),
    ('Gr', 'Rd', 'Ye', 'Bu', 'Wh', 'OR'),
    ('Gr', 'Rd', 'Ye', 'OR', 'Bu', 'Wh'),
    ('Gr', 'Rd', 'Ye', 'OR', 'Wh', 'Bu'),
    ('Gr', 'Rd', 'Ye', 'Wh', 'Bu', 'OR'),
    ('Gr', 'Rd', 'Ye', 'Wh', 'OR', 'Bu'),
    ('Gr', 'Wh', 'Bu', 'OR', 'Rd', 'Ye'),
    ('Gr', 'Wh', 'Bu', 'OR', 'Ye', 'Rd'),
    ('Gr', 'Wh', 'Bu', 'Rd', 'OR', 'Ye'),
    ('Gr', 'Wh', 'Bu', 'Rd', 'Ye', 'OR'),
    ('Gr', 'Wh', 'Bu', 'Ye', 'OR', 'Rd'),
    ('Gr', 'Wh', 'Bu', 'Ye', 'Rd', 'OR'),
    ('Gr', 'Wh', 'OR', 'Bu', 'Rd', 'Ye'),
    ('Gr', 'Wh', 'OR', 'Bu', 'Ye', 'Rd'),
    ('Gr', 'Wh', 'OR', 'Rd', 'Bu', 'Ye'),
    ('Gr', 'Wh', 'OR', 'Rd', 'Ye', 'Bu'),
    ('Gr', 'Wh', 'OR', 'Ye', 'Bu', 'Rd'),
    ('Gr', 'Wh', 'OR', 'Ye', 'Rd', 'Bu'),
    ('Gr', 'Wh', 'Rd', 'Bu', 'OR', 'Ye'),
    ('Gr', 'Wh', 'Rd', 'Bu', 'Ye', 'OR'),
    ('Gr', 'Wh', 'Rd', 'OR', 'Bu', 'Ye'),
    ('Gr', 'Wh', 'Rd', 'OR', 'Ye', 'Bu'),
    ('Gr', 'Wh', 'Rd', 'Ye', 'Bu', 'OR'),
    ('Gr', 'Wh', 'Rd', 'Ye', 'OR', 'Bu'),
    ('Gr', 'Wh', 'Ye', 'Bu', 'OR', 'Rd'),
    ('Gr', 'Wh', 'Ye', 'Bu', 'Rd', 'OR'),
    ('Gr', 'Wh', 'Ye', 'OR', 'Bu', 'Rd'),
    ('Gr', 'Wh', 'Ye', 'OR', 'Rd', 'Bu'),
    ('Gr', 'Wh', 'Ye', 'Rd', 'Bu', 'OR'),
    ('Gr', 'Wh', 'Ye', 'Rd', 'OR', 'Bu'),
    ('Gr', 'Ye', 'Bu', 'OR', 'Rd', 'Wh'),
    ('Gr', 'Ye', 'Bu', 'OR', 'Wh', 'Rd'),
    ('Gr', 'Ye', 'Bu', 'Rd', 'OR', 'Wh'),
    ('Gr', 'Ye', 'Bu', 'Rd', 'Wh', 'OR'),
    ('Gr', 'Ye', 'Bu', 'Wh', 'OR', 'Rd'),
    ('Gr', 'Ye', 'Bu', 'Wh', 'Rd', 'OR'),
    ('Gr', 'Ye', 'OR', 'Bu', 'Rd', 'Wh'),
    ('Gr', 'Ye', 'OR', 'Bu', 'Wh', 'Rd'),
    ('Gr', 'Ye', 'OR', 'Rd', 'Bu', 'Wh'),
    ('Gr', 'Ye', 'OR', 'Rd', 'Wh', 'Bu'),
    ('Gr', 'Ye', 'OR', 'Wh', 'Bu', 'Rd'),
    ('Gr', 'Ye', 'OR', 'Wh', 'Rd', 'Bu'),
    ('Gr', 'Ye', 'Rd', 'Bu', 'OR', 'Wh'),
    ('Gr', 'Ye', 'Rd', 'Bu', 'Wh', 'OR'),
    ('Gr', 'Ye', 'Rd', 'OR', 'Bu', 'Wh'),
    ('Gr', 'Ye', 'Rd', 'OR', 'Wh', 'Bu'),
    ('Gr', 'Ye', 'Rd', 'Wh', 'Bu', 'OR'),
    ('Gr', 'Ye', 'Rd', 'Wh', 'OR', 'Bu'),
    ('Gr', 'Ye', 'Wh', 'Bu', 'OR', 'Rd'),
    ('Gr', 'Ye', 'Wh', 'Bu', 'Rd', 'OR'),
    ('Gr', 'Ye', 'Wh', 'OR', 'Bu', 'Rd'),
    ('Gr', 'Ye', 'Wh', 'OR', 'Rd', 'Bu'),
    ('Gr', 'Ye', 'Wh', 'Rd', 'Bu', 'OR'),
    ('Gr', 'Ye', 'Wh', 'Rd', 'OR', 'Bu'),
    ('OR', 'Bu', 'Gr', 'Rd', 'Wh', 'Ye'),
    ('OR', 'Bu', 'Gr', 'Rd', 'Ye', 'Wh'),
    ('OR', 'Bu', 'Gr', 'Wh', 'Rd', 'Ye'),
    ('OR', 'Bu', 'Gr', 'Wh', 'Ye', 'Rd'),
    ('OR', 'Bu', 'Gr', 'Ye', 'Rd', 'Wh'),
    ('OR', 'Bu', 'Gr', 'Ye', 'Wh', 'Rd'),
    ('OR', 'Bu', 'Rd', 'Gr', 'Wh', 'Ye'),
    ('OR', 'Bu', 'Rd', 'Gr', 'Ye', 'Wh'),
    ('OR', 'Bu', 'Rd', 'Wh', 'Gr', 'Ye'),
    ('OR', 'Bu', 'Rd', 'Wh', 'Ye', 'Gr'),
    ('OR', 'Bu', 'Rd', 'Ye', 'Gr', 'Wh'),
    ('OR', 'Bu', 'Rd', 'Ye', 'Wh', 'Gr'),
    ('OR', 'Bu', 'Wh', 'Gr', 'Rd', 'Ye'),
    ('OR', 'Bu', 'Wh', 'Gr', 'Ye', 'Rd'),
    ('OR', 'Bu', 'Wh', 'Rd', 'Gr', 'Ye'),
    ('OR', 'Bu', 'Wh', 'Rd', 'Ye', 'Gr'),
    ('OR', 'Bu', 'Wh', 'Ye', 'Gr', 'Rd'),
    ('OR', 'Bu', 'Wh', 'Ye', 'Rd', 'Gr'),
    ('OR', 'Bu', 'Ye', 'Gr', 'Rd', 'Wh'),
    ('OR', 'Bu', 'Ye', 'Gr', 'Wh', 'Rd'),
    ('OR', 'Bu', 'Ye', 'Rd', 'Gr', 'Wh'),
    ('OR', 'Bu', 'Ye', 'Rd', 'Wh', 'Gr'),
    ('OR', 'Bu', 'Ye', 'Wh', 'Gr', 'Rd'),
    ('OR', 'Bu', 'Ye', 'Wh', 'Rd', 'Gr'),
    ('OR', 'Gr', 'Bu', 'Rd', 'Wh', 'Ye'),
    ('OR', 'Gr', 'Bu', 'Rd', 'Ye', 'Wh'),
    ('OR', 'Gr', 'Bu', 'Wh', 'Rd', 'Ye'),
    ('OR', 'Gr', 'Bu', 'Wh', 'Ye', 'Rd'),
    ('OR', 'Gr', 'Bu', 'Ye', 'Rd', 'Wh'),
    ('OR', 'Gr', 'Bu', 'Ye', 'Wh', 'Rd'),
    ('OR', 'Gr', 'Rd', 'Bu', 'Wh', 'Ye'),
    ('OR', 'Gr', 'Rd', 'Bu', 'Ye', 'Wh'),
    ('OR', 'Gr', 'Rd', 'Wh', 'Bu', 'Ye'),
    ('OR', 'Gr', 'Rd', 'Wh', 'Ye', 'Bu'),
    ('OR', 'Gr', 'Rd', 'Ye', 'Bu', 'Wh'),
    ('OR', 'Gr', 'Rd', 'Ye', 'Wh', 'Bu'),
    ('OR', 'Gr', 'Wh', 'Bu', 'Rd', 'Ye'),
    ('OR', 'Gr', 'Wh', 'Bu', 'Ye', 'Rd'),
    ('OR', 'Gr', 'Wh', 'Rd', 'Bu', 'Ye'),
    ('OR', 'Gr', 'Wh', 'Rd', 'Ye', 'Bu'),
    ('OR', 'Gr', 'Wh', 'Ye', 'Bu', 'Rd'),
    ('OR', 'Gr', 'Wh', 'Ye', 'Rd', 'Bu'),
    ('OR', 'Gr', 'Ye', 'Bu', 'Rd', 'Wh'),
    ('OR', 'Gr', 'Ye', 'Bu', 'Wh', 'Rd'),
    ('OR', 'Gr', 'Ye', 'Rd', 'Bu', 'Wh'),
    ('OR', 'Gr', 'Ye', 'Rd', 'Wh', 'Bu'),
    ('OR', 'Gr', 'Ye', 'Wh', 'Bu', 'Rd'),
    ('OR', 'Gr', 'Ye', 'Wh', 'Rd', 'Bu'),
    ('OR', 'Rd', 'Bu', 'Gr', 'Wh', 'Ye'),
    ('OR', 'Rd', 'Bu', 'Gr', 'Ye', 'Wh'),
    ('OR', 'Rd', 'Bu', 'Wh', 'Gr', 'Ye'),
    ('OR', 'Rd', 'Bu', 'Wh', 'Ye', 'Gr'),
    ('OR', 'Rd', 'Bu', 'Ye', 'Gr', 'Wh'),
    ('OR', 'Rd', 'Bu', 'Ye', 'Wh', 'Gr'),
    ('OR', 'Rd', 'Gr', 'Bu', 'Wh', 'Ye'),
    ('OR', 'Rd', 'Gr', 'Bu', 'Ye', 'Wh'),
    ('OR', 'Rd', 'Gr', 'Wh', 'Bu', 'Ye'),
    ('OR', 'Rd', 'Gr', 'Wh', 'Ye', 'Bu'),
    ('OR', 'Rd', 'Gr', 'Ye', 'Bu', 'Wh'),
    ('OR', 'Rd', 'Gr', 'Ye', 'Wh', 'Bu'),
    ('OR', 'Rd', 'Wh', 'Bu', 'Gr', 'Ye'),
    ('OR', 'Rd', 'Wh', 'Bu', 'Ye', 'Gr'),
    ('OR', 'Rd', 'Wh', 'Gr', 'Bu', 'Ye'),
    ('OR', 'Rd', 'Wh', 'Gr', 'Ye', 'Bu'),
    ('OR', 'Rd', 'Wh', 'Ye', 'Bu', 'Gr'),
    ('OR', 'Rd', 'Wh', 'Ye', 'Gr', 'Bu'),
    ('OR', 'Rd', 'Ye', 'Bu', 'Gr', 'Wh'),
    ('OR', 'Rd', 'Ye', 'Bu', 'Wh', 'Gr'),
    ('OR', 'Rd', 'Ye', 'Gr', 'Bu', 'Wh'),
    ('OR', 'Rd', 'Ye', 'Gr', 'Wh', 'Bu'),
    ('OR', 'Rd', 'Ye', 'Wh', 'Bu', 'Gr'),
    ('OR', 'Rd', 'Ye', 'Wh', 'Gr', 'Bu'),
    ('OR', 'Wh', 'Bu', 'Gr', 'Rd', 'Ye'),
    ('OR', 'Wh', 'Bu', 'Gr', 'Ye', 'Rd'),
    ('OR', 'Wh', 'Bu', 'Rd', 'Gr', 'Ye'),
    ('OR', 'Wh', 'Bu', 'Rd', 'Ye', 'Gr'),
    ('OR', 'Wh', 'Bu', 'Ye', 'Gr', 'Rd'),
    ('OR', 'Wh', 'Bu', 'Ye', 'Rd', 'Gr'),
    ('OR', 'Wh', 'Gr', 'Bu', 'Rd', 'Ye'),
    ('OR', 'Wh', 'Gr', 'Bu', 'Ye', 'Rd'),
    ('OR', 'Wh', 'Gr', 'Rd', 'Bu', 'Ye'),
    ('OR', 'Wh', 'Gr', 'Rd', 'Ye', 'Bu'),
    ('OR', 'Wh', 'Gr', 'Ye', 'Bu', 'Rd'),
    ('OR', 'Wh', 'Gr', 'Ye', 'Rd', 'Bu'),
    ('OR', 'Wh', 'Rd', 'Bu', 'Gr', 'Ye'),
    ('OR', 'Wh', 'Rd', 'Bu', 'Ye', 'Gr'),
    ('OR', 'Wh', 'Rd', 'Gr', 'Bu', 'Ye'),
    ('OR', 'Wh', 'Rd', 'Gr', 'Ye', 'Bu'),
    ('OR', 'Wh', 'Rd', 'Ye', 'Bu', 'Gr'),
    ('OR', 'Wh', 'Rd', 'Ye', 'Gr', 'Bu'),
    ('OR', 'Wh', 'Ye', 'Bu', 'Gr', 'Rd'),
    ('OR', 'Wh', 'Ye', 'Bu', 'Rd', 'Gr'),
    ('OR', 'Wh', 'Ye', 'Gr', 'Bu', 'Rd'),
    ('OR', 'Wh', 'Ye', 'Gr', 'Rd', 'Bu'),
    ('OR', 'Wh', 'Ye', 'Rd', 'Bu', 'Gr'),
    ('OR', 'Wh', 'Ye', 'Rd', 'Gr', 'Bu'),
    ('OR', 'Ye', 'Bu', 'Gr', 'Rd', 'Wh'),
    ('OR', 'Ye', 'Bu', 'Gr', 'Wh', 'Rd'),
    ('OR', 'Ye', 'Bu', 'Rd', 'Gr', 'Wh'),
    ('OR', 'Ye', 'Bu', 'Rd', 'Wh', 'Gr'),
    ('OR', 'Ye', 'Bu', 'Wh', 'Gr', 'Rd'),
    ('OR', 'Ye', 'Bu', 'Wh', 'Rd', 'Gr'),
    ('OR', 'Ye', 'Gr', 'Bu', 'Rd', 'Wh'),
    ('OR', 'Ye', 'Gr', 'Bu', 'Wh', 'Rd'),
    ('OR', 'Ye', 'Gr', 'Rd', 'Bu', 'Wh'),
    ('OR', 'Ye', 'Gr', 'Rd', 'Wh', 'Bu'),
    ('OR', 'Ye', 'Gr', 'Wh', 'Bu', 'Rd'),
    ('OR', 'Ye', 'Gr', 'Wh', 'Rd', 'Bu'),
    ('OR', 'Ye', 'Rd', 'Bu', 'Gr', 'Wh'),
    ('OR', 'Ye', 'Rd', 'Bu', 'Wh', 'Gr'),
    ('OR', 'Ye', 'Rd', 'Gr', 'Bu', 'Wh'),
    ('OR', 'Ye', 'Rd', 'Gr', 'Wh', 'Bu'),
    ('OR', 'Ye', 'Rd', 'Wh', 'Bu', 'Gr'),
    ('OR', 'Ye', 'Rd', 'Wh', 'Gr', 'Bu'),
    ('OR', 'Ye', 'Wh', 'Bu', 'Gr', 'Rd'),
    ('OR', 'Ye', 'Wh', 'Bu', 'Rd', 'Gr'),
    ('OR', 'Ye', 'Wh', 'Gr', 'Bu', 'Rd'),
    ('OR', 'Ye', 'Wh', 'Gr', 'Rd', 'Bu'),
    ('OR', 'Ye', 'Wh', 'Rd', 'Bu', 'Gr'),
    ('OR', 'Ye', 'Wh', 'Rd', 'Gr', 'Bu'),
    ('Rd', 'Bu', 'Gr', 'OR', 'Wh', 'Ye'),
    ('Rd', 'Bu', 'Gr', 'OR', 'Ye', 'Wh'),
    ('Rd', 'Bu', 'Gr', 'Wh', 'OR', 'Ye'),
    ('Rd', 'Bu', 'Gr', 'Wh', 'Ye', 'OR'),
    ('Rd', 'Bu', 'Gr', 'Ye', 'OR', 'Wh'),
    ('Rd', 'Bu', 'Gr', 'Ye', 'Wh', 'OR'),
    ('Rd', 'Bu', 'OR', 'Gr', 'Wh', 'Ye'),
    ('Rd', 'Bu', 'OR', 'Gr', 'Ye', 'Wh'),
    ('Rd', 'Bu', 'OR', 'Wh', 'Gr', 'Ye'),
    ('Rd', 'Bu', 'OR', 'Wh', 'Ye', 'Gr'),
    ('Rd', 'Bu', 'OR', 'Ye', 'Gr', 'Wh'),
    ('Rd', 'Bu', 'OR', 'Ye', 'Wh', 'Gr'),
    ('Rd', 'Bu', 'Wh', 'Gr', 'OR', 'Ye'),
    ('Rd', 'Bu', 'Wh', 'Gr', 'Ye', 'OR'),
    ('Rd', 'Bu', 'Wh', 'OR', 'Gr', 'Ye'),
    ('Rd', 'Bu', 'Wh', 'OR', 'Ye', 'Gr'),
    ('Rd', 'Bu', 'Wh', 'Ye', 'Gr', 'OR'),
    ('Rd', 'Bu', 'Wh', 'Ye', 'OR', 'Gr'),
    ('Rd', 'Bu', 'Ye', 'Gr', 'OR', 'Wh'),
    ('Rd', 'Bu', 'Ye', 'Gr', 'Wh', 'OR'),
    ('Rd', 'Bu', 'Ye', 'OR', 'Gr', 'Wh'),
    ('Rd', 'Bu', 'Ye', 'OR', 'Wh', 'Gr'),
    ('Rd', 'Bu', 'Ye', 'Wh', 'Gr', 'OR'),
    ('Rd', 'Bu', 'Ye', 'Wh', 'OR', 'Gr'),
    ('Rd', 'Gr', 'Bu', 'OR', 'Wh', 'Ye'),
    ('Rd', 'Gr', 'Bu', 'OR', 'Ye', 'Wh'),
    ('Rd', 'Gr', 'Bu', 'Wh', 'OR', 'Ye'),
    ('Rd', 'Gr', 'Bu', 'Wh', 'Ye', 'OR'),
    ('Rd', 'Gr', 'Bu', 'Ye', 'OR', 'Wh'),
    ('Rd', 'Gr', 'Bu', 'Ye', 'Wh', 'OR'),
    ('Rd', 'Gr', 'OR', 'Bu', 'Wh', 'Ye'),
    ('Rd', 'Gr', 'OR', 'Bu', 'Ye', 'Wh'),
    ('Rd', 'Gr', 'OR', 'Wh', 'Bu', 'Ye'),
    ('Rd', 'Gr', 'OR', 'Wh', 'Ye', 'Bu'),
    ('Rd', 'Gr', 'OR', 'Ye', 'Bu', 'Wh'),
    ('Rd', 'Gr', 'OR', 'Ye', 'Wh', 'Bu'),
    ('Rd', 'Gr', 'Wh', 'Bu', 'OR', 'Ye'),
    ('Rd', 'Gr', 'Wh', 'Bu', 'Ye', 'OR'),
    ('Rd', 'Gr', 'Wh', 'OR', 'Bu', 'Ye'),
    ('Rd', 'Gr', 'Wh', 'OR', 'Ye', 'Bu'),
    ('Rd', 'Gr', 'Wh', 'Ye', 'Bu', 'OR'),
    ('Rd', 'Gr', 'Wh', 'Ye', 'OR', 'Bu'),
    ('Rd', 'Gr', 'Ye', 'Bu', 'OR', 'Wh'),
    ('Rd', 'Gr', 'Ye', 'Bu', 'Wh', 'OR'),
    ('Rd', 'Gr', 'Ye', 'OR', 'Bu', 'Wh'),
    ('Rd', 'Gr', 'Ye', 'OR', 'Wh', 'Bu'),
    ('Rd', 'Gr', 'Ye', 'Wh', 'Bu', 'OR'),
    ('Rd', 'Gr', 'Ye', 'Wh', 'OR', 'Bu'),
    ('Rd', 'OR', 'Bu', 'Gr', 'Wh', 'Ye'),
    ('Rd', 'OR', 'Bu', 'Gr', 'Ye', 'Wh'),
    ('Rd', 'OR', 'Bu', 'Wh', 'Gr', 'Ye'),
    ('Rd', 'OR', 'Bu', 'Wh', 'Ye', 'Gr'),
    ('Rd', 'OR', 'Bu', 'Ye', 'Gr', 'Wh'),
    ('Rd', 'OR', 'Bu', 'Ye', 'Wh', 'Gr'),
    ('Rd', 'OR', 'Gr', 'Bu', 'Wh', 'Ye'),
    ('Rd', 'OR', 'Gr', 'Bu', 'Ye', 'Wh'),
    ('Rd', 'OR', 'Gr', 'Wh', 'Bu', 'Ye'),
    ('Rd', 'OR', 'Gr', 'Wh', 'Ye', 'Bu'),
    ('Rd', 'OR', 'Gr', 'Ye', 'Bu', 'Wh'),
    ('Rd', 'OR', 'Gr', 'Ye', 'Wh', 'Bu'),
    ('Rd', 'OR', 'Wh', 'Bu', 'Gr', 'Ye'),
    ('Rd', 'OR', 'Wh', 'Bu', 'Ye', 'Gr'),
    ('Rd', 'OR', 'Wh', 'Gr', 'Bu', 'Ye'),
    ('Rd', 'OR', 'Wh', 'Gr', 'Ye', 'Bu'),
    ('Rd', 'OR', 'Wh', 'Ye', 'Bu', 'Gr'),
    ('Rd', 'OR', 'Wh', 'Ye', 'Gr', 'Bu'),
    ('Rd', 'OR', 'Ye', 'Bu', 'Gr', 'Wh'),
    ('Rd', 'OR', 'Ye', 'Bu', 'Wh', 'Gr'),
    ('Rd', 'OR', 'Ye', 'Gr', 'Bu', 'Wh'),
    ('Rd', 'OR', 'Ye', 'Gr', 'Wh', 'Bu'),
    ('Rd', 'OR', 'Ye', 'Wh', 'Bu', 'Gr'),
    ('Rd', 'OR', 'Ye', 'Wh', 'Gr', 'Bu'),
    ('Rd', 'Wh', 'Bu', 'Gr', 'OR', 'Ye'),
    ('Rd', 'Wh', 'Bu', 'Gr', 'Ye', 'OR'),
    ('Rd', 'Wh', 'Bu', 'OR', 'Gr', 'Ye'),
    ('Rd', 'Wh', 'Bu', 'OR', 'Ye', 'Gr'),
    ('Rd', 'Wh', 'Bu', 'Ye', 'Gr', 'OR'),
    ('Rd', 'Wh', 'Bu', 'Ye', 'OR', 'Gr'),
    ('Rd', 'Wh', 'Gr', 'Bu', 'OR', 'Ye'),
    ('Rd', 'Wh', 'Gr', 'Bu', 'Ye', 'OR'),
    ('Rd', 'Wh', 'Gr', 'OR', 'Bu', 'Ye'),
    ('Rd', 'Wh', 'Gr', 'OR', 'Ye', 'Bu'),
    ('Rd', 'Wh', 'Gr', 'Ye', 'Bu', 'OR'),
    ('Rd', 'Wh', 'Gr', 'Ye', 'OR', 'Bu'),
    ('Rd', 'Wh', 'OR', 'Bu', 'Gr', 'Ye'),
    ('Rd', 'Wh', 'OR', 'Bu', 'Ye', 'Gr'),
    ('Rd', 'Wh', 'OR', 'Gr', 'Bu', 'Ye'),
    ('Rd', 'Wh', 'OR', 'Gr', 'Ye', 'Bu'),
    ('Rd', 'Wh', 'OR', 'Ye', 'Bu', 'Gr'),
    ('Rd', 'Wh', 'OR', 'Ye', 'Gr', 'Bu'),
    ('Rd', 'Wh', 'Ye', 'Bu', 'Gr', 'OR'),
    ('Rd', 'Wh', 'Ye', 'Bu', 'OR', 'Gr'),
    ('Rd', 'Wh', 'Ye', 'Gr', 'Bu', 'OR'),
    ('Rd', 'Wh', 'Ye', 'Gr', 'OR', 'Bu'),
    ('Rd', 'Wh', 'Ye', 'OR', 'Bu', 'Gr'),
    ('Rd', 'Wh', 'Ye', 'OR', 'Gr', 'Bu'),
    ('Rd', 'Ye', 'Bu', 'Gr', 'OR', 'Wh'),
    ('Rd', 'Ye', 'Bu', 'Gr', 'Wh', 'OR'),
    ('Rd', 'Ye', 'Bu', 'OR', 'Gr', 'Wh'),
    ('Rd', 'Ye', 'Bu', 'OR', 'Wh', 'Gr'),
    ('Rd', 'Ye', 'Bu', 'Wh', 'Gr', 'OR'),
    ('Rd', 'Ye', 'Bu', 'Wh', 'OR', 'Gr'),
    ('Rd', 'Ye', 'Gr', 'Bu', 'OR', 'Wh'),
    ('Rd', 'Ye', 'Gr', 'Bu', 'Wh', 'OR'),
    ('Rd', 'Ye', 'Gr', 'OR', 'Bu', 'Wh'),
    ('Rd', 'Ye', 'Gr', 'OR', 'Wh', 'Bu'),
    ('Rd', 'Ye', 'Gr', 'Wh', 'Bu', 'OR'),
    ('Rd', 'Ye', 'Gr', 'Wh', 'OR', 'Bu'),
    ('Rd', 'Ye', 'OR', 'Bu', 'Gr', 'Wh'),
    ('Rd', 'Ye', 'OR', 'Bu', 'Wh', 'Gr'),
    ('Rd', 'Ye', 'OR', 'Gr', 'Bu', 'Wh'),
    ('Rd', 'Ye', 'OR', 'Gr', 'Wh', 'Bu'),
    ('Rd', 'Ye', 'OR', 'Wh', 'Bu', 'Gr'),
    ('Rd', 'Ye', 'OR', 'Wh', 'Gr', 'Bu'),
    ('Rd', 'Ye', 'Wh', 'Bu', 'Gr', 'OR'),
    ('Rd', 'Ye', 'Wh', 'Bu', 'OR', 'Gr'),
    ('Rd', 'Ye', 'Wh', 'Gr', 'Bu', 'OR'),
    ('Rd', 'Ye', 'Wh', 'Gr', 'OR', 'Bu'),
    ('Rd', 'Ye', 'Wh', 'OR', 'Bu', 'Gr'),
    ('Rd', 'Ye', 'Wh', 'OR', 'Gr', 'Bu'),
    ('Wh', 'Bu', 'Gr', 'OR', 'Rd', 'Ye'),
    ('Wh', 'Bu', 'Gr', 'OR', 'Ye', 'Rd'),
    ('Wh', 'Bu', 'Gr', 'Rd', 'OR', 'Ye'),
    ('Wh', 'Bu', 'Gr', 'Rd', 'Ye', 'OR'),
    ('Wh', 'Bu', 'Gr', 'Ye', 'OR', 'Rd'),
    ('Wh', 'Bu', 'Gr', 'Ye', 'Rd', 'OR'),
    ('Wh', 'Bu', 'OR', 'Gr', 'Rd', 'Ye'),
    ('Wh', 'Bu', 'OR', 'Gr', 'Ye', 'Rd'),
    ('Wh', 'Bu', 'OR', 'Rd', 'Gr', 'Ye'),
    ('Wh', 'Bu', 'OR', 'Rd', 'Ye', 'Gr'),
    ('Wh', 'Bu', 'OR', 'Ye', 'Gr', 'Rd'),
    ('Wh', 'Bu', 'OR', 'Ye', 'Rd', 'Gr'),
    ('Wh', 'Bu', 'Rd', 'Gr', 'OR', 'Ye'),
    ('Wh', 'Bu', 'Rd', 'Gr', 'Ye', 'OR'),
    ('Wh', 'Bu', 'Rd', 'OR', 'Gr', 'Ye'),
    ('Wh', 'Bu', 'Rd', 'OR', 'Ye', 'Gr'),
    ('Wh', 'Bu', 'Rd', 'Ye', 'Gr', 'OR'),
    ('Wh', 'Bu', 'Rd', 'Ye', 'OR', 'Gr'),
    ('Wh', 'Bu', 'Ye', 'Gr', 'OR', 'Rd'),
    ('Wh', 'Bu', 'Ye', 'Gr', 'Rd', 'OR'),
    ('Wh', 'Bu', 'Ye', 'OR', 'Gr', 'Rd'),
    ('Wh', 'Bu', 'Ye', 'OR', 'Rd', 'Gr'),
    ('Wh', 'Bu', 'Ye', 'Rd', 'Gr', 'OR'),
    ('Wh', 'Bu', 'Ye', 'Rd', 'OR', 'Gr'),
    ('Wh', 'Gr', 'Bu', 'OR', 'Rd', 'Ye'),
    ('Wh', 'Gr', 'Bu', 'OR', 'Ye', 'Rd'),
    ('Wh', 'Gr', 'Bu', 'Rd', 'OR', 'Ye'),
    ('Wh', 'Gr', 'Bu', 'Rd', 'Ye', 'OR'),
    ('Wh', 'Gr', 'Bu', 'Ye', 'OR', 'Rd'),
    ('Wh', 'Gr', 'Bu', 'Ye', 'Rd', 'OR'),
    ('Wh', 'Gr', 'OR', 'Bu', 'Rd', 'Ye'),
    ('Wh', 'Gr', 'OR', 'Bu', 'Ye', 'Rd'),
    ('Wh', 'Gr', 'OR', 'Rd', 'Bu', 'Ye'),
    ('Wh', 'Gr', 'OR', 'Rd', 'Ye', 'Bu'),
    ('Wh', 'Gr', 'OR', 'Ye', 'Bu', 'Rd'),
    ('Wh', 'Gr', 'OR', 'Ye', 'Rd', 'Bu'),
    ('Wh', 'Gr', 'Rd', 'Bu', 'OR', 'Ye'),
    ('Wh', 'Gr', 'Rd', 'Bu', 'Ye', 'OR'),
    ('Wh', 'Gr', 'Rd', 'OR', 'Bu', 'Ye'),
    ('Wh', 'Gr', 'Rd', 'OR', 'Ye', 'Bu'),
    ('Wh', 'Gr', 'Rd', 'Ye', 'Bu', 'OR'),
    ('Wh', 'Gr', 'Rd', 'Ye', 'OR', 'Bu'),
    ('Wh', 'Gr', 'Ye', 'Bu', 'OR', 'Rd'),
    ('Wh', 'Gr', 'Ye', 'Bu', 'Rd', 'OR'),
    ('Wh', 'Gr', 'Ye', 'OR', 'Bu', 'Rd'),
    ('Wh', 'Gr', 'Ye', 'OR', 'Rd', 'Bu'),
    ('Wh', 'Gr', 'Ye', 'Rd', 'Bu', 'OR'),
    ('Wh', 'Gr', 'Ye', 'Rd', 'OR', 'Bu'),
    ('Wh', 'OR', 'Bu', 'Gr', 'Rd', 'Ye'),
    ('Wh', 'OR', 'Bu', 'Gr', 'Ye', 'Rd'),
    ('Wh', 'OR', 'Bu', 'Rd', 'Gr', 'Ye'),
    ('Wh', 'OR', 'Bu', 'Rd', 'Ye', 'Gr'),
    ('Wh', 'OR', 'Bu', 'Ye', 'Gr', 'Rd'),
    ('Wh', 'OR', 'Bu', 'Ye', 'Rd', 'Gr'),
    ('Wh', 'OR', 'Gr', 'Bu', 'Rd', 'Ye'),
    ('Wh', 'OR', 'Gr', 'Bu', 'Ye', 'Rd'),
    ('Wh', 'OR', 'Gr', 'Rd', 'Bu', 'Ye'),
    ('Wh', 'OR', 'Gr', 'Rd', 'Ye', 'Bu'),
    ('Wh', 'OR', 'Gr', 'Ye', 'Bu', 'Rd'),
    ('Wh', 'OR', 'Gr', 'Ye', 'Rd', 'Bu'),
    ('Wh', 'OR', 'Rd', 'Bu', 'Gr', 'Ye'),
    ('Wh', 'OR', 'Rd', 'Bu', 'Ye', 'Gr'),
    ('Wh', 'OR', 'Rd', 'Gr', 'Bu', 'Ye'),
    ('Wh', 'OR', 'Rd', 'Gr', 'Ye', 'Bu'),
    ('Wh', 'OR', 'Rd', 'Ye', 'Bu', 'Gr'),
    ('Wh', 'OR', 'Rd', 'Ye', 'Gr', 'Bu'),
    ('Wh', 'OR', 'Ye', 'Bu', 'Gr', 'Rd'),
    ('Wh', 'OR', 'Ye', 'Bu', 'Rd', 'Gr'),
    ('Wh', 'OR', 'Ye', 'Gr', 'Bu', 'Rd'),
    ('Wh', 'OR', 'Ye', 'Gr', 'Rd', 'Bu'),
    ('Wh', 'OR', 'Ye', 'Rd', 'Bu', 'Gr'),
    ('Wh', 'OR', 'Ye', 'Rd', 'Gr', 'Bu'),
    ('Wh', 'Rd', 'Bu', 'Gr', 'OR', 'Ye'),
    ('Wh', 'Rd', 'Bu', 'Gr', 'Ye', 'OR'),
    ('Wh', 'Rd', 'Bu', 'OR', 'Gr', 'Ye'),
    ('Wh', 'Rd', 'Bu', 'OR', 'Ye', 'Gr'),
    ('Wh', 'Rd', 'Bu', 'Ye', 'Gr', 'OR'),
    ('Wh', 'Rd', 'Bu', 'Ye', 'OR', 'Gr'),
    ('Wh', 'Rd', 'Gr', 'Bu', 'OR', 'Ye'),
    ('Wh', 'Rd', 'Gr', 'Bu', 'Ye', 'OR'),
    ('Wh', 'Rd', 'Gr', 'OR', 'Bu', 'Ye'),
    ('Wh', 'Rd', 'Gr', 'OR', 'Ye', 'Bu'),
    ('Wh', 'Rd', 'Gr', 'Ye', 'Bu', 'OR'),
    ('Wh', 'Rd', 'Gr', 'Ye', 'OR', 'Bu'),
    ('Wh', 'Rd', 'OR', 'Bu', 'Gr', 'Ye'),
    ('Wh', 'Rd', 'OR', 'Bu', 'Ye', 'Gr'),
    ('Wh', 'Rd', 'OR', 'Gr', 'Bu', 'Ye'),
    ('Wh', 'Rd', 'OR', 'Gr', 'Ye', 'Bu'),
    ('Wh', 'Rd', 'OR', 'Ye', 'Bu', 'Gr'),
    ('Wh', 'Rd', 'OR', 'Ye', 'Gr', 'Bu'),
    ('Wh', 'Rd', 'Ye', 'Bu', 'Gr', 'OR'),
    ('Wh', 'Rd', 'Ye', 'Bu', 'OR', 'Gr'),
    ('Wh', 'Rd', 'Ye', 'Gr', 'Bu', 'OR'),
    ('Wh', 'Rd', 'Ye', 'Gr', 'OR', 'Bu'),
    ('Wh', 'Rd', 'Ye', 'OR', 'Bu', 'Gr'),
    ('Wh', 'Rd', 'Ye', 'OR', 'Gr', 'Bu'),
    ('Wh', 'Ye', 'Bu', 'Gr', 'OR', 'Rd'),
    ('Wh', 'Ye', 'Bu', 'Gr', 'Rd', 'OR'),
    ('Wh', 'Ye', 'Bu', 'OR', 'Gr', 'Rd'),
    ('Wh', 'Ye', 'Bu', 'OR', 'Rd', 'Gr'),
    ('Wh', 'Ye', 'Bu', 'Rd', 'Gr', 'OR'),
    ('Wh', 'Ye', 'Bu', 'Rd', 'OR', 'Gr'),
    ('Wh', 'Ye', 'Gr', 'Bu', 'OR', 'Rd'),
    ('Wh', 'Ye', 'Gr', 'Bu', 'Rd', 'OR'),
    ('Wh', 'Ye', 'Gr', 'OR', 'Bu', 'Rd'),
    ('Wh', 'Ye', 'Gr', 'OR', 'Rd', 'Bu'),
    ('Wh', 'Ye', 'Gr', 'Rd', 'Bu', 'OR'),
    ('Wh', 'Ye', 'Gr', 'Rd', 'OR', 'Bu'),
    ('Wh', 'Ye', 'OR', 'Bu', 'Gr', 'Rd'),
    ('Wh', 'Ye', 'OR', 'Bu', 'Rd', 'Gr'),
    ('Wh', 'Ye', 'OR', 'Gr', 'Bu', 'Rd'),
    ('Wh', 'Ye', 'OR', 'Gr', 'Rd', 'Bu'),
    ('Wh', 'Ye', 'OR', 'Rd', 'Bu', 'Gr'),
    ('Wh', 'Ye', 'OR', 'Rd', 'Gr', 'Bu'),
    ('Wh', 'Ye', 'Rd', 'Bu', 'Gr', 'OR'),
    ('Wh', 'Ye', 'Rd', 'Bu', 'OR', 'Gr'),
    ('Wh', 'Ye', 'Rd', 'Gr', 'Bu', 'OR'),
    ('Wh', 'Ye', 'Rd', 'Gr', 'OR', 'Bu'),
    ('Wh', 'Ye', 'Rd', 'OR', 'Bu', 'Gr'),
    ('Wh', 'Ye', 'Rd', 'OR', 'Gr', 'Bu'),
    ('Ye', 'Bu', 'Gr', 'OR', 'Rd', 'Wh'),
    ('Ye', 'Bu', 'Gr', 'OR', 'Wh', 'Rd'),
    ('Ye', 'Bu', 'Gr', 'Rd', 'OR', 'Wh'),
    ('Ye', 'Bu', 'Gr', 'Rd', 'Wh', 'OR'),
    ('Ye', 'Bu', 'Gr', 'Wh', 'OR', 'Rd'),
    ('Ye', 'Bu', 'Gr', 'Wh', 'Rd', 'OR'),
    ('Ye', 'Bu', 'OR', 'Gr', 'Rd', 'Wh'),
    ('Ye', 'Bu', 'OR', 'Gr', 'Wh', 'Rd'),
    ('Ye', 'Bu', 'OR', 'Rd', 'Gr', 'Wh'),
    ('Ye', 'Bu', 'OR', 'Rd', 'Wh', 'Gr'),
    ('Ye', 'Bu', 'OR', 'Wh', 'Gr', 'Rd'),
    ('Ye', 'Bu', 'OR', 'Wh', 'Rd', 'Gr'),
    ('Ye', 'Bu', 'Rd', 'Gr', 'OR', 'Wh'),
    ('Ye', 'Bu', 'Rd', 'Gr', 'Wh', 'OR'),
    ('Ye', 'Bu', 'Rd', 'OR', 'Gr', 'Wh'),
    ('Ye', 'Bu', 'Rd', 'OR', 'Wh', 'Gr'),
    ('Ye', 'Bu', 'Rd', 'Wh', 'Gr', 'OR'),
    ('Ye', 'Bu', 'Rd', 'Wh', 'OR', 'Gr'),
    ('Ye', 'Bu', 'Wh', 'Gr', 'OR', 'Rd'),
    ('Ye', 'Bu', 'Wh', 'Gr', 'Rd', 'OR'),
    ('Ye', 'Bu', 'Wh', 'OR', 'Gr', 'Rd'),
    ('Ye', 'Bu', 'Wh', 'OR', 'Rd', 'Gr'),
    ('Ye', 'Bu', 'Wh', 'Rd', 'Gr', 'OR'),
    ('Ye', 'Bu', 'Wh', 'Rd', 'OR', 'Gr'),
    ('Ye', 'Gr', 'Bu', 'OR', 'Rd', 'Wh'),
    ('Ye', 'Gr', 'Bu', 'OR', 'Wh', 'Rd'),
    ('Ye', 'Gr', 'Bu', 'Rd', 'OR', 'Wh'),
    ('Ye', 'Gr', 'Bu', 'Rd', 'Wh', 'OR'),
    ('Ye', 'Gr', 'Bu', 'Wh', 'OR', 'Rd'),
    ('Ye', 'Gr', 'Bu', 'Wh', 'Rd', 'OR'),
    ('Ye', 'Gr', 'OR', 'Bu', 'Rd', 'Wh'),
    ('Ye', 'Gr', 'OR', 'Bu', 'Wh', 'Rd'),
    ('Ye', 'Gr', 'OR', 'Rd', 'Bu', 'Wh'),
    ('Ye', 'Gr', 'OR', 'Rd', 'Wh', 'Bu'),
    ('Ye', 'Gr', 'OR', 'Wh', 'Bu', 'Rd'),
    ('Ye', 'Gr', 'OR', 'Wh', 'Rd', 'Bu'),
    ('Ye', 'Gr', 'Rd', 'Bu', 'OR', 'Wh'),
    ('Ye', 'Gr', 'Rd', 'Bu', 'Wh', 'OR'),
    ('Ye', 'Gr', 'Rd', 'OR', 'Bu', 'Wh'),
    ('Ye', 'Gr', 'Rd', 'OR', 'Wh', 'Bu'),
    ('Ye', 'Gr', 'Rd', 'Wh', 'Bu', 'OR'),
    ('Ye', 'Gr', 'Rd', 'Wh', 'OR', 'Bu'),
    ('Ye', 'Gr', 'Wh', 'Bu', 'OR', 'Rd'),
    ('Ye', 'Gr', 'Wh', 'Bu', 'Rd', 'OR'),
    ('Ye', 'Gr', 'Wh', 'OR', 'Bu', 'Rd'),
    ('Ye', 'Gr', 'Wh', 'OR', 'Rd', 'Bu'),
    ('Ye', 'Gr', 'Wh', 'Rd', 'Bu', 'OR'),
    ('Ye', 'Gr', 'Wh', 'Rd', 'OR', 'Bu'),
    ('Ye', 'OR', 'Bu', 'Gr', 'Rd', 'Wh'),
    ('Ye', 'OR', 'Bu', 'Gr', 'Wh', 'Rd'),
    ('Ye', 'OR', 'Bu', 'Rd', 'Gr', 'Wh'),
    ('Ye', 'OR', 'Bu', 'Rd', 'Wh', 'Gr'),
    ('Ye', 'OR', 'Bu', 'Wh', 'Gr', 'Rd'),
    ('Ye', 'OR', 'Bu', 'Wh', 'Rd', 'Gr'),
    ('Ye', 'OR', 'Gr', 'Bu', 'Rd', 'Wh'),
    ('Ye', 'OR', 'Gr', 'Bu', 'Wh', 'Rd'),
    ('Ye', 'OR', 'Gr', 'Rd', 'Bu', 'Wh'),
    ('Ye', 'OR', 'Gr', 'Rd', 'Wh', 'Bu'),
    ('Ye', 'OR', 'Gr', 'Wh', 'Bu', 'Rd'),
    ('Ye', 'OR', 'Gr', 'Wh', 'Rd', 'Bu'),
    ('Ye', 'OR', 'Rd', 'Bu', 'Gr', 'Wh'),
    ('Ye', 'OR', 'Rd', 'Bu', 'Wh', 'Gr'),
    ('Ye', 'OR', 'Rd', 'Gr', 'Bu', 'Wh'),
    ('Ye', 'OR', 'Rd', 'Gr', 'Wh', 'Bu'),
    ('Ye', 'OR', 'Rd', 'Wh', 'Bu', 'Gr'),
    ('Ye', 'OR', 'Rd', 'Wh', 'Gr', 'Bu'),
    ('Ye', 'OR', 'Wh', 'Bu', 'Gr', 'Rd'),
    ('Ye', 'OR', 'Wh', 'Bu', 'Rd', 'Gr'),
    ('Ye', 'OR', 'Wh', 'Gr', 'Bu', 'Rd'),
    ('Ye', 'OR', 'Wh', 'Gr', 'Rd', 'Bu'),
    ('Ye', 'OR', 'Wh', 'Rd', 'Bu', 'Gr'),
    ('Ye', 'OR', 'Wh', 'Rd', 'Gr', 'Bu'),
    ('Ye', 'Rd', 'Bu', 'Gr', 'OR', 'Wh'),
    ('Ye', 'Rd', 'Bu', 'Gr', 'Wh', 'OR'),
    ('Ye', 'Rd', 'Bu', 'OR', 'Gr', 'Wh'),
    ('Ye', 'Rd', 'Bu', 'OR', 'Wh', 'Gr'),
    ('Ye', 'Rd', 'Bu', 'Wh', 'Gr', 'OR'),
    ('Ye', 'Rd', 'Bu', 'Wh', 'OR', 'Gr'),
    ('Ye', 'Rd', 'Gr', 'Bu', 'OR', 'Wh'),
    ('Ye', 'Rd', 'Gr', 'Bu', 'Wh', 'OR'),
    ('Ye', 'Rd', 'Gr', 'OR', 'Bu', 'Wh'),
    ('Ye', 'Rd', 'Gr', 'OR', 'Wh', 'Bu'),
    ('Ye', 'Rd', 'Gr', 'Wh', 'Bu', 'OR'),
    ('Ye', 'Rd', 'Gr', 'Wh', 'OR', 'Bu'),
    ('Ye', 'Rd', 'OR', 'Bu', 'Gr', 'Wh'),
    ('Ye', 'Rd', 'OR', 'Bu', 'Wh', 'Gr'),
    ('Ye', 'Rd', 'OR', 'Gr', 'Bu', 'Wh'),
    ('Ye', 'Rd', 'OR', 'Gr', 'Wh', 'Bu'),
    ('Ye', 'Rd', 'OR', 'Wh', 'Bu', 'Gr'),
    ('Ye', 'Rd', 'OR', 'Wh', 'Gr', 'Bu'),
    ('Ye', 'Rd', 'Wh', 'Bu', 'Gr', 'OR'),
    ('Ye', 'Rd', 'Wh', 'Bu', 'OR', 'Gr'),
    ('Ye', 'Rd', 'Wh', 'Gr', 'Bu', 'OR'),
    ('Ye', 'Rd', 'Wh', 'Gr', 'OR', 'Bu'),
    ('Ye', 'Rd', 'Wh', 'OR', 'Bu', 'Gr'),
    ('Ye', 'Rd', 'Wh', 'OR', 'Gr', 'Bu'),
    ('Ye', 'Wh', 'Bu', 'Gr', 'OR', 'Rd'),
    ('Ye', 'Wh', 'Bu', 'Gr', 'Rd', 'OR'),
    ('Ye', 'Wh', 'Bu', 'OR', 'Gr', 'Rd'),
    ('Ye', 'Wh', 'Bu', 'OR', 'Rd', 'Gr'),
    ('Ye', 'Wh', 'Bu', 'Rd', 'Gr', 'OR'),
    ('Ye', 'Wh', 'Bu', 'Rd', 'OR', 'Gr'),
    ('Ye', 'Wh', 'Gr', 'Bu', 'OR', 'Rd'),
    ('Ye', 'Wh', 'Gr', 'Bu', 'Rd', 'OR'),
    ('Ye', 'Wh', 'Gr', 'OR', 'Bu', 'Rd'),
    ('Ye', 'Wh', 'Gr', 'OR', 'Rd', 'Bu'),
    ('Ye', 'Wh', 'Gr', 'Rd', 'Bu', 'OR'),
    ('Ye', 'Wh', 'Gr', 'Rd', 'OR', 'Bu'),
    ('Ye', 'Wh', 'OR', 'Bu', 'Gr', 'Rd'),
    ('Ye', 'Wh', 'OR', 'Bu', 'Rd', 'Gr'),
    ('Ye', 'Wh', 'OR', 'Gr', 'Bu', 'Rd'),
    ('Ye', 'Wh', 'OR', 'Gr', 'Rd', 'Bu'),
    ('Ye', 'Wh', 'OR', 'Rd', 'Bu', 'Gr'),
    ('Ye', 'Wh', 'OR', 'Rd', 'Gr', 'Bu'),
    ('Ye', 'Wh', 'Rd', 'Bu', 'Gr', 'OR'),
    ('Ye', 'Wh', 'Rd', 'Bu', 'OR', 'Gr'),
    ('Ye', 'Wh', 'Rd', 'Gr', 'Bu', 'OR'),
    ('Ye', 'Wh', 'Rd', 'Gr', 'OR', 'Bu'),
    ('Ye', 'Wh', 'Rd', 'OR', 'Bu', 'Gr'),
    ('Ye', 'Wh', 'Rd', 'OR', 'Gr', 'Bu'),
]


edge_color_pair_map = {

    # Up (white)
    "Gr/Wh" : "Gr/Wh",
    "Wh/Gr" : "Gr/Wh",

    "Bu/Wh" : "Bu/Wh",
    "Wh/Bu" : "Bu/Wh",

    "OR/Wh" : "OR/Wh",
    "Wh/OR" : "OR/Wh",

    "Rd/Wh" : "Rd/Wh",
    "Wh/Rd" : "Rd/Wh",

    # Left (orange)
    "Gr/OR" : "Gr/OR",
    "OR/Gr" : "Gr/OR",

    "Bu/OR" : "Bu/OR",
    "OR/Bu" : "Bu/OR",

    # Right (red)
    "Gr/Rd" : "Gr/Rd",
    "Rd/Gr" : "Gr/Rd",

    "Bu/Rd" : "Bu/Rd",
    "Rd/Bu" : "Bu/Rd",

    # Down (yellow)
    "Gr/Ye" : "Gr/Ye",
    "Ye/Gr" : "Gr/Ye",

    "Bu/Ye" : "Bu/Ye",
    "Ye/Bu" : "Bu/Ye",

    "OR/Ye" : "OR/Ye",
    "Ye/OR" : "OR/Ye",

    "Rd/Ye" : "Rd/Ye",
    "Ye/Rd" : "Rd/Ye",
}

corner_tuples = {
    2 : (
        (1, 5, 18),
        (2, 17, 14),
        (3, 9, 6),
        (4, 13, 10),
        (21, 8, 11),
        (22, 12, 15),
        (23, 20, 7),
        (24, 16, 19),
    ),
    3 : (
        (1, 10, 39),
        (3, 37, 30),
        (7, 19, 12),
        (9, 28, 21),
        (46, 18, 25),
        (48, 27, 34),
        (52, 45, 16),
        (54, 36, 43),
    ),
    4 : (
        (1, 17, 68),
        (4, 65, 52),
        (13, 33, 20),
        (16, 49, 36),
        (81, 32, 45),
        (84, 48, 61),
        (93, 80, 29),
        (96, 64, 77),
    ),
    5 : (
        (1, 26, 105),
        (5, 101, 80),
        (21, 51, 30),
        (25, 76, 55),
        (126, 50, 71),
        (130, 75, 96),
        (146, 125, 46),
        (150, 100, 121),
    ),
    6 : (
        (1, 37, 150),
        (6, 145, 114),
        (31, 73, 42),
        (36, 109, 78),
        (181, 72, 103),
        (186, 108, 139),
        (211, 180, 67),
        (216, 144, 175 ),
    ),
    7 : (
        (1, 50, 203),
        (7, 197, 154),
        (43, 99, 56),
        (49, 148, 105),
        (246, 98, 141),
        (252, 147, 190),
        (288, 245, 92),
        (294, 196, 239),
    ),
}

edge_orbit_id = {
    3: {
        2: 0, 4: 0, 6: 0, 8: 0, # Upper
        11: 0, 13: 0, 15: 0, 17: 0, # Left
        20: 0, 22: 0, 24: 0, 26: 0, # Front
        29: 0, 31: 0, 33: 0, 35: 0, # Right
        38: 0, 40: 0, 42: 0, 44: 0, # Back
        47: 0, 49: 0, 51: 0, 53: 0, # Down
    },
    4: {
        2: 0, 3: 0, 5: 0, 9: 0, 8: 0, 12: 0, 14: 0, 15: 0, # Upper
        18: 0, 19: 0, 21: 0, 25: 0, 24: 0, 28: 0, 30: 0, 31: 0, # Left
        34: 0, 35: 0, 37: 0, 41: 0, 40: 0, 44: 0, 46: 0, 47: 0, # Front
        50: 0, 51: 0, 53: 0, 57: 0, 56: 0, 60: 0, 62: 0, 63: 0, # Right
        66: 0, 67: 0, 69: 0, 73: 0, 72: 0, 76: 0, 78: 0, 79: 0, # Back
        82: 0, 83: 0, 85: 0, 89: 0, 88: 0, 92: 0, 94: 0, 95: 0, # Down
    },
    5: {
        2: 0, 3: 1, 4: 0, 6: 0, 11: 1, 16: 0, 10: 0, 15: 1, 20: 0, 22: 0, 23: 1, 24: 0, # Upper
        27: 0, 28: 1, 29: 0, 31: 0, 36: 1, 41: 0, 35: 0, 40: 1, 45: 0, 47: 0, 48: 1, 49: 0, # Left
        52: 0, 53: 1, 54: 0, 56: 0, 61: 1, 66: 0, 60: 0, 65: 1, 70: 0, 72: 0, 73: 1, 74: 0, # Front
        77: 0, 78: 1, 79: 0, 81: 0, 86: 1, 91: 0, 85: 0, 90: 1, 95: 0, 97: 0, 98: 1, 99: 0, # Right
        102: 0, 103: 1, 104: 0, 106: 0, 111: 1, 116: 0, 110: 0, 115: 1, 120: 0, 122: 0, 123: 1, 124: 0, # Back
        127: 0, 128: 1, 129: 0, 131: 0, 136: 1, 141: 0, 135: 0, 140: 1, 145: 0, 147: 0, 148: 1, 149: 0, # Down
    },
    6: {
        # orbit 0
        2: 0, 5: 0, 7: 0, 25: 0, 12: 0, 30: 0, 32: 0, 35: 0, # Upper
        38: 0, 41: 0, 43: 0, 61: 0, 48: 0, 66: 0, 68: 0, 71: 0, # Left
        74: 0, 77: 0, 79: 0, 97: 0, 84: 0, 102: 0, 104: 0, 107: 0, # Front
        110: 0, 113: 0, 115: 0, 133: 0, 120: 0, 138: 0, 140: 0, 143: 0, # Right
        146: 0, 149: 0, 151: 0, 169: 0, 156: 0, 174: 0, 176: 0, 179: 0, # Back
        182: 0, 185: 0, 187: 0, 205: 0, 192: 0, 210: 0, 212: 0, 215: 0, # Down

        # orbit 1
        3: 1, 4: 1, 13: 1, 19: 1, 18: 1, 24: 1, 33: 1, 34: 1, # Upper
        39: 1, 40: 1, 49: 1, 55: 1, 54: 1, 60: 1, 69: 1, 70: 1, # Left
        75: 1, 76: 1, 85: 1, 91: 1, 90: 1, 96: 1, 105: 1, 106: 1, # Front
        111: 1, 112: 1, 121: 1, 127: 1, 126: 1, 132: 1, 141: 1, 142: 1, # Right
        147: 1, 148: 1, 157: 1, 163: 1, 162: 1, 168: 1, 177: 1, 178: 1, # Back
        183: 1, 184: 1, 193: 1, 199: 1, 198: 1, 204: 1, 213: 1, 214: 1, # Down
    },
    7: {
        # orbit 0
        2: 0, 6: 0, 8: 0, 14: 0, 36: 0, 42: 0, 44: 0, 48: 0, # Upper
        51: 0, 55: 0, 57: 0, 63: 0, 85: 0, 91: 0, 93: 0, 97: 0, # Left
        100: 0, 104: 0, 106: 0, 112: 0, 134: 0, 140: 0, 142: 0, 146: 0, # Front
        149: 0, 153: 0, 155: 0, 161: 0, 183: 0, 189: 0, 191: 0, 195: 0, # Right
        198: 0, 202: 0, 204: 0, 210: 0, 232: 0, 238: 0, 240: 0, 244: 0, # Back
        247: 0, 251: 0, 253: 0, 259: 0, 281: 0, 287: 0, 289: 0, 293: 0, # Down

        # orbit 1
        3: 1, 5: 1, 15: 1, 21: 1, 29: 1, 35: 1, 45: 1, 47: 1, # Upper
        52: 1, 54: 1, 64: 1, 70: 1, 78: 1, 84: 1, 94: 1, 96: 1, # Left
        101: 1, 103: 1, 113: 1, 119: 1, 127: 1, 133: 1, 143: 1, 145: 1, # Front
        150: 1, 152: 1, 162: 1, 168: 1, 176: 1, 182: 1, 192: 1, 194: 1, # Right
        199: 1, 201: 1, 211: 1, 217: 1, 225: 1, 231: 1, 241: 1, 243: 1, # Back
        248: 1, 250: 1, 260: 1, 266: 1, 274: 1, 280: 1, 290: 1, 292: 1, # Down

        # orbit 2
        4: 2, 22: 2, 28: 2, 46: 2, # Upper
        53: 2, 71: 2, 77: 2, 95: 2, # Left
        102: 2, 120: 2, 126: 2, 144: 2, # Front
        151: 2, 169: 2, 175: 2, 193: 2, # Right
        200: 2, 218: 2, 224: 2, 242: 2, # Back
        249: 2, 267: 2, 273: 2, 291: 2, # Down
    }
}

edge_orbit_wing_pairs = {
    2 : (()),
    3 : (
        # orbit 0
        ((2, 38), (4, 11), (6, 29), (8, 20),
         (13, 42), (15, 22),
         (31, 24), (33, 40),
         (47, 26), (49, 17), (51, 35), (53, 44)
        ),
    ),

    4 : (
        # orbit 0
        ((2, 67), (3, 66), (5, 18), (9, 19), (8, 51), (12, 50), (14, 34), (15, 35),
         (21, 72), (25, 76), (24, 37), (28, 41),
         (53, 40), (57, 44), (56, 69), (60, 73),
         (82, 46), (83, 47), (85, 31), (89, 30), (88, 62), (92, 63), (94, 79), (95, 78)
        ),
    ),

    5 : (
        # orbit 0
        ((2, 104), (4, 102), (6, 27), (16, 29), (10, 79), (20, 77), (22, 52), (24, 54),
         (31, 110), (41, 120), (35, 56), (45, 66),
         (81, 60), (91, 70), (85, 106), (95, 116),
         (72, 127), (74, 129), (131, 49), (141, 47), (135, 97), (145, 99), (147, 124), (149, 122)
        ),

        # orbit 1
        ((3, 103), (11, 28), (15, 78), (23, 53),
         (36, 115), (40, 61),
         (86, 65), (90, 111),
         (128, 73), (136, 48), (140, 98), (148, 123)
        ),
    ),

    6 : (
        # orbit 0
        ((2, 149), (5, 146), (7, 38), (25, 41), (12, 113), (30, 110), (32, 74), (35, 77),
         (43, 156), (61, 174), (48, 79), (66, 97),
         (115, 84), (133, 102), (120, 151), (138, 169),
         (182, 104), (185, 107), (187, 71), (205, 68), (192, 140), (210, 143), (212, 179), (215, 176),
        ),

        # orbit 1
        ((3, 148), (4, 147), (13, 39), (19, 40), (18, 112), (24, 111), (33, 75), (34, 76),
         (49, 162), (55, 168), (54, 85), (60, 91),
         (90, 121), (96, 127), (126, 157), (132, 163),
         (183, 105), (184, 106), (193, 70), (199, 69), (198, 141), (204, 142), (213, 178), (214, 177),
        ),
    ),

    7 : (
        # orbit 0
        ((2, 202), (6, 198), (14, 153), (42, 149), (48, 104), (44, 100), (36, 55), (8, 51),  # Upper
         (63, 106), (91, 134), (85, 238), (57, 210), # Left
         (161, 204), (189, 232), (183, 140), (155, 112), # Right
         (247, 142), (251, 146), (259, 191), (287, 195), (293, 240), (289, 244), (281, 93), (253, 97), # Down
        ),

        # orbit 1
        ((3, 201), (5, 199), (21, 152), (35, 150), (47, 103), (45, 101), (29, 54), (15, 52), # Upper
         (70, 113), (84, 127), (78, 231), (64, 217), # Left
         (168, 211), (182, 225), (176, 133), (162, 119), # Right
         (248, 143), (250, 145), (266, 192), (280, 194), (292, 241), (290, 243), (274, 94), (260, 96), # Down
        ),

        # orbit 2
        ((4, 200), (28, 151), (46, 102), (22, 53), # Upper
         (77, 120), (71, 224), # Left
         (175, 218), (169, 126), # Right
         (249, 144), (273, 193), (291, 242), (267, 95), # Down
        ),
    ),
}

center_groups = {
    2: (),
    3: (
        ("centers", (5, 14, 23, 32, 41, 50)),
    ),
    4: (
        ("x-centers", (
            6, 7, 10, 11, # Upper
            22, 23, 26, 27, # Left
            38, 39, 42, 43, # Front
            54, 55, 58, 59, # Right
            70, 71, 74, 75, # Back
            86, 87, 90, 91, # Down
        )),
    ),
    5: (
        ("centers", (13, 38, 63, 88, 113, 138)),
        ("x-centers", (
            7, 9, 13, 17, 19, # Upper
            32, 34, 38, 42, 44, # Left
            57, 59, 63, 67, 69, # Front
            82, 84, 88, 92, 94, # Right
            107, 109, 113, 117, 119, # Back
            132, 134, 138, 142, 144, # Down
        )),
        ("t-centers", (
            8, 12, 13, 14, 18, # Upper
            33, 37, 38, 39, 43, # Left
            58, 62, 63, 64, 68, # Front
            83, 87, 88, 89, 93, # Right
            108, 112, 113, 114, 118, # Back
            133, 137, 138, 139, 143, # Down
        )),
    ),
    6: (
        ("inner x-centers", (
            15, 16, 21, 22, # Upper
            51, 52, 57, 58, # Left
            87, 88, 93, 94, # Front
            123, 124, 129, 130, # Right
            159, 160, 165, 166, # Back
            195, 196, 201, 202, # Down
        )),
        ("outer x-centers", (
            8, 11, 26, 29, # Upper
            44, 47, 62, 65, # Left
            80, 83, 98, 101, # Front
            116, 119, 134, 137, # Right
            152, 155, 170, 173, # Back
            188, 191, 206, 209, # Down
        )),
        ("left centers (oblique edge)", (
            9, 17, 28, 20, # Upper
            45, 53, 64, 56, # Left
            81, 89, 100, 92, # Front
            117, 125, 136, 128, # Right
            153, 161, 172, 164, # Back
            189, 197, 208, 200, # Down
        )),
        ("right centers (oblique edges)", (
            10, 23, 27, 14, # Upper
            46, 59, 63, 50, # Left
            82, 95, 99, 86, # Front
            118, 131, 135, 122, # Right
            154, 167, 171, 158, # Back
            190, 203, 207, 194, # Down
        )),
    ),
    7: (
        ("centers", (25, 74, 123, 172, 221, 270)),
        ("inside-x-centers", (
            17, 19, 31, 33, # Upper
            66, 68, 80, 82, # Left
            115, 117, 129, 131, # Front
            164, 166, 178, 180, # Right
            213, 215, 227, 229, # Back
            262, 264, 276, 278, # Down
        )),
        ("inside-t-centers", (
            18, 24, 26, 32, # Upper
            67, 73, 75, 81, # Left
            116, 122, 124, 130, # Front
            165, 171, 173, 179, # Right
            214, 220, 222, 228, # Back
            263, 269, 271, 277, # Down
        )),
        ("outside-x-centers", (
            9, 13, 37, 41, # Upper
            58, 62, 86, 90, # Left
            107, 111, 135, 139, # Front
            156, 160, 184, 188, # Right
            205, 209, 233, 237, # Back
            254, 258, 282, 286, # Down
        )),
        ("outside-t-centers", (
            11, 23, 27, 39, # Upper
            60, 72, 76, 88, # Left
            109, 121, 125, 137, # Front
            158, 170, 174, 186, # Right
            207, 219, 223, 235, # Back
            256, 268, 272, 284, # Down
        )),
        ("left-oblique", (
            10, 20, 40, 30, # Upper
            59, 69, 89, 79, # Left
            108, 118, 138, 128, # Front
            157, 167, 187, 177, # Right
            206, 216, 236, 226, # Back
            255, 265, 285, 275, # Down
        )),
        ("right-oblique", (
            12, 34, 38, 16, # Upper
            61, 83, 87, 65, # Left
            110, 132, 136, 114, # Front
            159, 181, 185, 163, # Right
            208, 230, 234, 212, # Back
            257, 279, 283, 261, # Down
        )),
    )
}


SIDES_COUNT = 6
HTML_DIRECTORY = '/tmp/rubiks-color-resolver/'
HTML_FILENAME = HTML_DIRECTORY + 'index.html'


class ListMissingValue(Exception):
    pass


def median(l):
    l = sorted(l)
    l_len = len(l)

    if l_len < 1:
        return None

    # Even number of entries
    if l_len % 2 == 0 :
        return (l[int((l_len-1)/2)] + l[int((l_len+1)/2)]) / 2.0

    # Odd number of entries
    else:
        return l[(l_len-1)/2]


def get_euclidean_lab_distance(lab1, lab2):
    """
    http://www.w3resource.com/python-exercises/math/python-math-exercise-79.php

    In mathematics, the Euclidean distance or Euclidean metric is the "ordinary"
    (i.e. straight-line) distance between two points in Euclidean space. With this
    distance, Euclidean space becomes a metric space. The associated norm is called
    the Euclidean norm.
    """
    return sqrt(((lab1.L - lab2.L) ** 2) + ((lab1.a - lab2.a) ** 2) + ((lab1.b - lab2.b) ** 2))


def delta_e_cie2000(lab1, lab2):
    """
    Ported from this php implementation
    https://github.com/renasboy/php-color-difference/blob/master/lib/color_difference.class.php
    """
    l1 = lab1.L
    a1 = lab1.a
    b1 = lab1.b

    l2 = lab2.L
    a2 = lab2.a
    b2 = lab2.b

    if use_cie2000_cache:
        delta_e = cie2000_cache.get((l1, a1, b1, l2, a2, b2))

        if delta_e is not None:
            return delta_e

        delta_e = cie2000_cache.get((l2, a2, b2, l1, a1, b1))

        if delta_e is not None:
            return delta_e

    avg_lp = (l1 + l2) / 2.0
    c1 = sqrt(a1**2 + b1**2)
    c2 = sqrt(a2**2 + b2**2)
    avg_c = (c1 + c2) / 2.0
    g = (1 - sqrt(avg_c**7 / (avg_c**7 + 25**7))) / 2.0
    a1p = a1 * (1 + g)
    a2p = a2 * (1 + g)
    c1p = sqrt(a1p**2 + b1**2)
    c2p = sqrt(a2p**2 + b2**2)
    avg_cp = (c1p + c2p) / 2.0
    h1p = degrees(atan2(b1, a1p))

    if h1p < 0:
        h1p += 360

    h2p = degrees(atan2(b2, a2p))

    if h2p < 0:
        h2p += 360

    if abs(h1p - h2p) > 180:
        avg_hp = (h1p + h2p + 360) / 2.0
    else:
        avg_hp = (h1p + h2p) / 2.0

    t = (1 - 0.17 * cos(radians(avg_hp - 30)) +
         0.24 * cos(radians(2 * avg_hp)) +
         0.32 * cos(radians(3 * avg_hp + 6)) - 0.2 * cos(radians(4 * avg_hp - 63)))
    delta_hp = h2p - h1p

    if abs(delta_hp) > 180:
        if h2p <= h1p:
            delta_hp += 360
        else:
            delta_hp -= 360

    delta_lp = l2 - l1
    delta_cp = c2p - c1p
    delta_hp = 2 * sqrt(c1p * c2p) * sin(radians(delta_hp) / 2.0)
    s_l = 1 + ((0.015 * ((avg_lp - 50) ** 2)) / sqrt(20 + ((avg_lp - 50) ** 2)))
    s_c = 1 + 0.045 * avg_cp
    s_h = 1 + 0.015 * avg_cp * t

    delta_ro = 30 * exp(-((((avg_hp - 275) / 25.0) ** 2)))

    r_c = 2 * sqrt((avg_cp**7) / ((avg_cp ** 7) + (25 ** 7)))
    r_t = -r_c * sin(2 * radians(delta_ro))
    kl = 1.0
    kc = 1.0
    kh = 1.0
    delta_e = sqrt(((delta_lp / (s_l * kl)) ** 2) +
                   ((delta_cp / (s_c * kc)) ** 2) +
                   ((delta_hp / (s_h * kh)) ** 2) +
                   r_t * (delta_cp / (s_c * kc)) * (delta_hp / (s_h * kh)))

    if use_cie2000_cache:
        cie2000_cache[(l1, a1, b1, l2, a2, b2)] = delta_e
        cie2000_cache[(l2, a2, b2, l1, a1, b1)] = delta_e

    return delta_e


def get_lab_distance(lab1, lab2):

    if LAB_DISTANCE_ALGORITHM == 'cie2000':
        distance = delta_e_cie2000(lab1, lab2)

    elif LAB_DISTANCE_ALGORITHM == 'euclidean':
        distance = get_euclidean_lab_distance(lab1, lab2)

    elif LAB_DISTANCE_ALGORITHM == 'both':
        distance = delta_e_cie2000(lab1, lab2)
        distance += get_euclidean_lab_distance(lab1, lab2)

    else:
        raise Exception("Invalid LAB_DISTANCE_ALGORITHM %s" % LAB_DISTANCE_ALGORITHM)

    return distance


def find_index_for_value(list_foo, target, min_index):
    for (index, value) in enumerate(list_foo):
        if value == target and index >= min_index:
            return index
    raise ListMissingValue("Did not find %s in list %s".format(target, list_foo))


def get_swap_count(listA, listB, debug):
    """
    How many swaps do we have to make in listB for it to match listA
    Example:

        A = [1, 2, 3, 0, 4]
        B = [3, 4, 1, 0, 2]

    would require 2 swaps
    """
    A_length = len(listA)
    B_length = len(listB)
    swaps = 0
    index = 0

    if A_length != B_length:
        log.info("listA %s" % ' '.join(listA))
        log.info("listB %s" % ' '.join(listB))
        assert False, "listA (len %d) and listB (len %d) must be the same length" % (A_length, B_length)

    if debug:
        log.info("INIT")
        log.info("listA: %s" % ' '.join(listA))
        log.info("listB: %s" % ' '.join(listB))
        log.info("")

    while listA != listB:
        if listA[index] != listB[index]:
            listA_value = listA[index]
            listB_index_with_A_value = find_index_for_value(listB, listA_value, index+1)
            tmp = listB[index]
            listB[index] = listB[listB_index_with_A_value]
            listB[listB_index_with_A_value] = tmp
            swaps += 1

            if debug:
                log.info("index %d, swaps %d" % (index, swaps))
                log.info("listA: %s" % ' '.join(listA))
                log.info("listB: %s" % ' '.join(listB))
                log.info("")
        index += 1

    if debug:
        log.info("swaps: %d" % swaps)
        log.info("")
    return swaps


def traveling_salesman(squares, alg):

    # build a full matrix of color to color distances
    len_squares = len(squares)
    matrix = [[0 for i in range(len_squares)] for j in range(len_squares)]

    for x in range(len_squares):
        x_square = squares[x]
        (x_red, x_green, x_blue) = x_square.rgb
        #x_lab = rgb2lab((x_red, x_green, x_blue))
        x_lab = x_square.lab

        for y in range(len_squares):

            if x == y:
                matrix[x][y] = 0
                matrix[y][x] = 0
                continue

            if matrix[x][y] or matrix[y][x]:
                continue

            y_square = squares[y]
            (y_red, y_green, y_blue) = y_square.rgb
            #y_lab = rgb2lab((y_red, y_green, y_blue))
            y_lab = y_square.lab

            if alg == "cie2000":
                distance_xy = delta_e_cie2000(x_lab, y_lab)
                distance_yx = delta_e_cie2000(y_lab, x_lab)
                distance = max(distance_xy, distance_yx)

            elif alg == "euclidean":
                distance = get_euclidean_lab_distance(x_lab, y_lab)

            elif alg == "both":
                distance_xy = delta_e_cie2000(x_lab, y_lab)
                distance_yx = delta_e_cie2000(y_lab, x_lab)
                distance = max(distance_xy, distance_yx)
                distance += get_euclidean_lab_distance(x_lab, y_lab)

            else:
                raise Exception("Implement algorithm %s" % alg)

            matrix[x][y] = distance
            matrix[y][x] = distance

    global cie2000_cache
    #log.info("cache has %d entries" % len(list(cie2000_cache.keys())))
    cie2000_cache = {}
    gc.collect()
    path = solve_tsp(matrix)
    return [squares[x] for x in path]


def get_important_square_indexes(size):
    squares_per_side = size * size
    min_square = 1
    max_square = squares_per_side * 6
    first_squares = []
    last_squares = []

    for index in range(1, max_square + 1):
        if (index - 1) % squares_per_side == 0:
            first_squares.append(index)
        elif index % squares_per_side == 0:
            last_squares.append(index)

    last_UBD_squares = (last_squares[0], last_squares[4], last_squares[5])
    #log.info("first    squares: %s".format(first_squares))
    #log.info("last     squares: %s".format(last_squares))
    #log.info("last UBD squares: %s".format(last_UBD_squares))
    return (first_squares, last_squares, last_UBD_squares)


class LabColor(object):

    def __init__(self, L, a, b, red, green, blue):
        self.L = L
        self.a = a
        self.b = b
        self.red = red
        self.green = green
        self.blue = blue

    def __str__(self):
        return ("Lab (%s, %s, %s)" % (self.L, self.a, self.b))

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        if self.L != other.L:
            return self.L < other.L

        if self.a != other.a:
            return self.a < other.a

        return self.b < other.b

    def update_rgb(self):
        """
        https://github.com/antimatter15/rgb-lab/blob/master/color.js
        """
        y = (self.L + 16) / 116
        x = self.a / 500 + y
        z = y - self.b / 200

        x = 0.95047 * (x ** 3 if (x**3 > 0.008856) else (x - 16/116) / 7.787)
        y = 1.00000 * (y ** 3 if (y ** 3 > 0.008856) else (y - 16/116) / 7.787)
        z = 1.08883 * ( z ** 3 if (z ** 3 > 0.008856) else (z - 16/116) / 7.787)

        r = x *  3.2406 + y * -1.5372 + z * -0.4986
        g = x * -0.9689 + y *  1.8758 + z *  0.0415
        b = x *  0.0557 + y * -0.2040 + z *  1.0570

        r = (1.055 * r ** (1/2.4) - 0.055) if (r > 0.0031308) else 12.92 * r
        g = (1.055 * g ** (1/2.4) - 0.055) if (g > 0.0031308) else 12.92 * g
        b = (1.055 * b ** (1/2.4) - 0.055) if (b > 0.0031308) else 12.92 * b

        self.red = int(max(0, min(1, r)) * 255)
        self.green = int(max(0, min(1, g)) * 255)
        self.blue = int(max(0, min(1, b)) * 255)


def rgb2lab(inputColor):
    (red, green, blue) = inputColor

    # XYZ -> Standard-RGB
    # https://www.easyrgb.com/en/math.php
    var_R = red / 255
    var_G = green / 255
    var_B = blue / 255

    if var_R > 0.04045:
        var_R = pow(((var_R + 0.055) / 1.055), 2.4)
    else:
        var_R = var_R / 12.92

    if var_G > 0.04045:
        var_G = pow(((var_G + 0.055 ) / 1.055), 2.4)
    else:
        var_G = var_G / 12.92

    if var_B > 0.04045:
        var_B = pow(((var_B + 0.055 ) / 1.055), 2.4)
    else:
        var_B = var_B / 12.92

    var_R = var_R * 100
    var_G = var_G * 100
    var_B = var_B * 100

    X = var_R * 0.4124 + var_G * 0.3576 + var_B * 0.1805
    Y = var_R * 0.2126 + var_G * 0.7152 + var_B * 0.0722
    Z = var_R * 0.0193 + var_G * 0.1192 + var_B * 0.9505

    reference_X = 95.047
    reference_Y = 100.0
    reference_Z = 108.883

    # XYZ -> CIE-L*ab
    # //www.easyrgb.com/en/math.php
    var_X = X / reference_X
    var_Y = Y / reference_Y
    var_Z = Z / reference_Z

    if var_X > 0.008856:
        var_X = pow(var_X, 1/3)
    else:
        var_X = (7.787 * var_X) + (16 / 116)

    if var_Y > 0.008856:
        var_Y = pow(var_Y, 1/3)
    else:
        var_Y = (7.787 * var_Y) + (16 / 116)

    if var_Z > 0.008856:
        var_Z = pow(var_Z, 1/3)
    else:
        var_Z = (7.787 * var_Z) + (16 / 116)

    L = (116 * var_Y) - 16
    a = 500 * (var_X - var_Y)
    b = 200 * (var_Y - var_Z)
    #log.info("RGB ({}, {}, {}), L {}, a {}, b {}".format(red, green, blue, L, a, b))

    return LabColor(L, a, b, red, green, blue)


def hex_to_rgb(rgb_string):
    """
    Takes #112233 and returns the RGB values in decimal
    """
    if rgb_string.startswith('#'):
        rgb_string = rgb_string[1:]

    red = int(rgb_string[0:2], 16)
    green = int(rgb_string[2:4], 16)
    blue = int(rgb_string[4:6], 16)
    return (red, green, blue)


def hashtag_rgb_to_labcolor(rgb_string):
    (red, green, blue) = hex_to_rgb(rgb_string)
    return rgb2lab((red, green, blue))


crayola_colors = {
    # Handy website for converting RGB tuples to hex
    # http://www.w3schools.com/colors/colors_converter.asp
    #
    # These are the RGB values as seen via a webcam
    #   white = (235, 254, 250)
    #   green = (20, 105, 74)
    #   yellow = (210, 208, 2)
    #   orange = (148, 53, 9)
    #   blue = (22, 57, 103)
    #   red = (104, 4, 2)
    #
    'Wh': hashtag_rgb_to_labcolor('#FFFFFF'),
    'Gr': hashtag_rgb_to_labcolor('#14694a'),
    'Ye': hashtag_rgb_to_labcolor('#FFFF00'),
    'OR': hashtag_rgb_to_labcolor('#943509'),
    'Bu': hashtag_rgb_to_labcolor('#163967'),
    'Rd': hashtag_rgb_to_labcolor('#680402')
}


def get_row_color_distances(squares, row_baseline_lab):
    """
    'colors' is list if (index, (red, green, blue)) tuples
    'row_baseline_lab' is a list of Lab colors, one for each row of colors

    Return the total distance of the colors in a row vs their baseline
    """
    results = []
    squares_per_row = int(len(squares)/6)
    count = 0
    row_index = 0
    distance = 0
    baseline_lab = row_baseline_lab[row_index]

    for square in squares:
        baseline_lab = row_baseline_lab[row_index]
        distance += get_lab_distance(baseline_lab, square.lab)
        count += 1

        if count % squares_per_row == 0:
            results.append(int(distance))
            row_index += 1
            distance = 0

    return results


def get_squares_for_row(squares, target_row_index):
    results = []
    squares_per_row = int(len(squares)/6)
    count = 0
    row_index = 0

    for square in squares:
        if row_index == target_row_index:
            results.append(square)
        count += 1

        if count % squares_per_row == 0:
            row_index += 1

    return results


def rgb_list_to_lab(rgbs):
    reds = array.array('B')
    greens = array.array('B')
    blues = array.array('B')

    for (red, green, blue) in rgbs:
        reds.append(red)
        greens.append(green)
        blues.append(blue)

    median_red = int(median(reds))
    median_green = int(median(greens))
    median_blue = int(median(blues))

    return rgb2lab((median_red, median_green, median_blue))


class Square(object):

    def __init__(self, side, cube, position, red, green, blue):
        self.cube = cube
        self.side = side
        self.position = position
        self.rgb = (red, green, blue)
        self.red = red
        self.green = green
        self.blue = blue
        self.lab = rgb2lab((red, green, blue))
        self.color_name = None
        self.side_name = None # ULFRBD

    def __str__(self):
        return "%s%d" % (self.side, self.position)

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return self.position < other.position


class Side(object):

    def __init__(self, cube, width, name):
        self.cube = cube
        self.name = name  # U, L, etc
        self.color = None
        self.squares = OrderedDict()
        self.width = width
        self.squares_per_side = width * width
        self.center_squares = []
        self.edge_squares = []
        self.corner_squares = []
        self.wing_partner = {}

        if self.name == 'U':
            index = 0
        elif self.name == 'L':
            index = 1
        elif self.name == 'F':
            index = 2
        elif self.name == 'R':
            index = 3
        elif self.name == 'B':
            index = 4
        elif self.name == 'D':
            index = 5

        self.min_pos = (index * self.squares_per_side) + 1
        self.max_pos = (index * self.squares_per_side) + self.squares_per_side

        # If this is a cube of odd width (3x3x3) then define a mid_pos
        if self.width % 2 == 0:
            self.mid_pos = None
        else:
            self.mid_pos = (self.min_pos + self.max_pos) / 2

        self.corner_pos = (self.min_pos,
                           self.min_pos + self.width - 1,
                           self.max_pos - self.width + 1,
                           self.max_pos)
        self.edge_pos = []
        self.edge_north_pos = []
        self.edge_west_pos = []
        self.edge_south_pos = []
        self.edge_east_pos = []
        self.center_pos = []

        for position in range(self.min_pos, self.max_pos):
            if position in self.corner_pos:
                pass

            # Edges at the north
            elif position > self.corner_pos[0] and position < self.corner_pos[1]:
                self.edge_pos.append(position)
                self.edge_north_pos.append(position)

            # Edges at the south
            elif position > self.corner_pos[2] and position < self.corner_pos[3]:
                self.edge_pos.append(position)
                self.edge_south_pos.append(position)

            elif (position - 1) % self.width == 0:
                west_edge = position
                east_edge = west_edge + self.width - 1

                # Edges on the west
                self.edge_pos.append(west_edge)
                self.edge_west_pos.append(west_edge)

                # Edges on the east
                self.edge_pos.append(east_edge)
                self.edge_east_pos.append(east_edge)

                # Center squares
                for x in range(west_edge + 1, east_edge):
                    self.center_pos.append(x)


    def __str__(self):
        return "side-" + self.name

    def __repr__(self):
        return self.__str__()

    def set_square(self, position, red, green, blue):
        self.squares[position] = Square(self, self.cube, position, red, green, blue)

        if position in self.center_pos:
            self.center_squares.append(self.squares[position])

        elif position in self.edge_pos:
            self.edge_squares.append(self.squares[position])

        elif position in self.corner_pos:
            self.corner_squares.append(self.squares[position])

        else:
            raise Exception('Could not determine egde vs corner vs center')

    def calculate_wing_partners(self):
        for (pos1, pos2) in self.cube.all_edge_positions:
            if pos1 >= self.min_pos and pos1 <= self.max_pos:
                self.wing_partner[pos1] = pos2
            elif pos2 >= self.min_pos and pos2 <= self.max_pos:
                self.wing_partner[pos2] = pos1

    def get_wing_partner(self, wing_index):
        try:
            return self.wing_partner[wing_index]
        except KeyError:
            log.info("wing_partner\n%s\n".format(self.wing_partner))
            raise


class RubiksColorSolverGeneric(object):

    def __init__(self, width):
        self.width = width
        self.height = width
        self.squares_per_side = self.width * self.width
        self.scan_data = {}
        self.orbits = int(ceil((self.width - 2) / 2.0))
        self.state = []
        self.orange_baseline = None
        self.red_baseline = None
        self.white_squares = []
        self.all_edge_positions = []

        if self.width % 2 == 0:
            self.even = True
            self.odd = False
        else:
            self.even = False
            self.odd = True

        if not os.path.exists(HTML_DIRECTORY):
            os.makedirs(HTML_DIRECTORY)
            # os.chmod(HTML_DIRECTORY, 0o777)

        with open(HTML_FILENAME, 'w') as fh:
            pass
        # os.chmod(HTML_FILENAME, 0o777)

        self.sides = {
            'U': Side(self, self.width, 'U'),
            'L': Side(self, self.width, 'L'),
            'F': Side(self, self.width, 'F'),
            'R': Side(self, self.width, 'R'),
            'B': Side(self, self.width, 'B'),
            'D': Side(self, self.width, 'D')
        }

        self.sideU = self.sides['U']
        self.sideL = self.sides['L']
        self.sideF = self.sides['F']
        self.sideR = self.sides['R']
        self.sideB = self.sides['B']
        self.sideD = self.sides['D']
        self.side_order = ('U', 'L', 'F', 'R', 'B', 'D')

        # U and B
        for (pos1, pos2) in zip(self.sideU.edge_north_pos, reversed(self.sideB.edge_north_pos)):
            self.all_edge_positions.append((pos1, pos2))

        # U and L
        for (pos1, pos2) in zip(self.sideU.edge_west_pos, self.sideL.edge_north_pos):
            self.all_edge_positions.append((pos1, pos2))

        # U and F
        for (pos1, pos2) in zip(self.sideU.edge_south_pos, self.sideF.edge_north_pos):
            self.all_edge_positions.append((pos1, pos2))

        # U and R
        for (pos1, pos2) in zip(self.sideU.edge_east_pos, reversed(self.sideR.edge_north_pos)):
            self.all_edge_positions.append((pos1, pos2))

        # F and L
        for (pos1, pos2) in zip(self.sideF.edge_west_pos, self.sideL.edge_east_pos):
            self.all_edge_positions.append((pos1, pos2))

        # F and R
        for (pos1, pos2) in zip(self.sideF.edge_east_pos, self.sideR.edge_west_pos):
            self.all_edge_positions.append((pos1, pos2))

        # F and D
        for (pos1, pos2) in zip(self.sideF.edge_south_pos, self.sideD.edge_north_pos):
            self.all_edge_positions.append((pos1, pos2))

        # L and B
        for (pos1, pos2) in zip(self.sideL.edge_west_pos, self.sideB.edge_east_pos):
            self.all_edge_positions.append((pos1, pos2))

        # L and D
        for (pos1, pos2) in zip(self.sideL.edge_south_pos, reversed(self.sideD.edge_west_pos)):
            self.all_edge_positions.append((pos1, pos2))

        # R and D
        for (pos1, pos2) in zip(self.sideR.edge_south_pos, self.sideD.edge_east_pos):
            self.all_edge_positions.append((pos1, pos2))

        # R and B
        for (pos1, pos2) in zip(self.sideR.edge_east_pos, self.sideB.edge_west_pos):
            self.all_edge_positions.append((pos1, pos2))

        # B and D
        for (pos1, pos2) in zip(reversed(self.sideB.edge_south_pos), self.sideD.edge_south_pos):
            self.all_edge_positions.append((pos1, pos2))

        for side in self.sides.values():
            side.calculate_wing_partners()

        self.www_header()

    def www_header(self):
        """
        Write the <head> including css
        """
        side_margin = 10
        square_size = 40
        size = self.width # 3 for 3x3x3, etc

        with open(HTML_FILENAME, 'a') as fh:
            fh.write("""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
div.clear {
    clear: both;
}

div.clear_left {
    clear: left;
}

div.side {
    margin: %dpx;
    float: left;
}

""" % side_margin)

            for x in range(1, size-1):
                fh.write("div.col%d,\n" % x)

            fh.write("""div.col%d {
    float: left;
}

div.col%d {
    margin-left: %dpx;
}
div#upper,
div#down {
    margin-left: %dpx;
}
""" % (size-1,
       size,
       (size - 1) * square_size,
       (size * square_size) + (3 * side_margin)))

            fh.write("""
span.square {
    width: %dpx;
    height: %dpx;
    white-space-collapsing: discard;
    display: inline-block;
    color: black;
    font-weight: bold;
    line-height: %dpx;
    text-align: center;
}

div.square {
    width: %dpx;
    height: %dpx;
    color: black;
    font-weight: bold;
    line-height: %dpx;
    text-align: center;
}

div.square span {
  display:        inline-block;
  vertical-align: middle;
  line-height:    normal;
}

div#colormapping {
    float: left;
}

</style>
<title>CraneCuber</title>
</head>
<body>
""" % (square_size, square_size, square_size, square_size, square_size, square_size))

    def write_colors(self, desc, squares):
        with open(HTML_FILENAME, 'a') as fh:
            squares_per_row = int(len(squares)/6)
            fh.write("<h2>%s</h2>\n" % desc)
            fh.write("<div class='clear colors'>\n")

            count = 0
            for square in squares:
                (red, green, blue) = square.rgb
                fh.write("<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s, side %s'>%d</span>\n" %
                    (red, green, blue,
                     red, green, blue,
                     int(square.lab.L), int(square.lab.a), int(square.lab.b),
                     square.color_name,
                     square.side_name,
                     square.position))

                count += 1

                if count % squares_per_row == 0:
                    fh.write("<br>")
            fh.write("</div>\n")

    def www_footer(self):
        with open(HTML_FILENAME, 'a') as fh:
            fh.write("""
</body>
</html>
""")

    def get_side(self, position):
        """
        Given a position on the cube return the Side object
        that contians that position
        """
        for side in self.sides.values():
            if position >= side.min_pos and position <= side.max_pos:
                return side
        raise Exception("Could not find side for %d" % position)

    def get_square(self, position):
        side = self.get_side(position)
        return side.squares[position]

    def enter_scan_data(self, scan_data):
        self.scan_data = scan_data

        for (position, (red, green, blue)) in sorted(self.scan_data.items()):
            position = int(position)
            side = self.get_side(position)
            side.set_square(position, red, green, blue)

        with open(HTML_FILENAME, 'a') as fh:
            fh.write("<h1>JSON Input</h1>\n")
            fh.write("<pre>%s</pre>\n" % json_dumps(self.scan_data))

    def write_cube(self, desc, use_html_colors):
        # TODO clean this up...should not need the 'cube' var
        cube = ['dummy',]

        for side in (self.sideU, self.sideL, self.sideF, self.sideR, self.sideB, self.sideD):
            for position in range(side.min_pos, side.max_pos+1):
                square = side.squares[position]

                if use_html_colors:
                    red = html_color[square.color_name]['red']
                    green = html_color[square.color_name]['green']
                    blue = html_color[square.color_name]['blue']
                else:
                    red = square.red
                    green = square.green
                    blue = square.blue

                cube.append((red, green, blue, square.color_name))

        col = 1
        squares_per_side = self.width * self.width
        min_square = 1
        max_square = squares_per_side * 6

        sides = ('upper', 'left', 'front', 'right', 'back', 'down')
        side_index = -1
        (first_squares, last_squares, last_UBD_squares) = get_important_square_indexes(self.width)

        with open(HTML_FILENAME, 'a') as fh:
            fh.write("<h1>%s</h1>\n" % desc)
            for index in range(1, max_square + 1):
                if index in first_squares:
                    side_index += 1
                    fh.write("<div class='side' id='%s'>\n" % sides[side_index])

                (red, green, blue, color_name) = cube[index]
                lab = rgb2lab((red, green, blue))

                fh.write("    <div class='square col%d' title='RGB (%d, %d, %d), Lab (%s, %s, %s), color %s' style='background-color: #%02x%02x%02x;'><span>%02d</span></div>\n" %
                    (col,
                     red, green, blue,
                     int(lab.L), int(lab.a), int(lab.b),
                     color_name,
                     red, green, blue,
                     index))

                if index in last_squares:
                    fh.write("</div>\n")

                    if index in last_UBD_squares:
                        fh.write("<div class='clear'></div>\n")

                col += 1

                if col == self.width + 1:
                    col = 1

    def print_cube(self):
        data = []
        for x in range(3 * self.height):
            data.append([])

        color_codes = {
          'OR': 90,
          'Rd': 91,
          'Gr': 92,
          'Ye': 93,
          'Bu': 94,
          'Wh': 97
        }

        for side_name in self.side_order:
            side = self.sides[side_name]

            if side_name == 'U':
                line_number = 0
                prefix = (' ' * self.width * 3) +  ' '
            elif side_name in ('L', 'F', 'R', 'B'):
                line_number = self.width
                prefix = ''
            else:
                line_number = self.width * 2
                prefix = (' ' * self.width * 3) +  ' '

            # rows
            for y in range(self.width):
                data[line_number].append(prefix)

                # cols
                for x in range(self.width):
                    color_name = side.squares[side.min_pos + (y * self.width) + x].color_name
                    color_code = color_codes.get(color_name)

                    if color_name is None:
                        color_code = 97
                        data[line_number].append('\033[%dmFo\033[0m' % color_code)
                    else:
                        data[line_number].append('\033[%dm%s\033[0m' % (color_code, color_name))
                line_number += 1

        output = []
        for row in data:
            output.append(' '.join(row))

        log.info("Cube\n\n%s\n" % '\n'.join(output))

    def write_color_box(self):
        with open(HTML_FILENAME, 'a') as fh:
            fh.write("<h2>color_box</h2>\n")
            fh.write("<div class='clear colors'>\n")
            for color_name in ("Wh", "Ye", "Gr", "Bu", "OR", "Rd"):
                lab = self.color_box[color_name]

                fh.write("<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%s</span>\n" %
                    (lab.red, lab.green, lab.blue,
                    lab.red, lab.green, lab.blue,
                    int(lab.L), int(lab.a), int(lab.b),
                    color_name,
                    color_name))

            fh.write("<br>")
            fh.write("</div>\n")

    def set_state(self):
        self.state = []

        if self.sideU.mid_pos is not None:

            # Assign a color name to each center square. Compute
            # which naming scheme results in the least total color distance in
            # terms of the assigned color name vs. the colors in crayola_colors.
            min_distance = None
            min_distance_permutation = None

            # Build a list of all center squares
            center_squares = []
            for side in (self.sideU, self.sideL, self.sideF, self.sideR, self.sideB, self.sideD):
                square = side.squares[side.mid_pos]
                center_squares.append(square)
            desc = "middle center"
            #log.info("center_squares: %s".format(center_squares))

            for permutation in odd_cube_center_color_permutations:
                distance = 0

                for (index, center_square) in enumerate(center_squares):
                    color_name = permutation[index]
                    color_obj = crayola_colors[color_name]
                    distance += get_lab_distance(center_square.lab, color_obj)

                if min_distance is None or distance < min_distance:
                    min_distance = distance
                    min_distance_permutation = permutation
                    '''
                    log.info("{} PERMUTATION {}, DISTANCE {:,} (NEW MIN)".format(desc, permutation, int(distance)))
                else:
                    log.info("{} PERMUTATION {}, DISTANCE {}".format(desc, permutation, distance))
                    '''

            self.color_to_side_name = {
                min_distance_permutation[0] : 'U',
                min_distance_permutation[1] : 'L',
                min_distance_permutation[2] : 'F',
                min_distance_permutation[3] : 'R',
                min_distance_permutation[4] : 'B',
                min_distance_permutation[5] : 'D'
            }

            #log.info("{} FINAL PERMUTATION {}".format(desc, min_distance_permutation))

        else:
            self.color_to_side_name = {
                'Wh' : 'U',
                'OR' : 'L',
                'Gr' : 'F',
                'Rd' : 'R',
                'Bu' : 'B',
                'Ye' : 'D'
            }

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]
                square.side_name = self.color_to_side_name[square.color_name]

    def cube_for_kociemba_strict(self):
        log.info("color_to_side_name:\n{}\n".format(self.color_to_side_name))
        data = []
        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]
                #data.append(self.color_to_side_name[square.color_name])
                data.append(square.side_name)

        return data

    def cube_for_json(self):
        """
        Return a dictionary of the cube data so that we can json dump it
        """
        data = {}
        data['kociemba'] = ''.join(self.cube_for_kociemba_strict())
        data['sides'] = {}
        data['squares'] = {}

        '''
        for side in self.sides.values():
            data['sides'][side.name] = {
                'colorName' : side.color_name,
                'colorHTML' : html_color[side.color_name]
            }
        '''

        #log.info("color_to_side_name:\n{}\n".format(self.color_to_side_name))

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]
                color = square.color_name
                data['squares'][square.position] = {
                    'finalSide' : self.color_to_side_name[color]
                }

        return data

    def assign_color_names(self, desc, squares_lists_all, color_permutations, color_box):
        assert color_permutations
        assert color_box

        #log.info(f"assign_color_names for '{desc}'")
        #log.info(f"squares_lists_all {squares_lists_all}")
        #log.info(f"color_permutations {color_permutations}")
        #log.info(f"color_box {color_box}")

        # split squares_lists_all up into 6 evenly sized lists
        squares_per_row = int(len(squares_lists_all)/6)
        squares_lists = []
        square_list = []

        for square in squares_lists_all:
            square_list.append(square)

            if len(square_list) == squares_per_row:
                squares_lists.append(square_list)
                square_list = []

        # Assign a color name to each squares in each square_list. Compute
        # which naming scheme results in the least total color distance in
        # terms of the assigned color name vs. the colors in color_box.
        min_distance = None
        min_distance_permutation = None

        for permutation in color_permutations:
            distance = 0

            for (index, squares_list) in enumerate(squares_lists):
                color_name = permutation[index]
                color_lab = color_box[color_name]

                for square in squares_list:
                    distance += get_lab_distance(square.lab, color_lab)

            if min_distance is None or distance < min_distance:
                min_distance = distance
                min_distance_permutation = permutation
            #    log.info("{} PERMUTATION {}, DISTANCE {:,} (NEW MIN)".format(desc, permutation, int(distance)))
            #else:
            #    log.info("{} PERMUTATION {}, DISTANCE {}".format(desc, permutation, distance))

        # Assign the color name to the Square object
        for (index, squares_list) in enumerate(squares_lists):
            color_name = min_distance_permutation[index]

            for square in squares_list:
                square.color_name = color_name

    def resolve_color_box(self):
        """
        Assign names to the corner squares, use crayola colors as reference point.

        We use these name assignments to build our "color_box" which will be our
        references Wh, Ye, OR, Rd, Gr, Bu colors for assigning color names to edge
        and center squares.
        """
        log.debug('\n\n\n\n')
        log.info('Resolve color_box')
        corner_squares = []

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for square in side.corner_squares:
                corner_squares.append(square)

        sorted_corner_squares = traveling_salesman(corner_squares, LAB_DISTANCE_ALGORITHM)
        self.assign_color_names('corners', sorted_corner_squares, even_cube_center_color_permutations, crayola_colors)
        self.sanity_check_corner_squares()
        self.write_colors('color_box corners', sorted_corner_squares)

        # Build a color_box dictionary from the centers
        self.color_box = {}

        white_corners = []
        yellow_corners = []
        orange_corners = []
        red_corners = []
        green_corners = []
        blue_corners = []

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for square in side.corner_squares:
                if square.color_name == "Wh":
                    white_corners.append(square.rgb)
                elif square.color_name == "Ye":
                    yellow_corners.append(square.rgb)
                elif square.color_name == "OR":
                    orange_corners.append(square.rgb)
                elif square.color_name == "Rd":
                    red_corners.append(square.rgb)
                elif square.color_name == "Gr":
                    green_corners.append(square.rgb)
                elif square.color_name == "Bu":
                    blue_corners.append(square.rgb)

        self.color_box["Wh"] = rgb_list_to_lab(white_corners)
        self.color_box["Ye"] = rgb_list_to_lab(yellow_corners)
        self.color_box["OR"] = rgb_list_to_lab(orange_corners)
        self.color_box["Rd"] = rgb_list_to_lab(red_corners)
        self.color_box["Gr"] = rgb_list_to_lab(green_corners)
        self.color_box["Bu"] = rgb_list_to_lab(blue_corners)
        # log.info(f"self.color_box: {self.color_box}")

        self.orange_baseline = self.color_box["OR"]
        self.red_baseline = self.color_box["Rd"]

    def resolve_corner_squares(self):
        """
        Assign names to the corner squares
        """
        log.debug('\n\n\n\n')
        log.info('Resolve corners')
        corner_squares = []

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for square in side.corner_squares:
                corner_squares.append(square)

        #corner_squares.extend(self.color_box_squares)

        sorted_corner_squares = traveling_salesman(corner_squares, LAB_DISTANCE_ALGORITHM)
        self.assign_color_names('corners', sorted_corner_squares, even_cube_center_color_permutations, self.color_box)
        self.sanity_check_corner_squares()
        self.write_colors('corners', sorted_corner_squares)

    def validate_edge_orbit(self, orbit_id):
        valid = True

        # We need to see which orange/red we can flip that will make the edges valid
        wing_pair_counts = {}

        for (square1_position, square2_position) in edge_orbit_wing_pairs[self.width][orbit_id]:
            square1 = self.get_square(square1_position)
            square2 = self.get_square(square2_position)
            wing_pair_string = ", ".join(sorted([square1.color_name, square2.color_name]))
            #log.info("orbit {}: ({}, {}) is ({})".format(orbit_id, square1_position, square2_position, wing_pair_string))

            if wing_pair_string not in wing_pair_counts:
                wing_pair_counts[wing_pair_string] = 0
            wing_pair_counts[wing_pair_string] += 1

        # Are all counts the same?
        target_count = None
        for (wing_pair, count) in wing_pair_counts.items():

            if target_count is None:
                target_count = count
            else:
                if count != target_count:
                    valid = False
                    break

        if not valid:
            log.info("wing_pair_counts:\n{}\n".format(wing_pair_counts))
            log.warning("valid: {}".format(valid))

        #assert valid, "Cube is invalid"
        return valid

    def find_corners_by_color(self):
        green_white_corners = []
        green_yellow_corners = []
        blue_white_corners = []
        blue_yellow_corners = []

        for corner_tuple in corner_tuples[self.width]:
            corner_colors = []

            for position in corner_tuple:
                square = self.get_square(position)
                #log.info("square %s is %s" % (square, square.color_name))
                corner_colors.append(square.color_name)

            if "Gr" in corner_colors and "Wh" in corner_colors:
                #log.info("%s is Gr/Wh corner" % " ".join(map(str, corner_tuple)))
                green_white_corners.append(corner_tuple)

            elif "Gr" in corner_colors and "Ye" in corner_colors:
                #log.info("%s is Gr/Ye corner" % " ".join(map(str, corner_tuple)))
                green_yellow_corners.append(corner_tuple)

            elif "Bu" in corner_colors and "Wh" in corner_colors:
                #log.info("%s is Bu/Wh corner" % " ".join(map(str, corner_tuple)))
                blue_white_corners.append(corner_tuple)

            elif "Bu" in corner_colors and "Ye" in corner_colors:
                #log.info("%s is Bu/Ye corner" % " ".join(map(str, corner_tuple)))
                blue_yellow_corners.append(corner_tuple)

        return (green_white_corners, green_yellow_corners, blue_white_corners, blue_yellow_corners)

    def find_edges_by_color(self, orbit_id):
        green_red_orange_color_names = ("Gr", "Rd", "OR")
        blue_red_orange_color_names = ("Bu", "Rd", "OR")
        white_red_orange_color_names = ("Wh", "Rd", "OR")
        yellow_red_orange_color_names = ("Ye", "Rd", "OR")
        green_red_or_orange_edges = []
        blue_red_or_orange_edges = []
        white_red_or_orange_edges = []
        yellow_red_or_orange_edges = []

        for (square_index, partner_index) in edge_orbit_wing_pairs[self.width][orbit_id]:
            square = self.get_square(square_index)
            partner = self.get_square(partner_index)

            if square.color_name in green_red_orange_color_names and partner.color_name in green_red_orange_color_names:
                if square.color_name == "Gr":
                    green_red_or_orange_edges.append((square, partner))
                else:
                    green_red_or_orange_edges.append((partner, square))

            elif square.color_name in blue_red_orange_color_names and partner.color_name in blue_red_orange_color_names:
                if square.color_name == "Bu":
                    blue_red_or_orange_edges.append((square, partner))
                else:
                    blue_red_or_orange_edges.append((partner, square))

            elif square.color_name in white_red_orange_color_names and partner.color_name in white_red_orange_color_names:
                if square.color_name == "Wh":
                    white_red_or_orange_edges.append((square, partner))
                else:
                    white_red_or_orange_edges.append((partner, square))

            elif square.color_name in yellow_red_orange_color_names and partner.color_name in yellow_red_orange_color_names:
                if square.color_name == "Ye":
                    yellow_red_or_orange_edges.append((square, partner))
                else:
                    yellow_red_or_orange_edges.append((partner, square))

        return (green_red_or_orange_edges, blue_red_or_orange_edges, white_red_or_orange_edges, yellow_red_or_orange_edges)

    def sanity_check_edges_red_orange_count_for_orbit(self, target_orbit_id):

        def fix_orange_vs_red_for_color(target_color, target_color_red_or_orange_edges):

            if len(target_color_red_or_orange_edges) == 2:
                red_orange_permutations = (
                    ("OR", "Rd"),
                    ("Rd", "OR"),
                )
            elif len(target_color_red_or_orange_edges) == 4:
                # 4!/(2!*2!) = 6
                red_orange_permutations = (
                    ("OR", "OR", "Rd", "Rd"),
                    ("OR", "Rd", "OR", "Rd"),
                    ("OR", "Rd", "Rd", "OR"),
                    ("Rd", "Rd", "OR", "OR"),
                    ("Rd", "OR", "Rd", "OR"),
                    ("Rd", "OR", "OR", "Rd"),
                )
            else:
                raise Exception("There should be either 2 or 4 but we have %s".format(target_color_red_or_orange_edges))

            min_distance = None
            min_distance_permutation = None

            for red_orange_permutation in red_orange_permutations:
                distance = 0

                for (index, (target_color_square, partner_square)) in enumerate(target_color_red_or_orange_edges):
                    red_orange = red_orange_permutation[index]

                    if red_orange == "OR":
                        distance += get_lab_distance(partner_square.lab, self.orange_baseline)
                    elif red_orange == "Rd":
                        distance += get_lab_distance(partner_square.lab, self.red_baseline)
                    else:
                        raise Exception(red_orange)

                    partner_square.color_name = red_orange
                    partner_square.side_name = self.color_to_side_name[partner_square.color_name]

                if self.width == 4 or self.width == 6 or (self.width == 5 and target_orbit_id == 0):
                    for (index, (target_color_square, partner_square)) in enumerate(target_color_red_or_orange_edges):
                        red_orange = red_orange_permutation[index]
                        high_low_edge_per_color = self.get_high_low_per_edge_color(target_orbit_id)
                        edge_color_pair = edge_color_pair_map["%s/%s" % (target_color_square.color_name, partner_square.color_name)]
                        #log.info("high_low_edge_per_color\n%s".format(high_low_edge_per_color))

                        if len(high_low_edge_per_color[edge_color_pair]) != 2:
                            #log.warning("*" * 40)
                            #log.warning("edge_color_pair %s high_low is %s" % (edge_color_pair, high_low_edge_per_color[edge_color_pair]))
                            #log.warning("*" * 40)
                            distance += 999

                if min_distance is None or distance < min_distance:
                    min_distance = distance
                    min_distance_permutation = red_orange_permutation
                    log.info("target edge %s, red_orange_permutation %s, distance %s (NEW MIN)" %
                        (target_color, ",".join(red_orange_permutation), distance))
                else:
                    log.info("target edge %s, red_orange_permutation %s, distance %s)" %
                        (target_color, ",".join(red_orange_permutation), distance))

            log.info("min_distance_permutation %s" % ",".join(min_distance_permutation))

            for (index, (target_color_square, partner_square)) in enumerate(target_color_red_or_orange_edges):
                if partner_square.color_name != min_distance_permutation[index]:
                    log.warning("change %s edge partner %s from %s to %s" %
                        (target_color, partner_square, partner_square.color_name, min_distance_permutation[index]))
                    partner_square.color_name = min_distance_permutation[index]
                    partner_square.side_name = self.color_to_side_name[partner_square.color_name]
                else:
                    log.info("%s edge partner %s is %s" %
                        (target_color, partner_square, partner_square.color_name))

            log.info("\n\n")

        (green_red_or_orange_edges, blue_red_or_orange_edges,
         white_red_or_orange_edges, yellow_red_or_orange_edges) = self.find_edges_by_color(target_orbit_id)
        log.info("orbit %s green_red_or_orange_edges %s" % (target_orbit_id, green_red_or_orange_edges))
        fix_orange_vs_red_for_color('green', green_red_or_orange_edges)

        log.info("orbit %s blue_red_or_orange_edges %s" % (target_orbit_id, blue_red_or_orange_edges))
        fix_orange_vs_red_for_color('blue', blue_red_or_orange_edges)

        log.info("orbit %s white_red_or_orange_edges %s" % (target_orbit_id, white_red_or_orange_edges))
        fix_orange_vs_red_for_color('white', white_red_or_orange_edges)

        log.info("orbit %s yellow_red_or_orange_edges %s" % (target_orbit_id, yellow_red_or_orange_edges))
        fix_orange_vs_red_for_color('yellow', yellow_red_or_orange_edges)

        self.validate_edge_orbit(target_orbit_id)

    def get_high_low_per_edge_color(self, target_orbit_id):

        high_low_per_edge_color = {
            "Gr/Wh" : set(),
            "Bu/Wh" : set(),
            "OR/Wh" : set(),
            "Rd/Wh" : set(),

            "Gr/OR" : set(),
            "Bu/OR" : set(),
            "Gr/Rd" : set(),
            "Bu/Rd" : set(),

            "Gr/Ye" : set(),
            "Bu/Ye" : set(),
            "OR/Ye" : set(),
            "Rd/Ye" : set(),
        }

        for (square_index, partner_index) in edge_orbit_wing_pairs[self.width][target_orbit_id]:
            square = self.get_square(square_index)
            partner = self.get_square(partner_index)

            if self.width == 6:
                highlow = highlow_edge_values_666[(square_index, partner_index, square.side_name, partner.side_name)]
            elif self.width == 5:
                highlow = highlow_edge_values_555[(square_index, partner_index, square.side_name, partner.side_name)]
            elif self.width == 4:
                highlow = highlow_edge_values_444[(square_index, partner_index, square.side_name, partner.side_name)]

            edge_color_pair = edge_color_pair_map["%s/%s" % (square.color_name, partner.color_name)]
            high_low_per_edge_color[edge_color_pair].add(highlow)

        # log.info("high_low_per_edge_color for orbit %d\n%s" % (target_orbit_id, high_low_per_edge_color))
        # log.info("")
        return high_low_per_edge_color

    def sanity_check_edge_squares(self):
        for orbit_id in range(self.orbits):
            self.sanity_check_edges_red_orange_count_for_orbit(orbit_id)

    def resolve_edge_squares(self):
        """
        Use traveling salesman algorithm to sort the colors
        """

        # Nothing to be done for 2x2x2
        if self.width == 2:
            return True

        for target_orbit_id in range(self.orbits):
            log.debug('\n\n\n\n')
            log.info('Resolve edges for orbit %d' % target_orbit_id)
            edge_squares = []

            for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
                for square in side.edge_squares:
                    orbit_id = edge_orbit_id[self.width][square.position]
                    #log.info("{}: {}, position {}, orbit_id {}".format(self.width, square, square.position, orbit_id))

                    if orbit_id == target_orbit_id:
                        edge_squares.append(square)

            #edge_squares.extend(self.color_box_squares)
            sorted_edge_squares = traveling_salesman(edge_squares, LAB_DISTANCE_ALGORITHM)
            self.assign_color_names('edge orbit %d' % target_orbit_id, sorted_edge_squares, even_cube_center_color_permutations, self.color_box)
            self.write_colors(
                'edges - orbit %d' % target_orbit_id,
                sorted_edge_squares)

    def assign_green_white_corners(self, green_white_corners):
        #log.info("Gr/Wh corner tuples %s".format(green_white_corners))
        valid_green_orange_white = (
            ['Gr', 'OR', 'Wh'],
            ['Wh', 'Gr', 'OR'],
            ['OR', 'Wh', 'Gr'],
        )

        valid_green_white_red = (
            ['Gr', 'Wh', 'Rd'],
            ['Rd', 'Gr', 'Wh'],
            ['Wh', 'Rd', 'Gr'],
        )

        for (corner1_index, corner2_index, corner3_index) in green_white_corners:
            corner1 = self.get_square(corner1_index)
            corner2 = self.get_square(corner2_index)
            corner3 = self.get_square(corner3_index)
            color_seq = [x.color_name for x in (corner1, corner2, corner3)]

            # If this is the case we must flip the orange to red or vice versa
            if color_seq not in valid_green_orange_white and color_seq not in valid_green_white_red:
                if corner1.color_name == "OR":
                    corner1.color_name = "Rd"
                    log.warning("change Gr/Wh corner partner %s from OR to Rd" % corner1)
                elif corner1.color_name == "Rd":
                    corner1.color_name = "OR"
                    log.warning("change Gr/Wh corner partner %s from Rd to OR" % corner1)
                elif corner2.color_name == "OR":
                    corner2.color_name = "Rd"
                    log.warning("change Gr/Wh corner partner %s from OR to Rd" % corner2)
                elif corner2.color_name == "Rd":
                    corner2.color_name = "OR"
                    log.warning("change Gr/Wh corner partner %s from Rd to OR" % corner2)
                elif corner3.color_name == "OR":
                    corner3.color_name = "Rd"
                    log.warning("change Gr/Wh corner partner %s from OR to Rd" % corner3)
                elif corner3.color_name == "Rd":
                    corner3.color_name = "OR"
                    log.warning("change Gr/Wh corner partner %s from Rd to OR" % corner3)

    def assign_green_yellow_corners(self, green_yellow_corners):
        valid_green_yellow_orange = (
            ['Gr', 'Ye', 'OR'],
            ['OR', 'Gr', 'Ye'],
            ['Ye', 'OR', 'Gr'],
        )

        valid_green_red_yellow = (
            ['Gr', 'Rd', 'Ye'],
            ['Ye', 'Gr', 'Rd'],
            ['Rd', 'Ye', 'Gr'],
        )

        for (corner1_index, corner2_index, corner3_index) in green_yellow_corners:
            corner1 = self.get_square(corner1_index)
            corner2 = self.get_square(corner2_index)
            corner3 = self.get_square(corner3_index)
            color_seq = [x.color_name for x in (corner1, corner2, corner3)]

            # If this is the case we must flip the orange to red or vice versa
            if color_seq not in valid_green_yellow_orange and color_seq not in valid_green_red_yellow:

                if corner1.color_name == "OR":
                    corner1.color_name = "Rd"
                    log.warning("change Gr/Ye corner partner %s from OR to Rd" % corner1)
                elif corner1.color_name == "Rd":
                    corner1.color_name = "OR"
                    log.warning("change Gr/Ye corner partner %s from Rd to OR" % corner1)
                elif corner2.color_name == "OR":
                    corner2.color_name = "Rd"
                    log.warning("change Gr/Ye corner partner %s from OR to Rd" % corner2)
                elif corner2.color_name == "Rd":
                    corner2.color_name = "OR"
                    log.warning("change Gr/Ye corner partner %s from Rd to OR" % corner2)
                elif corner3.color_name == "OR":
                    corner3.color_name = "Rd"
                    log.warning("change Gr/Ye corner partner %s from OR to Rd" % corner3)
                elif corner3.color_name == "Rd":
                    corner3.color_name = "OR"
                    log.warning("change Gr/Ye corner partner %s from Rd to OR" % corner3)

    def assign_blue_white_corners(self, blue_white_corners):
        #log.info("Bu/Wh corner tuples %s".format(blue_white_corners))
        valid_blue_white_orange = (
            ['Bu', 'Wh', 'OR'],
            ['OR', 'Bu', 'Wh'],
            ['Wh', 'OR', 'Bu'],
        )

        valid_blue_red_white = (
            ['Bu', 'Rd', 'Wh'],
            ['Wh', 'Bu', 'Rd'],
            ['Rd', 'Wh', 'Bu'],
        )

        for (corner1_index, corner2_index, corner3_index) in blue_white_corners:
            corner1 = self.get_square(corner1_index)
            corner2 = self.get_square(corner2_index)
            corner3 = self.get_square(corner3_index)
            color_seq = [x.color_name for x in (corner1, corner2, corner3)]

            # If this is the case we must flip the orange to red or vice versa
            if color_seq not in valid_blue_white_orange and color_seq not in valid_blue_red_white:

                if corner1.color_name == "OR":
                    corner1.color_name = "Rd"
                    log.warning("change Bu/Wh corner partner %s from OR to Rd" % corner1)
                elif corner1.color_name == "Rd":
                    corner1.color_name = "OR"
                    log.warning("change Bu/Wh corner partner %s from Rd to OR" % corner1)
                elif corner2.color_name == "OR":
                    corner2.color_name = "Rd"
                    log.warning("change Bu/Wh corner partner %s from OR to Rd" % corner2)
                elif corner2.color_name == "Rd":
                    corner2.color_name = "OR"
                    log.warning("change Bu/Wh corner partner %s from Rd to OR" % corner2)
                elif corner3.color_name == "OR":
                    corner3.color_name = "Rd"
                    log.warning("change Bu/Wh corner partner %s from OR to Rd" % corner3)
                elif corner3.color_name == "Rd":
                    corner3.color_name = "OR"
                    log.warning("change Bu/Wh corner partner %s from Rd to OR" % corner3)

    def assign_blue_yellow_corners(self, blue_yellow_corners):
        valid_blue_yellow_red = (
            ['Bu', 'Ye', 'Rd'],
            ['Rd', 'Bu', 'Ye'],
            ['Ye', 'Rd', 'Bu'],
        )

        valid_blue_orange_yellow = (
            ['Bu', 'OR', 'Ye'],
            ['Ye', 'Bu', 'OR'],
            ['OR', 'Ye', 'Bu'],
        )

        for (corner1_index, corner2_index, corner3_index) in blue_yellow_corners:
            corner1 = self.get_square(corner1_index)
            corner2 = self.get_square(corner2_index)
            corner3 = self.get_square(corner3_index)
            color_seq = [x.color_name for x in (corner1, corner2, corner3)]

            # If this is the case we must flip the orange to red or vice versa
            if color_seq not in valid_blue_yellow_red and color_seq not in valid_blue_orange_yellow:

                if corner1.color_name == "OR":
                    corner1.color_name = "Rd"
                    log.warning("change Bu/Ye corner partner %s from OR to Rd" % corner1)
                elif corner1.color_name == "Rd":
                    corner1.color_name = "OR"
                    log.warning("change Bu/Ye corner partner %s from Rd to OR" % corner1)
                elif corner2.color_name == "OR":
                    corner2.color_name = "Rd"
                    log.warning("change Bu/Ye corner partner %s from OR to Rd" % corner2)
                elif corner2.color_name == "Rd":
                    corner2.color_name = "OR"
                    log.warning("change Bu/Ye corner partner %s from Rd to OR" % corner2)
                elif corner3.color_name == "OR":
                    corner3.color_name = "Rd"
                    log.warning("change Bu/Ye corner partner %s from OR to Rd" % corner3)
                elif corner3.color_name == "Rd":
                    corner3.color_name = "OR"
                    log.warning("change Bu/Ye corner partner %s from Rd to OR" % corner3)

    def sanity_check_corner_squares(self):
        (green_white_corners, green_yellow_corners, blue_white_corners, blue_yellow_corners) = self.find_corners_by_color()
        self.assign_green_white_corners(green_white_corners)
        self.assign_green_yellow_corners(green_yellow_corners)
        self.assign_blue_white_corners(blue_white_corners)
        self.assign_blue_yellow_corners(blue_yellow_corners)

    def resolve_center_squares(self):
        """
        Use traveling salesman algorithm to sort the squares by color
        """
        for (desc, centers_squares) in center_groups[self.width]:
            log.debug('\n\n\n\n')
            log.info('Resolve {}'.format(desc))
            center_squares = []

            for position in centers_squares:
                square = self.get_square(position)
                center_squares.append(square)


            if desc == "centers":
                sorted_center_squares = center_squares[:]
                permutations = odd_cube_center_color_permutations
                #permutations = even_cube_center_color_permutations
            else:
                sorted_center_squares = traveling_salesman(center_squares, LAB_DISTANCE_ALGORITHM)
                permutations = even_cube_center_color_permutations

            self.assign_color_names(desc, sorted_center_squares, permutations, self.color_box)
            self.write_colors(desc, sorted_center_squares)

    def get_corner_swap_count(self, debug=False):

        needed_corners = [
            'BLU',
            'BRU',
            'FLU',
            'FRU',
            'DFL',
            'DFR',
            'BDL',
            'BDR']

        to_check = [
            (self.sideU.corner_pos[0], self.sideL.corner_pos[0], self.sideB.corner_pos[1]), # ULB
            (self.sideU.corner_pos[1], self.sideR.corner_pos[1], self.sideB.corner_pos[0]), # URB
            (self.sideU.corner_pos[2], self.sideL.corner_pos[1], self.sideF.corner_pos[0]), # ULF
            (self.sideU.corner_pos[3], self.sideF.corner_pos[1], self.sideR.corner_pos[0]), # UFR
            (self.sideD.corner_pos[0], self.sideL.corner_pos[3], self.sideF.corner_pos[2]), # DLF
            (self.sideD.corner_pos[1], self.sideF.corner_pos[3], self.sideR.corner_pos[2]), # DFR
            (self.sideD.corner_pos[2], self.sideL.corner_pos[2], self.sideB.corner_pos[3]), # DLB
            (self.sideD.corner_pos[3], self.sideR.corner_pos[3], self.sideB.corner_pos[2])  # DRB
        ]

        current_corners = []
        for (square_index1, square_index2, square_index3) in to_check:
            square1 = self.get_square(square_index1)
            square2 = self.get_square(square_index2)
            square3 = self.get_square(square_index3)
            corner_str = ''.join(sorted([square1.side_name, square2.side_name, square3.side_name]))
            current_corners.append(corner_str)

        if debug:
            log.info("to_check:\n%s".format(to_check))
            to_check_str = ''
            for (a, b, c) in to_check:
                to_check_str += "%4s" % a

            log.info("to_check       :%s" % to_check_str)
            log.info("needed corners : %s" % ' '.join(needed_corners))
            log.info("currnet corners: %s" % ' '.join(current_corners))
            log.info("")

        return get_swap_count(needed_corners, current_corners, debug)

    def corner_swaps_even(self, debug=False):
        if self.get_corner_swap_count(debug) % 2 == 0:
            return True
        return False

    def corner_swaps_odd(self, debug=False):
        if self.get_corner_swap_count(debug) % 2 == 1:
            return True
        return False

    def get_edge_swap_count(self, orbit, debug=False):
        needed_edges = []
        to_check = []
        edges_per_side = len(self.sideU.edge_north_pos)

        # Upper
        for (edge_index, square_index) in enumerate(self.sideU.edge_north_pos):
            to_check.append(square_index)
            needed_edges.append('UB')
            break

        for (edge_index, square_index) in enumerate(reversed(self.sideU.edge_west_pos)):
            to_check.append(square_index)
            needed_edges.append('UL')
            break

        for (edge_index, square_index) in enumerate(reversed(self.sideU.edge_south_pos)):
            to_check.append(square_index)
            needed_edges.append('UF')
            break

        for (edge_index, square_index) in enumerate(self.sideU.edge_east_pos):
            to_check.append(square_index)
            needed_edges.append('UR')
            break

        # Left
        for (edge_index, square_index) in enumerate(reversed(self.sideL.edge_west_pos)):
            to_check.append(square_index)
            needed_edges.append('LB')
            break

        for (edge_index, square_index) in enumerate(self.sideL.edge_east_pos):
            to_check.append(square_index)
            needed_edges.append('LF')
            break

        # Right
        for (edge_index, square_index) in enumerate(reversed(self.sideR.edge_west_pos)):
            to_check.append(square_index)
            needed_edges.append('RF')
            break

        for (edge_index, square_index) in enumerate(self.sideR.edge_east_pos):
            to_check.append(square_index)
            needed_edges.append('RB')
            break

        # Down
        for (edge_index, square_index) in enumerate(self.sideD.edge_north_pos):
            to_check.append(square_index)
            needed_edges.append('DF')
            break

        for (edge_index, square_index) in enumerate(reversed(self.sideD.edge_west_pos)):
            to_check.append(square_index)
            needed_edges.append('DL')
            break

        for (edge_index, square_index) in enumerate(reversed(self.sideD.edge_south_pos)):
            to_check.append(square_index)
            needed_edges.append('DB')
            break

        for (edge_index, square_index) in enumerate(self.sideD.edge_east_pos):
            to_check.append(square_index)
            needed_edges.append('DR')
            break

        if debug:
            to_check_str = ''

            for x in to_check:
                to_check_str += "%3s" % x

            log.info("to_check     :%s" % to_check_str)
            log.info("needed edges : %s" % ' '.join(needed_edges))

        current_edges = []

        for square_index in to_check:
            side = self.get_side(square_index)
            partner_index = side.get_wing_partner(square_index)
            square1 = self.get_square(square_index)
            square2 = self.get_square(partner_index)

            if square1.side_name in ('U', 'D'):
                wing_str = square1.side_name + square2.side_name
            elif square2.side_name in ('U', 'D'):
                wing_str = square2.side_name + square1.side_name
            elif square1.side_name in ('L', 'R'):
                wing_str = square1.side_name + square2.side_name
            elif square2.side_name in ('L', 'R'):
                wing_str = square2.side_name + square1.side_name
            else:
                raise Exception("Could not determine wing_str for (%s, %s)" % (square1, square2))

            current_edges.append(wing_str)

        if debug:
            log.info("current edges: %s" % ' '.join(current_edges))

        return get_swap_count(needed_edges, current_edges, debug)

    def edge_swaps_even(self, orbit, debug):
        if self.get_edge_swap_count(orbit, debug) % 2 == 0:
            return True
        return False

    def edge_swaps_odd(self, orbit, debug):
        if self.get_edge_swap_count(orbit, debug) % 2 == 1:
            return True
        return False

    def validate_all_corners_found(self):
        needed_corners = [
            'BLU',
            'BRU',
            'FLU',
            'FRU',
            'DFL',
            'DFR',
            'BDL',
            'BDR']

        to_check = [
            (self.sideU.corner_pos[0], self.sideL.corner_pos[0], self.sideB.corner_pos[1]), # ULB
            (self.sideU.corner_pos[1], self.sideR.corner_pos[1], self.sideB.corner_pos[0]), # URB
            (self.sideU.corner_pos[2], self.sideL.corner_pos[1], self.sideF.corner_pos[0]), # ULF
            (self.sideU.corner_pos[3], self.sideF.corner_pos[1], self.sideR.corner_pos[0]), # UFR
            (self.sideD.corner_pos[0], self.sideL.corner_pos[3], self.sideF.corner_pos[2]), # DLF
            (self.sideD.corner_pos[1], self.sideF.corner_pos[3], self.sideR.corner_pos[2]), # DFR
            (self.sideD.corner_pos[2], self.sideL.corner_pos[2], self.sideB.corner_pos[3]), # DLB
            (self.sideD.corner_pos[3], self.sideR.corner_pos[3], self.sideB.corner_pos[2])  # DRB
        ]

        current_corners = []
        for (square_index1, square_index2, square_index3) in to_check:
            square1 = self.get_square(square_index1)
            square2 = self.get_square(square_index2)
            square3 = self.get_square(square_index3)
            corner_str = ''.join(sorted([square1.side_name, square2.side_name, square3.side_name]))
            current_corners.append(corner_str)

        # We need a way to validate all of the needed_corners are present and
        # if not, what do we flip so that we do have all of the needed corners?
        for corner in needed_corners:
            if corner not in current_corners:
                raise Exception("corner %s is missing".format(corner))

    def validate_odd_cube_midge_vs_corner_parity(self):
        """
        http://www.ryanheise.com/cube/parity.html

        When considering the permutation of all edges and corners together, the
        overall parity must be even, as dictated by laws of the cube. However,
        when considering only edges or corners alone, it is possible for their
        parity to be either even or odd. To obey the laws of the cube, if the edge
        parity is even then the corner parity must also be even, and if the edge
        parity is odd then the corner parity must also be odd.
        """

        if self.even:
            return

        # TODO add support for 555 and 777
        if self.width != 3:
            return

        debug = False

        try:
            edges_even = self.edge_swaps_even(None, debug)
            corners_even = self.corner_swaps_even(debug)

            if edges_even == corners_even:
                return

            log.warning("edges_even %s != corners_even %s, swap most ambiguous orange or red edges to create valid parity" % (edges_even, corners_even))

        except ListMissingValue:
            log.warning("Either edges or corners are off, swap most ambiguous orange or red edges to create valid parity")

        # Reasonable assumptions we can make about why our parity is off:
        # - we have a red vs orange backwards somewhere
        # - the error will be made on an edge, not a corner.  Corners are much easier to get
        #   correct because once you have correctly IDed green, white, blue and yellow you
        #   can figure out which corner squares are red and which are orange.  Green, white,
        #   yellow and blue are easy to get correct so it is extremely rare for us to mislabel
        #   a corner
        green_orange_position = None
        green_red_position = None
        blue_orange_position = None
        blue_red_position = None

        for side in (self.sideU, self.sideL, self.sideF, self.sideR, self.sideB, self.sideD):
            for square in side.edge_squares:
                partner_position = side.get_wing_partner(square.position)
                partner = self.get_square(partner_position)

                if square.color_name == "Gr" and partner.color_name == "OR":
                    green_orange_position = partner_position
                elif square.color_name == "Gr" and partner.color_name == "Rd":
                    green_red_position = partner_position
                elif square.color_name == "Bu" and partner.color_name == "OR":
                    blue_orange_position = partner_position
                elif square.color_name == "Bu" and partner.color_name == "Rd":
                    blue_red_position = partner_position

        log.debug("green_orange_position %s".format(green_orange_position))
        log.debug("green_red_position %s".format(green_red_position))
        log.debug("blue_orange_position %s".format(blue_orange_position))
        log.debug("blue_red_position %s".format(blue_red_position))

        square_green_orange = self.get_square(green_orange_position)
        square_green_red = self.get_square(green_red_position)
        square_blue_orange = self.get_square(blue_orange_position)
        square_blue_red = self.get_square(blue_red_position)

        # To correct the parity we can swap orange/red for the green edges or
        # we can swap orange/red for the blue edges. Which will result in the
        # lowest color distance with our orange/red baselines?
        distance_swap_green_edge = 0
        distance_swap_green_edge += get_lab_distance(square_blue_orange.lab, self.orange_baseline)
        distance_swap_green_edge += get_lab_distance(square_blue_red.lab, self.red_baseline)
        distance_swap_green_edge += get_lab_distance(square_green_orange.lab, self.red_baseline)
        distance_swap_green_edge += get_lab_distance(square_green_red.lab, self.orange_baseline)

        distance_swap_blue_edge = 0
        distance_swap_blue_edge += get_lab_distance(square_green_orange.lab, self.orange_baseline)
        distance_swap_blue_edge += get_lab_distance(square_green_red.lab, self.red_baseline)
        distance_swap_blue_edge += get_lab_distance(square_blue_orange.lab, self.red_baseline)
        distance_swap_blue_edge += get_lab_distance(square_blue_red.lab, self.orange_baseline)

        log.info("distance_swap_green_edge %s" % distance_swap_green_edge)
        log.info("distance_swap_blue_edge %s" % distance_swap_blue_edge)

        if distance_swap_green_edge < distance_swap_blue_edge:
            log.warning("edge parity correction: change %s from %s to Rd" % (square_green_orange, square_green_orange.color_name))
            log.warning("edge parity correction: change %s from %s to OR" % (square_green_red, square_green_red.color_name))
            square_green_orange.color_name = "Rd"
            square_green_red.color_name = "OR"
            square_green_orange.side_name = self.color_to_side_name[square_green_orange.color_name]
            square_green_red.side_name = self.color_to_side_name[square_green_red.color_name]
        else:
            log.warning("edge parity correction: change %s from %s to Rd" % (square_blue_orange, square_blue_orange.color_name))
            log.warning("edge parity correction: change %s from %s to OR" % (square_blue_red, square_blue_red.color_name))
            square_blue_orange.color_name = "Rd"
            square_blue_red.color_name = "OR"
            square_blue_orange.side_name = self.color_to_side_name[square_blue_orange.color_name]
            square_blue_red.side_name = self.color_to_side_name[square_blue_red.color_name]

        edges_even = self.edge_swaps_even(None, debug)
        corners_even = self.corner_swaps_even(debug)
        assert edges_even == corners_even, "parity is still broken, edges_even %s, corners_even %s" % (edges_even, corners_even)

    def crunch_colors(self):
        self.write_cube("Initial RGB values", False)

        self.resolve_color_box()
        self.write_color_box()

        # corners
        self.resolve_corner_squares()

        # centers
        self.resolve_center_squares()

        # edges
        self.resolve_edge_squares()
        self.set_state()
        self.sanity_check_edge_squares()
        self.validate_all_corners_found()
        self.validate_odd_cube_midge_vs_corner_parity()

        self.write_cube("Final Cube", True)
        self.print_cube()
        self.www_footer()


def resolve_colors(argv):
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

    while argv_index < len(argv):

        if argv[argv_index] == "--help":
            print(help_string)
            sys.exit(0)

        elif argv[argv_index] == "--filename":
            filename = argv[argv_index + 1]
            argv_index += 2

        elif argv[argv_index] == "--rgb":
            rgb = argv[argv_index + 1]
            argv_index += 2

        elif argv[argv_index] == "--json" or argv[argv_index] == "-j":
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
