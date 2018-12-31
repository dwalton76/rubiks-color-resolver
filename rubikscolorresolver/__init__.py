
from tsp_solver.greedy import solve_tsp
from collections import OrderedDict
from copy import deepcopy, copy
from itertools import permutations
from math import atan2, cos, degrees, exp, factorial, radians, sin, sqrt, ceil
from pprint import pformat
import itertools
import json
import logging
import os
import sys

if sys.version_info < (3,4):
    raise SystemError('Must be using Python 3.4 or higher')

log = logging.getLogger(__name__)


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

edge_orbit_wing_pairs = {
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
    )
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
        ("x-centers", (
            7, 9, 17, 19, # Upper
            32, 34, 42, 44, # Left
            57, 59, 67, 69, # Front
            82, 84, 92, 94, # Right
            107, 109, 117, 119, # Back
            132, 134, 142, 144, # Down
        )),
        ("t-centers", (
            8, 12, 14, 18, # Upper
            33, 37, 39, 43, # Left
            58, 62, 64, 68, # Front
            83, 87, 89, 93, # Right
            108, 112, 114, 118, # Back
            133, 137, 139, 143, # Down
        )),
        ("middle-centers", (13, 38, 63, 88, 113, 138)),
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


def traveling_salesman(colors, alg):

    # build a full matrix of cie2000 distances
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
                distance = delta_e_cie2000(x_lab, y_lab)

            elif alg == "euclidean":
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

class RubiksColorSolverGeneric(object):

    def __init__(self, width):
        self.width = width
        self.height = width
        self.squares_per_side = self.width * self.width
        self.scan_data = {}
        self.orbits = int(ceil((self.width - 2) / 2.0))
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
                lab = rgb2lab((red, green, blue))

                fh.write("    <div class='square col%d' title='RGB (%d, %d, %d), Lab (%s, %s, %s)' style='background-color: #%02x%02x%02x;'><span>%02d</span></div>\n" %
                    (col,
                     red, green, blue,
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
                total_distance = 0

                for cluster_square in cluster_square_list:
                    (red, green, blue) = cluster_square.rgb
                    lab = rgb2lab((red, green, blue))

                    fh.write("<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s)'>%d</span>\n" %
                        (red, green, blue,
                         red, green, blue,
                         lab.L, lab.a, lab.b,
                         cluster_square.index))

                fh.write("<br>")
            fh.write("</div>\n")

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
                #log.info("PERMUTATION {}, DISTANCE {:,} (NEW MIN)".format(permutation, int(distance)))
            #else:
            #    log.info("PERMUTATION {}, DISTANCE {}".format(permutation, distance))

        for (index, squares_list) in enumerate(squares_lists):
            color_name = min_distance_permutation[index]

            for cluster_square in squares_list:
                cluster_square.color_name = color_name

                # Find the Square object for this ClusterSquare
                square = self.get_square(cluster_square.index)
                square.color_name = color_name

    def validate_edge_orbit(self, orbit_id):
        valid = True
        colors_to_flip = []

        # dwalton here now
        # We need to see which orange/red we can flip that will make the edges valid
        wing_pair_counts = {}

        for (square1_position, square2_position) in edge_orbit_wing_pairs[self.width][orbit_id]:
            square1 = self.get_square(square1_position)
            square2 = self.get_square(square2_position)
            wing_pair_string = ", ".join(sorted([square1.color_name, square2.color_name]))
            #log.info("({}, {}) is ({})".format(square1_position, square2_position, wing_pair_string))

            if wing_pair_string not in wing_pair_counts:
                wing_pair_counts[wing_pair_string] = 0
            wing_pair_counts[wing_pair_string] += 1

        for (wing_pair, count) in wing_pair_counts.items():
            if count != 2:
                valid = False
        log.info("wing_pair_counts:\n{}\n".format(pformat(wing_pair_counts)))
        log.info("valid: {}".format(valid))
        log.info("colors_to_flip: {}".format(colors_to_flip))
        return (valid, colors_to_flip)

    def resolve_edge_squares(self):
        """
        Use traveling salesman algorithm to sort the colors
        """

        # Nothing to be done for 2x2x2
        if self.width == 2:
            return

        for target_orbit_id in range(self.orbits):
            log.info('Resolve edges for orbit %d' % target_orbit_id)
            edge_colors = []

            for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
                for square in side.edge_squares:
                    orbit_id = edge_orbit_id[self.width][square.position]
                    #log.info("{}: {}, position {}, orbit_id {}".format(self.width, square, square.position, orbit_id))

                    if orbit_id == target_orbit_id:
                        edge_colors.append((square.position, square.rgb))

            #edge_colors.append((0, (0, 0, 0)))
            #edge_colors.append((999, (255, 255, 255)))
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
            (valid, colors_to_flip) = self.validate_edge_orbit(target_orbit_id)

            # dwalton
            if not valid:
                pass

            self.write_colors(
                'edges - orbit %d' % target_orbit_id,
                sorted_edge_colors_cluster_squares)

    def resolve_corner_squares(self):
        """
        Use traveling salesman algorithm to sort the colors
        """
        log.info('Resolve corners')
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

    def resolve_center_squares(self):
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
            self.write_colors(desc, sorted_center_colors_cluster_squares)

    def write_final_cube(self):
        data = self.cube_for_json()
        cube = ['dummy', ]

        for square_index in sorted(data['squares'].keys()):
            value = data['squares'][square_index]
            html_colors = data['sides'][value['finalSide']]['colorHTML']
            cube.append((html_colors['red'], html_colors['green'], html_colors['blue']))

        self.write_cube('Final Cube', cube)

    def crunch_colors(self):
        self.resolve_edge_squares()
        self.resolve_corner_squares()
        self.resolve_center_squares()

        self.print_cube()
        self.write_final_cube()
        self.www_footer()
