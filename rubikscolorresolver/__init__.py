#!/usr/bin/env python

from copy import deepcopy
from itertools import permutations
from math import atan2, cos, degrees, exp, factorial, radians, sin, sqrt
from kociemba.pykociemba.verify import verify as verify_parity
from pprint import pformat
import json
import logging
import sys

log = logging.getLogger(__name__)

# Calculating color distances is expensive in terms of CPU so
# cache the results
dcache = {}


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


class LabColor(object):

    def __init__(self, L, a, b):
        self.L = L
        self.a = a
        self.b = b
        self.name = None

    def __str__(self):
        return ("Lab (%s, %s, %s)" % (self.L, self.a, self.b))

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

    return LabColor(L, a, b)


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


def get_color_distance(c1, c2):
    try:
        return dcache[(c1, c2)]
    except KeyError:
        try:
            return dcache[(c2, c1)]
        except KeyError:
            distance = delta_e_cie2000(c1, c2)
            dcache[(c1, c2)] = distance
            return distance


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

    def __lt__(self, other):
        return self.position < other.position

    def find_closest_match(self, crayon_box, debug=False, set_color=True):
        cie_data = []

        for (color_name, color_obj) in crayon_box.items():
            distance = get_color_distance(self.rawcolor, color_obj)
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


class Edge(object):

    def __init__(self, cube, pos1, pos2):
        self.valid = False
        self.square1 = cube.get_square(pos1)
        self.square2 = cube.get_square(pos2)
        self.cube = cube
        self.dcache = {}

    def __str__(self):
        result = "%s%d/%s%d" %\
            (self.square1.side, self.square1.position,
             self.square2.side, self.square2.position)

        if self.square1.color and self.square2.color:
            result += " %s/%s" % (self.square1.color.name, self.square2.color.name)
        elif self.square1.color and not self.square2.color:
            result += " %s/None" % self.square1.color.name
        elif not self.square1.color and self.square2.color:
            result += " None/%s" % self.square2.color.name

        return result

    def __lt__(self, other):
        return 0

    def colors_match(self, colorA, colorB):
        if (colorA in (self.square1.color, self.square2.color) and
            colorB in (self.square1.color, self.square2.color)):
            return True
        return False

    def _get_color_distances(self, colorA, colorB):
        distanceAB = (get_color_distance(self.square1.rawcolor, colorA) +
                      get_color_distance(self.square2.rawcolor, colorB))

        distanceBA = (get_color_distance(self.square1.rawcolor, colorB) +
                      get_color_distance(self.square2.rawcolor, colorA))

        return (distanceAB, distanceBA)

    def color_distance(self, colorA, colorB):
        """
        Given two colors, return our total color distance
        """
        try:
            return self.dcache[(colorA, colorB)]
        except KeyError:
            value = min(self._get_color_distances(colorA, colorB))
            self.dcache[(colorA, colorB)] = value
            return value

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
        self.dcache = {}

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

    def __lt__(self, other):
        return 0

    def colors_match(self, colorA, colorB, colorC):
        if (colorA in (self.square1.color, self.square2.color, self.square3.color) and
            colorB in (self.square1.color, self.square2.color, self.square3.color) and
            colorC in (self.square1.color, self.square2.color, self.square3.color)):
            return True
        return False

    def _get_color_distances(self, colorA, colorB, colorC):
        distanceABC = (get_color_distance(self.square1.rawcolor, colorA) +
                       get_color_distance(self.square2.rawcolor, colorB) +
                       get_color_distance(self.square3.rawcolor, colorC))

        distanceCAB = (get_color_distance(self.square1.rawcolor, colorC) +
                       get_color_distance(self.square2.rawcolor, colorA) +
                       get_color_distance(self.square3.rawcolor, colorB))

        distanceBCA = (get_color_distance(self.square1.rawcolor, colorB) +
                       get_color_distance(self.square2.rawcolor, colorC) +
                       get_color_distance(self.square3.rawcolor, colorA))
        return (distanceABC, distanceCAB, distanceBCA)

    def color_distance(self, colorA, colorB, colorC):
        """
        Given three colors, return our total color distance
        """
        try:
            return self.dcache[(colorA, colorB, colorC)]
        except KeyError:
            value = min(self._get_color_distances(colorA, colorB, colorC))
            self.dcache[(colorA, colorB, colorC)] = value
            return value

    def update_colors(self, colorA, colorB, colorC):
        (distanceABC, distanceCAB, distanceBCA) = self._get_color_distances(colorA, colorB, colorC)
        min_distance = min(distanceABC, distanceCAB, distanceBCA)

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
        self.color = None  # Will be the color of the middle square
        self.squares = {}
        self.width = width
        self.squares_per_side = width * width
        self.center_squares = []
        self.edge_squares = []
        self.corner_squares = []

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
        return self.name

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
            #   blue = (3, 40, 146)
            #   red = (104, 4, 2)
            #
            'Wh': hashtag_rgb_to_labcolor('#ebfefa'),
            'Gr': hashtag_rgb_to_labcolor('#14694a'),
            'Ye': hashtag_rgb_to_labcolor('#d2d002'),
            'OR': hashtag_rgb_to_labcolor('#943509'),
            'Bu': hashtag_rgb_to_labcolor('#032892'),
            'Rd': hashtag_rgb_to_labcolor('#680402')
        }
        self.crayon_box = deepcopy(self.crayola_colors)

        # 8! = 40320
        # 7! = 5040
        # 6! = 720
        # 5! = 120
        # 4! = 24
        # With a limit of 40320 it takes 3.6s to resolve the colors for a cube
        # With a limit of  5040 it takes 1.5s to resolve the colors for a cube
        # With a limit of   720 it takes 1.2s to resolve the colors for a cube
        # These numbers are from a beefy server, not EV3
        self.edge_permutation_limit = 720
        self.corner_permutation_limit = 720

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
            side = self.get_side(position)
            side.set_square(position, red, green, blue)

        '''
        for side_name in self.side_order:
            side = self.sides[side_name]

            for (position, square) in side.squares.items():
                log.info("SCAN DATA %d: %s RGB (%d, %d, %d)" % (position, square, square.red, square.green, square.blue))
        '''

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

    def cube_for_kociemba_strict(self):
        data = []

        if self.sideU.mid_pos is not None:
            color_to_side_name = {}

            for side_name in self.side_order:
                side = self.sides[side_name]
                mid_square = side.squares[side.mid_pos]

                if mid_square.color_name in color_to_side_name:
                    log.info("color_to_side_name:\n%s" % pformat(color_to_side_name))
                    raise Exception("side %s with color %s, %s is already in color_to_side_name" % (side, mid_square.color_name, mid_square.color_name))
                color_to_side_name[mid_square.color_name] = side.name

            # log.info("cube_for_kociemba_strict:\n%s" % pformat(color_to_side_name))
        else:
            color_to_side_name = {
                'Wh' : 'U',
                'OR' : 'L',
                'Gr' : 'F',
                'Rd' : 'R',
                'Ye' : 'D',
                'Bu' : 'B'
            }

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                color_name = side.squares[x].color_name
                data.append(color_to_side_name[color_name])

        return data

    def sort_squares(self, target_square, squares_to_sort):
        rank = []
        for square in squares_to_sort:
            distance = get_color_distance(target_square.rawcolor, square.rawcolor)
            rank.append((distance, square))
        rank = list(sorted(rank))

        result = []
        for (distance, square) in rank:
            result.append(square)
        return result

    def valid_cube_parity(self, fake_corner_parity):
        # TODO
        return True

    def valid_edge_parity(self):
        return self.valid_cube_parity(True)

    def identify_anchor_squares(self, use_centers):

        if use_centers:
            num_of_center_squares_per_side = len(self.sideU.center_squares)
            to_keep = num_of_center_squares_per_side - 1

            # Build a list of the center squares from all six sides
            all_center_squares = []
            for side_name in self.side_order:
                side = self.sides[side_name]
                all_center_squares.extend(side.center_squares)

            # Take the first center square on the list and for a 4x4x4 cube find
            # the 3 (see 'to_keep' above) other center squares that are closest in color
            while all_center_squares:
                anchor_square = all_center_squares.pop(0)
                self.anchor_squares.append(anchor_square)
                log.info("center anchor square %s with color %s" % (anchor_square, anchor_square.color_name))

                if to_keep:
                    closest = self.sort_squares(anchor_square, all_center_squares)[0:to_keep]

                    for square in closest:
                        square.anchor_square = anchor_square
                        all_center_squares.remove(square)

        # use corners
        else:
            # If we are here we are dealing with a 2x2x2 cube
            to_keep = 3

            # Build a list of the corner squares from all six sides
            all_corner_squares = []
            for side_name in self.side_order:
                side = self.sides[side_name]
                all_corner_squares.extend(side.corner_squares)

            # Take the first corner square on the list and find the other
            # three (to_keep) corner squares that are closest in color
            while all_corner_squares:
                anchor_square = all_corner_squares.pop(0)
                self.anchor_squares.append(anchor_square)
                log.info("corner anchor square %s with color %s" % (anchor_square, anchor_square.color_name))

                closest = self.sort_squares(anchor_square, all_corner_squares)[0:to_keep]

                for square in closest:
                    all_corner_squares.remove(square)

        # Assign color names to each anchor_square. We compute which naming
        # scheme results in the least total color distance in terms of the anchor
        # square colors vs the colors in crayola_colors
        min_distance = None
        min_distance_permutation = None

        for permutation in permutations(self.crayola_colors.keys()):
            distance = 0

            for (anchor_square, color_name) in zip(self.anchor_squares, permutation):
                color_obj = self.crayola_colors[color_name]
                distance += get_color_distance(anchor_square.rawcolor, color_obj)

            if min_distance is None or distance < min_distance:
                min_distance = distance
                min_distance_permutation = permutation

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


        if use_centers:
            # Now that our anchor squares have been assigned a color/color_name, go back and
            # assign the same color/color_name to all of the other center_squares. This ends
            # up being a no-op for 2x2x2 and 3x3x3 but 4x4x4 and up larger this does something.
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
                side.color = side.squares[side.mid_pos].color
                side.color_name = side.squares[side.mid_pos].color_name
        else:
            '''
            color_to_side_name = {
                'Ye' : 'U',
                'Gr' : 'L',
                'OR' : 'F',
                'Bu' : 'R',
                'Wh' : 'D',
                'Rd' : 'B'
            }
            '''
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
                        side.color = square.color
                        side.color_name = square.color_name
                        break
                else:
                    raise Exception("%s: could not determine color, target %s" % (side, target_color_name))

    def identify_center_squares(self):
        num_of_center_squares_per_side = len(self.sideU.center_squares)
        self.anchor_squares = []

        # A 2x2x2 does not have center squares
        if not num_of_center_squares_per_side:
            return

        self.identify_anchor_squares(True)

    def identify_corner_squares(self):

        if not self.anchor_squares:
            self.identify_anchor_squares(False)

        self.valid_corners = []
        self.valid_corners.append((self.sideU.color, self.sideF.color, self.sideL.color))
        self.valid_corners.append((self.sideU.color, self.sideR.color, self.sideF.color))
        self.valid_corners.append((self.sideU.color, self.sideL.color, self.sideB.color))
        self.valid_corners.append((self.sideU.color, self.sideB.color, self.sideR.color))

        self.valid_corners.append((self.sideD.color, self.sideL.color, self.sideF.color))
        self.valid_corners.append((self.sideD.color, self.sideF.color, self.sideR.color))
        self.valid_corners.append((self.sideD.color, self.sideB.color, self.sideL.color))
        self.valid_corners.append((self.sideD.color, self.sideR.color, self.sideB.color))
        self.valid_corners = sorted(self.valid_corners)

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

    def identify_edge_squares(self):

        # valid_edges are the color combos that we need to look for. edges are Edge
        # objects, eventually we try to fill in the colors for each Edge object with
        # a color tuple from valid_edges
        self.valid_edges = []
        self.edges = []

        num_of_edge_squares_per_side = len(self.sideU.edge_squares)

        # A 2x2x2 has no edges
        if not num_of_edge_squares_per_side:
            return

        # For a 3x3x3 there is only one edge between F and U but for a 4x4x4
        # there are 2 of them and for a 5x5x5 there are 3 of them...so loop
        # so that we add the correct number
        for x in range(int(num_of_edge_squares_per_side/4)):
            self.valid_edges.append((self.sideU.color, self.sideB.color))
            self.valid_edges.append((self.sideU.color, self.sideL.color))
            self.valid_edges.append((self.sideU.color, self.sideF.color))
            self.valid_edges.append((self.sideU.color, self.sideR.color))

            self.valid_edges.append((self.sideF.color, self.sideL.color))
            self.valid_edges.append((self.sideF.color, self.sideR.color))

            self.valid_edges.append((self.sideB.color, self.sideL.color))
            self.valid_edges.append((self.sideB.color, self.sideR.color))

            self.valid_edges.append((self.sideD.color, self.sideF.color))
            self.valid_edges.append((self.sideD.color, self.sideL.color))
            self.valid_edges.append((self.sideD.color, self.sideR.color))
            self.valid_edges.append((self.sideD.color, self.sideB.color))
        self.valid_edges = sorted(self.valid_edges)

        # U and B
        for (pos1, pos2) in zip(self.sideU.edge_north_pos, reversed(self.sideB.edge_north_pos)):
            self.edges.append(Edge(self, pos1, pos2))

        # U and L
        for (pos1, pos2) in zip(self.sideU.edge_west_pos, self.sideL.edge_north_pos):
            self.edges.append(Edge(self, pos1, pos2))

        # U and F
        for (pos1, pos2) in zip(self.sideU.edge_south_pos, self.sideF.edge_north_pos):
            self.edges.append(Edge(self, pos1, pos2))

        # U and R
        for (pos1, pos2) in zip(self.sideU.edge_east_pos, self.sideR.edge_north_pos):
            self.edges.append(Edge(self, pos1, pos2))

        # F and L
        for (pos1, pos2) in zip(self.sideF.edge_west_pos, self.sideL.edge_east_pos):
            self.edges.append(Edge(self, pos1, pos2))

        # F and R
        for (pos1, pos2) in zip(self.sideF.edge_east_pos, self.sideR.edge_west_pos):
            self.edges.append(Edge(self, pos1, pos2))

        # F and D
        for (pos1, pos2) in zip(self.sideF.edge_south_pos, self.sideD.edge_north_pos):
            self.edges.append(Edge(self, pos1, pos2))

        # L and B
        for (pos1, pos2) in zip(self.sideL.edge_west_pos, self.sideB.edge_east_pos):
            self.edges.append(Edge(self, pos1, pos2))

        # L and D
        for (pos1, pos2) in zip(self.sideL.edge_south_pos, self.sideD.edge_west_pos):
            self.edges.append(Edge(self, pos1, pos2))

        # R and D
        for (pos1, pos2) in zip(self.sideR.edge_south_pos, self.sideD.edge_east_pos):
            self.edges.append(Edge(self, pos1, pos2))

        # R and B
        for (pos1, pos2) in zip(self.sideR.edge_east_pos, self.sideB.edge_west_pos):
            self.edges.append(Edge(self, pos1, pos2))

        # B and D
        for (pos1, pos2) in zip(reversed(self.sideB.edge_south_pos), self.sideD.edge_south_pos):
            self.edges.append(Edge(self, pos1, pos2))

    def resolve_edge_squares(self):

        # A 2x2x2 will not have edges
        if not self.edges:
            return

        log.info('Resolve edges')

        # Initially we flag all of our Edge objects as invalid
        for edge in self.edges:
            edge.valid = False

        # And our 'needed' list will hold all 12 edges
        needed_edges = sorted(self.valid_edges)

        unresolved_edges = [edge for edge in self.edges if edge.valid is False]
        permutation_count = factorial(len(needed_edges))
        best_match_total_distance = 0

        # 12 edges will mean 479,001,600 permutations which is too many.  Examine
        # all 12 edges and find the one we can match against a needed_edge that produces
        # the lowest color distance. update_colors() for this edge, mark it as
        # valid and remove it from the needed_edges.  Repeat this until the
        # number of permutations of needed_edges is down to our permutation_limit.
        if permutation_count > self.edge_permutation_limit:
            scores_by_edge_pair = {}

            for edge in unresolved_edges:
                for (colorA, colorB) in needed_edges:
                    distance = edge.color_distance(colorA, colorB)

                    if edge not in scores_by_edge_pair:
                        scores_by_edge_pair[edge] = []

                    scores_by_edge_pair[edge].append((distance, (colorA, colorB)))

            # For each edge keep the top two scores
            for (edge, value) in scores_by_edge_pair.items():
                scores_by_edge_pair[edge] = sorted(value)[0:2]

            # Now compute the delta between the first place score and the second place score for each edge
            score_delta = []

            for (edge, value) in scores_by_edge_pair.items():
                first_place_distance = value[0][0]
                second_place_distance = value[1][0]
                first_place_color = value[0][1]

                for (distance, (colorA, colorB)) in value:
                    log.info("edge_best_match %s, score %s, colorA %s, colorB %s" % (edge, distance, colorA.name, colorB.name))
                log.info('')
                score_delta.append((second_place_distance - first_place_distance, first_place_distance, edge, (first_place_color[0], first_place_color[1])))

            score_delta = list(reversed(sorted(score_delta)))

            log.info("SCORES DELTA")
            for (delta_distance, distance, edge_best_match, (colorA, colorB)) in score_delta:
                log.info("dd %s, %s, edge_best_match %s, colorA %s, colorB %s" %
                     (delta_distance, distance, edge_best_match, colorA.name, colorB.name))

            # for edge in unresolved_edges:
            #     log.info("unresolved_edge: %s" % edge)
            #
            # for (colorA, colorB) in needed_edges:
            #     log.info("needed_edges: %s/%s" % (colorA.name, colorB.name))

            while permutation_count > self.edge_permutation_limit:

                for (delta_distance, distance, edge_best_match, (colorA, colorB)) in score_delta:
                    if edge_best_match in unresolved_edges and (colorA, colorB) in needed_edges:
                        break
                else:
                    log.warning("permutation_count %d, edge_permutation_limit %d" % (permutation_count, self.edge_permutation_limit))
                    for (colorA, colorB) in needed_edges:
                        log.warning("needed_edge: %s/%s" % (colorA.name, colorB.name))

                    for edge in unresolved_edges:
                        log.warning("unresolved_edge: %s" % edge)

                    raise Exception("Did not find an edge in unresolved_edges")

                best_match_total_distance += distance
                edge_best_match.update_colors(colorA, colorB)
                edge_best_match.valid = True
                needed_edges.remove((colorA, colorB))

                unresolved_edges = [edge for edge in self.edges if edge.valid is False]
                permutation_count = factorial(len(needed_edges))
                log.info("%s/%s best match is %s with distance %s (permutations %d/%d)" %
                         (colorA.name, colorB.name, edge_best_match, distance, permutation_count, self.edge_permutation_limit))

        score_per_permutation = []

        log.info("Calculate edge score for each permutation")
        for edge_permutation in permutations(unresolved_edges):
            total_distance = 0

            for (edge, (colorA, colorB)) in zip(edge_permutation, needed_edges):
                total_distance += edge.color_distance(colorA, colorB)

            score_per_permutation.append((total_distance, edge_permutation))

        score_per_permutation = sorted(score_per_permutation)

        # Now traverse the permutations from best score to worst. The first
        # permutation that produces a set of edges with valid parity is the
        # permutation we want (most of the time the first entry has valid parity).
        log.info("Find edge permutation with the lowest score with valid parity")

        for (_, permutation) in score_per_permutation:
            total_distance = best_match_total_distance

            for (edge_best_match, (colorA, colorB)) in zip(permutation, needed_edges):
                distance = edge_best_match.color_distance(colorA, colorB)
                total_distance += distance
                edge_best_match.update_colors(colorA, colorB)
                edge_best_match.valid = True

            if self.valid_edge_parity():
                log.info("%s/%s potential match is %s with distance %d" %
                         (colorA.name, colorB.name, edge_best_match, distance))
                log.info("Total distance: %d, edge parity is valid" % total_distance)
                break
            else:
                log.debug("Total distance: %d, edge parity is NOT valid" % total_distance)

        log.info('\n')

    def resolve_corner_squares(self):
        log.info('Resolve corners')

        # Initially we flag all of our Edge objects as invalid
        for corner in self.corners:
            corner.valid = False

        # And our 'needed' list will hold all 8 corners.
        needed_corners = sorted(self.valid_corners)

        unresolved_corners = [corner for corner in self.corners if corner.valid is False]
        permutation_count = factorial(len(needed_corners))
        best_match_total_distance = 0

        # 8 corners will mean 40320 permutations which is too many.  Examine
        # all 8 and find the one we can match against a needed_corner that produces
        # the lowest color distance. update_colors() for this corner, mark it as
        # valid and remove it from the needed_corners.  Repeat this until the
        # number of permutations of needed_corners is down to our permutation_limit.
        if permutation_count > self.corner_permutation_limit:

            scores_by_corner = {}

            for corner in unresolved_corners:
                for (colorA, colorB, colorC) in needed_corners:
                    distance = corner.color_distance(colorA, colorB, colorC)

                    if corner not in scores_by_corner:
                        scores_by_corner[corner] = []
                    scores_by_corner[corner].append((distance, (colorA, colorB, colorC)))

            # For each corner keep the top two scores
            for (corner, value) in scores_by_corner.items():
                scores_by_corner[corner] = sorted(value)[0:2]

            # Now compute the delta between the first place score and the second place score for each edge
            score_delta = []

            for (corner, value) in scores_by_corner.items():
                first_place_distance = value[0][0]
                second_place_distance = value[1][0]
                first_place_color = value[0][1]

                for (distance, (colorA, colorB, colorC)) in value:
                    log.info("corner_best_match %s, score %s, colorA %s, colorB %s, colorC %s" % (corner, distance, colorA.name, colorB.name, colorC.name))
                log.info('')
                score_delta.append((second_place_distance - first_place_distance, first_place_distance, corner, (first_place_color[0], first_place_color[1], first_place_color[2])))

            score_delta = list(reversed(sorted(score_delta)))

            log.info("SCORES DELTA")
            for (delta_distance, distance, corner_best_match, (colorA, colorB, colorC)) in score_delta:
                log.info("dd %s, %s, corner_best_match %s, colorA %s, colorB %s, colorC %s" %
                        (delta_distance, distance, corner_best_match, colorA.name, colorB.name, colorC.name))

            while permutation_count > self.corner_permutation_limit:

                for (delta_distance, distance, corner_best_match, (colorA, colorB, colorC)) in score_delta:
                    if corner_best_match in unresolved_corners and (colorA, colorB, colorC) in needed_corners:
                        break
                else:
                    raise Exception("Did not find a corner in unresolved_corners")

                best_match_total_distance += distance
                corner_best_match.update_colors(colorA, colorB, colorC)
                corner_best_match.valid = True
                needed_corners.remove((colorA, colorB, colorC))

                unresolved_corners = [corner for corner in self.corners if corner.valid is False]
                permutation_count = factorial(len(needed_corners))
                log.info("%s/%s/%s best match is %s with distance %d (total %d) (permutations %d/%d)" %
                         (colorA.name, colorB.name, colorC.name, corner_best_match,
                          distance, best_match_total_distance,
                          permutation_count, self.corner_permutation_limit))

        score_per_permutation = []

        # for corner in unresolved_corners:
        #     log.info("unresolved_corners: %s" % corner)
        #
        # for (colorA, colorB, colorC) in needed_corners:
        #     log.info("needed_corners: %s/%s/%s" % (colorA.name, colorB.name, colorC.name))

        for corner_permutation in permutations(unresolved_corners):
            total_distance = 0

            for (corner, (colorA, colorB, colorC)) in zip(corner_permutation, needed_corners):
                total_distance += corner.color_distance(colorA, colorB, colorC)

            score_per_permutation.append((total_distance, corner_permutation))

        score_per_permutation = sorted(score_per_permutation)
        # log.info("score_per_permutation:\n%s\n" % pformat(score_per_permutation[0:5]))

        # Now traverse the permutations from best score to worst. The first
        # permutation that produces a cube with valid parity is the permutation
        # we want (most of the time the first entry has valid parity).
        for (_, permutation) in score_per_permutation:
            total_distance = best_match_total_distance

            for (corner_best_match, (colorA, colorB, colorC)) in zip(permutation, needed_corners):
                distance = corner_best_match.color_distance(colorA, colorB, colorC)
                total_distance += distance
                corner_best_match.update_colors(colorA, colorB, colorC)
                corner_best_match.valid = True
                log.info("%s/%s/%s best match is %s with distance %d (%d total)" %
                         (colorA.name, colorB.name, colorC.name, corner_best_match, distance, total_distance))

            if self.valid_cube_parity(fake_corner_parity=False):
                log.info("Total distance: %d (%d from best_match), cube parity is valid" % (total_distance, best_match_total_distance))
                break
            else:
                log.info("Total distance: %d (%d from best_match), cube parity is NOT valid" % (total_distance, best_match_total_distance))

        log.info('\n')

    def crunch_colors(self):
        self.identify_center_squares()
        self.identify_corner_squares()
        self.identify_edge_squares()

        self.resolve_edge_squares()
        self.resolve_corner_squares()

        self.print_layout()
        self.print_cube()


# ******************************
# Original 3x3x3 code below here
# ******************************
class CubeSideOld(object):

    def __init__(self, cube, name):
        self.cube = cube
        self.name = name  # U, L, etc
        self.color = None  # Will be the color of the middle square
        self.squares = {}

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

        self.min_pos = (index * 9) + 1
        self.max_pos = (index * 9) + 9
        self.mid_pos = (self.min_pos + self.max_pos) / 2
        self.edge_pos = (self.min_pos + 1, self.min_pos + 3, self.min_pos + 5, self.min_pos + 7)
        self.corner_pos = (self.min_pos, self.min_pos + 2, self.min_pos + 6, self.min_pos + 8)

        self.middle_square = None
        self.edge_squares = []
        self.corner_squares = []

        log.info("Side %s, min/mid/max %d/%d/%d" % (self.name, self.min_pos, self.mid_pos, self.max_pos))

    def __str__(self):
        return self.name

    def set_square(self, position, red, green, blue):
        self.squares[position] = Square(self, self.cube, position, red, green, blue)

        if position == self.mid_pos:
            self.middle_square = self.squares[position]

        elif position in self.edge_pos:
            self.edge_squares.append(self.squares[position])

        elif position in self.corner_pos:
            self.corner_squares.append(self.squares[position])


class RubiksColorSolver3x3x3(object):

    """
    This class accepts a RGB value for all 54 squares on a Rubiks cube and
    figures out which of the 6 cube colors each square is.

    The names of the sides are (Up, Left, Front, Right, Back, Down)
      U
    L F R B
      D
    """

    def __init__(self, width=3):
        self.width = width
        self.colors = []
        self.scan_data = {}
        self.tools_file = None

        # 4! = 24
        # 5! = 120
        # 6! = 720
        # 7! = 5040
        # 8! = 40320

        # With a limit of 40320 it takes 3.6s to resolve the colors for a cube
        # With a limit of  5040 it takes 1.5s to resolve the colors for a cube
        # With a limit of   720 it takes 1.2s to resolve the colors for a cube
        # These numbers are from a beefy server, not EV3
        self.edge_permutation_limit = 720
        self.corner_permutation_limit = 720

        self.sides = {
            'U': CubeSideOld(self, 'U'),
            'L': CubeSideOld(self, 'L'),
            'F': CubeSideOld(self, 'F'),
            'R': CubeSideOld(self, 'R'),
            'B': CubeSideOld(self, 'B'),
            'D': CubeSideOld(self, 'D')
        }

        self.sideU = self.sides['U']
        self.sideL = self.sides['L']
        self.sideF = self.sides['F']
        self.sideR = self.sides['R']
        self.sideB = self.sides['B']
        self.sideD = self.sides['D']

        self.side_order = ('U', 'L', 'F', 'R', 'B', 'D')
        self.edges = []
        self.corners = []

        self.crayola_colors = {
            # Handy website for converting RGB tuples to hex
            # http://www.w3schools.com/colors/colors_converter.asp
            #
            # The RGB values in comments are the originals used, they came
            # from crayola's website. These are the RGB values for each color
            # as seen via the EV3 color sensor.
            #   white = (60, 100, 70)
            #   green = (6, 35, 13)
            #   yellow = (34, 43, 8)
            #   orange = (40, 20, 6)
            #   blue = (6, 19, 20)
            #   red = (30, 12, 6)
            #
            #'Wh': hashtag_rgb_to_labcolor('#3C6446'),  # White  - FFFFFF
            #'Gr': hashtag_rgb_to_labcolor('#06230D'),  # Green  - 1C8E0D
            #'Ye': hashtag_rgb_to_labcolor('#222B08'),  # Yellow - F6EB20
            #'OR': hashtag_rgb_to_labcolor('#281406'),  # Orange - FF80000
            #'Bu': hashtag_rgb_to_labcolor('#061314'),  # Blue   - 2862B9
            #'Rd': hashtag_rgb_to_labcolor('#1E0C06')   # Red    - C91111
            #
            # Note that the values from the EV3 color sensor are not as accurate
            # as those we get from a webcam so lets use the webcam numbers

            # These are the RGB values as seen via a webcam
            #   white = (142, 171, 215)
            #   green = (20, 105, 74)
            #   yellow = (160, 160, 48)
            #   orange = (148, 53, 9)
            #   blue = (3, 40, 146)
            #   red = (104, 4, 2)
            #
            'Wh': hashtag_rgb_to_labcolor('#8eabd7'),
            'Gr': hashtag_rgb_to_labcolor('#14694a'),
            'Ye': hashtag_rgb_to_labcolor('#a0a030'),
            'OR': hashtag_rgb_to_labcolor('#943509'),
            'Bu': hashtag_rgb_to_labcolor('#032892'),
            'Rd': hashtag_rgb_to_labcolor('#680402')

            # RGB values for other colors according to crayola's website
            # 'Yg': hashtag_rgb_to_labcolor('#51C201'),  # Yellow Green
            # 'Or': hashtag_rgb_to_labcolor('#D84E09'),  # Red Orange
            # 'Sy': hashtag_rgb_to_labcolor('#09C5F4'),  # Sky Blue
            # 'Pu': hashtag_rgb_to_labcolor('#7E44BC'),  # Purple
            # 'Bl': hashtag_rgb_to_labcolor('#000000')   # Black
        }

    # ================
    # Printing methods
    # ================
    def print_layout(self):
        log.info('\n' + get_cube_layout(self.width) + '\n')

    def print_cube(self):
        """
           Wh Wh Wh
           Wh Wh Wh
           Wh Wh Wh
 Rd Rd Rd  Bu Bu Bu  OR OR OR  Gr Gr Gr
 Rd Rd Rd  Bu Bu Bu  OR OR OR  Gr Gr Gr
 Rd Rd Rd  Bu Bu Bu  OR OR OR  Gr Gr Gr
           Ye Ye Ye
           Ye Ye Ye
           Ye Ye Ye
        """
        data = [[], [], [], [], [], [], [], [], []]

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
                prefix = '          '
            elif side_name in ('L', 'F', 'R', 'B'):
                line_number = 3
                prefix = ''
            else:
                line_number = 6
                prefix = '          '

            for x in range(3):
                data[line_number].append(prefix)

                for color_name in (side.squares[side.min_pos + (x * 3)].color.name,
                                   side.squares[side.min_pos + (x * 3) + 1].color.name,
                                   side.squares[side.min_pos + (x * 3) + 2].color.name):
                    color_code = color_codes.get(color_name)

                    # default to white
                    if color_code is None:
                        color_code = 97

                    data[line_number].append('\033[%dm%s\033[0m' % (color_code, color_name))
                line_number += 1

        output = []
        for row in data:
            output.append(' '.join(row))

        log.info("Cube\n\n%s\n" % '\n'.join(output))

    def cube_for_kociemba(self):
        """
        Say for example our cube is

                   Wh Wh Bu
                   Wh Wh OR
                   Wh Wh OR
         Rd Rd Rd  Bu Bu Ye  Gr Gr OR  Wh Gr Gr
         Bu Bu Bu  OR OR Ye  Gr Gr OR  Wh Rd Rd
         Bu Bu Bu  OR OR Ye  Gr Gr OR  Wh Rd Rd
                   Ye Ye Rd
                   Ye Ye Rd
                   Ye Ye Gr

        The kociemba representation of this cube is UULUUFUUFRRFRRFRRFLLDFFDFFDDDBDDBDDRBBBLLLLLLURRUBBUBB
        So how to read that string? Break it down in groups of 9 so we have one row per side.

        UULUUFUUF
        RRFRRFRRF
        LLDFFDFFD
        DDBDDBDDR
        BBBLLLLLL
        URRUBBUBB
            ^
            |-- This column is the middle square for each side

        The sides are printed Upper, Right, Front, Down, Left, Back because this is the
        order expected by kociemba. The Upper side

            Wh Wh Bu
            Wh Wh OR
            Wh Wh OR

        is represented via UULUUFUUF but lets lay it out to be nice and neat:

             U U L
             U U F
             U U F

        So Bu was replaced with L because Bu is the color of side L, Or was replaced
        with F because Or is the color of side F, etc
        """
        data = []
        color_to_side_name = {}

        for side in self.sides.values():
            color_to_side_name[side.middle_square.color] = side.name

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                color = side.squares[x].color
                data.append(color_to_side_name[color])

        return data

    def cube_for_kociemba_strict(self):
        return self.cube_for_kociemba()

    def cube_for_json(self):
        """
        Return a dictionary of the cube data so that we can json dump it
        A sample entry for a square:

          "1": {
            "color": "Wh",
            "currentPosition": 1,
            "currentSide": "U",
            "finalSide": "U",
            "rgb": {
              "blue": 43,
              "green": 71,
              "red": 39
            }
          },
        """
        data = {}
        color_to_side_name = {}

        for side in self.sides.values():
            color_to_side_name[side.middle_square.color] = side.name

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]
                color = square.color
                data[square.position] = {
                    'currentSide' : side.name,
                    'currentPosition' : square.position,
                    'rgb' : {
                        'red' : square.red,
                        'green' : square.green,
                        'blue' : square.blue,
                    },
                    'color' : color.name,
                    'finalSide' : color_to_side_name[color]
                }

        return data

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

        for (position, (red, green, blue)) in self.scan_data.items():
            side = self.get_side(position)
            side.set_square(position, red, green, blue)

    def get_squares_with_color(self, target_color):
        squares = []
        for side in self.sides.values():
            for square in side.squares.values():
                if square.color == target_color:
                    squares.append(square)
        return squares

    def name_middle_square_colors(self):
        """
        Assign a color name to the square's LabColor object.
        This name is only used for debug output.
        """
        self.crayon_box = {}

        min_distance = None
        min_distance_permutation = None

        for permutation in permutations(self.crayola_colors.keys()):
            distance = 0

            for (side_name, color_name) in zip(self.side_order, permutation):
                side = self.sides[side_name]
                color_obj = self.crayola_colors[color_name]
                distance += get_color_distance(side.middle_square.rawcolor, color_obj)

            if min_distance is None or distance < min_distance:
                min_distance = distance
                min_distance_permutation = permutation

        log.info("Crayon box (middle square colors)")
        for (side_name, color_name) in zip(self.side_order, min_distance_permutation):
            side = self.sides[side_name]
            self.crayon_box[side.name] = side.middle_square.rawcolor
            side.middle_square.rawcolor.name = color_name
            log.info("%s --> %s" % (side_name, color_name))
        log.info("")

    def identify_middle_squares(self):
        log.info('ID middle square colors')

        for side_name in self.side_order:
            side = self.sides[side_name]
            side.color = self.crayon_box[side_name]

            # The middle square must match the color in the crayon_box for this side
            # so pass a dictionary with just this one color
            side.middle_square.find_closest_match({'foo': side.color})
            log.info("%s is %s" % (side.middle_square, side.middle_square.color.name))
        log.info('\n')

        self.valid_edges = []
        self.valid_edges.append((self.sideU.color, self.sideF.color))
        self.valid_edges.append((self.sideU.color, self.sideL.color))
        self.valid_edges.append((self.sideU.color, self.sideR.color))
        self.valid_edges.append((self.sideU.color, self.sideB.color))

        self.valid_edges.append((self.sideF.color, self.sideL.color))
        self.valid_edges.append((self.sideF.color, self.sideR.color))
        self.valid_edges.append((self.sideB.color, self.sideL.color))
        self.valid_edges.append((self.sideB.color, self.sideR.color))

        self.valid_edges.append((self.sideD.color, self.sideF.color))
        self.valid_edges.append((self.sideD.color, self.sideL.color))
        self.valid_edges.append((self.sideD.color, self.sideR.color))
        self.valid_edges.append((self.sideD.color, self.sideB.color))
        self.valid_edges = sorted(self.valid_edges)

        self.valid_corners = []
        self.valid_corners.append((self.sideU.color, self.sideF.color, self.sideL.color))
        self.valid_corners.append((self.sideU.color, self.sideR.color, self.sideF.color))
        self.valid_corners.append((self.sideU.color, self.sideL.color, self.sideB.color))
        self.valid_corners.append((self.sideU.color, self.sideB.color, self.sideR.color))

        self.valid_corners.append((self.sideD.color, self.sideL.color, self.sideF.color))
        self.valid_corners.append((self.sideD.color, self.sideF.color, self.sideR.color))
        self.valid_corners.append((self.sideD.color, self.sideB.color, self.sideL.color))
        self.valid_corners.append((self.sideD.color, self.sideR.color, self.sideB.color))
        self.valid_corners = sorted(self.valid_corners)

    def identify_edge_squares(self):
        log.info('ID edge square colors')

        for side in self.sides.values():
            for square in side.edge_squares:
                square.find_closest_match(self.crayon_box)

    def identify_corner_squares(self):
        log.info('ID corner square colors')

        for side in self.sides.values():
            for square in side.corner_squares:
                square.find_closest_match(self.crayon_box)

    def create_edges_and_corners(self):
        """
        The Edge objects below are used to represent a tuple of two Square objects.
        Not to be confused with self.valid_edges which are the tuples of color
        combinations we know we must have based on the colors of the six sides.
        """

        # Edges
        # U
        self.edges.append(Edge(self, 2, 38))
        self.edges.append(Edge(self, 4, 11))
        self.edges.append(Edge(self, 6, 29))
        self.edges.append(Edge(self, 8, 20))

        # F
        self.edges.append(Edge(self, 15, 22))
        self.edges.append(Edge(self, 24, 31))
        self.edges.append(Edge(self, 26, 47))

        # L
        self.edges.append(Edge(self, 13, 42))
        self.edges.append(Edge(self, 17, 49))

        # R
        self.edges.append(Edge(self, 35, 51))
        self.edges.append(Edge(self, 33, 40))

        # B
        self.edges.append(Edge(self, 44, 53))

        # Corners
        # U
        self.corners.append(Corner(self, 1, 10, 39))
        self.corners.append(Corner(self, 3, 37, 30))
        self.corners.append(Corner(self, 7, 19, 12))
        self.corners.append(Corner(self, 9, 28, 21))

        # B
        self.corners.append(Corner(self, 46, 18, 25))
        self.corners.append(Corner(self, 48, 27, 34))
        self.corners.append(Corner(self, 52, 45, 16))
        self.corners.append(Corner(self, 54, 36, 43))

    def valid_cube_parity(self, fake_corner_parity):
        """
        verify_parity() returns
         0: Cube is solvable
        -1: There is not exactly one facelet of each colour
        -2: Not all 12 edges exist exactly once
        -3: Flip error: One edge has to be flipped
        -4: Not all 8 corners exist exactly once
        -5: Twist error: One corner has to be twisted
        -6: Parity error: Two corners or two edges have to be exchanged

        Given how we assign colors it is not possible for us to generate a cube
        that returns -1, -2, or -4
        """
        cube_string = ''.join(map(str, self.cube_for_kociemba()))

        if fake_corner_parity:

            # Fill in the corners with data that we know to be valid parity
            # We do this when we are validating the parity of the edges
            cube_string = list(cube_string)
            cube_string[0] = 'U'
            cube_string[2] = 'U'
            cube_string[6] = 'U'
            cube_string[8] = 'U'

            cube_string[9] = 'R'
            cube_string[11] = 'R'
            cube_string[15] = 'R'
            cube_string[17] = 'R'

            cube_string[18] = 'F'
            cube_string[20] = 'F'
            cube_string[24] = 'F'
            cube_string[26] = 'F'

            cube_string[27] = 'D'
            cube_string[29] = 'D'
            cube_string[33] = 'D'
            cube_string[35] = 'D'

            cube_string[36] = 'L'
            cube_string[38] = 'L'
            cube_string[42] = 'L'
            cube_string[44] = 'L'

            cube_string[45] = 'B'
            cube_string[47] = 'B'
            cube_string[51] = 'B'
            cube_string[53] = 'B'
            cube_string = ''.join(cube_string)

        result = verify_parity(cube_string)

        if not result:
            return True

        # Must ignore this one since we made up the corners
        if fake_corner_parity and result == -6:
            return True

        # This gives a false positive on 2x2x2
        if isinstance(self, RubiksColorSolver2x2x2) and result == -6:
            return True

        log.info("parity is %s" % result)
        return False

    def valid_edge_parity(self):
        return self.valid_cube_parity(fake_corner_parity=True)

    def resolve_edge_squares(self):
        log.info('Resolve edges')

        # Initially we flag all of our Edge objects as invalid
        for edge in self.edges:
            edge.valid = False

        # And our 'needed' list will hold all 12 edges
        needed_edges = sorted(self.valid_edges)

        unresolved_edges = [edge for edge in self.edges if edge.valid is False]
        permutation_count = factorial(len(needed_edges))
        best_match_total_distance = 0

        # 12 edges will mean 479,001,600 permutations which is too many.  Examine
        # all 12 edges and find the one we can match against a needed_edge that produces
        # the lowest color distance. update_colors() for this edge, mark it as
        # valid and remove it from the needed_edges.  Repeat this until the
        # number of permutations of needed_edges is down to our permutation_limit.
        if permutation_count > self.edge_permutation_limit:
            scores_by_edge_pair = {}

            for edge in unresolved_edges:
                for (colorA, colorB) in needed_edges:
                    distance = edge.color_distance(colorA, colorB)

                    if edge not in scores_by_edge_pair:
                        scores_by_edge_pair[edge] = []

                    scores_by_edge_pair[edge].append((distance, (colorA, colorB)))

            # For each edge keep the top two scores
            for (edge, value) in scores_by_edge_pair.items():
                scores_by_edge_pair[edge] = sorted(value)[0:2]

            # Now compute the delta between the first place score and the second place score for each edge
            score_delta = []

            for (edge, value) in scores_by_edge_pair.items():
                first_place_distance = value[0][0]
                second_place_distance = value[1][0]
                first_place_color = value[0][1]

                for (distance, (colorA, colorB)) in value:
                    log.info("edge_best_match %s, score %s, colorA %s, colorB %s" % (edge, distance, colorA.name, colorB.name))
                log.info('')
                score_delta.append((second_place_distance - first_place_distance, first_place_distance, edge, (first_place_color[0], first_place_color[1])))

            score_delta = list(reversed(sorted(score_delta)))

            log.info("SCORES DELTA")
            for (delta_distance, distance, edge_best_match, (colorA, colorB)) in score_delta:
                log.info("%s, edge_best_match %s, colorA %s, colorB %s" % (distance, edge_best_match, colorA.name, colorB.name))

            # for edge in unresolved_edges:
            #     log.info("unresolved_edge: %s" % edge)
            #
            # for (colorA, colorB) in needed_edges:
            #     log.info("needed_edges: %s/%s" % (colorA.name, colorB.name))

            while permutation_count > self.edge_permutation_limit:

                for (delta_distance, distance, edge_best_match, (colorA, colorB)) in score_delta:
                    if edge_best_match in unresolved_edges and (colorA, colorB) in needed_edges:
                        break
                else:
                    raise Exception("Did not find an edge in unresolved_edges")

                best_match_total_distance += distance
                edge_best_match.update_colors(colorA, colorB)
                edge_best_match.valid = True
                needed_edges.remove((colorA, colorB))

                unresolved_edges = [edge for edge in self.edges if edge.valid is False]
                permutation_count = factorial(len(needed_edges))
                log.info("%s/%s best match is %s with distance %d (permutations %d/%d)" %
                         (colorA.name, colorB.name, edge_best_match, distance, permutation_count, self.edge_permutation_limit))

        score_per_permutation = []

        log.info("Calculate edge score for each permutation")
        for edge_permutation in permutations(unresolved_edges):
            total_distance = 0

            for (edge, (colorA, colorB)) in zip(edge_permutation, needed_edges):
                total_distance += edge.color_distance(colorA, colorB)

            score_per_permutation.append((total_distance, edge_permutation))

        score_per_permutation = sorted(score_per_permutation)

        # Now traverse the permutations from best score to worst. The first
        # permutation that produces a set of edges with valid parity is the
        # permutation we want (most of the time the first entry has valid parity).
        log.info("Find edge permutation with the lowest score with valid parity")

        for (_, permutation) in score_per_permutation:
            total_distance = best_match_total_distance

            for (edge_best_match, (colorA, colorB)) in zip(permutation, needed_edges):
                distance = edge_best_match.color_distance(colorA, colorB)
                total_distance += distance
                edge_best_match.update_colors(colorA, colorB)
                edge_best_match.valid = True

            if self.valid_edge_parity():
                log.info("%s/%s potential match is %s with distance %d" %
                         (colorA.name, colorB.name, edge_best_match, distance))
                log.info("Total distance: %d, edge parity is valid" % total_distance)
                break
            else:
                log.debug("Total distance: %d, edge parity is NOT valid" % total_distance)

        log.info('\n')

    def resolve_corner_squares(self):
        log.info('Resolve corners')

        # Initially we flag all of our Edge objects as invalid
        for corner in self.corners:
            corner.valid = False

        # And our 'needed' list will hold all 8 corners.
        needed_corners = sorted(self.valid_corners)

        unresolved_corners = [corner for corner in self.corners if corner.valid is False]
        permutation_count = factorial(len(needed_corners))
        best_match_total_distance = 0

        # 8 corners will mean 40320 permutations which is too many.  Examine
        # all 8 and find the one we can match against a needed_corner that produces
        # the lowest color distance. update_colors() for this corner, mark it as
        # valid and remove it from the needed_corners.  Repeat this until the
        # number of permutations of needed_corners is down to our permutation_limit.
        if permutation_count > self.corner_permutation_limit:

            scores_by_corner = {}

            for corner in unresolved_corners:
                for (colorA, colorB, colorC) in needed_corners:
                    distance = corner.color_distance(colorA, colorB, colorC)

                    if corner not in scores_by_corner:
                        scores_by_corner[corner] = []
                    scores_by_corner[corner].append((distance, (colorA, colorB, colorC)))

            # For each corner keep the top two scores
            for (corner, value) in scores_by_corner.items():
                scores_by_corner[corner] = sorted(value)[0:2]

            # Now compute the delta between the first place score and the second place score for each edge
            score_delta = []

            for (corner, value) in scores_by_corner.items():
                first_place_distance = value[0][0]
                second_place_distance = value[1][0]
                first_place_color = value[0][1]

                for (distance, (colorA, colorB, colorC)) in value:
                    log.info("corner_best_match %s, score %s, colorA %s, colorB %s, colorC %s" % (corner, distance, colorA.name, colorB.name, colorC.name))
                log.info('')
                score_delta.append((second_place_distance - first_place_distance, first_place_distance, corner, (first_place_color[0], first_place_color[1], first_place_color[2])))

            score_delta = list(reversed(sorted(score_delta)))

            log.info("SCORES DELTA")
            for (delta_distance, distance, corner_best_match, (colorA, colorB, colorC)) in score_delta:
                log.info("%s, corner_best_match %s, colorA %s, colorB %s, colorC %s" % (distance, corner_best_match, colorA.name, colorB.name, colorC.name))

            while permutation_count > self.corner_permutation_limit:

                for (delta_distance, distance, corner_best_match, (colorA, colorB, colorC)) in score_delta:
                    if corner_best_match in unresolved_corners and (colorA, colorB, colorC) in needed_corners:
                        break
                else:
                    raise Exception("Did not find a corner in unresolved_corners")

                best_match_total_distance += distance
                corner_best_match.update_colors(colorA, colorB, colorC)
                corner_best_match.valid = True
                needed_corners.remove((colorA, colorB, colorC))

                unresolved_corners = [corner for corner in self.corners if corner.valid is False]
                permutation_count = factorial(len(needed_corners))
                log.info("%s/%s/%s best match is %s with distance %d (total %d) (permutations %d/%d)" %
                         (colorA.name, colorB.name, colorC.name, corner_best_match,
                          distance, best_match_total_distance,
                          permutation_count, self.corner_permutation_limit))

        score_per_permutation = []

        # for corner in unresolved_corners:
        #     log.info("unresolved_corners: %s" % corner)
        #
        # for (colorA, colorB, colorC) in needed_corners:
        #     log.info("needed_corners: %s/%s/%s" % (colorA.name, colorB.name, colorC.name))

        for corner_permutation in permutations(unresolved_corners):
            total_distance = 0

            for (corner, (colorA, colorB, colorC)) in zip(corner_permutation, needed_corners):
                total_distance += corner.color_distance(colorA, colorB, colorC)

            score_per_permutation.append((total_distance, corner_permutation))

        score_per_permutation = sorted(score_per_permutation)
        # log.info("score_per_permutation:\n%s\n" % pformat(score_per_permutation[0:5]))

        # Now traverse the permutations from best score to worst. The first
        # permutation that produces a cube with valid parity is the permutation
        # we want (most of the time the first entry has valid parity).
        for (_, permutation) in score_per_permutation:
            total_distance = best_match_total_distance

            for (corner_best_match, (colorA, colorB, colorC)) in zip(permutation, needed_corners):
                distance = corner_best_match.color_distance(colorA, colorB, colorC)
                total_distance += distance
                corner_best_match.update_colors(colorA, colorB, colorC)
                corner_best_match.valid = True
                log.info("%s/%s/%s best match is %s with distance %d (%d total)" %
                         (colorA.name, colorB.name, colorC.name, corner_best_match, distance, total_distance))

            if self.valid_cube_parity(fake_corner_parity=False):
                log.info("Total distance: %d (%d from best_match), cube parity is valid" % (total_distance, best_match_total_distance))
                break
            else:
                log.info("Total distance: %d (%d from best_match), cube parity is NOT valid" % (total_distance, best_match_total_distance))

        log.info('\n')

    def crunch_colors(self):
        log.info('Discover the six colors')
        self.name_middle_square_colors()

        # 6 middles, 12 edges, 8 corners
        self.identify_middle_squares()
        self.identify_edge_squares()
        self.identify_corner_squares()

        self.create_edges_and_corners()
        self.resolve_edge_squares()
        self.resolve_corner_squares()

        self.print_layout()
        self.print_cube()
        return self.cube_for_kociemba_strict()


class RubiksColorSolver2x2x2(RubiksColorSolver3x3x3):

    def __init__(self):
        RubiksColorSolver3x3x3.__init__(self)

    def enter_scan_data(self, scan_data):
        """
        Take the data from scanning a 2x2x2 cube and manipulate it to look
        like a scan of a 3x3x3 cube. This allows us to re-use the majority
        of code in RubiksColorSolver3x3x3 for resolving the colors of a 2x2x2 cube
        """
        self.scan_data = scan_data

        position_2x2x2_to_3x3x3 = {
            1 : 1,
            2 : 3,
            3 : 7,
            4 : 9,
            5 : 10,
            6 : 12,
            7 : 16,
            8 : 18,
            9 : 19,
            10 : 21,
            11 : 25,
            12 : 27,
            13 : 28,
            14 : 30,
            15 : 34,
            16 : 36,
            17 : 37,
            18 : 39,
            19 : 43,
            20 : 45,
            21 : 46,
            22 : 48,
            23 : 52,
            24 : 54,
        }

        for (position_2x2x2, (red, green, blue)) in self.scan_data.items():
            position = position_2x2x2_to_3x3x3[position_2x2x2]
            side = self.get_side(position)
            side.set_square(position, red, green, blue)

        # These are the RGB values for each color as seen via a webcam
        white = (142, 171, 215)
        green = (20, 105, 74)
        yellow = (160, 160, 48)
        orange = (148, 53, 9)
        blue = (3, 40, 146)
        red = (104, 4, 2)

        fake_data = {
            # Use the standard color layout
            # https://ruwix.com/online-rubiks-cube-solver-program/

            # Upper will be yellow
            2 : yellow,
            4 : yellow,
            5 : yellow,
            6 : yellow,
            8 : yellow,

            # Left will be green
            11 : green,
            13 : green,
            14 : green,
            15 : green,
            17 : green,

            # Front will be orange
            20 : orange,
            22 : orange,
            23 : orange,
            24 : orange,
            26 : orange,

            # Right will be blue
            29 : blue,
            31 : blue,
            32 : blue,
            33 : blue,
            35 : blue,

            # Back will be red
            38 : red,
            40 : red,
            41 : red,
            42 : red,
            44 : red,

            # Down will be white
            47 : white,
            49 : white,
            50 : white,
            51 : white,
            53 : white,
        }

        for (position, (red, green, blue)) in fake_data.items():
            side = self.get_side(position)
            side.set_square(position, red, green, blue)

    def print_cube(self):
        """
        Print the cube but skip the 3x3x3 faked data entries
        """
        data = [[], [], [], [], [], []]

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
                prefix = '       '
            elif side_name in ('L', 'F', 'R', 'B'):
                line_number = 2
                prefix = ''
            else:
                line_number = 4
                prefix = '       '

            for x in range(self.width):

                # rows 0 and 2 are real, 1 is faked so skip it
                if x == 1:
                    continue

                data[line_number].append(prefix)

                for color_name in (side.squares[side.min_pos + (x * self.width)].color.name,
                                   # side.squares[side.min_pos + (x * self.width) + 1].color.name, # faked, skip it
                                   side.squares[side.min_pos + (x * self.width) + 2].color.name):
                    color_code = color_codes.get(color_name)

                    # default to white
                    if color_code is None:
                        color_code = 97

                    data[line_number].append('\033[%dm%s\033[0m' % (color_code, color_name))
                line_number += 1

        output = []
        for row in data:
            output.append(' '.join(row))

        log.info("Cube\n\n%s\n" % '\n'.join(output))

    def cube_for_kociemba_strict(self):
        """
        By "strict" here we do not include the fake 3x3x3 squares
        """
        data = []
        color_to_side_name = {
            'Ye' : 'U',
            'Gr' : 'L',
            'OR' : 'F',
            'Bu' : 'R',
            'Rd' : 'B',
            'Wh' : 'D',
        }

        for side_name in self.side_order:
            side = self.sides[side_name]

            for x in range(self.width):

                # rows 0 and 2 are real, 1 is faked so skip it
                if x == 1:
                    continue

                for color_name in (side.squares[side.min_pos + (x * self.width)].color.name,
                                   # side.squares[side.min_pos + (x * self.width) + 1].color.name, # faked, skip it
                                   side.squares[side.min_pos + (x * self.width) + 2].color.name):
                    data.append(color_to_side_name[color_name])

        return data
