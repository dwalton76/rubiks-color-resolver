
from tsp_solver.greedy import solve_tsp
from collections import OrderedDict
from copy import deepcopy, copy
from itertools import permutations
from math import atan2, cos, degrees, exp, factorial, radians, sin, sqrt, ceil
from pprint import pformat
import colorsys
import itertools
import json
import logging
import os
import sys

if sys.version_info < (3,4):
    raise SystemError('Must be using Python 3.4 or higher')

log = logging.getLogger(__name__)

SIDES_COUNT = 6


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
        # oribit 0
        2: 0, 5: 0, 7: 0, 25: 0, 12: 0, 30: 0, 32: 0, 35: 0, # Upper
        38: 0, 41: 0, 43: 0, 61: 0, 48: 0, 66: 0, 68: 0, 71: 0, # Left
        74: 0, 77: 0, 79: 0, 97: 0, 84: 0, 102: 0, 104: 0, 107: 0, # Front
        110: 0, 113: 0, 115: 0, 133: 0, 120: 0, 138: 0, 140: 0, 143: 0, # Right
        146: 0, 149: 0, 151: 0, 169: 0, 156: 0, 174: 0, 176: 0, 179: 0, # Back
        182: 0, 185: 0, 187: 0, 205: 0, 192: 0, 210: 0, 212: 0, 215: 0, # Down

        # oribit 1
        3: 1, 4: 1, 13: 1, 19: 1, 18: 1, 24: 1, 33: 1, 34: 1, # Upper
        39: 1, 40: 1, 49: 1, 55: 1, 54: 1, 60: 1, 69: 1, 70: 1, # Left
        75: 1, 76: 1, 85: 1, 91: 1, 90: 1, 96: 1, 105: 1, 106: 1, # Front
        111: 1, 112: 1, 121: 1, 127: 1, 126: 1, 132: 1, 141: 1, 142: 1, # Right
        147: 1, 148: 1, 157: 1, 163: 1, 162: 1, 168: 1, 177: 1, 178: 1, # Back
        183: 1, 184: 1, 193: 1, 199: 1, 198: 1, 204: 1, 213: 1, 214: 1, # Down
    }
}


def get_euclidean_lab_distance(lab1, lab2):
    """
    http://www.w3resource.com/python-exercises/math/python-math-exercise-79.php

    In mathematics, the Euclidean distance or Euclidean metric is the "ordinary"
    (i.e. straight-line) distance between two points in Euclidean space. With this
    distance, Euclidean space becomes a metric space. The associated norm is called
    the Euclidean norm.
    """
    # I experiment with this sometimes
    # return delta_e_cie2000(lab1, lab2)

    lab1_tuple = (lab1.L, lab1.a, lab1.b)
    lab2_tuple = (lab2.L, lab2.a, lab2.b)
    return sqrt(sum([(a - b) ** 2 for a, b in zip(lab1_tuple, lab2_tuple)]))


def find_index_for_value(list_foo, target, min_index):
    for (index, value) in enumerate(list_foo):
        if value == target and index >= min_index:
            return index
    raise Exception("Did not find %s in list %s" % (target, pformat(list_foo)))


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


def traveling_salesman(colors, alg):

    # build a full matrix of cie2000 distances
    len_colors = len(colors)
    matrix = [[0 for i in range(len_colors)] for j in range(len_colors)]

    for x in range(len_colors):
        (_x_square_index, (x_red, x_green, x_blue)) = colors[x]
        x_lab = rgb2lab((x_red, x_green, x_blue))
        x_hsv = colorsys.rgb_to_hsv(x_red, x_green, x_blue)
        x_hls = colorsys.rgb_to_hls(x_red, x_green, x_blue)

        for y in range(len_colors):

            if x == y:
                matrix[x][y] = 0
                matrix[y][x] = 0
                continue

            if matrix[x][y] or matrix[y][x]:
                continue

            (_y_square_index, (y_red, y_green, y_blue)) = colors[y]

            if alg == "cie2000":
                y_lab = rgb2lab((y_red, y_green, y_blue))
                distance = delta_e_cie2000(x_lab, y_lab)

            elif alg == "HSV":
                y_hsv = colorsys.rgb_to_hsv(y_red, y_green, y_blue)
                distance = get_euclidean_distance_two_points(x_hsv, y_hsv)

            elif alg == "HLS":
                y_hls = colorsys.rgb_to_hls(y_red, y_green, y_blue)
                distance = get_euclidean_distance_two_points(x_hls, y_hls)

            elif alg == "euclidean":
                y_lab = rgb2lab((y_red, y_green, y_blue))
                distance = get_euclidean_lab_distance(x_lab, y_lab)

            else:
                raise Exception("Implement {}".format(alg))

            matrix[x][y] = distance
            matrix[y][x] = distance

    path = solve_tsp(matrix)
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


def get_cube_layout(size):
    """
    Example: size is 3, return the following string:

              01 02 03
              04 05 06
              07 08 09

    10 11 12  19 20 21  28 29 30  37 38 39
    13 14 15  22 23 24  31 32 33  40 41 42
    16 17 18  25 26 27  34 35 36  43 44 45

              46 47 48
              49 50 51
              52 53 54
    """
    result = []

    squares = (size * size) * 6
    square_index = 1

    if squares >= 1000:
        digits_size = 4
        digits_format = "%04d "
    elif squares >= 100:
        digits_size = 3
        digits_format = "%03d "
    else:
        digits_size = 2
        digits_format = "%02d "

    indent = ((digits_size * size) + size + 1) * ' '
    rows = size * 3

    for row in range(1, rows + 1):
        line = []

        if row <= size:
            line.append(indent)
            for col in range(1, size + 1):
                line.append(digits_format % square_index)
                square_index += 1

        elif row > rows - size:
            line.append(indent)
            for col in range(1, size + 1):
                line.append(digits_format % square_index)
                square_index += 1

        else:
            init_square_index = square_index
            last_col = size * 4
            for col in range(1, last_col + 1):
                line.append(digits_format % square_index)

                if col == last_col:
                    square_index += 1
                elif col % size == 0:
                    square_index += (size * size) - size + 1
                    line.append(' ')
                else:
                    square_index += 1

            if row % size:
                square_index = init_square_index + size

        result.append(''.join(line))

        if row == size or row == rows - size:
            result.append('')
    return '\n'.join(result)


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
    """
    http://stackoverflow.com/questions/13405956/convert-an-image-rgb-lab-with-python
    """
    RGB = [0, 0, 0]
    XYZ = [0, 0, 0]

    for (num, value) in enumerate(inputColor):
        if value > 0.04045:
            value = pow(((value + 0.055) / 1.055), 2.4)
        else:
            value = value / 12.92

        RGB[num] = value * 100.0

    # http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
    # sRGB
    # 0.4124564  0.3575761  0.1804375
    # 0.2126729  0.7151522  0.0721750
    # 0.0193339  0.1191920  0.9503041
    X = (RGB[0] * 0.4124564) + (RGB[1] * 0.3575761) + (RGB[2] * 0.1804375)
    Y = (RGB[0] * 0.2126729) + (RGB[1] * 0.7151522) + (RGB[2] * 0.0721750)
    Z = (RGB[0] * 0.0193339) + (RGB[1] * 0.1191920) + (RGB[2] * 0.9503041)

    XYZ[0] = X / 95.047   # ref_X =  95.047
    XYZ[1] = Y / 100.0    # ref_Y = 100.000
    XYZ[2] = Z / 108.883  # ref_Z = 108.883

    for (num, value) in enumerate(XYZ):
        if value > 0.008856:
            value = pow(value, (1.0 / 3.0))
        else:
            value = (7.787 * value) + (16 / 116.0)

        XYZ[num] = value

    L = (116.0 * XYZ[1]) - 16
    a = 500.0 * (XYZ[0] - XYZ[1])
    b = 200.0 * (XYZ[1] - XYZ[2])

    L = round(L, 4)
    a = round(a, 4)
    b = round(b, 4)

    (red, green, blue) = inputColor
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
        self.anchor_square = None

    def __str__(self):
        return "%s%d" % (self.side, self.position)

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return self.position < other.position

    def find_closest_match(self, crayon_box, debug=False, set_color=True):
        cie_data = []

        for (color_name, color_obj) in crayon_box.items():
            distance = get_euclidean_lab_distance(self.rawcolor, color_obj)
            cie_data.append((distance, color_name, color_obj))
        cie_data = sorted(cie_data)

        distance = cie_data[0][0]
        color_name = cie_data[0][1]
        color_obj = cie_data[0][2]

        if set_color:
            self.distance = distance
            self.color_name = color_name
            self.color = color_obj

        if debug:
            log.info("%s is %s" % (self, color_obj))

        return (color_obj, distance)


def get_orbit_id(cube_size, edge_index):
    orbit = None

    if cube_size == 3 or cube_size == 4:
        orbit = 0

    elif cube_size == 5:

        if edge_index == 0 or edge_index == 2:
            orbit = 0
        else:
            orbit = 1

    elif cube_size == 6:

        if edge_index == 0 or edge_index == 3:
            orbit = 0
        else:
            orbit = 1

    elif cube_size == 7:

        if edge_index == 0 or edge_index == 4:
            orbit = 0
        elif edge_index == 1 or edge_index == 3:
            orbit = 1
        else:
            orbit = 2

    else:
        raise Exception("Add orbit ID support for %dx%dx%d cubes" % (cube_size, cube_size, cube_size))

    return orbit


class Edge(object):

    def __init__(self, cube, pos1, pos2, edge_index):
        self.valid = False
        self.square1 = cube.get_square(pos1)
        self.square2 = cube.get_square(pos2)
        self.cube = cube
        self.color_distance_cache = {}
        self.orbit_id = get_orbit_id(self.cube.width, edge_index)
        self.orbit_index = None

        assert self.square1.position < self.square2.position, "square1 pos %d, square2 pos %d" % (self.square1.position, self.square2.position)

    def __str__(self):
        result = "%s%d/%s%d(%d/%s) " %\
            (self.square1.side, self.square1.position,
             self.square2.side, self.square2.position, self.orbit_id, self.orbit_index)

        if self.square1.color and self.square2.color:
            result += " %s/%s" % (self.square1.color.name, self.square2.color.name)
        elif self.square1.color and not self.square2.color:
            result += " %s/None" % self.square1.color.name
        elif not self.square1.color and self.square2.color:
            result += " None/%s" % self.square2.color.name

        return result

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return 0

    def colors_match(self, colorA, colorB):
        if (colorA in (self.square1.color, self.square2.color) and
            colorB in (self.square1.color, self.square2.color)):
            return True
        return False

    def _get_color_distances(self, colorA, colorB):
        distanceAB = (get_euclidean_lab_distance(self.square1.rawcolor, colorA) +
                      get_euclidean_lab_distance(self.square2.rawcolor, colorB))

        distanceBA = (get_euclidean_lab_distance(self.square1.rawcolor, colorB) +
                      get_euclidean_lab_distance(self.square2.rawcolor, colorA))

        return (distanceAB, distanceBA)

    def color_distance(self, colorA, colorB):
        """
        Given two colors, return our total color distance
        """
        try:
            return self.color_distance_cache[(colorA, colorB)]
        except KeyError:
            value = min(self._get_color_distances(colorA, colorB))
            self.color_distance_cache[(colorA, colorB)] = value
            return value

    def reset_colors(self):
        self.square1.color = None
        self.square1.color_name = None
        self.square2.color = None
        self.square2.color_name = None

    def update_colors(self, colorA, colorB):
        (distanceAB, distanceBA) = self._get_color_distances(colorA, colorB)

        if distanceAB < distanceBA:
            self.square1.color = colorA
            self.square1.color_name = colorA.name
            self.square2.color = colorB
            self.square2.color_name = colorB.name
        else:
            self.square1.color = colorB
            self.square1.color_name = colorB.name
            self.square2.color = colorA
            self.square2.color_name = colorA.name

    def reset_orbit_index(self):
        self.orbit_index = None

    def update_orbit_index(self):
        """
        Colors have been assigned, we must now determine if this is a UF0 or a UF1 edge
        """
        color_to_side_name = {
            'Wh' : 'U',
            'OR' : 'L',
            'Gr' : 'F',
            'Rd' : 'R',
            'Bu' : 'B',
            'Ye' : 'D'
        }

        square1_side_name = color_to_side_name[self.square1.color.name]
        square2_side_name = color_to_side_name[self.square2.color.name]

        if self.cube.width == 2 or self.cube.width == 3:
            pass

        elif self.cube.width == 4:
            from rubikscolorresolver.cube_444 import orbit_index_444
            self.orbit_index = orbit_index_444[(self.square1.position, self.square2.position, square1_side_name, square2_side_name)]

        elif self.cube.width == 5:
            from rubikscolorresolver.cube_555 import orbit_index_555
            self.orbit_index = orbit_index_555[(self.square1.position, self.square2.position, square1_side_name, square2_side_name)]

        elif self.cube.width == 6:
            from rubikscolorresolver.cube_666 import orbit_index_666
            self.orbit_index = orbit_index_666[(self.square1.position, self.square2.position, square1_side_name, square2_side_name)]

        elif self.cube.width == 7:
            from rubikscolorresolver.cube_777 import orbit_index_777
            self.orbit_index = orbit_index_777[(self.square1.position, self.square2.position, square1_side_name, square2_side_name)]

        else:
            # orbit_index_444, etc were generated via https://github.com/dwalton76/rubiks-cube-NxNxN-solver
            # If you need to build an orbit_index_XYZ for a larger cube search in "orbit_index_444" in rubikscubennnsolver/__init__.py
            # for instructions on how to do so.
            raise Exception("Add update_orbit_index support for %dx%dx%d cubes" % (self.cube.width, self.cube.width, self.cube.width))

    def validate(self):

        if self.square1.color == self.square2.color:
            self.valid = False
            log.info("%s is an invalid edge (duplicate colors)" % self)
        elif ((self.square1.color, self.square2.color) in self.cube.valid_edges or
              (self.square2.color, self.square1.color) in self.cube.valid_edges):
            self.valid = True
        else:
            self.valid = False
            log.info("%s is an invalid edge" % self)


class Corner(object):

    def __init__(self, cube, pos1, pos2, pos3):
        self.valid = False
        self.square1 = cube.get_square(pos1)
        self.square2 = cube.get_square(pos2)
        self.square3 = cube.get_square(pos3)
        self.cube = cube
        self.color_distance_cache = {}

    def __str__(self):
        if self.square1.color and self.square2.color and self.square3.color:
            return "%s%d/%s%d/%s%d %s/%s/%s" %\
                (self.square1.side, self.square1.position,
                 self.square2.side, self.square2.position,
                 self.square3.side, self.square3.position,
                 self.square1.color.name, self.square2.color.name, self.square3.color.name)
        else:
            return "%s%d/%s%d/%s%d" %\
                (self.square1.side, self.square1.position,
                 self.square2.side, self.square2.position,
                 self.square3.side, self.square3.position)

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return 0

    def colors_match(self, colorA, colorB, colorC):
        if (colorA in (self.square1.color, self.square2.color, self.square3.color) and
            colorB in (self.square1.color, self.square2.color, self.square3.color) and
            colorC in (self.square1.color, self.square2.color, self.square3.color)):
            return True
        return False

    def _get_color_distances(self, colorA, colorB, colorC):
        distanceABC = (get_euclidean_lab_distance(self.square1.rawcolor, colorA) +
                       get_euclidean_lab_distance(self.square2.rawcolor, colorB) +
                       get_euclidean_lab_distance(self.square3.rawcolor, colorC))

        distanceCAB = (get_euclidean_lab_distance(self.square1.rawcolor, colorC) +
                       get_euclidean_lab_distance(self.square2.rawcolor, colorA) +
                       get_euclidean_lab_distance(self.square3.rawcolor, colorB))

        distanceBCA = (get_euclidean_lab_distance(self.square1.rawcolor, colorB) +
                       get_euclidean_lab_distance(self.square2.rawcolor, colorC) +
                       get_euclidean_lab_distance(self.square3.rawcolor, colorA))

        return (distanceABC, distanceCAB, distanceBCA)

    def color_distance(self, colorA, colorB, colorC):
        """
        Given three colors, return our total color distance
        """
        try:
            return self.color_distance_cache[(colorA, colorB, colorC)]
        except KeyError:
            value = min(self._get_color_distances(colorA, colorB, colorC))
            self.color_distance_cache[(colorA, colorB, colorC)] = value
            return value

    def update_colors(self, colorA, colorB, colorC):
        (distanceABC, distanceCAB, distanceBCA) = self._get_color_distances(colorA, colorB, colorC)
        min_distance = min(distanceABC, distanceCAB, distanceBCA)

        #log.debug("%s vs %s/%s/%s, distanceABC %s, distanceCAB %s, distanceBCA %s, min %s" %
        #            (self, colorA.name, colorB.name, colorC.name,
        #            distanceABC, distanceCAB, distanceBCA, min_distance))

        if min_distance == distanceABC:
            self.square1.color = colorA
            self.square1.color_name = colorA.name
            self.square2.color = colorB
            self.square2.color_name = colorB.name
            self.square3.color = colorC
            self.square3.color_name = colorC.name

        elif min_distance == distanceCAB:
            self.square1.color = colorC
            self.square1.color_name = colorC.name
            self.square2.color = colorA
            self.square2.color_name = colorA.name
            self.square3.color = colorB
            self.square3.color_name = colorB.name

        elif min_distance == distanceBCA:
            self.square1.color = colorB
            self.square1.color_name = colorB.name
            self.square2.color = colorC
            self.square2.color_name = colorC.name
            self.square3.color = colorA
            self.square3.color_name = colorA.name

        else:
            raise Exception("We should not be here")

    def validate(self):

        if (self.square1.color == self.square2.color or
            self.square1.color == self.square3.color or
                self.square2.color == self.square3.color):
            self.valid = False
            log.info("%s is an invalid edge (duplicate colors)" % self)
        elif ((self.square1.color, self.square2.color, self.square3.color) in self.cube.valid_corners or
              (self.square1.color, self.square3.color, self.square2.color) in self.cube.valid_corners or
              (self.square2.color, self.square1.color, self.square3.color) in self.cube.valid_corners or
              (self.square2.color, self.square3.color, self.square1.color) in self.cube.valid_corners or
              (self.square3.color, self.square1.color, self.square2.color) in self.cube.valid_corners or
              (self.square3.color, self.square2.color, self.square1.color) in self.cube.valid_corners):
            self.valid = True
        else:
            self.valid = False
            log.info("%s (%s, %s, %s) is an invalid corner" %
                     (self, self.square1.color, self.square2.color, self.square3.color))



class CubeSide(object):

    def __init__(self, cube, width, name):
        self.cube = cube
        self.name = name  # U, L, etc
        self.color = None  # Will be the color of the anchor square
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

        log.info("Side %s, min/max %d/%d, edges %s, corners %s, centers %s" %
            (self.name, self.min_pos, self.max_pos,
             pformat(self.edge_pos),
             pformat(self.corner_pos),
             pformat(self.center_pos)))

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
            log.info("wing_partner\n%s\n" % pformat(self.wing_partner))
            raise


class RubiksColorSolverGeneric(object):

    def __init__(self, width):
        self.width = width
        self.height = width
        self.squares_per_side = self.width * self.width
        self.scan_data = {}
        self.orbits = int(ceil((self.width - 2) / 2.0))
        self.all_edge_positions = []
        self.state = []

        if self.width % 2 == 0:
            self.even = True
            self.odd = False
        else:
            self.even = False
            self.odd = True

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
        self.crayon_box = deepcopy(self.crayola_colors)
        self.www_header()

    def www_header(self):
        """
        Write the <head> including css
        """
        side_margin = 10
        square_size = 40
        size = self.width # 3 for 3x3x3, etc
        filename = '/tmp/rubiks-color-resolver.html'

        if os.path.exists(filename):
            os.remove(filename)

        with open(filename, 'w') as fh:
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

div#anchorsquares {
    margin-left: 350px;
}

</style>
<title>CraneCuber</title>
</head>
<body>
""" % (square_size, square_size, square_size, square_size, square_size, square_size))

        os.chmod(filename, 0o777)

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

        with open('/tmp/rubiks-color-resolver.html', 'a') as fh:
            fh.write("<h1>%s</h1>\n" % desc)
            for index in range(1, max_square + 1):
                if index in first_squares:
                    side_index += 1
                    fh.write("<div class='side' id='%s'>\n" % sides[side_index])

                (red, green, blue) = cube[index]
                (H, S, V) = colorsys.rgb_to_hsv(float(red/255), float(green/255), float(blue/255))
                H = int(H * 360)
                S = int(S * 100)
                V = int(V * 100)
                lab = rgb2lab((red, green, blue))

                fh.write("    <div class='square col%d' title='RGB (%d, %d, %d) HSV (%d, %d, %d), Lab (%s, %s, %s)' style='background-color: #%02x%02x%02x;'><span>%02d</span></div>\n" %
                    (col,
                     red, green, blue,
                     H, S, V,
                     lab.L, lab.a, lab.b,
                     red, green, blue,
                     index))

                if index in last_squares:
                    fh.write("</div>\n")

                    if index in last_UBD_squares:
                        fh.write("<div class='clear'></div>\n")

                col += 1

                if col == self.width + 1:
                    col = 1

    def write_colors(self, desc, colors):
        with open('/tmp/rubiks-color-resolver.html', 'a') as fh:
            squares_per_side = int(len(colors)/6)
            fh.write("<h2>%s</h2>\n" % desc)
            fh.write("<div class='clear colors'>\n")

            for cluster_square_list in colors:
                anchor = None
                total_distance = 0

                for cluster_square in cluster_square_list:

                    # The anchor is always the first one on the list
                    if anchor is None:
                        anchor = cluster_square
                        distance_to_anchor = 0
                    else:
                        distance_to_anchor = get_euclidean_lab_distance(cluster_square.lab, anchor.lab)

                    (red, green, blue) = cluster_square.rgb

                    # to use python coloursys convertion we have to rescale to range 0-1
                    (H, S, V) = colorsys.rgb_to_hsv(float(red/255), float(green/255), float(blue/255))

                    # rescale H to 360 degrees and S, V to percent of 100%
                    H = int(H * 360)
                    S = int(S * 100)
                    V = int(V * 100)
                    lab = rgb2lab((red, green, blue))

                    fh.write("<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), HSV (%s, %s, %s), Lab (%s, %s, %s) Distance %d'>%d</span>\n" %
                        (red, green, blue,
                         red, green, blue,
                         H, S, V,
                         lab.L, lab.a, lab.b,
                         distance_to_anchor,
                         cluster_square.index))
                    total_distance += distance_to_anchor

                fh.write("<span class='square'>%d</span>\n" % total_distance)
                fh.write("<br>")

            fh.write("</div>\n")
            log.info('\n\n')


    def write_colors2(self, title, colors_to_write):
        with open('/tmp/rubiks-color-resolver.html', 'a') as fh:
            fh.write("<h2>{}</h2>\n".format(title))
            fh.write("<div class='clear colors'>\n")
            for (red, green, blue) in colors_to_write:
                lab = rgb2lab((red, green, blue))
                hsv = colorsys.rgb_to_hsv(red, green, blue)
                hls = colorsys.rgb_to_hls(red, green, blue)

                fh.write("<span class='square' style='background-color: #%02x%02x%02x;' title='RGB (%d, %d, %d)) Lab (%s, %s, %s), HSV (%s, %s, %s), HLS (%s, %s, %s)'></span>" % (
                    red, green, blue, red, green, blue, lab.L, lab.a, lab.b, *hsv, *hls))

            fh.write("<br></div>")

    def www_footer(self):
        with open('/tmp/rubiks-color-resolver.html', 'a') as fh:
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
        cube = ['dummy',]

        for (position, (red, green, blue)) in sorted(self.scan_data.items()):
            position = int(position)
            side = self.get_side(position)
            side.set_square(position, red, green, blue)
            cube.append((red, green, blue))

        # write the input to the web page so we can reproduce bugs, etc just from the web page
        with open('/tmp/rubiks-color-resolver.html', 'a') as fh:
            fh.write("<h1>JSON Input</h1>\n")
            fh.write("<pre>%s</pre>\n" % json.dumps(scan_data))

        self.write_cube('Input RGB values', cube)

    def print_layout(self):
        log.info('\n' + get_cube_layout(self.width) + '\n')

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

        # If we've already set the state the return
        if self.state:
            return

        if self.sideU.mid_pos is not None:
            self.color_to_side_name = {}

            for side_name in self.side_order:
                side = self.sides[side_name]
                mid_square = side.squares[side.mid_pos]

                if mid_square.color_name in self.color_to_side_name:
                    log.info("color_to_side_name:\n%s" % pformat(self.color_to_side_name))
                    raise Exception("side %s with color %s, %s is already in color_to_side_name" %\
                        (side, mid_square.color_name, mid_square.color_name))
                self.color_to_side_name[mid_square.color_name] = side.name

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
        #log.info("color_to_side_name:\n{}".format(self.color_to_side_name))

        for side_name in self.side_order:
            side = self.sides[side_name]

            for x in range(side.min_pos, side.max_pos + 1):
                color_name = side.squares[x].color_name
                #log.info("set_state(): side {}, x {}, color_name {}".format(side, x, color_name))
                self.state.append(self.color_to_side_name[color_name])

    def cube_for_kociemba_strict(self):
        self.set_state()

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

    def sort_squares(self, target_square, squares_to_sort):
        rank = []
        for square in squares_to_sort:
            distance = get_euclidean_lab_distance(target_square.rawcolor, square.rawcolor)
            rank.append((distance, square))
        rank = list(sorted(rank))

        result = []
        for (distance, square) in rank:
            log.info("%s vs %s distance %s (%s vs %s)" % (target_square, square, distance, pformat(target_square.rgb), pformat(square.rgb)))
            result.append(square)
        return result

    def bind_center_squares_to_anchor(self, square_indexes, desc):
        center_colors = OrderedDict()

        # We must add the anchor squares first
        for anchor_square in self.anchor_squares:
            center_colors[anchor_square.position] = anchor_square.rgb

        for side_name in self.side_order:
            side = self.sides[side_name]

            for square_index in square_indexes:
                square = side.center_squares[square_index]
                if square not in self.anchor_squares:
                    center_colors[square.position] = square.rgb

        sorted_center_colors = kmeans_sort_colors_static_anchors(desc, self, center_colors)
        self.write_colors(desc, sorted_center_colors)

        # The first entry on each list is the anchor square
        for cluster_square_list in sorted_center_colors:
            anchor_square_index = cluster_square_list[0].index
            anchor_square = self.get_square(anchor_square_index)

            for cluster_square in cluster_square_list[1:]:
                square = self.get_square(cluster_square.index)
                square.anchor_square = anchor_square
                log.info("%s: square %s anchor square is %s" % (desc, square, anchor_square))

    def identify_anchor_squares(self):

        # Odd cube, use the centers
        if self.width % 2 == 1:

            for side_name in self.side_order:
                side = self.sides[side_name]
                anchor_square = side.squares[side.mid_pos]
                self.anchor_squares.append(anchor_square)
                log.info("center anchor square %s (odd) with color %s" % (anchor_square, anchor_square.color_name))

        # Even cube, use corners
        else:

            # Start with the LFU corner, that corner will give us the first three anchor squares
            self.anchor_squares.append(self.sideL.corner_squares[1])
            self.anchor_squares.append(self.sideF.corner_squares[0])
            self.anchor_squares.append(self.sideU.corner_squares[2])
            anchor1 = self.sideL.corner_squares[1]
            anchor2 = self.sideF.corner_squares[0]
            anchor3 = self.sideU.corner_squares[2]
            anchor1_rgb = (anchor1.red, anchor1.green, anchor1.blue)
            anchor2_rgb = (anchor2.red, anchor2.green, anchor2.blue)
            anchor3_rgb = (anchor3.red, anchor3.green, anchor3.blue)

            # Build an OrderedDict we can pass to kmeans_sort_colors_static_anchors()
            # This will contain all corner squares. Add the three anchors first, this
            # is a must for kmeans_sort_colors_static_anchors().
            square_by_index = {}
            corner_colors = OrderedDict()
            corner_colors[anchor1.position] = anchor1_rgb
            corner_colors[anchor2.position] = anchor2_rgb
            corner_colors[anchor3.position] = anchor3_rgb

            for corner in self.corners:
                if corner.square1.position not in corner_colors:
                    corner_colors[corner.square1.position] = corner.square1.rgb
                    square_by_index[corner.square1.position] = corner.square1

                if corner.square2.position not in corner_colors:
                    corner_colors[corner.square2.position] = corner.square2.rgb
                    square_by_index[corner.square2.position] = corner.square2

                if corner.square3.position not in corner_colors:
                    corner_colors[corner.square3.position] = corner.square3.rgb
                    square_by_index[corner.square3.position] = corner.square3

            # We know three anchors for sure, group all corner squares into three
            # groups based on these anchors
            sorted_corner_colors = kmeans_sort_colors_static_anchors("First Three Anchors", self, corner_colors, 3)
            self.write_colors("find anchors among corners", sorted_corner_colors)

            # Now we have three "rows" of colors where the anchor squares we know
            # for sure are on the far left.  Use the three squares on the far
            # right as the other three anchor squares.
            for cluster_squares_for_anchor in sorted_corner_colors:
                last_cluster_square = cluster_squares_for_anchor[-2]
                last_square = square_by_index[last_cluster_square.index]
                self.anchor_squares.append(last_square)

        # Assign color names to each anchor_square. We compute which naming
        # scheme results in the least total color distance in terms of the anchor
        # square colors vs the colors in crayola_colors
        min_distance = None
        min_distance_permutation = None

        for permutation in permutations(self.crayola_colors.keys()):
            distance = 0

            for (anchor_square, color_name) in zip(self.anchor_squares, permutation):
                color_obj = self.crayola_colors[color_name]
                distance += get_euclidean_lab_distance(anchor_square.rawcolor, color_obj)

            # TODO for odd cubes there are fewer permutations to eval, white and yellow must
            # be opposites, etc
            if min_distance is None or distance < min_distance:
                min_distance = distance
                min_distance_permutation = permutation
                log.warning("PERMUTATION {}, DISTANCE {:,} (NEW MIN)".format(permutation, int(distance)))
            else:
                if str(permutation) == "('Wh', 'Bu', 'OR', 'Gr', 'Rd', 'Ye')":
                    log.info("PERMUTATION {}, DISTANCE {:,}".format(permutation, int(distance)))

        log.info('assign color names to anchor squares and sides')
        for (anchor_square, color_name) in zip(self.anchor_squares, min_distance_permutation):
            color_obj = self.crayola_colors[color_name]
            # I used to set this to the crayola_color object but I don't think
            # that buys us anything, it is better to use our rawcolor as our color
            # since other squares will be comparing themselves to our 'color'.  They
            # will line up more closely with it than they will the crayola_color object.
            # anchor_square.color = color_obj
            anchor_square.color = anchor_square.rawcolor
            anchor_square.color.name = color_name
            anchor_square.color_name = color_name

        for anchor_square in self.anchor_squares:
            log.info("anchor square %s with color %s" % (anchor_square, anchor_square.color_name))


        # No center squares
        if self.width == 2:
            pass

        # The only center squares are the anchors
        elif self.width == 3:
            pass

        elif self.width == 4:
            self.bind_center_squares_to_anchor((0, 1, 2, 3), '4x4x4 centers')

        elif self.width == 5:
            # t-centers
            #self.bind_center_squares_to_anchor((1, 3, 5, 7), '5x5x5 t-centers')

            # x-centers
            #self.bind_center_squares_to_anchor((0, 2, 6, 8), '5x5x5 x-centers')
            pass

        elif self.width == 6:

            # inside x-centers
            self.bind_center_squares_to_anchor((5, 6, 9, 10), '6x6x6 inside x-centers')

            # outside x-centers
            self.bind_center_squares_to_anchor((0, 3, 12, 15), '6x6x6 outside x-centers')

            # left oblique edges
            self.bind_center_squares_to_anchor((1, 7, 8, 14), '6x6x6 left oblique edges')

            # right oblique edges
            self.bind_center_squares_to_anchor((2, 4, 11, 13), '6x6x6 right oblique edges')

        elif self.width == 7:
            # inside x-centers
            self.bind_center_squares_to_anchor((6, 8, 16, 18), '7x7x7 inside x-centers')

            # inside t-centers
            self.bind_center_squares_to_anchor((7, 11, 13, 17), '7x7x7 inside t-centers')

            # left oblique edges
            self.bind_center_squares_to_anchor((1, 9, 15, 23), '7x7x7 left oblique edges')

            # right oblique edges
            self.bind_center_squares_to_anchor((3, 5, 19, 21), '7x7x7 right oblique edges')

            # outside x-centers
            self.bind_center_squares_to_anchor((0, 4, 20, 24), '7x7x7 outside x-centers')

            # outside t-centers
            self.bind_center_squares_to_anchor((2, 10, 14, 22), '7x7x7 outside t-centers')

        else:
            raise Exception("Add anchor/center support for %dx%dx%d cubes" % (self.width, self.width, self.width))

        # Now that our anchor squares have been assigned a color/color_name, go back and
        # assign the same color/color_name to all of the other center_squares. This ends
        # up being a no-op for 2x2x2 and 3x3x3 but for 4x4x4 and up larger this does something.
        for side_name in self.side_order:
            side = self.sides[side_name]

            for square in side.center_squares:
                if square.anchor_square:
                    square.color = square.anchor_square.color
                    square.color_name = square.anchor_square.color_name
                    square.color.name = square.anchor_square.color.name

        # Assign each Side a color
        if self.sideU.mid_pos:
            for side_name in self.side_order:
                side = self.sides[side_name]
                side.red = side.squares[side.mid_pos].red
                side.green = side.squares[side.mid_pos].green
                side.blue = side.squares[side.mid_pos].blue
                side.color = side.squares[side.mid_pos].color
                side.color_name = side.squares[side.mid_pos].color_name

        else:
            all_squares = []
            for side_name in self.side_order:
                side = self.sides[side_name]
                all_squares.extend(side.squares.values())

            for side_name in self.side_order:
                side = self.sides[side_name]

                if side_name == 'U':
                    target_color_name = 'Wh'
                elif side_name == 'L':
                    target_color_name = 'OR'
                elif side_name == 'F':
                    target_color_name = 'Gr'
                elif side_name == 'R':
                    target_color_name = 'Rd'
                elif side_name == 'D':
                    target_color_name = 'Ye'
                elif side_name == 'B':
                    target_color_name = 'Bu'

                for square in all_squares:
                    if square.color_name == target_color_name:
                        side.red = square.red
                        side.green = square.green
                        side.blue = square.blue
                        side.color = square.color
                        side.color_name = square.color_name
                        break
                else:
                    raise Exception("%s: could not determine color, target %s" % (side, target_color_name))

        with open('/tmp/rubiks-color-resolver.html', 'a') as fh:
            fh.write('<div id="colormapping">\n')
            fh.write('<h1>Side => Color Mapping</h1>\n')
            fh.write('<ul>\n')
            for side_name in self.side_order:
                side = self.sides[side_name]
                fh.write('<li>%s => %s</li>\n' % (side_name, side.color_name))
            fh.write('</ul>\n')
            fh.write('</div>\n')

            fh.write('<div id="anchorsquares">\n')
            fh.write('<h1>Anchor Squares</h1>\n')
            for anchor_square in self.anchor_squares:
                fh.write("<div class='square' title='RGB (%d, %d, %d)' style='background-color: #%02x%02x%02x;'><span>%02d/%s</span></div>\n" %
                         (anchor_square.color.red, anchor_square.color.green, anchor_square.color.blue,
                          anchor_square.color.red, anchor_square.color.green, anchor_square.color.blue,
                          anchor_square.position, anchor_square.color_name))
            fh.write('</div>\n')

    def create_corner_objects(self):
        # Corners
        self.corners = []

        # U
        self.corners.append(Corner(self, self.sideU.corner_pos[0], self.sideL.corner_pos[0], self.sideB.corner_pos[1]))
        self.corners.append(Corner(self, self.sideU.corner_pos[1], self.sideB.corner_pos[0], self.sideR.corner_pos[1]))
        self.corners.append(Corner(self, self.sideU.corner_pos[2], self.sideF.corner_pos[0], self.sideL.corner_pos[1]))
        self.corners.append(Corner(self, self.sideU.corner_pos[3], self.sideR.corner_pos[0], self.sideF.corner_pos[1]))

        # D
        self.corners.append(Corner(self, self.sideD.corner_pos[0], self.sideL.corner_pos[3], self.sideF.corner_pos[2]))
        self.corners.append(Corner(self, self.sideD.corner_pos[1], self.sideF.corner_pos[3], self.sideR.corner_pos[2]))
        self.corners.append(Corner(self, self.sideD.corner_pos[2], self.sideB.corner_pos[3], self.sideL.corner_pos[2]))
        self.corners.append(Corner(self, self.sideD.corner_pos[3], self.sideR.corner_pos[3], self.sideB.corner_pos[2]))

    def identify_corner_squares(self):
        self.valid_corner_colors = []
        self.valid_corner_colors.append((self.sideU.color, self.sideF.color, self.sideL.color))
        self.valid_corner_colors.append((self.sideU.color, self.sideR.color, self.sideF.color))
        self.valid_corner_colors.append((self.sideU.color, self.sideL.color, self.sideB.color))
        self.valid_corner_colors.append((self.sideU.color, self.sideB.color, self.sideR.color))

        self.valid_corner_colors.append((self.sideD.color, self.sideL.color, self.sideF.color))
        self.valid_corner_colors.append((self.sideD.color, self.sideF.color, self.sideR.color))
        self.valid_corner_colors.append((self.sideD.color, self.sideB.color, self.sideL.color))
        self.valid_corner_colors.append((self.sideD.color, self.sideR.color, self.sideB.color))
        self.valid_corner_colors = sorted(self.valid_corner_colors)

    def max_orbit_index(self, orbit_id):

        if (self.width == 4 or self.width == 6 or
            (self.width == 5 and orbit_id == 0) or
            (self.width == 7 and (orbit_id == 0 or orbit_id == 1))):
            return 1

        if self.width > 7:
            raise Exception("Add max_orbit_index() support for this size cube")

        return 0

    def identify_edge_squares(self):

        # valid_edges are the color combos that we need to look for. edges are Edge
        # objects, eventually we try to fill in the colors for each Edge object with
        # a color tuple from valid_edges
        self.valid_edge_colors = []
        self.edges = []

        num_of_edge_squares_per_side = len(self.sideU.edge_squares)

        # A 2x2x2 has no edges
        if not num_of_edge_squares_per_side:
            return

        for orbit_id in range(self.orbits):
            self.valid_edge_colors.append((self.sideU.color, self.sideB.color, orbit_id))
            self.valid_edge_colors.append((self.sideU.color, self.sideL.color, orbit_id))
            self.valid_edge_colors.append((self.sideU.color, self.sideF.color, orbit_id))
            self.valid_edge_colors.append((self.sideU.color, self.sideR.color, orbit_id))

            self.valid_edge_colors.append((self.sideF.color, self.sideL.color, orbit_id))
            self.valid_edge_colors.append((self.sideF.color, self.sideR.color, orbit_id))

            self.valid_edge_colors.append((self.sideB.color, self.sideL.color, orbit_id))
            self.valid_edge_colors.append((self.sideB.color, self.sideR.color, orbit_id))

            self.valid_edge_colors.append((self.sideD.color, self.sideF.color, orbit_id))
            self.valid_edge_colors.append((self.sideD.color, self.sideL.color, orbit_id))
            self.valid_edge_colors.append((self.sideD.color, self.sideR.color, orbit_id))
            self.valid_edge_colors.append((self.sideD.color, self.sideB.color, orbit_id))

            if self.max_orbit_index(orbit_id):
                self.valid_edge_colors.append((self.sideU.color, self.sideB.color, orbit_id))
                self.valid_edge_colors.append((self.sideU.color, self.sideL.color, orbit_id))
                self.valid_edge_colors.append((self.sideU.color, self.sideF.color, orbit_id))
                self.valid_edge_colors.append((self.sideU.color, self.sideR.color, orbit_id))

                self.valid_edge_colors.append((self.sideF.color, self.sideL.color, orbit_id))
                self.valid_edge_colors.append((self.sideF.color, self.sideR.color, orbit_id))

                self.valid_edge_colors.append((self.sideB.color, self.sideL.color, orbit_id))
                self.valid_edge_colors.append((self.sideB.color, self.sideR.color, orbit_id))

                self.valid_edge_colors.append((self.sideD.color, self.sideF.color, orbit_id))
                self.valid_edge_colors.append((self.sideD.color, self.sideL.color, orbit_id))
                self.valid_edge_colors.append((self.sideD.color, self.sideR.color, orbit_id))
                self.valid_edge_colors.append((self.sideD.color, self.sideB.color, orbit_id))
        self.valid_edge_colors = sorted(self.valid_edge_colors)

        # U and B
        for (edge_index, (pos1, pos2)) in enumerate(zip(self.sideU.edge_north_pos, reversed(self.sideB.edge_north_pos))):
            self.edges.append(Edge(self, pos1, pos2, edge_index))

        # U and L
        for (edge_index, (pos1, pos2)) in enumerate(zip(self.sideU.edge_west_pos, self.sideL.edge_north_pos)):
            self.edges.append(Edge(self, pos1, pos2, edge_index))

        # U and F
        for (edge_index, (pos1, pos2)) in enumerate(zip(self.sideU.edge_south_pos, self.sideF.edge_north_pos)):
            self.edges.append(Edge(self, pos1, pos2, edge_index))

        # U and R
        for (edge_index, (pos1, pos2)) in enumerate(zip(self.sideU.edge_east_pos, reversed(self.sideR.edge_north_pos))):
            self.edges.append(Edge(self, pos1, pos2, edge_index))

        # F and L
        for (edge_index, (pos1, pos2)) in enumerate(zip(self.sideL.edge_east_pos, self.sideF.edge_west_pos)):
            self.edges.append(Edge(self, pos1, pos2, edge_index))

        # F and R
        for (edge_index, (pos1, pos2)) in enumerate(zip(self.sideF.edge_east_pos, self.sideR.edge_west_pos)):
            self.edges.append(Edge(self, pos1, pos2, edge_index))

        # F and D
        for (edge_index, (pos1, pos2)) in enumerate(zip(self.sideF.edge_south_pos, self.sideD.edge_north_pos)):
            self.edges.append(Edge(self, pos1, pos2, edge_index))

        # L and B
        for (edge_index, (pos1, pos2)) in enumerate(zip(self.sideL.edge_west_pos, self.sideB.edge_east_pos)):
            self.edges.append(Edge(self, pos1, pos2, edge_index))

        # L and D
        for (edge_index, (pos1, pos2)) in enumerate(zip(self.sideL.edge_south_pos, reversed(self.sideD.edge_west_pos))):
            self.edges.append(Edge(self, pos1, pos2, edge_index))

        # R and D
        for (edge_index, (pos1, pos2)) in enumerate(zip(self.sideR.edge_south_pos, self.sideD.edge_east_pos)):
            self.edges.append(Edge(self, pos1, pos2, edge_index))

        # R and B
        for (edge_index, (pos1, pos2)) in enumerate(zip(self.sideR.edge_east_pos, self.sideB.edge_west_pos)):
            self.edges.append(Edge(self, pos1, pos2, edge_index))

        # B and D
        for (edge_index, (pos1, pos2)) in enumerate(zip(reversed(self.sideB.edge_south_pos), self.sideD.edge_south_pos)):
            self.edges.append(Edge(self, pos1, pos2, edge_index))

    def assign_color_names(self, squares_lists):
        assert len(squares_lists) == 6, "There are %d squares_list, there should be 6" % len(squares_lists)
        #log.info("SQUARES_LIST:\n{}\n".format(pformat(squares_lists)))

        # Assign a color name to each squares in each square_list. Compute
        # which naming scheme results in the least total color distance in
        # terms of the assigned color name vs. the colors in crayola_colors.
        min_distance = None
        min_distance_permutation = None

        for permutation in permutations(self.crayola_colors.keys()):
            distance = 0

            for (index, squares_list) in enumerate(squares_lists):
                color_name = permutation[index]
                color_obj = self.crayola_colors[color_name]

                for cluster_square in squares_list:
                    distance += get_euclidean_lab_distance(cluster_square.lab, color_obj)

            if min_distance is None or distance < min_distance:
                min_distance = distance
                min_distance_permutation = permutation
                log.info("PERMUTATION {}, DISTANCE {:,} (NEW MIN)".format(permutation, int(distance)))
            #else:
            #    log.info("PERMUTATION {}, DISTANCE {}".format(permutation, distance))

        for (index, squares_list) in enumerate(squares_lists):
            color_name = min_distance_permutation[index]

            for cluster_square in squares_list:
                cluster_square.color_name = color_name

                # Find the Square object for this ClusterSquare
                square = self.get_square(cluster_square.index)
                square.color_name = color_name

    def resolve_edge_squares_experiment(self):
        """
        Use traveling salesman algorithm to sort the colors
        """

        # Nothing to be done for 2x2x2
        if self.width == 2:
            return

        for target_orbit_id in range(self.orbits):
            log.warning('Resolve edges for orbit %d' % target_orbit_id)
            edge_colors = []

            for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
                for square in side.edge_squares:
                    orbit_id = edge_orbit_id[self.width][square.position]
                    log.info("{}: {}, position {}, orbit_id {}".format(self.width, square, square.position, orbit_id))

                    if orbit_id == target_orbit_id:
                        edge_colors.append((square.position, square.rgb))

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

            self.assign_color_names(sorted_edge_colors_cluster_squares)
            self.write_colors(
                'edges - orbit %d' % target_orbit_id,
                sorted_edge_colors_cluster_squares)

    def resolve_corner_squares_experiment(self):
        """
        Use traveling salesman algorithm to sort the colors
        """
        log.warning('Resolve corners')
        corner_colors = []

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for square in side.corner_squares:
                corner_colors.append((square.position, square.rgb))

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

        self.assign_color_names(sorted_corner_colors_cluster_squares)
        self.write_colors('corners', sorted_corner_colors_cluster_squares)

    def resolve_center_squares_experiment(self):
        """
        Use traveling salesman algorithm to sort the colors
        """

        # Nothing to be done for 2x2x2
        if self.width == 2:
            return

        log.warning('Resolve centers')
        center_colors = []

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for square in side.center_squares:
                center_colors.append((square.position, square.rgb))

        sorted_center_colors = traveling_salesman(center_colors, "euclidean")
        sorted_center_colors_cluster_squares = []
        squares_list = []
        squares_per_cluster = int(len(sorted_center_colors) / 6)

        for (index, (square_index, rgb)) in enumerate(sorted_center_colors):
            index += 1
            squares_list.append(ClusterSquare(square_index, rgb))
            if index % squares_per_cluster == 0:
                sorted_center_colors_cluster_squares.append(squares_list)
                squares_list = []

        self.assign_color_names(sorted_center_colors_cluster_squares)
        self.write_colors('centers', sorted_center_colors_cluster_squares)

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
            square1 = self.state[square_index1]
            square2 = self.state[square_index2]
            square3 = self.state[square_index3]
            corner_str = ''.join(sorted([square1, square2, square3]))
            current_corners.append(corner_str)

        if debug:
            log.info("to_check:\n%s" % pformat(to_check))
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

    def get_edge_swap_count(self, edges_paired, orbit, debug=False):
        needed_edges = []
        to_check = []

        # should not happen
        if edges_paired and orbit is not None:
            raise Exception("edges_paired is True and orbit is %s" % orbit)

        edges_per_side = len(self.sideU.edge_north_pos)

        # Upper
        for (edge_index, square_index) in enumerate(self.sideU.edge_north_pos):
            if edges_paired:
                to_check.append(square_index)
                needed_edges.append('UB')
                break
            else:
                if orbit_matches(edges_per_side, orbit, edge_index):
                    to_check.append(square_index)
                    needed_edges.append('UB%d' % edge_index)

        for (edge_index, square_index) in enumerate(reversed(self.sideU.edge_west_pos)):
            if edges_paired:
                to_check.append(square_index)
                needed_edges.append('UL')
                break
            else:
                if orbit_matches(edges_per_side, orbit, edge_index):
                    to_check.append(square_index)
                    needed_edges.append('UL%d' % edge_index)

        for (edge_index, square_index) in enumerate(reversed(self.sideU.edge_south_pos)):
            if edges_paired:
                to_check.append(square_index)
                needed_edges.append('UF')
                break
            else:
                if orbit_matches(edges_per_side, orbit, edge_index):
                    to_check.append(square_index)
                    needed_edges.append('UF%d' % edge_index)

        for (edge_index, square_index) in enumerate(self.sideU.edge_east_pos):
            if edges_paired:
                to_check.append(square_index)
                needed_edges.append('UR')
                break
            else:
                if orbit_matches(edges_per_side, orbit, edge_index):
                    to_check.append(square_index)
                    needed_edges.append('UR%d' % edge_index)


        # Left
        for (edge_index, square_index) in enumerate(reversed(self.sideL.edge_west_pos)):
            if edges_paired:
                to_check.append(square_index)
                needed_edges.append('LB')
                break
            else:
                if orbit_matches(edges_per_side, orbit, edge_index):
                    to_check.append(square_index)
                    needed_edges.append('LB%d' % edge_index)

        for (edge_index, square_index) in enumerate(self.sideL.edge_east_pos):
            if edges_paired:
                to_check.append(square_index)
                needed_edges.append('LF')
                break
            else:
                if orbit_matches(edges_per_side, orbit, edge_index):
                    to_check.append(square_index)
                    needed_edges.append('LF%d' % edge_index)


        # Right
        for (edge_index, square_index) in enumerate(reversed(self.sideR.edge_west_pos)):
            if edges_paired:
                to_check.append(square_index)
                needed_edges.append('RF')
                break
            else:
                if orbit_matches(edges_per_side, orbit, edge_index):
                    to_check.append(square_index)
                    needed_edges.append('RF%d' % edge_index)

        for (edge_index, square_index) in enumerate(self.sideR.edge_east_pos):
            if edges_paired:
                to_check.append(square_index)
                needed_edges.append('RB')
                break
            else:
                if orbit_matches(edges_per_side, orbit, edge_index):
                    to_check.append(square_index)
                    needed_edges.append('RB%d' % edge_index)

        # Down
        for (edge_index, square_index) in enumerate(self.sideD.edge_north_pos):
            if edges_paired:
                to_check.append(square_index)
                needed_edges.append('DF')
                break
            else:
                if orbit_matches(edges_per_side, orbit, edge_index):
                    to_check.append(square_index)
                    needed_edges.append('DF%d' % edge_index)

        for (edge_index, square_index) in enumerate(reversed(self.sideD.edge_west_pos)):
            if edges_paired:
                to_check.append(square_index)
                needed_edges.append('DL')
                break
            else:
                if orbit_matches(edges_per_side, orbit, edge_index):
                    to_check.append(square_index)
                    needed_edges.append('DL%d' % edge_index)

        for (edge_index, square_index) in enumerate(reversed(self.sideD.edge_south_pos)):
            if edges_paired:
                to_check.append(square_index)
                needed_edges.append('DB')
                break
            else:
                if orbit_matches(edges_per_side, orbit, edge_index):
                    to_check.append(square_index)
                    needed_edges.append('DB%d' % edge_index)

        for (edge_index, square_index) in enumerate(self.sideD.edge_east_pos):
            if edges_paired:
                to_check.append(square_index)
                needed_edges.append('DR')
                break
            else:
                if orbit_matches(edges_per_side, orbit, edge_index):
                    to_check.append(square_index)
                    needed_edges.append('DR%d' % edge_index)

        if debug:
            to_check_str = ''

            for x in to_check:
                if edges_paired:
                    to_check_str += "%3s" % x
                else:
                    to_check_str += "%4s" % x

            log.info("to_check     :%s" % to_check_str)
            log.info("needed edges : %s" % ' '.join(needed_edges))

        current_edges = []

        for square_index in to_check:
            side = self.get_side(square_index)
            partner_index = side.get_wing_partner(square_index)
            square1 = self.state[square_index]
            square2 = self.state[partner_index]

            if square1 in ('U', 'D'):
                wing_str = square1 + square2
            elif square2 in ('U', 'D'):
                wing_str = square2 + square1
            elif square1 in ('L', 'R'):
                wing_str = square1 + square2
            elif square2 in ('L', 'R'):
                wing_str = square2 + square1
            else:
                raise Exception("Could not determine wing_str for (%s, %s)" % (square1, square2))

            if not edges_paired:
                # - backup the current state
                # - add an 'x' to the end of the square_index/partner_index
                # - move square_index/partner_index to its final edge location
                # - look for the 'x' to determine if this is the '0' vs '1' wing
                # - restore the original state

                square1_with_x = square1 + 'x'
                square2_with_x = square2 + 'x'

                original_state = self.state[:]
                original_solution = self.solution[:]
                self.state[square_index] = square1_with_x
                self.state[partner_index] = square2_with_x

                # 'UB0', 'UB1', 'UL0', 'UL1', 'UF0', 'UF1', 'UR0', 'UR1',
                # 'LB0', 'LB1', 'LF0', 'LF1', 'RF0', 'RF1', 'RB0', 'RB1',
                # 'DF0', 'DF1', 'DL0', 'DL1', 'DB0', 'DB1', 'DR0', 'DR1
                if wing_str == 'UB':
                    self.move_wing_to_U_north(square_index)
                    edge_to_check = self.sideU.edge_north_pos
                    target_side = self.sideU

                elif wing_str == 'UL':
                    self.move_wing_to_U_west(square_index)
                    edge_to_check = reversed(self.sideU.edge_west_pos)
                    target_side = self.sideU

                elif wing_str == 'UF':
                    self.move_wing_to_U_south(square_index)
                    edge_to_check = reversed(self.sideU.edge_south_pos)
                    target_side = self.sideU

                elif wing_str == 'UR':
                    self.move_wing_to_U_east(square_index)
                    edge_to_check = self.sideU.edge_east_pos
                    target_side = self.sideU

                elif wing_str == 'LB':
                    self.move_wing_to_L_west(square_index)
                    edge_to_check = reversed(self.sideL.edge_west_pos)
                    target_side = self.sideL

                elif wing_str == 'LF':
                    self.move_wing_to_L_east(square_index)
                    edge_to_check = self.sideL.edge_east_pos
                    target_side = self.sideL

                elif wing_str == 'RF':
                    self.move_wing_to_R_west(square_index)
                    edge_to_check = reversed(self.sideR.edge_west_pos)
                    target_side = self.sideR

                elif wing_str == 'RB':
                    self.move_wing_to_R_east(square_index)
                    edge_to_check = self.sideR.edge_east_pos
                    target_side = self.sideR

                elif wing_str == 'DF':
                    self.move_wing_to_D_north(square_index)
                    edge_to_check = self.sideD.edge_north_pos
                    target_side = self.sideD

                elif wing_str == 'DL':
                    self.move_wing_to_D_west(square_index)
                    edge_to_check = reversed(self.sideD.edge_west_pos)
                    target_side = self.sideD

                elif wing_str == 'DB':
                    self.move_wing_to_D_south(square_index)
                    edge_to_check = reversed(self.sideD.edge_south_pos)
                    target_side = self.sideD

                elif wing_str == 'DR':
                    self.move_wing_to_D_east(square_index)
                    edge_to_check = self.sideD.edge_east_pos
                    target_side = self.sideD

                else:
                    raise Exception("invalid wing %s" % wing_str)

                for (edge_index, wing_index) in enumerate(edge_to_check):
                    wing_value = self.state[wing_index]

                    if wing_value.endswith('x'):
                        if wing_value.startswith(target_side.name):
                            wing_str += str(edge_index)
                        else:
                            max_edge_index = len(target_side.edge_east_pos) - 1
                            wing_str += str(max_edge_index - edge_index)
                        break
                else:
                    raise Exception("Could not find wing %s (%d, %d) among %s" % (wing_str, square_index, partner_index, str(edge_to_check)))

                self.state = original_state[:]
                self.solution = original_solution[:]

            current_edges.append(wing_str)

        if debug:
            log.info("current edges: %s" % ' '.join(current_edges))

        return get_swap_count(needed_edges, current_edges, debug)

    def edge_swaps_even(self, edges_paired, orbit, debug):
        if self.get_edge_swap_count(edges_paired, orbit, debug) % 2 == 0:
            return True
        return False

    def edge_swaps_odd(self, edges_paired, orbit, debug):
        if self.get_edge_swap_count(edges_paired, orbit, debug) % 2 == 1:
            return True
        return False

    def validate_parity(self):
        self.set_state()

        if self.width == 3:
            '''
            http://www.ryanheise.com/cube/parity.html

            When considering the permutation of all edges and corners together, the
            overall parity must be even, as dictated by laws of the cube. However,
            when considering only edges or corners alone, it is possible for their
            parity to be either even or odd. To obey the laws of the cube, if the edge
            parity is even then the corner parity must also be even, and if the edge
            parity is odd then the corner parity must also be odd.
            '''
            debug = False
            edges_even = self.edge_swaps_even(True, None, debug)
            corners_even = self.corner_swaps_even(debug)

            if edges_even != corners_even:
                log.warning("edges_even %s != corners_even %s, swap most ambiguous corner or edge to create valid parity" % (edges_even, corners_even))
                distances = []

                # which two corners are the closest in terms of color
                for cornerA in self.corners:
                    for cornerB in self.corners:
                        if cornerA == cornerB:
                            continue

                        distance = cornerA.color_distance(cornerB.square1.color, cornerB.square2.color, cornerB.square3.color)
                        distance = float(distance / 3)
                        distances.append((distance, cornerA, cornerB))

                # which two edges are the closest in terms of color
                for edgeA in self.edges:
                    for edgeB in self.edges:
                        if edgeA == edgeB:
                            continue

                        distance = edgeA.color_distance(edgeB.square1.color, edgeB.square2.color)
                        distance = float(distance / 2)
                        distances.append((distance, edgeA, edgeB))

                distances = sorted(distances)
                log.info("distances\n%s\n" % pformat(distances))
                (_, corner_or_edgeA, corner_or_edgeB) = distances[0]

                if isinstance(corner_or_edgeA, Corner):
                    cornerA = corner_or_edgeA
                    cornerB = corner_or_edgeB

                    tmp_cornerA_square1_color = cornerA.square1.color
                    tmp_cornerA_square2_color = cornerA.square2.color
                    tmp_cornerA_square3_color = cornerA.square3.color
                    tmp_cornerB_square1_color = cornerB.square1.color
                    tmp_cornerB_square2_color = cornerB.square2.color
                    tmp_cornerB_square3_color = cornerB.square3.color

                    cornerA.update_colors(tmp_cornerB_square1_color, tmp_cornerB_square2_color, tmp_cornerB_square3_color)
                    cornerB.update_colors(tmp_cornerA_square1_color, tmp_cornerA_square2_color, tmp_cornerA_square3_color)

                else:
                    edgeA = corner_or_edgeA
                    edgeB = corner_or_edgeB

                    tmp_edgeA_square1_color = edgeA.square1.color
                    tmp_edgeA_square2_color = edgeA.square2.color
                    tmp_edgeB_square1_color = edgeB.square1.color
                    tmp_edgeB_square2_color = edgeB.square2.color

                    edgeA.update_colors(tmp_edgeB_square1_color, tmp_edgeB_square2_color)
                    edgeB.update_colors(tmp_edgeA_square1_color, tmp_edgeA_square2_color)

                self.state = []
                self.set_state()
                edges_even = self.edge_swaps_even(True, None, debug)
                corners_even = self.corner_swaps_even(debug)
                log.warning("edges_even %s, corners_even %s" % (edges_even, corners_even))

    def write_final_cube(self):
        data = self.cube_for_json()
        cube = ['dummy', ]

        for square_index in sorted(data['squares'].keys()):
            value = data['squares'][square_index]
            html_colors = data['sides'][value['finalSide']]['colorHTML']
            cube.append((html_colors['red'], html_colors['green'], html_colors['blue']))

        self.write_cube('Final Cube', cube)

    def crunch_colors(self):
        #self.anchor_squares = []

        #self.create_corner_objects()
        #self.identify_anchor_squares()
        #self.identify_corner_squares()
        #self.identify_edge_squares()
        self.print_cube()

        self.resolve_edge_squares_experiment()
        self.resolve_corner_squares_experiment()
        self.resolve_center_squares_experiment()

        #self.validate_parity()
        self.print_cube()
        self.print_layout()
        self.write_final_cube()
        self.www_footer()
