
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

log = logging.getLogger(__name__)

use_endpoints = False
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

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


def traveling_salesman(colors, alg, endpoints=None):

    # build a full matrix of color to color distances
    len_colors = len(colors)
    matrix = [[0 for i in range(len_colors)] for j in range(len_colors)]

    for x in range(len_colors):
        (_x_square_index, (x_red, x_green, x_blue)) = colors[x]
        x_lab = rgb2lab((x_red, x_green, x_blue))

        for y in range(len_colors):

            if x == y:
                matrix[x][y] = 0
                matrix[y][x] = 0
                continue

            if matrix[x][y] or matrix[y][x]:
                continue

            (_y_square_index, (y_red, y_green, y_blue)) = colors[y]
            y_lab = rgb2lab((y_red, y_green, y_blue))

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
    return [colors[x] for x in path]


class ClusterSquare(object):

    def __init__(self, index, rgb):
        self.index = index
        self.rgb = rgb
        self.lab = rgb2lab(rgb)

    def __str__(self):
        if self.index:
            return "CS" + str(self.index)
        else:
            return "CS" + str(self.rgb)

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return self.index < other.index


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


class Square(object):

    def __init__(self, side, cube, position, red, green, blue):
        self.cube = cube
        self.side = side
        self.position = position
        self.rgb = (red, green, blue)
        self.red = red
        self.green = green
        self.blue = blue
        self.rawcolor = rgb2lab((red, green, blue))
        self.color = None
        self.color_name = None

    def __str__(self):
        return "%s%d" % (self.side, self.position)

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return self.position < other.position


class CubeSide(object):

    def __init__(self, cube, width, name):
        self.cube = cube
        self.name = name  # U, L, etc
        self.color = None
        self.squares = {}
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

        #log.info("Side %s\n    min/max %d/%d\n    edges %s\n    corners %s\n    centers %s\n" %
        #    (self.name, self.min_pos, self.max_pos,
        #     " ".join(map(str, self.edge_pos)),
        #     " ".join(map(str, self.corner_pos)),
        #     " ".join(map(str, self.center_pos))))

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
            'U': CubeSide(self, self.width, 'U'),
            'L': CubeSide(self, self.width, 'L'),
            'F': CubeSide(self, self.width, 'F'),
            'R': CubeSide(self, self.width, 'R'),
            'B': CubeSide(self, self.width, 'B'),
            'D': CubeSide(self, self.width, 'D')
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
            #'Gr': hashtag_rgb_to_labcolor('#00FF00'),
            #'OR': hashtag_rgb_to_labcolor('#ff8c00'),
            #'Bu': hashtag_rgb_to_labcolor('#0000FF'),
            #'Rd': hashtag_rgb_to_labcolor('#FF0000')
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

    def write_cube(self, desc, cube):
        """
        'cube' is a list of (R,G,B) tuples
        """
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

                (red, green, blue) = cube[index]
                lab = rgb2lab((red, green, blue))

                fh.write("    <div class='square col%d' title='RGB (%d, %d, %d), Lab (%s, %s, %s)' style='background-color: #%02x%02x%02x;'><span>%02d</span></div>\n" %
                    (col,
                     red, green, blue,
                     int(lab.L), int(lab.a), int(lab.b),
                     red, green, blue,
                     index))

                if index in last_squares:
                    fh.write("</div>\n")

                    if index in last_UBD_squares:
                        fh.write("<div class='clear'></div>\n")

                col += 1

                if col == self.width + 1:
                    col = 1

    def write_white_squares(self):
        self.white_squares.sort()

        with open(HTML_FILENAME, 'a') as fh:
            fh.write("<h2>white squares</h2>\n")
            fh.write("<div class='clear colors'>\n")

            for white_square in self.white_squares:
                (red, green, blue) = white_square.rgb
                lab = rgb2lab((red, green, blue))

                fh.write("<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%d</span>\n" %
                    (red, green, blue,
                     red, green, blue,
                     int(lab.L), int(lab.a), int(lab.b),
                     white_square.color_name,
                     white_square.position))

            fh.write("<br>")
            fh.write("</div>\n")

    def write_colors(self, desc, colors):
        with open(HTML_FILENAME, 'a') as fh:
            squares_per_side = int(len(colors)/6)
            fh.write("<h2>%s</h2>\n" % desc)
            fh.write("<div class='clear colors'>\n")

            for cluster_square_list in colors:
                total_distance = 0

                for cluster_square in cluster_square_list:
                    (red, green, blue) = cluster_square.rgb
                    lab = rgb2lab((red, green, blue))
                    square = self.get_square(cluster_square.index)

                    fh.write("<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%d</span>\n" %
                        (red, green, blue,
                         red, green, blue,
                         int(lab.L), int(lab.a), int(lab.b),
                         square.color_name,
                         cluster_square.index))

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
        Given a position on the cube return the CubeSide object
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

    def write_cube2(self, desc):
        cube = ['dummy',]

        for side in (self.sideU, self.sideL, self.sideF, self.sideR, self.sideB, self.sideD):
            for position in range(side.min_pos, side.max_pos+1):
                square = side.squares[position]
                cube.append((square.red, square.green, square.blue))

        self.write_cube(desc, cube)

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
                    distance += get_euclidean_lab_distance(center_square.rawcolor, color_obj)

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

        self.state = ['placeholder', ]
        # log.info("color_to_side_name:\n %s\n" % pformat(self.color_to_side_name))

        for side_name in self.side_order:
            side = self.sides[side_name]

            # odd cube use the center square for each side
            if side.mid_pos:
                side.color_name = side.squares[side.mid_pos].color_name

            # even cube assume:
            # - white on top
            # - orange on left
            # - green on front
            # - red on right
            # - blue on back
            # - yellow on bottom
            else:
                if side.name == "U":
                    side.color_name = "Wh"
                elif side.name == "L":
                    side.color_name = "OR"
                elif side.name == "F":
                    side.color_name = "Gr"
                elif side.name == "R":
                    side.color_name = "Rd"
                elif side.name == "B":
                    side.color_name = "Bu"
                elif side.name == "D":
                    side.color_name = "Ye"

            for x in range(side.min_pos, side.max_pos + 1):
                color_name = side.squares[x].color_name
                # log.info("set_state(): side {}, x {}, color_name {}".format(side, x, color_name))
                self.state.append(self.color_to_side_name[color_name])

    def cube_for_kociemba_strict(self):
        data = []
        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                data.append(self.state[x])

        return data

    def cube_for_json(self):
        """
        Return a dictionary of the cube data so that we can json dump it
        """
        data = {}
        data['kociemba'] = ''.join(self.cube_for_kociemba_strict())
        data['sides'] = {}
        data['squares'] = {}

        html_color = {
            'Gr' : {'red' :   0, 'green' : 102, 'blue' : 0},
            'Bu' : {'red' :   0, 'green' :   0, 'blue' : 153},
            'OR' : {'red' : 255, 'green' : 102, 'blue' : 0},
            'Rd' : {'red' : 204, 'green' :   0, 'blue' : 0},
            'Wh' : {'red' : 255, 'green' : 255, 'blue' : 255},
            'Ye' : {'red' : 255, 'green' : 204, 'blue' : 0},
        }

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
                final_side = self.color_to_side_name[color]
                data['squares'][square.position] = {
                    #'colorScan' : {
                    #    'red'   : square.red,
                    #    'green' : square.green,
                    #    'blue'  : square.blue,
                    #},
                    'finalSide' : self.color_to_side_name[color]
                }

        return data

    def assign_color_names(self, desc, squares_lists):
        assert len(squares_lists) == 6, "There are %d squares_list, there should be 6" % len(squares_lists)
        #log.info("SQUARES_LIST:\n{}\n".format(pformat(squares_lists)))

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
                color_obj = self.crayola_colors[color_name]

                for cluster_square in squares_list:
                    distance += get_euclidean_lab_distance(cluster_square.lab, color_obj)

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

        for (index, squares_list) in enumerate(squares_lists):
            color_name = min_distance_permutation[index]

            for cluster_square in squares_list:
                cluster_square.color_name = color_name

                # Find the Square object for this ClusterSquare
                square = self.get_square(cluster_square.index)
                square.color_name = color_name
                # log.info("SQUARE %s color_name is now %s" % (square, square.color_name))

                if color_name == "Wh":
                    self.white_squares.append(square)

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

    def resolve_edge_squares(self, write_to_html, fix_orange_vs_red):
        """
        Use traveling salesman algorithm to sort the colors
        """

        # Nothing to be done for 2x2x2
        if self.width == 2:
            return True

        all_orbits_valid = True

        for target_orbit_id in range(self.orbits):
            log.info('Resolve edges for orbit %d' % target_orbit_id)
            edge_colors = []

            if use_endpoints:
                edge_colors.append((0, WHITE))
                edge_colors.append((999, BLACK))

            for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
                for square in side.edge_squares:
                    orbit_id = edge_orbit_id[self.width][square.position]
                    #log.info("{}: {}, position {}, orbit_id {}".format(self.width, square, square.position, orbit_id))

                    if orbit_id == target_orbit_id:
                        edge_colors.append((square.position, square.rgb))

            if use_endpoints:
                sorted_edge_colors = traveling_salesman(edge_colors, "euclidean", (0, 1))
                sorted_edge_colors.remove((0, WHITE))
                sorted_edge_colors.remove((999, BLACK))
            else:
                sorted_edge_colors = traveling_salesman(edge_colors, "euclidean")

            sorted_edge_colors_cluster_squares = []
            squares_list = []
            squares_per_cluster = int(len(sorted_edge_colors) / 6)

            for (index, (square_index, rgb)) in enumerate(sorted_edge_colors):
                index += 1
                squares_list.append(ClusterSquare(square_index, rgb))
                if index % squares_per_cluster == 0:
                    sorted_edge_colors_cluster_squares.append(squares_list)
                    squares_list = []

            self.assign_color_names('edge orbit %d' % target_orbit_id, sorted_edge_colors_cluster_squares)

            if write_to_html:
                self.write_colors(
                    'edges - orbit %d' % target_orbit_id,
                    sorted_edge_colors_cluster_squares)

            if fix_orange_vs_red:
                green_red_or_orange_edges = []
                blue_red_or_orange_edges = []
                white_red_or_orange_edges = []
                yellow_red_or_orange_edges = []
                green_red_orange_color_names = ("Gr", "Rd", "OR")
                blue_red_orange_color_names = ("Bu", "Rd", "OR")
                white_red_orange_color_names = ("Wh", "Rd", "OR")
                yellow_red_orange_color_names = ("Ye", "Rd", "OR")

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
                log.info(f"blue_red_or_orange_edges {blue_red_or_orange_edges}")
                log.info(f"white_red_or_orange_edges {white_red_or_orange_edges}")
                log.info(f"yellow_red_or_orange_edges {yellow_red_or_orange_edges}")

                # There must be one Gr/OR edge and one Gr/Rd. Assign based on which combo
                # has the least color distance vs our OR/Rd baselines.
                distance_OR_Rd = 0
                distance_OR_Rd += get_euclidean_lab_distance(green_red_or_orange_edges[0][1].rawcolor, self.orange_baseline)
                distance_OR_Rd += get_euclidean_lab_distance(green_red_or_orange_edges[1][1].rawcolor, self.red_baseline)

                distance_Rd_OR = 0
                distance_Rd_OR += get_euclidean_lab_distance(green_red_or_orange_edges[0][1].rawcolor, self.red_baseline)
                distance_Rd_OR += get_euclidean_lab_distance(green_red_or_orange_edges[1][1].rawcolor, self.orange_baseline)

                log.info(f"distance_OR_Rd {distance_OR_Rd}")
                log.info(f"distance_Rd_OR {distance_Rd_OR}")

                if distance_OR_Rd <= distance_Rd_OR:
                    if green_red_or_orange_edges[0][1].color_name != "OR":
                        log.warning("change green edge partner %s from %s to OR" %
                            (green_red_or_orange_edges[0][1], green_red_or_orange_edges[0][1].color_name))
                        green_red_or_orange_edges[0][1].color_name = "OR"

                    if green_red_or_orange_edges[1][1].color_name != "Rd":
                        log.warning("change green edge partner %s from %s to Rd" %
                            (green_red_or_orange_edges[1][1], green_red_or_orange_edges[1][1].color_name))
                        green_red_or_orange_edges[1][1].color_name = "Rd"
                else:
                    if green_red_or_orange_edges[0][1].color_name != "Rd":
                        log.warning("change green edge partner %s from %s to Rd" %
                            (green_red_or_orange_edges[0][1], green_red_or_orange_edges[0][1].color_name))
                        green_red_or_orange_edges[0][1].color_name = "Rd"

                    if green_red_or_orange_edges[1][1].color_name != "OR":
                        log.warning("change green edge partner %s from %s to OR" %
                            (green_red_or_orange_edges[1][1], green_red_or_orange_edges[1][1].color_name))
                        green_red_or_orange_edges[1][1].color_name = "OR"

                # There must be one Bu/OR edge and one Bu/Rd. Assign based on which combo
                # has the least color distance vs our OR/Rd baselines.
                distance_OR_Rd = 0
                distance_OR_Rd += get_euclidean_lab_distance(blue_red_or_orange_edges[0][1].rawcolor, self.orange_baseline)
                distance_OR_Rd += get_euclidean_lab_distance(blue_red_or_orange_edges[1][1].rawcolor, self.red_baseline)

                distance_Rd_OR = 0
                distance_Rd_OR += get_euclidean_lab_distance(blue_red_or_orange_edges[0][1].rawcolor, self.red_baseline)
                distance_Rd_OR += get_euclidean_lab_distance(blue_red_or_orange_edges[1][1].rawcolor, self.orange_baseline)

                log.info(f"distance_OR_Rd {distance_OR_Rd}")
                log.info(f"distance_Rd_OR {distance_Rd_OR}")

                if distance_OR_Rd <= distance_Rd_OR:
                    if blue_red_or_orange_edges[0][1].color_name != "OR":
                        log.warning("change blue edge partner %s from %s to OR" %
                            (blue_red_or_orange_edges[0][1], blue_red_or_orange_edges[0][1].color_name))
                        blue_red_or_orange_edges[0][1].color_name = "OR"

                    if blue_red_or_orange_edges[1][1].color_name != "Rd":
                        log.warning("change blue edge partner %s from %s to Rd" %
                            (blue_red_or_orange_edges[1][1], blue_red_or_orange_edges[1][1].color_name))
                        blue_red_or_orange_edges[1][1].color_name = "Rd"
                else:
                    if blue_red_or_orange_edges[0][1].color_name != "Rd":
                        log.warning("change blue edge partner %s from %s to Rd" %
                            (blue_red_or_orange_edges[0][1], blue_red_or_orange_edges[0][1].color_name))
                        blue_red_or_orange_edges[0][1].color_name = "Rd"

                    if blue_red_or_orange_edges[1][1].color_name != "OR":
                        log.warning("change blue edge partner %s from %s to OR" %
                            (blue_red_or_orange_edges[1][1], blue_red_or_orange_edges[1][1].color_name))
                        blue_red_or_orange_edges[1][1].color_name = "OR"

                # There must be one Wh/OR edge and one Wh/Rd. Assign based on which combo
                # has the least color distance vs our OR/Rd baselines.
                distance_OR_Rd = 0
                distance_OR_Rd += get_euclidean_lab_distance(white_red_or_orange_edges[0][1].rawcolor, self.orange_baseline)
                distance_OR_Rd += get_euclidean_lab_distance(white_red_or_orange_edges[1][1].rawcolor, self.red_baseline)

                distance_Rd_OR = 0
                distance_Rd_OR += get_euclidean_lab_distance(white_red_or_orange_edges[0][1].rawcolor, self.red_baseline)
                distance_Rd_OR += get_euclidean_lab_distance(white_red_or_orange_edges[1][1].rawcolor, self.orange_baseline)

                log.info(f"distance_OR_Rd {distance_OR_Rd}")
                log.info(f"distance_Rd_OR {distance_Rd_OR}")

                if distance_OR_Rd <= distance_Rd_OR:
                    if white_red_or_orange_edges[0][1].color_name != "OR":
                        log.warning("change white edge partner %s from %s to OR" %
                            (white_red_or_orange_edges[0][1], white_red_or_orange_edges[0][1].color_name))
                        white_red_or_orange_edges[0][1].color_name = "OR"

                    if white_red_or_orange_edges[1][1].color_name != "Rd":
                        log.warning("change white edge partner %s from %s to Rd" %
                            (white_red_or_orange_edges[1][1], white_red_or_orange_edges[1][1].color_name))
                        white_red_or_orange_edges[1][1].color_name = "Rd"
                else:
                    if white_red_or_orange_edges[0][1].color_name != "Rd":
                        log.warning("change white edge partner %s from %s to Rd" %
                            (white_red_or_orange_edges[0][1], white_red_or_orange_edges[0][1].color_name))
                        white_red_or_orange_edges[0][1].color_name = "Rd"

                    if white_red_or_orange_edges[1][1].color_name != "OR":
                        log.warning("change white edge partner %s from %s to OR" %
                            (white_red_or_orange_edges[1][1], white_red_or_orange_edges[1][1].color_name))
                        white_red_or_orange_edges[1][1].color_name = "OR"

                # There must be one Wh/OR edge and one Wh/Rd. Assign based on which combo
                # has the least color distance vs our OR/Rd baselines.
                distance_OR_Rd = 0
                distance_OR_Rd += get_euclidean_lab_distance(yellow_red_or_orange_edges[0][1].rawcolor, self.orange_baseline)
                distance_OR_Rd += get_euclidean_lab_distance(yellow_red_or_orange_edges[1][1].rawcolor, self.red_baseline)

                distance_Rd_OR = 0
                distance_Rd_OR += get_euclidean_lab_distance(yellow_red_or_orange_edges[0][1].rawcolor, self.red_baseline)
                distance_Rd_OR += get_euclidean_lab_distance(yellow_red_or_orange_edges[1][1].rawcolor, self.orange_baseline)

                log.info(f"distance_OR_Rd {distance_OR_Rd}")
                log.info(f"distance_Rd_OR {distance_Rd_OR}")

                if distance_OR_Rd <= distance_Rd_OR:
                    if yellow_red_or_orange_edges[0][1].color_name != "OR":
                        log.warning("change yellow edge partner %s from %s to OR" %
                            (yellow_red_or_orange_edges[0][1], yellow_red_or_orange_edges[0][1].color_name))
                        yellow_red_or_orange_edges[0][1].color_name = "OR"

                    if yellow_red_or_orange_edges[1][1].color_name != "Rd":
                        log.warning("change yellow edge partner %s from %s to Rd" %
                            (yellow_red_or_orange_edges[1][1], yellow_red_or_orange_edges[1][1].color_name))
                        yellow_red_or_orange_edges[1][1].color_name = "Rd"
                else:
                    if yellow_red_or_orange_edges[0][1].color_name != "Rd":
                        log.warning("change yellow edge partner %s from %s to Rd" %
                            (yellow_red_or_orange_edges[0][1], yellow_red_or_orange_edges[0][1].color_name))
                        yellow_red_or_orange_edges[0][1].color_name = "Rd"

                    if yellow_red_or_orange_edges[1][1].color_name != "OR":
                        log.warning("change yellow edge partner %s from %s to OR" %
                            (yellow_red_or_orange_edges[1][1], yellow_red_or_orange_edges[1][1].color_name))
                        yellow_red_or_orange_edges[1][1].color_name = "OR"

                # TODO we need to validate parity if this is a 3x3x3, if parity is off figure out which Or/Rd edge
                # squares to swap to create valid parity

                # dwalton
                self.validate_edge_orbit(target_orbit_id)

            #log.info(f"sorted_edge_colors_cluster_squares:\n{sorted_edge_colors_cluster_squares}")
            log.info("\n\n")

        return all_orbits_valid

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

    def resolve_corner_squares(self, write_to_html):
        """
        Use traveling salesman algorithm to sort the colors
        """
        log.info('Resolve corners')
        corner_colors = []

        if use_endpoints:
            corner_colors.append((0, WHITE))
            corner_colors.append((999, BLACK))

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for square in side.corner_squares:
                corner_colors.append((square.position, square.rgb))

        if use_endpoints:
            sorted_corner_colors = traveling_salesman(corner_colors, "euclidean", (0, 1))
            sorted_corner_colors.remove((0, WHITE))
            sorted_corner_colors.remove((999, BLACK))
        else:
            sorted_corner_colors = traveling_salesman(corner_colors, "euclidean")

        sorted_corner_colors_cluster_squares = []
        squares_list = []
        squares_per_cluster = int(len(sorted_corner_colors) / 6)

        for (index, (square_index, rgb)) in enumerate(sorted_corner_colors):
            index += 1
            squares_list.append(ClusterSquare(square_index, rgb))
            if index % squares_per_cluster == 0:
                sorted_corner_colors_cluster_squares.append(squares_list)
                squares_list = []

        #log.info("sorted_corner_colors_cluster_squares:\n%s" % pformat(sorted_corner_colors_cluster_squares))
        self.assign_color_names('corners', sorted_corner_colors_cluster_squares)

        if write_to_html:
            self.write_colors('corners', sorted_corner_colors_cluster_squares)

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

        if self.width in (3, 4, 5, 7):
            centers_for_orange_red_baseline = "centers"
        elif self.width == 6:
            centers_for_orange_red_baseline = "x-centers"
        else:
            raise Exception("What centers to use for orange/red baseline?")

        for (desc, centers_squares) in center_groups[self.width]:
            if desc != centers_for_orange_red_baseline:
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

            '''
            for cluster_square_list in sorted_center_colors_cluster_squares:
                for cluster_square in cluster_square_list:
                    square = self.get_square(cluster_square.index)

                    if square.color_name == "OR":
                        orange_reds.append(square.red)
                        orange_greens.append(square.green)
                        orange_blues.append(square.blue)

                    elif square.color_name == "Rd":
                        red_reds.append(square.red)
                        red_greens.append(square.green)
                        red_blues.append(square.blue)
            '''

            new_orange_red = mean(orange_reds)
            new_orange_green = mean(orange_greens)
            new_orange_blue = mean(orange_blues)
            self.orange_baseline = rgb2lab((new_orange_red, new_orange_green, new_orange_blue))

            new_red_red = mean(red_reds)
            new_red_green = mean(red_greens)
            new_red_blue = mean(red_blues)
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

    def resolve_center_squares(self, write_to_html):
        """
        Use traveling salesman algorithm to sort the colors
        """

        # Nothing to be done for 2x2x2
        if self.width == 2:
            return

        for (desc, centers_squares) in center_groups[self.width]:
            log.info('Resolve {}'.format(desc))
            center_colors = []

            for position in centers_squares:
                square = self.get_square(position)
                center_colors.append((square.position, square.rgb))

            if len(centers_squares) == 6:
                sorted_center_colors = center_colors[:]
            else:
                if use_endpoints:
                    center_colors.append((998, WHITE))
                    center_colors.append((999, BLACK))
                    sorted_center_colors = traveling_salesman(center_colors, "euclidean", (-2, -1))
                    sorted_center_colors.remove((998, WHITE))
                    sorted_center_colors.remove((999, BLACK))
                else:
                    sorted_center_colors = traveling_salesman(center_colors, "euclidean")

            #log.info("center_colors: %s" % pformat(center_colors))
            #log.info("sorted_center_colors: %s" % pformat(sorted_center_colors))
            sorted_center_colors_cluster_squares = []
            squares_list = []
            squares_per_cluster = int(len(sorted_center_colors) / 6)

            for (index, (square_index, rgb)) in enumerate(sorted_center_colors):
                index += 1
                squares_list.append(ClusterSquare(square_index, rgb))
                if index % squares_per_cluster == 0:
                    sorted_center_colors_cluster_squares.append(squares_list)
                    squares_list = []

            self.assign_color_names(desc, sorted_center_colors_cluster_squares)

            if write_to_html:
                self.write_colors(desc, sorted_center_colors_cluster_squares)

    def contrast_stretch(self):
        log.info("WHITE squares %s" % pformat(self.white_squares))
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

            if square.color_name == "Wh":
                white_reds.append(red)
                white_greens.append(green)
                white_blues.append(blue)

                if red < darkest_white_red:
                    darkest_white_red = red

                if green < darkest_white_green:
                    darkest_white_green = green

                if blue < darkest_white_blue:
                    darkest_white_blue = blue

        log.info(f"min_input_red {min_input_red}, max_input_red {max_input_red}")
        log.info(f"min_input_green {min_input_green}, max_input_green {max_input_green}")
        log.info(f"min_input_blue {min_input_blue}, max_input_blue {max_input_blue}")
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
        log.info(f"WHITE reds {white_reds},  avg {avg_white_red}, median {median_white_red}")
        log.info(f"WHITE greens {white_greens},  avg {avg_white_green}, median {median_white_green}")
        log.info(f"WHITE blues {white_blues},  avg {avg_white_blue}, median {median_white_blue}")

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

        for side in (self.sideU, self.sideL, self.sideF, self.sideR, self.sideB, self.sideD):
            side_squares = side.corner_squares + side.center_squares + side.edge_squares
            for square in side_squares:
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
                square.rawcolor = rgb2lab((new_red, new_green, new_blue))

    def write_final_cube(self):
        data = self.cube_for_json()
        cube = ['dummy', ]

        for square_index in sorted(data['squares'].keys()):
            value = data['squares'][square_index]
            html_colors = data['sides'][value['finalSide']]['colorHTML']
            cube.append((html_colors['red'], html_colors['green'], html_colors['blue']))

        self.write_cube('Final Cube', cube)

    def crunch_colors(self):

        # The first step is to find all of the white squares so we can call contrast_stretch()
        # to create as much color separation as possible.
        self.write_cube2("Initial RGB values")
        self.resolve_center_squares(False)
        self.resolve_corner_squares(False)
        self.resolve_edge_squares(False, False)

        # Write the white squares to our html file
        self.write_white_squares()

        self.contrast_stretch()
        self.white_squares = []
        self.write_cube2("Contrast Stretched RBG values")

        self.find_orange_and_red_baselines()
        self.resolve_center_squares(True)
        self.resolve_corner_squares(True)
        self.resolve_edge_squares(True, True)
        self.set_state()

        self.print_cube()
        self.write_final_cube()
        self.www_footer()
