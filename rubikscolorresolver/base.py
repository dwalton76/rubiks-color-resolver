
#from rubikscolorresolver.profile import timed_function
from math import ceil, sqrt
import sys

if sys.version_info < (3, 4):
    raise SystemError("Must be using Python 3.4 or higher")


def is_micropython():
    return sys.implementation.name == "micropython"


if is_micropython():
    from ucollections import OrderedDict
else:
    from collections import OrderedDict
    from rubikscolorresolver.cie2000 import lab_distance_cie2000


# @timed_function
def lab_distance(lab1, lab2):
    """
    http://www.w3resource.com/python-exercises/math/python-math-exercise-79.php

    In mathematics, the Euclidean distance or Euclidean metric is the "ordinary"
    (i.e. straight-line) distance between two points in Euclidean space. With this
    distance, Euclidean space becomes a metric space. The associated norm is called
    the Euclidean norm.
    """

    if is_micropython():
        # CIE2000 takes much more CPU so use euclidean when on micropython
        # Use int instead of float to save a little memory
        return int(sqrt(((lab1.L - lab2.L) ** 2) + ((lab1.a - lab2.a) ** 2) + ((lab1.b - lab2.b) ** 2)))
    else:
        return lab_distance_cie2000(lab1, lab2)


html_color = {
    "Gr": {"red": 0, "green": 102, "blue": 0},
    "Bu": {"red": 0, "green": 0, "blue": 153},
    "OR": {"red": 255, "green": 153, "blue": 0},
    "Rd": {"red": 204, "green": 51, "blue": 0},
    "Wh": {"red": 255, "green": 255, "blue": 255},
    "Ye": {"red": 255, "green": 255, "blue": 0},
}


edge_color_pair_map = {
    # Up (white)
    "Gr/Wh": "Gr/Wh",
    "Wh/Gr": "Gr/Wh",
    "Bu/Wh": "Bu/Wh",
    "Wh/Bu": "Bu/Wh",
    "OR/Wh": "OR/Wh",
    "Wh/OR": "OR/Wh",
    "Rd/Wh": "Rd/Wh",
    "Wh/Rd": "Rd/Wh",
    # Left (orange)
    "Gr/OR": "Gr/OR",
    "OR/Gr": "Gr/OR",
    "Bu/OR": "Bu/OR",
    "OR/Bu": "Bu/OR",
    # Right (red)
    "Gr/Rd": "Gr/Rd",
    "Rd/Gr": "Gr/Rd",
    "Bu/Rd": "Bu/Rd",
    "Rd/Bu": "Bu/Rd",
    # Down (yellow)
    "Gr/Ye": "Gr/Ye",
    "Ye/Gr": "Gr/Ye",
    "Bu/Ye": "Bu/Ye",
    "Ye/Bu": "Bu/Ye",
    "OR/Ye": "OR/Ye",
    "Ye/OR": "OR/Ye",
    "Rd/Ye": "Rd/Ye",
    "Ye/Rd": "Rd/Ye",
}


class ListMissingValue(Exception):
    pass


# @timed_function
def find_index_for_value(list_foo, target, min_index):
    for (index, value) in enumerate(list_foo):
        if value == target and index >= min_index:
            return index
    raise ListMissingValue("Did not find %s in list %s".format(target, list_foo))


# @timed_function
def get_swap_count(listA, listB):
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
        #log.info("listA %s" % " ".join(listA))
        #log.info("listB %s" % " ".join(listB))
        assert False, "listA (len %d) and listB (len %d) must be the same length" % (
            A_length,
            B_length,
        )

    #if debug:
    #    log.info("INIT")
    #    log.info("listA: %s" % " ".join(listA))
    #    log.info("listB: %s" % " ".join(listB))
    #    log.info("")

    while listA != listB:
        if listA[index] != listB[index]:
            listA_value = listA[index]
            listB_index_with_A_value = find_index_for_value(
                listB, listA_value, index + 1
            )
            tmp = listB[index]
            listB[index] = listB[listB_index_with_A_value]
            listB[listB_index_with_A_value] = tmp
            swaps += 1

            #if debug:
            #    log.info("index %d, swaps %d" % (index, swaps))
            #    log.info("listA: %s" % " ".join(listA))
            #    log.info("listB: %s" % " ".join(listB))
            #    log.info("")
        index += 1

    #if debug:
    #    log.info("swaps: %d" % swaps)
    #    log.info("")
    return swaps


class LabColor(object):

    # @timed_function
    def __init__(self, L, a, b, red, green, blue):
        self.L = L
        self.a = a
        self.b = b
        self.red = red
        self.green = green
        self.blue = blue

    def __str__(self):
        return "Lab (%s, %s, %s)" % (self.L, self.a, self.b)

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        if self.L != other.L:
            return self.L < other.L

        if self.a != other.a:
            return self.a < other.a

        return self.b < other.b


# @timed_function
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
        var_G = pow(((var_G + 0.055) / 1.055), 2.4)
    else:
        var_G = var_G / 12.92

    if var_B > 0.04045:
        var_B = pow(((var_B + 0.055) / 1.055), 2.4)
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
        var_X = pow(var_X, 1 / 3)
    else:
        var_X = (7.787 * var_X) + (16 / 116)

    if var_Y > 0.008856:
        var_Y = pow(var_Y, 1 / 3)
    else:
        var_Y = (7.787 * var_Y) + (16 / 116)

    if var_Z > 0.008856:
        var_Z = pow(var_Z, 1 / 3)
    else:
        var_Z = (7.787 * var_Z) + (16 / 116)

    L = (116 * var_Y) - 16
    a = 500 * (var_X - var_Y)
    b = 200 * (var_Y - var_Z)
    # log.info("RGB ({}, {}, {}), L {}, a {}, b {}".format(red, green, blue, L, a, b))

    return LabColor(L, a, b, red, green, blue)


def rgb_to_hsv(r, g, b):
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx-mn

    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g-b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b-r) / df) + 120) % 360
    elif mx == b:
        h = (60 * ((r-g) / df) + 240) % 360

    if mx == 0:
        s = 0
    else:
        s = (df/mx) * 100

    v = mx * 100
    return (h, s, v)


class Square(object):

    def __init__(self, side, position, red, green, blue, side_name=None, color_name=None):
        self.position = position
        self.lab = rgb2lab((red, green, blue))
        self.side_name = side_name # ULFRBD
        self.color_name = color_name

    def __str__(self):
        return "{}{}-{}".format(self.side, self.position, self.color_name)

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

        if self.name == "U":
            index = 0
        elif self.name == "L":
            index = 1
        elif self.name == "F":
            index = 2
        elif self.name == "R":
            index = 3
        elif self.name == "B":
            index = 4
        elif self.name == "D":
            index = 5

        self.min_pos = (index * self.squares_per_side) + 1
        self.max_pos = (index * self.squares_per_side) + self.squares_per_side

        # If this is a cube of odd width (3x3x3) then define a mid_pos
        if self.width % 2 == 0:
            self.mid_pos = None
        else:
            self.mid_pos = int((self.min_pos + self.max_pos) / 2)

        self.corner_pos = (
            self.min_pos,
            self.min_pos + self.width - 1,
            self.max_pos - self.width + 1,
            self.max_pos,
        )
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
        return "side-{}".format(self.name)

    def __repr__(self):
        return self.__str__()

    # @timed_function
    def set_square(self, position, red, green, blue, side_name=None, color_name=None):
        self.squares[position] = Square(self, position, red, green, blue, side_name, color_name)

        if position in self.center_pos:
            self.center_squares.append(self.squares[position])

        elif position in self.edge_pos:
            self.edge_squares.append(self.squares[position])

        elif position in self.corner_pos:
            self.corner_squares.append(self.squares[position])

        else:
            raise Exception("Could not determine egde vs corner vs center")

    # @timed_function
    def calculate_wing_partners(self):
        for (pos1, pos2) in self.cube.all_edge_positions:
            if pos1 >= self.min_pos and pos1 <= self.max_pos:
                self.wing_partner[pos1] = pos2
            elif pos2 >= self.min_pos and pos2 <= self.max_pos:
                self.wing_partner[pos2] = pos1

    # @timed_function
    def get_wing_partner(self, wing_index):
        try:
            return self.wing_partner[wing_index]
        except KeyError:
            #log.info("wing_partner\n%s\n".format(self.wing_partner))
            raise


class RubiksColorSolverGenericBase(object):

    def __init__(self, width):
        self.width = width
        self.height = width
        self.squares_per_side = self.width * self.width
        self.orbits = int(ceil((self.width - 2) / 2.0))
        self.state = []
        self.orange_baseline = None
        self.red_baseline = None
        self.all_edge_positions = []
        self.write_debug_file = False

        if self.width % 2 == 0:
            self.even = True
            self.odd = False
        else:
            self.even = False
            self.odd = True

        #if not os.path.exists(HTML_DIRECTORY):
        #    os.makedirs(HTML_DIRECTORY)

        self.sides = {
            "U": Side(self, self.width, "U"),
            "L": Side(self, self.width, "L"),
            "F": Side(self, self.width, "F"),
            "R": Side(self, self.width, "R"),
            "B": Side(self, self.width, "B"),
            "D": Side(self, self.width, "D"),
        }

        self.sideU = self.sides["U"]
        self.sideL = self.sides["L"]
        self.sideF = self.sides["F"]
        self.sideR = self.sides["R"]
        self.sideB = self.sides["B"]
        self.sideD = self.sides["D"]
        self.side_order = ("U", "L", "F", "R", "B", "D")
        self.pos2side = {}
        self.pos2square = {}

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

        self.calculate_pos2side()

        # This is no longer neeeded now that the Side objects have been created
        self.all_edge_positions = []

    # @timed_function
    def calculate_pos2side(self):
        for side in self.sides.values():
            for x in range(side.min_pos, side.max_pos + 1):
                self.pos2side[x] = side

    # @timed_function
    def calculate_pos2square(self):
        for side in self.sides.values():
            for (position, square) in side.squares.items():
                self.pos2square[position] = square

    def enter_cube_state(self, input_state, order="URFDLB"):
        """
        If you already have the cube state this method allows you to enter it
        so we can then validate the cube state via:

            - sanity_check_edge_squares()
            - validate_all_corners_found()
            - validate_odd_cube_midge_vs_corner_parity()

        The primary use case for this is a robot with a color sensor that can
        return color names (red, green, etc) but not RGB values.
        """
        input_state = list(input_state)
        state = []

        # kociemba order
        if order == 'URFDLB':
            state.extend(input_state[0:self.squares_per_side])                            # U
            state.extend(input_state[(self.squares_per_side * 4):(self.squares_per_side * 5)]) # L
            state.extend(input_state[(self.squares_per_side * 2):(self.squares_per_side * 3)]) # F
            state.extend(input_state[(self.squares_per_side * 1):(self.squares_per_side * 2)]) # R
            state.extend(input_state[(self.squares_per_side * 5):(self.squares_per_side * 6)]) # B
            state.extend(input_state[(self.squares_per_side * 3):(self.squares_per_side * 4)]) # D
        elif order == 'ULFRBD':
            state.extend(input_state[0:self.squares_per_side])                            # U
            state.extend(input_state[(self.squares_per_side * 1):(self.squares_per_side * 2)]) # L
            state.extend(input_state[(self.squares_per_side * 2):(self.squares_per_side * 3)]) # F
            state.extend(input_state[(self.squares_per_side * 3):(self.squares_per_side * 4)]) # R
            state.extend(input_state[(self.squares_per_side * 4):(self.squares_per_side * 5)]) # B
            state.extend(input_state[(self.squares_per_side * 5):(self.squares_per_side * 6)]) # D
        else:
            raise Exception("Add support for order %s" % order)

        self.color_to_side_name = {
            "Wh": "U",
            "OR": "L",
            "Gr": "F",
            "Rd": "R",
            "Bu": "B",
            "Ye": "D",
        }

        side_name_to_color = {
            "U" : "Wh",
            "L" : "OR",
            "F" : "Gr",
            "R" : "Rd",
            "B" : "Bu",
            "D" : "Ye",
        }

        self.orange_baseline = rgb2lab((html_color["OR"]["red"], html_color["OR"]["green"], html_color["OR"]["blue"]))
        self.red_baseline = rgb2lab((html_color["Rd"]["red"], html_color["Rd"]["green"], html_color["Rd"]["blue"]))

        for position in range(1, (self.squares_per_side*6) + 1):
            side_name = state[position-1]
            color_name = side_name_to_color[side_name]

            red = html_color[color_name]["red"]
            green = html_color[color_name]["green"]
            blue = html_color[color_name]["blue"]

            side = self.pos2side[position]
            side.set_square(position, red, green, blue, side_name, color_name)

        self.calculate_pos2square()

    # @timed_function
    def print_cube(self):
        data = []
        for x in range(3 * self.height):
            data.append([])

        color_codes = {"OR": 90, "Rd": 91, "Gr": 92, "Ye": 93, "Bu": 94, "Wh": 97}

        for side_name in self.side_order:
            side = self.sides[side_name]

            if side_name == "U":
                line_number = 0
                prefix = (" " * self.width * 3) + " "
            elif side_name in ("L", "F", "R", "B"):
                line_number = self.width
                prefix = ""
            else:
                line_number = self.width * 2
                prefix = (" " * self.width * 3) + " "

            # rows
            for y in range(self.width):
                data[line_number].append(prefix)

                # cols
                for x in range(self.width):
                    color_name = side.squares[
                        side.min_pos + (y * self.width) + x
                    ].color_name
                    color_code = color_codes.get(color_name)

                    if color_name is None:
                        color_code = 97
                        data[line_number].append("\033[%dmFo\033[0m" % color_code)
                    else:
                        data[line_number].append(
                            "\033[%dm%s\033[0m" % (color_code, color_name)
                        )
                line_number += 1

        output = []
        for row in data:
            output.append(" ".join(row))

        sys.stderr.write("Cube\n\n%s\n" % "\n".join(output))

    # @timed_function
    def cube_for_kociemba_strict(self):
        #log.info("color_to_side_name:\n{}\n".format(self.color_to_side_name))
        data = []
        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]
                data.append(square.side_name)

        return data

    # @timed_function
    def validate_edge_orbit(self, orbit_id):

        if self.width == 2:
            from rubikscolorresolver.cube_333 import edge_orbit_wing_pairs
        elif self.width == 3:
            from rubikscolorresolver.cube_333 import edge_orbit_wing_pairs
        elif self.width == 4:
            from rubikscolorresolver.cube_444 import edge_orbit_wing_pairs
        elif self.width == 5:
            from rubikscolorresolver.cube_555 import edge_orbit_wing_pairs
        elif self.width == 6:
            from rubikscolorresolver.cube_666 import edge_orbit_wing_pairs
        elif self.width == 7:
            from rubikscolorresolver.cube_777 import edge_orbit_wing_pairs

        valid = True

        # We need to see which orange/red we can flip that will make the edges valid
        wing_pair_counts = {}

        for (square1_position, square2_position) in edge_orbit_wing_pairs[orbit_id]:
            square1 = self.pos2square[square1_position]
            square2 = self.pos2square[square2_position]
            wing_pair_string = ", ".join(
                sorted([square1.color_name, square2.color_name])
            )
            # log.info("orbit {}: ({}, {}) is ({})".format(orbit_id, square1_position, square2_position, wing_pair_string))

            if wing_pair_string not in wing_pair_counts:
                wing_pair_counts[wing_pair_string] = 0
            wing_pair_counts[wing_pair_string] += 1

        # Are all counts the same?
        target_count = None
        for (_wing_pair, count) in wing_pair_counts.items():

            if target_count is None:
                target_count = count
            else:
                if count != target_count:
                    valid = False
                    break

        #if not valid:
        #    log.info("wing_pair_counts:\n{}\n".format(wing_pair_counts))
        #    log.warning("valid: {}".format(valid))

        return valid

    # @timed_function
    def find_corners_by_color(self):
        green_white_corners = []
        green_yellow_corners = []
        blue_white_corners = []
        blue_yellow_corners = []

        if self.width == 2:
            from rubikscolorresolver.cube_222 import corner_tuples
        elif self.width == 3:
            from rubikscolorresolver.cube_333 import corner_tuples
        elif self.width == 4:
            from rubikscolorresolver.cube_444 import corner_tuples
        elif self.width == 5:
            from rubikscolorresolver.cube_555 import corner_tuples
        elif self.width == 6:
            from rubikscolorresolver.cube_666 import corner_tuples
        elif self.width == 7:
            from rubikscolorresolver.cube_777 import corner_tuples

        for corner_tuple in corner_tuples:
            corner_colors = []

            for position in corner_tuple:
                #square = self.pos2square[position]
                #corner_colors.add(square.color_name)
                corner_colors.append(self.pos2square[position].color_name)

            if "Gr" in corner_colors:
                if "Wh" in corner_colors:
                    green_white_corners.append(corner_tuple)
                elif "Ye" in corner_colors:
                    green_yellow_corners.append(corner_tuple)

            elif "Bu" in corner_colors:
                if "Wh" in corner_colors:
                    blue_white_corners.append(corner_tuple)
                elif "Ye" in corner_colors:
                    blue_yellow_corners.append(corner_tuple)

        return (
            green_white_corners,
            green_yellow_corners,
            blue_white_corners,
            blue_yellow_corners,
        )

    # @timed_function
    def find_edges_by_color(self, orbit_id):

        if self.width == 2:
            from rubikscolorresolver.cube_333 import edge_orbit_wing_pairs
        elif self.width == 3:
            from rubikscolorresolver.cube_333 import edge_orbit_wing_pairs
        elif self.width == 4:
            from rubikscolorresolver.cube_444 import edge_orbit_wing_pairs
        elif self.width == 5:
            from rubikscolorresolver.cube_555 import edge_orbit_wing_pairs
        elif self.width == 6:
            from rubikscolorresolver.cube_666 import edge_orbit_wing_pairs
        elif self.width == 7:
            from rubikscolorresolver.cube_777 import edge_orbit_wing_pairs

        green_red_orange_color_names = ("Gr", "Rd", "OR")
        blue_red_orange_color_names = ("Bu", "Rd", "OR")
        white_red_orange_color_names = ("Wh", "Rd", "OR")
        yellow_red_orange_color_names = ("Ye", "Rd", "OR")
        green_red_or_orange_edges = []
        blue_red_or_orange_edges = []
        white_red_or_orange_edges = []
        yellow_red_or_orange_edges = []

        for (square_index, partner_index) in edge_orbit_wing_pairs[orbit_id]:
            square = self.pos2square[square_index]
            partner = self.pos2square[partner_index]

            if (
                square.color_name in green_red_orange_color_names
                and partner.color_name in green_red_orange_color_names
            ):
                if square.color_name == "Gr":
                    green_red_or_orange_edges.append((square, partner))
                else:
                    green_red_or_orange_edges.append((partner, square))

            elif (
                square.color_name in blue_red_orange_color_names
                and partner.color_name in blue_red_orange_color_names
            ):
                if square.color_name == "Bu":
                    blue_red_or_orange_edges.append((square, partner))
                else:
                    blue_red_or_orange_edges.append((partner, square))

            elif (
                square.color_name in white_red_orange_color_names
                and partner.color_name in white_red_orange_color_names
            ):
                if square.color_name == "Wh":
                    white_red_or_orange_edges.append((square, partner))
                else:
                    white_red_or_orange_edges.append((partner, square))

            elif (
                square.color_name in yellow_red_orange_color_names
                and partner.color_name in yellow_red_orange_color_names
            ):
                if square.color_name == "Ye":
                    yellow_red_or_orange_edges.append((square, partner))
                else:
                    yellow_red_or_orange_edges.append((partner, square))

        return (
            green_red_or_orange_edges,
            blue_red_or_orange_edges,
            white_red_or_orange_edges,
            yellow_red_or_orange_edges,
        )

    # @timed_function
    def sanity_check_edges_red_orange_count_for_orbit(self, target_orbit_id):

        if (self.width == 4 or self.width == 6 or (self.width == 5 and target_orbit_id == 0)):
            high_low_edge_per_color = self.get_high_low_per_edge_color(target_orbit_id)
        else:
            high_low_edge_per_color = None

        def fix_orange_vs_red_for_color(target_color, target_color_red_or_orange_edges):

            if len(target_color_red_or_orange_edges) == 2:
                red_orange_permutations = (("OR", "Rd"), ("Rd", "OR"))
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
                raise Exception(
                    "There should be either 2 or 4 but we have %s"
                    % target_color_red_or_orange_edges
                )

            min_distance = None
            min_distance_permutation = None

            for red_orange_permutation in red_orange_permutations:
                distance = 0

                for (index, (target_color_square, partner_square)) in enumerate(target_color_red_or_orange_edges):
                    red_orange = red_orange_permutation[index]

                    if red_orange == "OR":
                        distance += lab_distance(partner_square.lab, self.orange_baseline)
                    elif red_orange == "Rd":
                        distance += lab_distance(partner_square.lab, self.red_baseline)
                    else:
                        raise Exception(red_orange)

                    partner_square.color_name = red_orange
                    partner_square.side_name = self.color_to_side_name[partner_square.color_name]

                if (self.width == 4 or self.width == 6 or (self.width == 5 and target_orbit_id == 0)):

                    for (index, (target_color_square, partner_square)) in enumerate(target_color_red_or_orange_edges):
                        red_orange = red_orange_permutation[index]
                        edge_color_pair = edge_color_pair_map[
                            "%s/%s"
                            % (
                                target_color_square.color_name,
                                partner_square.color_name,
                            )
                        ]
                        # log.info("high_low_edge_per_color\n%s".format(high_low_edge_per_color))

                        if len(high_low_edge_per_color[edge_color_pair]) != 2:
                            # log.warning("*" * 40)
                            # log.warning("edge_color_pair %s high_low is %s" % (edge_color_pair, high_low_edge_per_color[edge_color_pair]))
                            # log.warning("*" * 40)
                            distance += 999

                if min_distance is None or distance < min_distance:
                    min_distance = distance
                    min_distance_permutation = red_orange_permutation
                    '''
                    log.info(
                        "target edge %s, red_orange_permutation %s, distance %s (NEW MIN)"
                        % (target_color, ",".join(red_orange_permutation), distance)
                    )
                else:
                    log.info(
                        "target edge %s, red_orange_permutation %s, distance %s)"
                        % (target_color, ",".join(red_orange_permutation), distance)
                    )

            log.info("min_distance_permutation %s" % ",".join(min_distance_permutation))
                    '''

            for (index, (target_color_square, partner_square)) in enumerate(target_color_red_or_orange_edges):
                if partner_square.color_name != min_distance_permutation[index]:
                    '''
                    log.warning(
                        "change %s edge partner %s from %s to %s"
                        % (
                            target_color,
                            partner_square,
                            partner_square.color_name,
                            min_distance_permutation[index],
                        )
                    )
                    '''
                    partner_square.color_name = min_distance_permutation[index]
                    partner_square.side_name = self.color_to_side_name[
                        partner_square.color_name
                    ]
                    '''
                else:
                    log.info(
                        "%s edge partner %s is %s"
                        % (target_color, partner_square, partner_square.color_name)
                    )

            log.info("\n\n")
                    '''

        (
            green_red_or_orange_edges,
            blue_red_or_orange_edges,
            white_red_or_orange_edges,
            yellow_red_or_orange_edges,
        ) = self.find_edges_by_color(target_orbit_id)
        fix_orange_vs_red_for_color("green", green_red_or_orange_edges)
        fix_orange_vs_red_for_color("blue", blue_red_or_orange_edges)
        fix_orange_vs_red_for_color("white", white_red_or_orange_edges)
        fix_orange_vs_red_for_color("yellow", yellow_red_or_orange_edges)

        self.validate_edge_orbit(target_orbit_id)

    # @timed_function
    def get_high_low_per_edge_color(self, target_orbit_id):

        if self.width == 4:
            from rubikscolorresolver.cube_444 import edge_orbit_wing_pairs, highlow_edge_values
        elif self.width == 5:
            from rubikscolorresolver.cube_555 import edge_orbit_wing_pairs, highlow_edge_values
        elif self.width == 6:
            from rubikscolorresolver.cube_666 import edge_orbit_wing_pairs, highlow_edge_values
        else:
            raise Exception("Add support for %sx%sx%s" % (self.width, self.width, self.width))

        high_low_per_edge_color = {
            "Gr/Wh": set(),
            "Bu/Wh": set(),
            "OR/Wh": set(),
            "Rd/Wh": set(),
            "Gr/OR": set(),
            "Bu/OR": set(),
            "Gr/Rd": set(),
            "Bu/Rd": set(),
            "Gr/Ye": set(),
            "Bu/Ye": set(),
            "OR/Ye": set(),
            "Rd/Ye": set(),
        }

        for (square_index, partner_index) in edge_orbit_wing_pairs[target_orbit_id]:
            square = self.pos2square[square_index]
            partner = self.pos2square[partner_index]

            if self.width == 4:
                highlow = highlow_edge_values[(square_index, partner_index, square.side_name, partner.side_name)]
            elif self.width == 5:
                highlow = highlow_edge_values[(square_index, partner_index, square.side_name, partner.side_name)]
            elif self.width == 6:
                highlow = highlow_edge_values[(square_index, partner_index, square.side_name, partner.side_name)]

            edge_color_pair = edge_color_pair_map["%s/%s" % (square.color_name, partner.color_name)]
            high_low_per_edge_color[edge_color_pair].add(highlow)

        # log.info("high_low_per_edge_color for orbit %d\n%s" % (target_orbit_id, high_low_per_edge_color))
        # log.info("")
        return high_low_per_edge_color

    # @timed_function
    def sanity_check_edge_squares(self):
        for orbit_id in range(self.orbits):
            self.sanity_check_edges_red_orange_count_for_orbit(orbit_id)

    # @timed_function
    def assign_green_white_corners(self, green_white_corners):
        # log.info("Gr/Wh corner tuples %s".format(green_white_corners))
        valid_green_orange_white = (
            ["Gr", "OR", "Wh"],
            ["Wh", "Gr", "OR"],
            ["OR", "Wh", "Gr"],
        )

        valid_green_white_red = (
            ["Gr", "Wh", "Rd"],
            ["Rd", "Gr", "Wh"],
            ["Wh", "Rd", "Gr"],
        )

        for (corner1_index, corner2_index, corner3_index) in green_white_corners:
            corner1 = self.pos2square[corner1_index]
            corner2 = self.pos2square[corner2_index]
            corner3 = self.pos2square[corner3_index]
            color_seq = [x.color_name for x in (corner1, corner2, corner3)]

            # If this is the case we must flip the orange to red or vice versa
            if (
                color_seq not in valid_green_orange_white
                and color_seq not in valid_green_white_red
            ):
                if corner1.color_name == "OR":
                    corner1.color_name = "Rd"
                    #log.warning(
                    #    "change Gr/Wh corner partner %s from OR to Rd" % corner1
                    #)
                elif corner1.color_name == "Rd":
                    corner1.color_name = "OR"
                    #log.warning(
                    #    "change Gr/Wh corner partner %s from Rd to OR" % corner1
                    #)
                elif corner2.color_name == "OR":
                    corner2.color_name = "Rd"
                    #log.warning(
                    #    "change Gr/Wh corner partner %s from OR to Rd" % corner2
                    #)
                elif corner2.color_name == "Rd":
                    corner2.color_name = "OR"
                    #log.warning(
                    #    "change Gr/Wh corner partner %s from Rd to OR" % corner2
                    #)
                elif corner3.color_name == "OR":
                    corner3.color_name = "Rd"
                    #log.warning(
                    #    "change Gr/Wh corner partner %s from OR to Rd" % corner3
                    #)
                elif corner3.color_name == "Rd":
                    corner3.color_name = "OR"
                    #log.warning(
                    #    "change Gr/Wh corner partner %s from Rd to OR" % corner3
                    #)

    # @timed_function
    def assign_green_yellow_corners(self, green_yellow_corners):
        valid_green_yellow_orange = (
            ["Gr", "Ye", "OR"],
            ["OR", "Gr", "Ye"],
            ["Ye", "OR", "Gr"],
        )

        valid_green_red_yellow = (
            ["Gr", "Rd", "Ye"],
            ["Ye", "Gr", "Rd"],
            ["Rd", "Ye", "Gr"],
        )

        for (corner1_index, corner2_index, corner3_index) in green_yellow_corners:
            corner1 = self.pos2square[corner1_index]
            corner2 = self.pos2square[corner2_index]
            corner3 = self.pos2square[corner3_index]
            color_seq = [x.color_name for x in (corner1, corner2, corner3)]

            # If this is the case we must flip the orange to red or vice versa
            if (
                color_seq not in valid_green_yellow_orange
                and color_seq not in valid_green_red_yellow
            ):

                if corner1.color_name == "OR":
                    corner1.color_name = "Rd"
                    #log.warning(
                    #    "change Gr/Ye corner partner %s from OR to Rd" % corner1
                    #)
                elif corner1.color_name == "Rd":
                    corner1.color_name = "OR"
                    #log.warning(
                    #    "change Gr/Ye corner partner %s from Rd to OR" % corner1
                    #)
                elif corner2.color_name == "OR":
                    corner2.color_name = "Rd"
                    #log.warning(
                    #    "change Gr/Ye corner partner %s from OR to Rd" % corner2
                    #)
                elif corner2.color_name == "Rd":
                    corner2.color_name = "OR"
                    #log.warning(
                    #    "change Gr/Ye corner partner %s from Rd to OR" % corner2
                    #)
                elif corner3.color_name == "OR":
                    corner3.color_name = "Rd"
                    #log.warning(
                    #    "change Gr/Ye corner partner %s from OR to Rd" % corner3
                    #)
                elif corner3.color_name == "Rd":
                    corner3.color_name = "OR"
                    #log.warning(
                    #    "change Gr/Ye corner partner %s from Rd to OR" % corner3
                    #)

    # @timed_function
    def assign_blue_white_corners(self, blue_white_corners):
        # log.info("Bu/Wh corner tuples %s".format(blue_white_corners))
        valid_blue_white_orange = (
            ["Bu", "Wh", "OR"],
            ["OR", "Bu", "Wh"],
            ["Wh", "OR", "Bu"],
        )

        valid_blue_red_white = (
            ["Bu", "Rd", "Wh"],
            ["Wh", "Bu", "Rd"],
            ["Rd", "Wh", "Bu"],
        )

        for (corner1_index, corner2_index, corner3_index) in blue_white_corners:
            corner1 = self.pos2square[corner1_index]
            corner2 = self.pos2square[corner2_index]
            corner3 = self.pos2square[corner3_index]
            color_seq = [x.color_name for x in (corner1, corner2, corner3)]

            # If this is the case we must flip the orange to red or vice versa
            if (
                color_seq not in valid_blue_white_orange
                and color_seq not in valid_blue_red_white
            ):

                if corner1.color_name == "OR":
                    corner1.color_name = "Rd"
                    #log.warning(
                    #    "change Bu/Wh corner partner %s from OR to Rd" % corner1
                    #)
                elif corner1.color_name == "Rd":
                    corner1.color_name = "OR"
                    #log.warning(
                    #    "change Bu/Wh corner partner %s from Rd to OR" % corner1
                    #)
                elif corner2.color_name == "OR":
                    corner2.color_name = "Rd"
                    #log.warning(
                    #    "change Bu/Wh corner partner %s from OR to Rd" % corner2
                    #)
                elif corner2.color_name == "Rd":
                    corner2.color_name = "OR"
                    #log.warning(
                    #    "change Bu/Wh corner partner %s from Rd to OR" % corner2
                    #)
                elif corner3.color_name == "OR":
                    corner3.color_name = "Rd"
                    #log.warning(
                    #    "change Bu/Wh corner partner %s from OR to Rd" % corner3
                    #)
                elif corner3.color_name == "Rd":
                    corner3.color_name = "OR"
                    #log.warning(
                    #    "change Bu/Wh corner partner %s from Rd to OR" % corner3
                    #)

    # @timed_function
    def assign_blue_yellow_corners(self, blue_yellow_corners):
        valid_blue_yellow_red = (
            ["Bu", "Ye", "Rd"],
            ["Rd", "Bu", "Ye"],
            ["Ye", "Rd", "Bu"],
        )

        valid_blue_orange_yellow = (
            ["Bu", "OR", "Ye"],
            ["Ye", "Bu", "OR"],
            ["OR", "Ye", "Bu"],
        )

        for (corner1_index, corner2_index, corner3_index) in blue_yellow_corners:
            corner1 = self.pos2square[corner1_index]
            corner2 = self.pos2square[corner2_index]
            corner3 = self.pos2square[corner3_index]
            color_seq = [x.color_name for x in (corner1, corner2, corner3)]

            # If this is the case we must flip the orange to red or vice versa
            if (
                color_seq not in valid_blue_yellow_red
                and color_seq not in valid_blue_orange_yellow
            ):

                if corner1.color_name == "OR":
                    corner1.color_name = "Rd"
                    #log.warning(
                    #    "change Bu/Ye corner partner %s from OR to Rd" % corner1
                    #)
                elif corner1.color_name == "Rd":
                    corner1.color_name = "OR"
                    #log.warning(
                    #    "change Bu/Ye corner partner %s from Rd to OR" % corner1
                    #)
                elif corner2.color_name == "OR":
                    corner2.color_name = "Rd"
                    #log.warning(
                    #    "change Bu/Ye corner partner %s from OR to Rd" % corner2
                    #)
                elif corner2.color_name == "Rd":
                    corner2.color_name = "OR"
                    #log.warning(
                    #    "change Bu/Ye corner partner %s from Rd to OR" % corner2
                    #)
                elif corner3.color_name == "OR":
                    corner3.color_name = "Rd"
                    #log.warning(
                    #    "change Bu/Ye corner partner %s from OR to Rd" % corner3
                    #)
                elif corner3.color_name == "Rd":
                    corner3.color_name = "OR"
                    #log.warning(
                    #    "change Bu/Ye corner partner %s from Rd to OR" % corner3
                    #)

    # @timed_function
    def sanity_check_corner_squares(self):
        (green_white_corners, green_yellow_corners, blue_white_corners, blue_yellow_corners) = self.find_corners_by_color()
        self.assign_green_white_corners(green_white_corners)
        self.assign_green_yellow_corners(green_yellow_corners)
        self.assign_blue_white_corners(blue_white_corners)
        self.assign_blue_yellow_corners(blue_yellow_corners)

    # @timed_function
    def get_corner_swap_count(self):

        needed_corners = ["BLU", "BRU", "FLU", "FRU", "DFL", "DFR", "BDL", "BDR"]

        to_check = [
            (
                self.sideU.corner_pos[0],
                self.sideL.corner_pos[0],
                self.sideB.corner_pos[1],
            ),  # ULB
            (
                self.sideU.corner_pos[1],
                self.sideR.corner_pos[1],
                self.sideB.corner_pos[0],
            ),  # URB
            (
                self.sideU.corner_pos[2],
                self.sideL.corner_pos[1],
                self.sideF.corner_pos[0],
            ),  # ULF
            (
                self.sideU.corner_pos[3],
                self.sideF.corner_pos[1],
                self.sideR.corner_pos[0],
            ),  # UFR
            (
                self.sideD.corner_pos[0],
                self.sideL.corner_pos[3],
                self.sideF.corner_pos[2],
            ),  # DLF
            (
                self.sideD.corner_pos[1],
                self.sideF.corner_pos[3],
                self.sideR.corner_pos[2],
            ),  # DFR
            (
                self.sideD.corner_pos[2],
                self.sideL.corner_pos[2],
                self.sideB.corner_pos[3],
            ),  # DLB
            (
                self.sideD.corner_pos[3],
                self.sideR.corner_pos[3],
                self.sideB.corner_pos[2],
            ),  # DRB
        ]

        current_corners = []
        for (square_index1, square_index2, square_index3) in to_check:
            square1 = self.pos2square[square_index1]
            square2 = self.pos2square[square_index2]
            square3 = self.pos2square[square_index3]
            corner_str = "".join(
                sorted([square1.side_name, square2.side_name, square3.side_name])
            )
            current_corners.append(corner_str)

        return get_swap_count(needed_corners, current_corners)

    # @timed_function
    def corner_swaps_even(self):
        if self.get_corner_swap_count() % 2 == 0:
            return True
        return False

    # @timed_function
    def corner_swaps_odd(self):
        if self.get_corner_swap_count() % 2 == 1:
            return True
        return False

    # @timed_function
    def get_edge_swap_count(self, orbit):
        needed_edges = []
        to_check = []

        # Upper
        for square_index in self.sideU.edge_north_pos:
            to_check.append(square_index)
            needed_edges.append("UB")
            break

        for square_index in reversed(self.sideU.edge_west_pos):
            to_check.append(square_index)
            needed_edges.append("UL")
            break

        for square_index in reversed(self.sideU.edge_south_pos):
            to_check.append(square_index)
            needed_edges.append("UF")
            break

        for square_index in self.sideU.edge_east_pos:
            to_check.append(square_index)
            needed_edges.append("UR")
            break

        # Left
        for square_index in reversed(self.sideL.edge_west_pos):
            to_check.append(square_index)
            needed_edges.append("LB")
            break

        for square_index in self.sideL.edge_east_pos:
            to_check.append(square_index)
            needed_edges.append("LF")
            break

        # Right
        for square_index in reversed(self.sideR.edge_west_pos):
            to_check.append(square_index)
            needed_edges.append("RF")
            break

        for square_index in self.sideR.edge_east_pos:
            to_check.append(square_index)
            needed_edges.append("RB")
            break

        # Down
        for square_index in self.sideD.edge_north_pos:
            to_check.append(square_index)
            needed_edges.append("DF")
            break

        for square_index in reversed(self.sideD.edge_west_pos):
            to_check.append(square_index)
            needed_edges.append("DL")
            break

        for square_index in reversed(self.sideD.edge_south_pos):
            to_check.append(square_index)
            needed_edges.append("DB")
            break

        for square_index in self.sideD.edge_east_pos:
            to_check.append(square_index)
            needed_edges.append("DR")
            break

        current_edges = []

        for square_index in to_check:
            side = self.pos2side[square_index]
            partner_index = side.get_wing_partner(square_index)
            square1 = self.pos2square[square_index]
            square2 = self.pos2square[partner_index]

            if square1.side_name in ("U", "D"):
                wing_str = square1.side_name + square2.side_name
            elif square2.side_name in ("U", "D"):
                wing_str = square2.side_name + square1.side_name
            elif square1.side_name in ("L", "R"):
                wing_str = square1.side_name + square2.side_name
            elif square2.side_name in ("L", "R"):
                wing_str = square2.side_name + square1.side_name
            else:
                raise Exception(
                    "Could not determine wing_str for (%s, %s)" % (square1, square2)
                )

            current_edges.append(wing_str)

        return get_swap_count(needed_edges, current_edges)

    # @timed_function
    def edge_swaps_even(self, orbit):
        if self.get_edge_swap_count(orbit) % 2 == 0:
            return True
        return False

    # @timed_function
    def edge_swaps_odd(self, orbit):
        if self.get_edge_swap_count(orbit) % 2 == 1:
            return True
        return False

    # @timed_function
    def validate_all_corners_found(self):
        needed_corners = ["BLU", "BRU", "FLU", "FRU", "DFL", "DFR", "BDL", "BDR"]

        to_check = [
            (
                self.sideU.corner_pos[0],
                self.sideL.corner_pos[0],
                self.sideB.corner_pos[1],
            ),  # ULB
            (
                self.sideU.corner_pos[1],
                self.sideR.corner_pos[1],
                self.sideB.corner_pos[0],
            ),  # URB
            (
                self.sideU.corner_pos[2],
                self.sideL.corner_pos[1],
                self.sideF.corner_pos[0],
            ),  # ULF
            (
                self.sideU.corner_pos[3],
                self.sideF.corner_pos[1],
                self.sideR.corner_pos[0],
            ),  # UFR
            (
                self.sideD.corner_pos[0],
                self.sideL.corner_pos[3],
                self.sideF.corner_pos[2],
            ),  # DLF
            (
                self.sideD.corner_pos[1],
                self.sideF.corner_pos[3],
                self.sideR.corner_pos[2],
            ),  # DFR
            (
                self.sideD.corner_pos[2],
                self.sideL.corner_pos[2],
                self.sideB.corner_pos[3],
            ),  # DLB
            (
                self.sideD.corner_pos[3],
                self.sideR.corner_pos[3],
                self.sideB.corner_pos[2],
            ),  # DRB
        ]

        current_corners = []
        for (square_index1, square_index2, square_index3) in to_check:
            square1 = self.pos2square[square_index1]
            square2 = self.pos2square[square_index2]
            square3 = self.pos2square[square_index3]
            corner_str = "".join(
                sorted([square1.side_name, square2.side_name, square3.side_name])
            )
            current_corners.append(corner_str)

        # We need a way to validate all of the needed_corners are present and
        # if not, what do we flip so that we do have all of the needed corners?
        for corner in needed_corners:
            if corner not in current_corners:
                raise Exception("corner {} is missing".format(corner))

    # @timed_function
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
            edges_even = self.edge_swaps_even(None)
            corners_even = self.corner_swaps_even()

            if edges_even == corners_even:
                return

            #log.warning(
            #    "edges_even %s != corners_even %s, swap most ambiguous orange or red edges to create valid parity"
            #    % (edges_even, corners_even)
            #)

        except ListMissingValue:
            #log.warning(
            #    "Either edges or corners are off, swap most ambiguous orange or red edges to create valid parity"
            #)
            pass

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
                partner = self.pos2square[partner_position]

                if square.color_name == "Gr" and partner.color_name == "OR":
                    green_orange_position = partner_position
                elif square.color_name == "Gr" and partner.color_name == "Rd":
                    green_red_position = partner_position
                elif square.color_name == "Bu" and partner.color_name == "OR":
                    blue_orange_position = partner_position
                elif square.color_name == "Bu" and partner.color_name == "Rd":
                    blue_red_position = partner_position

        #log.debug("green_orange_position %s".format(green_orange_position))
        #log.debug("green_red_position %s".format(green_red_position))
        #log.debug("blue_orange_position %s".format(blue_orange_position))
        #log.debug("blue_red_position %s".format(blue_red_position))

        square_green_orange = self.pos2square[green_orange_position]
        square_green_red = self.pos2square[green_red_position]
        square_blue_orange = self.pos2square[blue_orange_position]
        square_blue_red = self.pos2square[blue_red_position]

        # To correct the parity we can swap orange/red for the green edges or
        # we can swap orange/red for the blue edges. Which will result in the
        # lowest color distance with our orange/red baselines?
        distance_swap_green_edge = 0
        distance_swap_green_edge += lab_distance(square_blue_orange.lab, self.orange_baseline)
        distance_swap_green_edge += lab_distance(square_blue_red.lab, self.red_baseline)
        distance_swap_green_edge += lab_distance(square_green_orange.lab, self.red_baseline)
        distance_swap_green_edge += lab_distance(square_green_red.lab, self.orange_baseline)

        distance_swap_blue_edge = 0
        distance_swap_blue_edge += lab_distance(square_green_orange.lab, self.orange_baseline)
        distance_swap_blue_edge += lab_distance(square_green_red.lab, self.red_baseline)
        distance_swap_blue_edge += lab_distance(square_blue_orange.lab, self.red_baseline)
        distance_swap_blue_edge += lab_distance(square_blue_red.lab, self.orange_baseline)

        #log.info("distance_swap_green_edge %s" % distance_swap_green_edge)
        #log.info("distance_swap_blue_edge %s" % distance_swap_blue_edge)

        if distance_swap_green_edge < distance_swap_blue_edge:
            '''
            log.warning(
                "edge parity correction: change %s from %s to Rd"
                % (square_green_orange, square_green_orange.color_name)
            )
            log.warning(
                "edge parity correction: change %s from %s to OR"
                % (square_green_red, square_green_red.color_name)
            )
            '''
            square_green_orange.color_name = "Rd"
            square_green_red.color_name = "OR"
            square_green_orange.side_name = self.color_to_side_name[square_green_orange.color_name]
            square_green_red.side_name = self.color_to_side_name[square_green_red.color_name]
        else:
            '''
            log.warning(
                "edge parity correction: change %s from %s to Rd"
                % (square_blue_orange, square_blue_orange.color_name)
            )
            log.warning(
                "edge parity correction: change %s from %s to OR"
                % (square_blue_red, square_blue_red.color_name)
            )
            '''
            square_blue_orange.color_name = "Rd"
            square_blue_red.color_name = "OR"
            square_blue_orange.side_name = self.color_to_side_name[square_blue_orange.color_name]
            square_blue_red.side_name = self.color_to_side_name[square_blue_red.color_name]

        edges_even = self.edge_swaps_even(None)
        corners_even = self.corner_swaps_even()
        assert edges_even == corners_even, (
            "parity is still broken, edges_even %s, corners_even %s"
            % (edges_even, corners_even)
        )
