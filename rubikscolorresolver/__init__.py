
from tsp_solver.greedy import solve_tsp
from collections import OrderedDict
from itertools import combinations, permutations
from math import atan2, cos, degrees, exp, radians, sin
from math import sqrt, ceil
from pprint import pformat
from statistics import median, mean
from json import dumps as json_dumps
import logging
import os
import sys

log = logging.getLogger(__name__)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

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
    3 : {
        0: ((2, 38), (4, 11), (6, 29), (8, 20),
            (13, 42), (15, 22),
            (31, 24), (33, 40),
            (47, 26), (49, 17), (51, 35), (53, 44)),
    },

    4 : {
        0: ((2, 67), (3, 66), (5, 18), (9, 19), (8, 51), (12, 50), (14, 34), (15, 35),
            (21, 72), (25, 76), (24, 37), (28, 41),
            (53, 40), (57, 44), (56, 69), (60, 73),
            (82, 46), (83, 47), (85, 31), (89, 30), (88, 62), (92, 63), (94, 79), (95, 78)),
    },

    5 : {
        # orbit 0
        0: ((2, 104), (4, 102), (6, 27), (16, 29), (10, 79), (20, 77), (22, 52), (24, 54),
            (31, 110), (41, 120), (35, 56), (45, 66),
            (81, 60), (91, 70), (85, 106), (95, 116),
            (72, 127), (74, 129), (131, 49), (141, 47), (135, 97), (145, 99), (147, 124), (149, 122)),

        # orbit 1
        1: ((3, 103), (11, 28), (15, 78), (23, 53),
            (36, 115), (40, 61),
            (86, 65), (90, 111),
            (128, 73), (136, 48), (140, 98), (148, 123)),
    },

    6 : {
        # orbit 0
        0: ((2, 149), (5, 146), (7, 38), (25, 41), (12, 113), (30, 110), (32, 74), (35, 77),
            (43, 156), (61, 174), (48, 79), (66, 97),
            (115, 84), (133, 102), (120, 151), (138, 169),
            (182, 104), (185, 107), (187, 71), (205, 68), (192, 140), (210, 143), (212, 179), (215, 176),
        ),

        # orbit 1
        1: ((3, 148), (4, 147), (13, 39), (19, 40), (18, 112), (24, 111), (33, 75), (34, 76),
            (49, 162), (55, 168), (54, 85), (60, 91),
            (90, 121), (96, 127), (126, 157), (132, 163),
            (183, 105), (184, 106), (193, 70), (199, 69), (198, 141), (204, 142), (213, 178), (214, 177),
        ),
    }
}

center_groups = {
    3: (
        ("centers", (5, 14, 23, 32, 41, 50)),
    ),
    4: (
        ("centers", (
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
HTML_FILENAME = os.path.join(HTML_DIRECTORY, 'index.html')


def get_euclidean_lab_distance(lab1, lab2):
    """
    http://www.w3resource.com/python-exercises/math/python-math-exercise-79.php

    In mathematics, the Euclidean distance or Euclidean metric is the "ordinary"
    (i.e. straight-line) distance between two points in Euclidean space. With this
    distance, Euclidean space becomes a metric space. The associated norm is called
    the Euclidean norm.
    """
    lab1_tuple = (lab1.L, lab1.a, lab1.b)
    lab2_tuple = (lab2.L, lab2.a, lab2.b)
    return sqrt(sum([(a - b) ** 2 for a, b in zip(lab1_tuple, lab2_tuple)]))


def find_index_for_value(list_foo, target, min_index):
    for (index, value) in enumerate(list_foo):
        if value == target and index >= min_index:
            return index
    raise Exception("Did not find %s in list %s" % (target, pformat(list_foo)))


def traveling_salesman(squares, alg, endpoints=None):

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

            else:
                raise Exception("Implement {}".format(alg))

            matrix[x][y] = distance
            matrix[y][x] = distance

    path = solve_tsp(matrix, endpoints=endpoints)
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
    #log.info("first    squares: %s" % pformat(first_squares))
    #log.info("last     squares: %s" % pformat(last_squares))
    #log.info("last UBD squares: %s" % pformat(last_UBD_squares))
    return (first_squares, last_squares, last_UBD_squares)


class LabColor(object):

    def __init__(self, L, a, b, red, green, blue):
        self.L = L
        self.a = a
        self.b = b
        self.red = red
        self.green = green
        self.blue = blue
        self.name = None

    def __str__(self):
        return ("Lab (%s, %s, %s)" % (self.L, self.a, self.b))

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return self.name < other.name


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

    avg_lp = (l1 + l2) / 2.0
    c1 = sqrt(pow(a1, 2) + pow(b1, 2))
    c2 = sqrt(pow(a2, 2) + pow(b2, 2))
    avg_c = (c1 + c2) / 2.0
    g = (1 - sqrt(pow(avg_c, 7) / (pow(avg_c, 7) + pow(25, 7)))) / 2.0
    a1p = a1 * (1 + g)
    a2p = a2 * (1 + g)
    c1p = sqrt(pow(a1p, 2) + pow(b1, 2))
    c2p = sqrt(pow(a2p, 2) + pow(b2, 2))
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
    s_l = 1 + ((0.015 * pow(avg_lp - 50, 2)) / sqrt(20 + pow(avg_lp - 50, 2)))
    s_c = 1 + 0.045 * avg_cp
    s_h = 1 + 0.015 * avg_cp * t

    delta_ro = 30 * exp(-(pow((avg_hp - 275) / 25.0, 2)))
    r_c = 2 * sqrt(pow(avg_cp, 7) / (pow(avg_cp, 7) + pow(25, 7)))
    r_t = -r_c * sin(2 * radians(delta_ro))
    kl = 1.0
    kc = 1.0
    kh = 1.0
    delta_e = sqrt(pow(delta_lp / (s_l * kl), 2) +
                   pow(delta_cp / (s_c * kc), 2) +
                   pow(delta_hp / (s_h * kh), 2) +
                   r_t * (delta_cp / (s_c * kc)) * (delta_hp / (s_h * kh)))

    return delta_e


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
        distance += get_euclidean_lab_distance(baseline_lab, square.lab)
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
        self.color = None
        self.color_name = None

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
        self.center_pos = []

        for position in range(self.min_pos, self.max_pos):
            if position in self.corner_pos:
                pass

            # Edges at the north
            elif position > self.corner_pos[0] and position < self.corner_pos[1]:
                self.edge_pos.append(position)

            # Edges at the south
            elif position > self.corner_pos[2] and position < self.corner_pos[3]:
                self.edge_pos.append(position)

            elif (position - 1) % self.width == 0:
                west_edge = position
                east_edge = west_edge + self.width - 1

                # Edges on the west
                self.edge_pos.append(west_edge)

                # Edges on the east
                self.edge_pos.append(east_edge)

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

        if self.width % 2 == 0:
            self.even = True
            self.odd = False
        else:
            self.even = False
            self.odd = True

        if not os.path.exists(HTML_DIRECTORY):
            os.makedirs(HTML_DIRECTORY)
            os.chmod(HTML_DIRECTORY, 0o777)

        with open(HTML_FILENAME, 'w') as fh:
            pass
        os.chmod(HTML_FILENAME, 0o777)

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

        self.crayola_colors = {
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
                fh.write("<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%d</span>\n" %
                    (red, green, blue,
                     red, green, blue,
                     int(square.lab.L), int(square.lab.a), int(square.lab.b),
                     square.color_name,
                     square.position))

                count += 1

                if count % squares_per_row == 0:
                    fh.write("<br>")
            fh.write("</div>\n")

    def find_white_squares(self):
        all_squares = []
        for side in (self.sideU, self.sideL, self.sideF, self.sideR, self.sideB, self.sideD):
            for square in side.squares.values():
                all_squares.append(square)

        sorted_all_squares = traveling_salesman(all_squares, "euclidean")
        self.write_colors(
            'finding white colors',
            sorted_all_squares)

        # There are six "rows" of colors, which row is the closest to pure white?
        white_lab = rgb2lab(WHITE)
        row_distances = get_row_color_distances(sorted_all_squares, [white_lab] * 6)
        log.debug(f"row_distances {row_distances}")
        min_distance = 99999
        min_distance_row_index = None

        for (row_index, distance) in enumerate(row_distances):
            if distance < min_distance:
                min_distance = distance
                min_distance_row_index = row_index

        self.white_squares = get_squares_for_row(sorted_all_squares, min_distance_row_index)
        self.white_squares.sort()

        with open(HTML_FILENAME, 'a') as fh:
            fh.write("<h2>white squares</h2>\n")
            fh.write("<div class='clear colors'>\n")

            for square in self.white_squares:
                (red, green, blue) = square.rgb
                fh.write("<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%d</span>\n" %
                    (red, green, blue,
                     red, green, blue,
                     int(square.lab.L), int(square.lab.a), int(square.lab.b),
                     square.color_name,
                     square.position))

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
            #log.info("center_squares: %s" % pformat(center_squares))

            for permutation in odd_cube_center_color_permutations:
                distance = 0

                for (index, center_square) in enumerate(center_squares):
                    color_name = permutation[index]
                    color_obj = self.crayola_colors[color_name]
                    distance += get_euclidean_lab_distance(center_square.lab, color_obj)

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

    def cube_for_kociemba_strict(self):
        log.info("color_to_side_name:\n{}\n".format(pformat(self.color_to_side_name)))
        data = []
        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]
                data.append(self.color_to_side_name[square.color_name])
                #data.append(self.state[x])

        return data

    def cube_for_json(self):
        """
        Return a dictionary of the cube data so that we can json dump it
        """
        data = {}
        data['kociemba'] = ''.join(self.cube_for_kociemba_strict())
        data['sides'] = {}
        data['squares'] = {}

        for side in self.sides.values():
            data['sides'][side.name] = {
                'colorName' : side.color_name,
                'colorHTML' : html_color[side.color_name]
            }

        #log.info("color_to_side_name:\n{}\n".format(pformat(self.color_to_side_name)))

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]
                color = square.color_name
                data['squares'][square.position] = {
                    'finalSide' : self.color_to_side_name[color]
                }

        return data

    def assign_color_names(self, desc, squares_lists_all):

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
        # terms of the assigned color name vs. the colors in crayola_colors.
        min_distance = None
        min_distance_permutation = None

        if self.odd and desc == "centers":
            crayola_color_permutations = odd_cube_center_color_permutations
        else:
            crayola_color_permutations = permutations(self.crayola_colors.keys())

        for permutation in crayola_color_permutations:
            distance = 0

            for (index, squares_list) in enumerate(squares_lists):
                color_name = permutation[index]
                crayola_color_lab = self.crayola_colors[color_name]

                for square in squares_list:
                    distance += get_euclidean_lab_distance(square.lab, crayola_color_lab)

            if min_distance is None or distance < min_distance:
                min_distance = distance
                min_distance_permutation = permutation

                '''
                if desc == "centers":
                    log.info("{} PERMUTATION {}, DISTANCE {:,} (NEW MIN)".format(desc, permutation, int(distance)))
            else:
                if desc == "centers":
                    log.info("{} PERMUTATION {}, DISTANCE {}".format(desc, permutation, distance))
                '''

        # Assign the color name to the Square object
        for (index, squares_list) in enumerate(squares_lists):
            color_name = min_distance_permutation[index]

            for square in squares_list:
                square.color_name = color_name
                #log.info("%s SQUARE %s color_name is now %s" % (desc, square, square.color_name))

                # dwalton what about for even cubes?
                # Odd cubes are awesome because we can easily find one square of each color by
                # looking at the square in the exact center.
                if self.odd and desc == "centers":
                    #log.warning(f"update crayola_colors[{color_name}] from {self.crayola_colors[color_name]} to {square.lab}")
                    self.crayola_colors[color_name] = square.lab

    def validate_edge_orbit(self, orbit_id):
        valid = True

        # We need to see which orange/red we can flip that will make the edges valid
        wing_pair_counts = {}

        # TODO do this for 7x7x7
        if self.width not in edge_orbit_wing_pairs:
            log.warning("*" * 50)
            log.warning("%s not in edge_orbit_wing_pairs" % self.width)
            log.warning("*" * 50)
            return True

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
            log.info("wing_pair_counts:\n{}\n".format(pformat(wing_pair_counts)))
            log.warning("valid: {}".format(valid))

        #assert valid, "Cube is invalid"
        return valid

    def sanity_check_edge_corner_for_orbit(self, target_orbit_id):

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
                raise Exception(f"There should be either 2 or 4 but we have {target_color_red_or_orange_edges}")

            min_distance = None
            min_distance_permutation = None

            for red_orange_permutation in red_orange_permutations:
                distance = 0

                for (index, (target_color_square, partner_square)) in enumerate(target_color_red_or_orange_edges):
                    red_orange = red_orange_permutation[index]

                    if red_orange == "OR":
                        distance += get_euclidean_lab_distance(partner_square.lab, self.orange_baseline)
                    elif red_orange == "Rd":
                        distance += get_euclidean_lab_distance(partner_square.lab, self.red_baseline)
                    else:
                        raise Exception(red_orange)

                if min_distance is None or distance < min_distance:
                    min_distance = distance
                    min_distance_permutation = red_orange_permutation
                    log.info(f"target edge {target_color}, red_orange_permutation {red_orange_permutation}, distance {distance} (NEW MIN)")
                else:
                    log.info(f"target edge {target_color}, red_orange_permutation {red_orange_permutation}, distance {distance}")

            # TODO this needs to consider the number of high/low edges in the orbit also so that
            # we do not create an invalid cube
            log.info(f"min_distance_permutation {min_distance_permutation}")
            for (index, (target_color_square, partner_square)) in enumerate(target_color_red_or_orange_edges):
                if partner_square.color_name != min_distance_permutation[index]:
                    log.warning("change %s edge partner %s from %s to %s" %
                        (target_color, partner_square, partner_square.color_name, min_distance_permutation[index]))
                    partner_square.color_name = min_distance_permutation[index]
                else:
                    log.info("%s edge partner %s is %s" %
                        (target_color, partner_square, partner_square.color_name))

            log.info("\n\n")

        green_red_orange_color_names = ("Gr", "Rd", "OR")
        blue_red_orange_color_names = ("Bu", "Rd", "OR")
        white_red_orange_color_names = ("Wh", "Rd", "OR")
        yellow_red_orange_color_names = ("Ye", "Rd", "OR")
        green_red_or_orange_edges = []
        blue_red_or_orange_edges = []
        white_red_or_orange_edges = []
        yellow_red_or_orange_edges = []

        for (square_index, partner_index) in edge_orbit_wing_pairs[self.width][target_orbit_id]:
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

        log.info(f"green_red_or_orange_edges {green_red_or_orange_edges}")
        fix_orange_vs_red_for_color('green', green_red_or_orange_edges)

        log.info(f"blue_red_or_orange_edges {blue_red_or_orange_edges}")
        fix_orange_vs_red_for_color('blue', blue_red_or_orange_edges)

        log.info(f"white_red_or_orange_edges {white_red_or_orange_edges}")
        fix_orange_vs_red_for_color('white', white_red_or_orange_edges)

        log.info(f"yellow_red_or_orange_edges {yellow_red_or_orange_edges}")
        fix_orange_vs_red_for_color('yellow', yellow_red_or_orange_edges)

        # TODO we need to validate parity if this is a 3x3x3, if parity is off figure out which OR/Rd edge
        # squares to swap to create valid parity. I think the same would apply for 5x5x5 and 7x7x7.
        self.validate_edge_orbit(target_orbit_id)

    def resolve_edge_squares(self):
        """
        Use traveling salesman algorithm to sort the colors
        """

        # Nothing to be done for 2x2x2
        if self.width == 2:
            return True

        for target_orbit_id in range(self.orbits):
            log.info('Resolve edges for orbit %d' % target_orbit_id)
            edge_squares = []

            for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
                for square in side.edge_squares:
                    orbit_id = edge_orbit_id[self.width][square.position]
                    #log.info("{}: {}, position {}, orbit_id {}".format(self.width, square, square.position, orbit_id))

                    if orbit_id == target_orbit_id:
                        edge_squares.append(square)

            sorted_edge_squares = traveling_salesman(edge_squares, "euclidean")
            self.assign_color_names('edge orbit %d' % target_orbit_id, sorted_edge_squares)
            self.write_colors(
                'edges - orbit %d' % target_orbit_id,
                sorted_edge_squares)

            log.info("\n\n")

    def sanity_check_edge_squares(self):

        # Nothing to be done for 2x2x2
        if self.width == 2:
            return True

        for orbit_id in range(self.orbits):
            self.sanity_check_edge_corner_for_orbit(orbit_id)

    def assign_green_white_corners(self, green_white_corners):
        #log.info("Gr/Wh corner tuples %s" % pformat(green_white_corners))
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
        #log.info("Bu/Wh corner tuples %s" % pformat(blue_white_corners))
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

    def resolve_corner_squares(self):
        """
        Use traveling salesman algorithm to sort the colors
        """
        log.info('Resolve corners')
        corner_squares = []

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for square in side.corner_squares:
                corner_squares.append(square)

        sorted_corner_squares = traveling_salesman(corner_squares, "euclidean")
        self.assign_color_names('corners', sorted_corner_squares)
        self.write_colors('corners', sorted_corner_squares)

    def sanity_check_corner_squares(self):
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

        self.assign_green_white_corners(green_white_corners)
        self.assign_green_yellow_corners(green_yellow_corners)
        self.assign_blue_white_corners(blue_white_corners)
        self.assign_blue_yellow_corners(blue_yellow_corners)

    def find_orange_and_red_baselines(self):

        # The ORANGE/RED baselines are only used for sanity checking edges
        # so we can return here for 2x2x2
        if self.width == 2:
            return
        elif self.width in (3, 4, 5, 7):
            centers_for_red_orange_baseline = "centers"
        elif self.width == 6:
            centers_for_red_orange_baseline = "inner x-centers"
        else:
            raise Exception("What centers to use for orange/red baseline?")

        for (desc, centers_squares) in center_groups[self.width]:
            if desc != centers_for_red_orange_baseline:
                continue

            orange_reds = []
            orange_greens = []
            orange_blues = []
            red_reds = []
            red_greens = []
            red_blues = []

            for index in centers_squares:
                square = self.get_square(index)

                if square.color_name == "OR":
                    orange_reds.append(square.red)
                    orange_greens.append(square.green)
                    orange_blues.append(square.blue)

                elif square.color_name == "Rd":
                    red_reds.append(square.red)
                    red_greens.append(square.green)
                    red_blues.append(square.blue)

            new_orange_red = int(mean(orange_reds))
            new_orange_green = int(mean(orange_greens))
            new_orange_blue = int(mean(orange_blues))
            self.orange_baseline = rgb2lab((new_orange_red, new_orange_green, new_orange_blue))

            new_red_red = int(mean(red_reds))
            new_red_green = int(mean(red_greens))
            new_red_blue = int(mean(red_blues))
            self.red_baseline = rgb2lab((new_red_red, new_red_green, new_red_blue))

            log.warning("ORANGE: %s" % self.orange_baseline)
            log.warning("RED: %s" % self.red_baseline)

            with open(HTML_FILENAME, 'a') as fh:
                fh.write("<h2>ORANGE baseline</h2>\n")
                fh.write("<div class='clear colors'>\n")
                fh.write("<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%d</span>\n" %
                    (new_orange_red, new_orange_green, new_orange_blue,
                     new_orange_red, new_orange_green, new_orange_blue,
                     int(self.orange_baseline.L), int(self.orange_baseline.a), int(self.orange_baseline.b),
                     'OR',
                     0))
                fh.write("<br>")
                fh.write("</div>\n")

                fh.write("<h2>RED baseline</h2>\n")
                fh.write("<div class='clear colors'>\n")
                fh.write("<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%d</span>\n" %
                    (new_red_red, new_red_green, new_red_blue,
                     new_red_red, new_red_green, new_red_blue,
                     int(self.red_baseline.L), int(self.red_baseline.a), int(self.red_baseline.b),
                     'Rd',
                     0))
                fh.write("<br>")
                fh.write("</div>\n")

    def resolve_center_squares(self):
        """
        Use traveling salesman algorithm to sort the squares by color
        """

        # Nothing to be done for 2x2x2
        if self.width == 2:
            return

        for (desc, centers_squares) in center_groups[self.width]:
            log.info('Resolve {}'.format(desc))
            center_squares = []

            for position in centers_squares:
                square = self.get_square(position)
                center_squares.append(square)

            if len(centers_squares) == 6:
                sorted_center_squares = center_squares[:]
            else:
                sorted_center_squares = traveling_salesman(center_squares, "euclidean")

            self.assign_color_names(desc, sorted_center_squares)
            self.write_colors(desc, sorted_center_squares)

    def contrast_stretch(self):
        white_reds = []
        white_greens = []
        white_blues = []
        all_squares = []

        for side in (self.sideU, self.sideL, self.sideF, self.sideR, self.sideB, self.sideD):
            side_squares = side.corner_squares + side.center_squares + side.edge_squares
            for square in side_squares:
                all_squares.append(square)

        min_input_red = 255
        min_input_green = 255
        min_input_blue = 255
        max_input_red = 0
        max_input_green = 0
        max_input_blue = 0
        darkest_white_red = 255
        darkest_white_green = 255
        darkest_white_blue = 255

        for square in all_squares:
            (red, green, blue) = square.rgb

            if red < min_input_red:
                min_input_red = red

            if red > max_input_red:
                max_input_red = red

            if green < min_input_green:
                min_input_green = green

            if green > max_input_green:
                max_input_green = green

            if blue < min_input_blue:
                min_input_blue = blue

            if blue > max_input_blue:
                max_input_blue = blue

        for square in self.white_squares:
            (red, green, blue) = square.rgb
            white_reds.append(red)
            white_greens.append(green)
            white_blues.append(blue)

            if red < darkest_white_red:
                darkest_white_red = red

            if green < darkest_white_green:
                darkest_white_green = green

            if blue < darkest_white_blue:
                darkest_white_blue = blue

        log.debug(f"min_input_red {min_input_red}, max_input_red {max_input_red}")
        log.debug(f"min_input_green {min_input_green}, max_input_green {max_input_green}")
        log.debug(f"min_input_blue {min_input_blue}, max_input_blue {max_input_blue}")
        min_output_red = 30
        min_output_green = 30
        min_output_blue = 30
        max_output_red = 255
        max_output_green = 255
        max_output_blue = 255

        white_reds.sort()
        white_greens.sort()
        white_blues.sort()
        avg_white_red = int(sum(white_reds) / len(white_reds))
        avg_white_green = int(sum(white_greens) / len(white_greens))
        avg_white_blue = int(sum(white_blues) / len(white_blues))
        median_white_red = median(white_reds)
        median_white_green = median(white_greens)
        median_white_blue = median(white_blues)
        log.debug(f"WHITE reds {white_reds},  avg {avg_white_red}, median {median_white_red}")
        log.debug(f"WHITE greens {white_greens},  avg {avg_white_green}, median {median_white_green}")
        log.debug(f"WHITE blues {white_blues},  avg {avg_white_blue}, median {median_white_blue}")

        with open(HTML_FILENAME, 'a') as fh:
            fh.write("<h2>Mean white square</h2>\n")
            fh.write("<div class='clear colors'>\n")
            lab = rgb2lab((avg_white_red, avg_white_green, avg_white_blue))

            fh.write("<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%d</span>\n" %
                (avg_white_red, avg_white_green, avg_white_blue,
                 avg_white_red, avg_white_green, avg_white_blue,
                 int(lab.L), int(lab.a), int(lab.b),
                 'Wh',
                 0))
            fh.write("<br>")
            fh.write("</div>\n")

        max_input_red = avg_white_red
        max_input_green = avg_white_green
        max_input_blue = avg_white_blue
        #max_input_red = median_white_red
        #max_input_green = median_white_green
        #max_input_blue = median_white_blue
        #max_input_red = darkest_white_red
        #max_input_green = darkest_white_green
        #max_input_blue = darkest_white_blue

        for square in all_squares:
            # https://pythontic.com/image-processing/pillow/contrast%20stretching
            # iO = (iI - minI) * (( (maxO - minO) / (maxI - minI)) + minO)
            new_red = int((square.red - min_input_red) * (max_output_red / (max_input_red - min_input_red)))
            new_green = int((square.green - min_input_green) * (max_output_green / (max_input_green - min_input_green)))
            new_blue = int((square.blue - min_input_blue) * (max_output_blue / (max_input_blue - min_input_blue)))

            #new_red = int((square.red - min_input_red) * (((max_output_red - min_output_red) / (max_input_red - min_input_red)) + min_output_red))
            #new_green = int((square.green - min_input_green) * (((max_output_green - min_output_green) / (max_input_green - min_input_green)) + min_output_green))
            #new_blue = int((square.blue - min_input_blue) * (((max_output_blue - min_output_blue) / (max_input_blue - min_input_blue)) + min_output_blue))

            new_red = min(max_output_red, new_red)
            new_green = min(max_output_green, new_green)
            new_blue = min(max_output_blue, new_blue)
            delta_to_add = 0

            if new_red < min_output_red:
                delta_to_add = max(delta_to_add, min_output_red - new_red)

            if new_green < min_output_green:
                delta_to_add = max(delta_to_add, min_output_green - new_green)

            if new_blue < min_output_blue:
                delta_to_add = max(delta_to_add, min_output_blue - new_blue)

            # Add enough so that red, green, and blue are all >= min_output_red, etc
            if delta_to_add:
                new_red += delta_to_add
                new_green += delta_to_add
                new_blue += delta_to_add

            new_red = min(max_output_red, new_red)
            new_green = min(max_output_green, new_green)
            new_blue = min(max_output_blue, new_blue)

            square.rgb = (new_red, new_green, new_blue)
            square.red = new_red
            square.green = new_green
            square.blue = new_blue
            square.lab = rgb2lab((new_red, new_green, new_blue))

    def crunch_colors(self):

        # Find all of the white squares
        self.write_cube("Initial RGB values", False)
        self.find_white_squares()

        # Now that we know what white looks like, contrast stretch the colors
        self.contrast_stretch()
        self.write_cube("Contrast Stretched RGB values", False)

        # Find baselines/anchor for each color
        #self.find_orange_and_red_baselines()

        self.resolve_center_squares()

        self.resolve_corner_squares()
        self.sanity_check_corner_squares()

        self.resolve_edge_squares()
        self.find_orange_and_red_baselines()
        self.sanity_check_edge_squares()

        self.set_state()
        self.write_cube("Final Cube", True)
        self.print_cube()
        self.www_footer()
