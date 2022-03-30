# standard libraries
import array
import logging
import os
import sys
from math import ceil, sqrt

try:
    # standard libraries
    from typing import Dict, List, Set, Tuple, Union
except ImportError:
    # this will barf for micropython...ignore it
    pass

# rubiks cube libraries
from rubikscolorresolver.permutations import (
    even_cube_center_color_permutations,
    len_even_cube_center_color_permutations,
    odd_cube_center_color_permutations,
)
from rubikscolorresolver.tsp_solver_greedy import solve_tsp

logger = logging.getLogger(__name__)

ALL_COLORS = ("Bu", "Gr", "OR", "Rd", "Wh", "Ye")
SIDES_COUNT = 6


def is_micropython() -> bool:
    return sys.implementation.name == "micropython"


if is_micropython():
    HTML_FILENAME = "rubiks-color-resolver.html"
else:
    HTML_FILENAME = "/tmp/rubiks-color-resolver.html"

try:
    os.unlink(HTML_FILENAME)
except Exception:
    pass

if is_micropython():
    # third party libraries
    from ucollections import OrderedDict
else:
    # standard libraries
    from collections import OrderedDict

    # rubiks cube libraries
    from rubikscolorresolver.cie2000 import lab_distance_cie2000

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


def find_index_for_value(list_foo: List[str], target: str, min_index: int) -> int:
    for (index, value) in enumerate(list_foo):
        if value == target and index >= min_index:
            return index
    raise ListMissingValue("Did not find %s in list %s" % (target, list_foo))


def get_swap_count(listA: List[str], listB: List[str]) -> int:
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
        # logger.info("listA %s" % " ".join(listA))
        # logger.info("listB %s" % " ".join(listB))
        assert False, "listA (len %d) and listB (len %d) must be the same length" % (
            A_length,
            B_length,
        )

    # if debug:
    #    logger.info("INIT")
    #    logger.info("listA: %s" % " ".join(listA))
    #    logger.info("listB: %s" % " ".join(listB))
    #    logger.info("")

    while listA != listB:
        if listA[index] != listB[index]:
            listA_value = listA[index]
            listB_index_with_A_value = find_index_for_value(listB, listA_value, index + 1)
            tmp = listB[index]
            listB[index] = listB[listB_index_with_A_value]
            listB[listB_index_with_A_value] = tmp
            swaps += 1

            # if debug:
            #    logger.info("index %d, swaps %d" % (index, swaps))
            #    logger.info("listA: %s" % " ".join(listA))
            #    logger.info("listB: %s" % " ".join(listB))
            #    logger.info("")
        index += 1

    # if debug:
    #    logger.info("swaps: %d" % swaps)
    #    logger.info("")
    return swaps


class LabColor(object):
    def __init__(self, L: float, a: float, b: float, red: int, green: int, blue: int) -> None:
        assert isinstance(red, int)
        assert isinstance(green, int)
        assert isinstance(blue, int)
        self.L = L
        self.a = a
        self.b = b
        self.red = red
        self.green = green
        self.blue = blue

    def __str__(self) -> str:
        return "Lab (%s, %s, %s)" % (self.L, self.a, self.b)

    def __repr__(self) -> str:
        return self.__str__()

    # def __hash__(self):
    #    return hash((self.L, self.a, self.b))

    def __eq__(self, other) -> bool:
        return bool(self.L == other.L and self.a == other.a and self.b == other.b)

    def __lt__(self, other) -> bool:
        if self.L != other.L:
            return self.L < other.L

        if self.a != other.a:
            return self.a < other.a

        return self.b < other.b


def lab_distance(lab1: LabColor, lab2: LabColor) -> int:
    """
    http://www.w3resource.com/python-exercises/math/python-math-exercise-79.php

    In mathematics, the Euclidean distance or Euclidean metric is the "ordinary"
    (i.e. straight-line) distance between two points in Euclidean space. With this
    distance, Euclidean space becomes a metric space. The associated norm is called
    the Euclidean norm.
    """
    # CIE2000 takes about 3x more CPU so use euclidean distance to save some cycles.  CIE2000
    # does give a more accurate distance metric but for our purposes it is no longer worth
    # the extra CPU cycles.
    if True or is_micropython():
        return int(sqrt(((lab1.L - lab2.L) ** 2) + ((lab1.a - lab2.a) ** 2) + ((lab1.b - lab2.b) ** 2)))
    else:
        return lab_distance_cie2000(lab1, lab2)


def rgb2lab(inputColor: Tuple[int, int, int]) -> LabColor:
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
    # logger.info("RGB ({}, {}, {}), L {}, a {}, b {}".format(red, green, blue, L, a, b))

    return LabColor(L, a, b, red, green, blue)


def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn

    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360

    if mx == 0:
        s = 0
    else:
        s = (df / mx) * 100

    v = mx * 100
    return (h, s, v)


class Square(object):
    def __init__(
        self,
        position: int,
        red: int,
        green: int,
        blue: int,
        side_name: None = None,
        color_name: None = None,
        via_color_box: bool = False,
    ) -> None:
        assert position is None or isinstance(position, int)
        assert isinstance(red, int)
        assert isinstance(green, int)
        assert isinstance(blue, int)
        assert side_name is None or isinstance(side_name, str)
        assert color_name is None or isinstance(color_name, str)

        if side_name is not None:
            assert side_name in ("U", "L", "F", "R", "B", "D")

        if color_name is not None:
            assert color_name in ("Wh", "Ye", "OR", "Rd", "Gr", "Bu")

        self.position = position
        self.lab = rgb2lab((red, green, blue))
        self.side_name = side_name  # ULFRBD
        self.color_name = color_name
        self.via_color_box = via_color_box

    def __str__(self) -> str:
        return "{}{}-{}".format(self.side_name, self.position, self.color_name)

    def __repr__(self) -> str:
        return self.__str__()

    def __lt__(self, other) -> bool:
        return self.position < other.position


class Side(object):
    def __init__(self, cube: "RubiksColorSolverGenericBase", width: int, name: str) -> None:
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

    def __str__(self) -> str:
        return "side-{}".format(self.name)

    def __repr__(self) -> str:
        return self.__str__()

    def set_square(
        self, position: int, red: int, green: int, blue: int, side_name: None = None, color_name: None = None
    ) -> None:
        self.squares[position] = Square(position, red, green, blue, side_name=side_name, color_name=color_name)

        if position in self.center_pos:
            self.center_squares.append(self.squares[position])

        elif position in self.edge_pos:
            self.edge_squares.append(self.squares[position])

        elif position in self.corner_pos:
            self.corner_squares.append(self.squares[position])

        else:
            raise Exception("Could not determine egde vs corner vs center")

    def calculate_wing_partners(self) -> None:
        for (pos1, pos2) in self.cube.all_edge_positions:
            if pos1 >= self.min_pos and pos1 <= self.max_pos:
                self.wing_partner[pos1] = pos2
            elif pos2 >= self.min_pos and pos2 <= self.max_pos:
                self.wing_partner[pos2] = pos1

    def get_wing_partner(self, wing_index: int) -> int:
        try:
            return self.wing_partner[wing_index]
        except KeyError:
            # logger.info("wing_partner\n%s\n".format(self.wing_partner))
            raise


class RubiksColorSolverGenericBase(object):
    def __init__(self, width: int) -> None:
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

        # if not os.path.exists(HTML_DIRECTORY):
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

    def calculate_pos2side(self) -> None:
        for side in self.sides.values():
            for x in range(side.min_pos, side.max_pos + 1):
                self.pos2side[x] = side

    def calculate_pos2square(self) -> None:
        for side in self.sides.values():
            for (position, square) in side.squares.items():
                self.pos2square[position] = square

    def enter_cube_state(self, input_state, order="URFDLB") -> None:
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
        if order == "URFDLB":
            state.extend(input_state[0 : self.squares_per_side])  # U
            state.extend(input_state[(self.squares_per_side * 4) : (self.squares_per_side * 5)])  # L
            state.extend(input_state[(self.squares_per_side * 2) : (self.squares_per_side * 3)])  # F
            state.extend(input_state[(self.squares_per_side * 1) : (self.squares_per_side * 2)])  # R
            state.extend(input_state[(self.squares_per_side * 5) : (self.squares_per_side * 6)])  # B
            state.extend(input_state[(self.squares_per_side * 3) : (self.squares_per_side * 4)])  # D
        elif order == "ULFRBD":
            state.extend(input_state[0 : self.squares_per_side])  # U
            state.extend(input_state[(self.squares_per_side * 1) : (self.squares_per_side * 2)])  # L
            state.extend(input_state[(self.squares_per_side * 2) : (self.squares_per_side * 3)])  # F
            state.extend(input_state[(self.squares_per_side * 3) : (self.squares_per_side * 4)])  # R
            state.extend(input_state[(self.squares_per_side * 4) : (self.squares_per_side * 5)])  # B
            state.extend(input_state[(self.squares_per_side * 5) : (self.squares_per_side * 6)])  # D
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
            "U": "Wh",
            "L": "OR",
            "F": "Gr",
            "R": "Rd",
            "B": "Bu",
            "D": "Ye",
        }

        self.orange_baseline = rgb2lab(
            (
                html_color["OR"]["red"],
                html_color["OR"]["green"],
                html_color["OR"]["blue"],
            )
        )
        self.red_baseline = rgb2lab(
            (
                html_color["Rd"]["red"],
                html_color["Rd"]["green"],
                html_color["Rd"]["blue"],
            )
        )

        for position in range(1, (self.squares_per_side * 6) + 1):
            side_name = state[position - 1]
            color_name = side_name_to_color[side_name]

            red = html_color[color_name]["red"]
            green = html_color[color_name]["green"]
            blue = html_color[color_name]["blue"]

            side = self.pos2side[position]
            side.set_square(position, red, green, blue, side_name, color_name)

        self.calculate_pos2square()

    def print_cube(self) -> None:
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
                    color_name = side.squares[side.min_pos + (y * self.width) + x].color_name
                    color_code = color_codes.get(color_name)

                    if color_name is None:
                        color_code = 97
                        data[line_number].append("\033[%dmFo\033[0m" % color_code)
                    else:
                        data[line_number].append("\033[%dm%s\033[0m" % (color_code, color_name))
                line_number += 1

        output = []
        for row in data:
            output.append(" ".join(row))

        sys.stderr.write("Cube\n\n%s\n" % "\n".join(output))

    def cube_for_kociemba_strict(self) -> List[str]:
        # logger.info("color_to_side_name:\n{}\n".format(self.color_to_side_name))
        data = []
        for side in (
            self.sideU,
            self.sideR,
            self.sideF,
            self.sideD,
            self.sideL,
            self.sideB,
        ):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]
                data.append(square.side_name)

        return data

    def validate_edge_orbit(self, orbit_id: int) -> bool:

        if self.width == 2:
            # rubiks cube libraries
            from rubikscolorresolver.cube_333 import edge_orbit_wing_pairs
        elif self.width == 3:
            # rubiks cube libraries
            from rubikscolorresolver.cube_333 import edge_orbit_wing_pairs
        elif self.width == 4:
            # rubiks cube libraries
            from rubikscolorresolver.cube_444 import edge_orbit_wing_pairs
        elif self.width == 5:
            # rubiks cube libraries
            from rubikscolorresolver.cube_555 import edge_orbit_wing_pairs
        elif self.width == 6:
            # rubiks cube libraries
            from rubikscolorresolver.cube_666 import edge_orbit_wing_pairs
        elif self.width == 7:
            # rubiks cube libraries
            from rubikscolorresolver.cube_777 import edge_orbit_wing_pairs

        valid = True

        # We need to see which orange/red we can flip that will make the edges valid
        wing_pair_counts = {}

        for (square1_position, square2_position) in edge_orbit_wing_pairs[orbit_id]:
            square1 = self.pos2square[square1_position]
            square2 = self.pos2square[square2_position]
            wing_pair_string = ", ".join(sorted([square1.color_name, square2.color_name]))
            # logger.info("orbit {}: ({}, {}) is ({})".format(orbit_id, square1_position, square2_position, wing_pair_string))  # noqa: E501

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

        # if not valid:
        #    logger.info("wing_pair_counts:\n{}\n".format(wing_pair_counts))
        #    logger.warning("valid: {}".format(valid))

        return valid

    def find_corners_by_color(self) -> Tuple:
        green_white_corners = []
        green_yellow_corners = []
        blue_white_corners = []
        blue_yellow_corners = []

        if self.width == 2:
            # rubiks cube libraries
            from rubikscolorresolver.cube_222 import corner_tuples
        elif self.width == 3:
            # rubiks cube libraries
            from rubikscolorresolver.cube_333 import corner_tuples
        elif self.width == 4:
            # rubiks cube libraries
            from rubikscolorresolver.cube_444 import corner_tuples
        elif self.width == 5:
            # rubiks cube libraries
            from rubikscolorresolver.cube_555 import corner_tuples
        elif self.width == 6:
            # rubiks cube libraries
            from rubikscolorresolver.cube_666 import corner_tuples
        elif self.width == 7:
            # rubiks cube libraries
            from rubikscolorresolver.cube_777 import corner_tuples

        for corner_tuple in corner_tuples:
            corner_colors = []

            for position in corner_tuple:
                # square = self.pos2square[position]
                # corner_colors.add(square.color_name)
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

    def find_edges_by_color(
        self, orbit_id: int
    ) -> Tuple[
        List[Tuple[Square, Square]],
        List[Tuple[Square, Square]],
        List[Tuple[Square, Square]],
        List[Tuple[Square, Square]],
    ]:

        if self.width == 2:
            # rubiks cube libraries
            from rubikscolorresolver.cube_333 import edge_orbit_wing_pairs
        elif self.width == 3:
            # rubiks cube libraries
            from rubikscolorresolver.cube_333 import edge_orbit_wing_pairs
        elif self.width == 4:
            # rubiks cube libraries
            from rubikscolorresolver.cube_444 import edge_orbit_wing_pairs
        elif self.width == 5:
            # rubiks cube libraries
            from rubikscolorresolver.cube_555 import edge_orbit_wing_pairs
        elif self.width == 6:
            # rubiks cube libraries
            from rubikscolorresolver.cube_666 import edge_orbit_wing_pairs
        elif self.width == 7:
            # rubiks cube libraries
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

            elif (
                square.color_name in white_red_orange_color_names and partner.color_name in white_red_orange_color_names
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

    def sanity_check_edges_red_orange_count_for_orbit(self, target_orbit_id: int) -> None:

        if self.width == 4 or self.width == 6 or (self.width == 5 and target_orbit_id == 0):
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
                raise Exception("There should be either 2 or 4 but we have %s" % target_color_red_or_orange_edges)

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

                if self.width == 4 or self.width == 6 or (self.width == 5 and target_orbit_id == 0):

                    for (index, (target_color_square, partner_square)) in enumerate(target_color_red_or_orange_edges):
                        red_orange = red_orange_permutation[index]
                        edge_color_pair = edge_color_pair_map[
                            "%s/%s"
                            % (
                                target_color_square.color_name,
                                partner_square.color_name,
                            )
                        ]
                        # logger.info("high_low_edge_per_color\n%s".format(high_low_edge_per_color))

                        if len(high_low_edge_per_color[edge_color_pair]) != 2:
                            # logger.warning("*" * 40)
                            # logger.warning("edge_color_pair %s high_low is %s" % (edge_color_pair, high_low_edge_per_color[edge_color_pair]))  # noqa: E501
                            # logger.warning("*" * 40)
                            distance += 999

                if min_distance is None or distance < min_distance:
                    min_distance = distance
                    min_distance_permutation = red_orange_permutation
                    """
                    logger.info(
                        "target edge %s, red_orange_permutation %s, distance %s (NEW MIN)"
                        % (target_color, ",".join(red_orange_permutation), distance)
                    )
                else:
                    logger.info(
                        "target edge %s, red_orange_permutation %s, distance %s)"
                        % (target_color, ",".join(red_orange_permutation), distance)
                    )

            logger.info("min_distance_permutation %s" % ",".join(min_distance_permutation))
                    """

            for (index, (target_color_square, partner_square)) in enumerate(target_color_red_or_orange_edges):
                if partner_square.color_name != min_distance_permutation[index]:
                    """
                    logger.warning(
                        "change %s edge partner %s from %s to %s"
                        % (
                            target_color,
                            partner_square,
                            partner_square.color_name,
                            min_distance_permutation[index],
                        )
                    )
                    """
                    partner_square.color_name = min_distance_permutation[index]
                    partner_square.side_name = self.color_to_side_name[partner_square.color_name]
                    """
                else:
                    logger.info(
                        "%s edge partner %s is %s"
                        % (target_color, partner_square, partner_square.color_name)
                    )

            logger.info("\n\n")
                    """

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

    def get_high_low_per_edge_color(self, target_orbit_id: int) -> Dict[str, Set[str]]:

        if self.width == 4:
            # rubiks cube libraries
            from rubikscolorresolver.cube_444 import edge_orbit_wing_pairs, highlow_edge_values
        elif self.width == 5:
            # rubiks cube libraries
            from rubikscolorresolver.cube_555 import edge_orbit_wing_pairs, highlow_edge_values
        elif self.width == 6:
            # rubiks cube libraries
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

        # logger.info("high_low_per_edge_color for orbit %d\n%s" % (target_orbit_id, high_low_per_edge_color))
        # logger.info("")
        return high_low_per_edge_color

    def sanity_check_edge_squares(self) -> None:
        for orbit_id in range(self.orbits):
            self.sanity_check_edges_red_orange_count_for_orbit(orbit_id)

    def assign_green_white_corners(self, green_white_corners) -> None:
        # logger.info("Gr/Wh corner tuples %s".format(green_white_corners))
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
            if color_seq not in valid_green_orange_white and color_seq not in valid_green_white_red:
                if corner1.color_name == "OR":
                    corner1.color_name = "Rd"
                    # logger.warning(
                    #    "change Gr/Wh corner partner %s from OR to Rd" % corner1
                    # )
                elif corner1.color_name == "Rd":
                    corner1.color_name = "OR"
                    # logger.warning(
                    #    "change Gr/Wh corner partner %s from Rd to OR" % corner1
                    # )
                elif corner2.color_name == "OR":
                    corner2.color_name = "Rd"
                    # logger.warning(
                    #    "change Gr/Wh corner partner %s from OR to Rd" % corner2
                    # )
                elif corner2.color_name == "Rd":
                    corner2.color_name = "OR"
                    # logger.warning(
                    #    "change Gr/Wh corner partner %s from Rd to OR" % corner2
                    # )
                elif corner3.color_name == "OR":
                    corner3.color_name = "Rd"
                    # logger.warning(
                    #    "change Gr/Wh corner partner %s from OR to Rd" % corner3
                    # )
                elif corner3.color_name == "Rd":
                    corner3.color_name = "OR"
                    # logger.warning(
                    #    "change Gr/Wh corner partner %s from Rd to OR" % corner3
                    # )

    def assign_green_yellow_corners(self, green_yellow_corners) -> None:
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
            if color_seq not in valid_green_yellow_orange and color_seq not in valid_green_red_yellow:

                if corner1.color_name == "OR":
                    corner1.color_name = "Rd"
                    # logger.warning(
                    #    "change Gr/Ye corner partner %s from OR to Rd" % corner1
                    # )
                elif corner1.color_name == "Rd":
                    corner1.color_name = "OR"
                    # logger.warning(
                    #    "change Gr/Ye corner partner %s from Rd to OR" % corner1
                    # )
                elif corner2.color_name == "OR":
                    corner2.color_name = "Rd"
                    # logger.warning(
                    #    "change Gr/Ye corner partner %s from OR to Rd" % corner2
                    # )
                elif corner2.color_name == "Rd":
                    corner2.color_name = "OR"
                    # logger.warning(
                    #    "change Gr/Ye corner partner %s from Rd to OR" % corner2
                    # )
                elif corner3.color_name == "OR":
                    corner3.color_name = "Rd"
                    # logger.warning(
                    #    "change Gr/Ye corner partner %s from OR to Rd" % corner3
                    # )
                elif corner3.color_name == "Rd":
                    corner3.color_name = "OR"
                    # logger.warning(
                    #    "change Gr/Ye corner partner %s from Rd to OR" % corner3
                    # )

    def assign_blue_white_corners(self, blue_white_corners) -> None:
        # logger.info("Bu/Wh corner tuples %s".format(blue_white_corners))
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
            if color_seq not in valid_blue_white_orange and color_seq not in valid_blue_red_white:

                if corner1.color_name == "OR":
                    corner1.color_name = "Rd"
                    # logger.warning(
                    #    "change Bu/Wh corner partner %s from OR to Rd" % corner1
                    # )
                elif corner1.color_name == "Rd":
                    corner1.color_name = "OR"
                    # logger.warning(
                    #    "change Bu/Wh corner partner %s from Rd to OR" % corner1
                    # )
                elif corner2.color_name == "OR":
                    corner2.color_name = "Rd"
                    # logger.warning(
                    #    "change Bu/Wh corner partner %s from OR to Rd" % corner2
                    # )
                elif corner2.color_name == "Rd":
                    corner2.color_name = "OR"
                    # logger.warning(
                    #    "change Bu/Wh corner partner %s from Rd to OR" % corner2
                    # )
                elif corner3.color_name == "OR":
                    corner3.color_name = "Rd"
                    # logger.warning(
                    #    "change Bu/Wh corner partner %s from OR to Rd" % corner3
                    # )
                elif corner3.color_name == "Rd":
                    corner3.color_name = "OR"
                    # logger.warning(
                    #    "change Bu/Wh corner partner %s from Rd to OR" % corner3
                    # )

    def assign_blue_yellow_corners(self, blue_yellow_corners) -> None:
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
            if color_seq not in valid_blue_yellow_red and color_seq not in valid_blue_orange_yellow:

                if corner1.color_name == "OR":
                    corner1.color_name = "Rd"
                    # logger.warning(
                    #    "change Bu/Ye corner partner %s from OR to Rd" % corner1
                    # )
                elif corner1.color_name == "Rd":
                    corner1.color_name = "OR"
                    # logger.warning(
                    #    "change Bu/Ye corner partner %s from Rd to OR" % corner1
                    # )
                elif corner2.color_name == "OR":
                    corner2.color_name = "Rd"
                    # logger.warning(
                    #    "change Bu/Ye corner partner %s from OR to Rd" % corner2
                    # )
                elif corner2.color_name == "Rd":
                    corner2.color_name = "OR"
                    # logger.warning(
                    #    "change Bu/Ye corner partner %s from Rd to OR" % corner2
                    # )
                elif corner3.color_name == "OR":
                    corner3.color_name = "Rd"
                    # logger.warning(
                    #    "change Bu/Ye corner partner %s from OR to Rd" % corner3
                    # )
                elif corner3.color_name == "Rd":
                    corner3.color_name = "OR"
                    # logger.warning(
                    #    "change Bu/Ye corner partner %s from Rd to OR" % corner3
                    # )

    def sanity_check_corner_squares(self) -> None:
        (
            green_white_corners,
            green_yellow_corners,
            blue_white_corners,
            blue_yellow_corners,
        ) = self.find_corners_by_color()
        self.assign_green_white_corners(green_white_corners)
        self.assign_green_yellow_corners(green_yellow_corners)
        self.assign_blue_white_corners(blue_white_corners)
        self.assign_blue_yellow_corners(blue_yellow_corners)

    def get_corner_swap_count(self) -> int:

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
            corner_str = "".join(sorted([square1.side_name, square2.side_name, square3.side_name]))
            current_corners.append(corner_str)

        return get_swap_count(needed_corners, current_corners)

    def corner_swaps_even(self) -> bool:
        if self.get_corner_swap_count() % 2 == 0:
            return True
        return False

    def corner_swaps_odd(self) -> bool:
        if self.get_corner_swap_count() % 2 == 1:
            return True
        return False

    def get_edge_swap_count(self, orbit: None) -> int:
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
                raise Exception("Could not determine wing_str for (%s, %s)" % (square1, square2))

            current_edges.append(wing_str)

        return get_swap_count(needed_edges, current_edges)

    def edge_swaps_even(self, orbit: None) -> bool:
        if self.get_edge_swap_count(orbit) % 2 == 0:
            return True
        return False

    def edge_swaps_odd(self, orbit) -> bool:
        if self.get_edge_swap_count(orbit) % 2 == 1:
            return True
        return False

    def validate_all_corners_found(self) -> None:
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
            corner_str = "".join(sorted([square1.side_name, square2.side_name, square3.side_name]))
            current_corners.append(corner_str)

        # We need a way to validate all of the needed_corners are present and
        # if not, what do we flip so that we do have all of the needed corners?
        for corner in needed_corners:
            if corner not in current_corners:
                raise Exception("corner {} is missing".format(corner))

    def validate_odd_cube_midge_vs_corner_parity(self) -> None:
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

        try:
            edges_even = self.edge_swaps_even(None)
            corners_even = self.corner_swaps_even()

            if edges_even == corners_even:
                return

            # logger.warning(
            #    "edges_even %s != corners_even %s, swap most ambiguous orange or red edges to create valid parity"
            #    % (edges_even, corners_even)
            # )

        except ListMissingValue:
            # logger.warning(
            #    "Either edges or corners are off, swap most ambiguous orange or red edges to create valid parity"
            # )
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

        for side in (
            self.sideU,
            self.sideL,
            self.sideF,
            self.sideR,
            self.sideB,
            self.sideD,
        ):
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

        # logger.debug("green_orange_position %s".format(green_orange_position))
        # logger.debug("green_red_position %s".format(green_red_position))
        # logger.debug("blue_orange_position %s".format(blue_orange_position))
        # logger.debug("blue_red_position %s".format(blue_red_position))

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

        # logger.info("distance_swap_green_edge %s" % distance_swap_green_edge)
        # logger.info("distance_swap_blue_edge %s" % distance_swap_blue_edge)

        if distance_swap_green_edge < distance_swap_blue_edge:
            """
            logger.warning(
                "edge parity correction: change %s from %s to Rd"
                % (square_green_orange, square_green_orange.color_name)
            )
            logger.warning(
                "edge parity correction: change %s from %s to OR"
                % (square_green_red, square_green_red.color_name)
            )
            """
            square_green_orange.color_name = "Rd"
            square_green_red.color_name = "OR"
            square_green_orange.side_name = self.color_to_side_name[square_green_orange.color_name]
            square_green_red.side_name = self.color_to_side_name[square_green_red.color_name]
        else:
            """
            logger.warning(
                "edge parity correction: change %s from %s to Rd"
                % (square_blue_orange, square_blue_orange.color_name)
            )
            logger.warning(
                "edge parity correction: change %s from %s to OR"
                % (square_blue_red, square_blue_red.color_name)
            )
            """
            square_blue_orange.color_name = "Rd"
            square_blue_red.color_name = "OR"
            square_blue_orange.side_name = self.color_to_side_name[square_blue_orange.color_name]
            square_blue_red.side_name = self.color_to_side_name[square_blue_red.color_name]

        edges_even = self.edge_swaps_even(None)
        corners_even = self.corner_swaps_even()
        assert edges_even == corners_even, "parity is still broken, edges_even %s, corners_even %s" % (
            edges_even,
            corners_even,
        )


def median(list_foo: List[float]) -> float:
    list_foo = sorted(list_foo)
    list_foo_len = len(list_foo)

    if list_foo_len < 1:
        return None

    # Even number of entries
    if list_foo_len % 2 == 0:
        return (list_foo[int((list_foo_len - 1) / 2)] + list_foo[int((list_foo_len + 1) / 2)]) / 2.0

    # Odd number of entries
    else:
        return list_foo[int((list_foo_len - 1) / 2)]


def tsp_matrix_corners(corners: List[Union[Tuple[Square, Square, Square], List[Square]]]) -> List[List[int]]:
    len_corners = len(corners)

    # build a full matrix of color to color distances
    # init the 2d list with 0s
    matrix = [x[:] for x in [[0] * len_corners] * len_corners]

    for x in range(len_corners):
        x_corner = corners[x]

        for y in range(x + 1, len_corners):
            y_corner = corners[y]

            if x_corner[0].via_color_box == y_corner[0].via_color_box:
                distance = 9999
            else:
                distance_012 = (
                    lab_distance(x_corner[0].lab, y_corner[0].lab)
                    + lab_distance(x_corner[1].lab, y_corner[1].lab)
                    + lab_distance(x_corner[2].lab, y_corner[2].lab)
                )

                distance_201 = (
                    lab_distance(x_corner[0].lab, y_corner[2].lab)
                    + lab_distance(x_corner[1].lab, y_corner[0].lab)
                    + lab_distance(x_corner[2].lab, y_corner[1].lab)
                )

                distance_120 = (
                    lab_distance(x_corner[0].lab, y_corner[1].lab)
                    + lab_distance(x_corner[1].lab, y_corner[2].lab)
                    + lab_distance(x_corner[2].lab, y_corner[0].lab)
                )

                distance = min(distance_012, distance_201, distance_120)

            matrix[x][y] = distance
            matrix[y][x] = distance

    # print("corners matrix")
    # for row in matrix:
    #     print(row)

    return matrix


def tsp_corner_distance(
    corner1: Tuple[Square, Square, Square], corner2: Union[Tuple[Square, Square, Square], List[Square]]
) -> int:
    return (
        lab_distance(corner1[0].lab, corner2[0].lab)
        + lab_distance(corner1[1].lab, corner2[1].lab)
        + lab_distance(corner1[2].lab, corner2[2].lab)
    )


def traveling_salesman_corners(
    corners: List[Union[Tuple[Square, Square, Square], List[Square]]], desc: str
) -> List[Union[Tuple[Square, Square, Square], List[Square]]]:
    matrix = tsp_matrix_corners(corners)
    path = solve_tsp(matrix)
    sorted_corners = [corners[x] for x in path]

    for x in range(0, len(sorted_corners), 2):
        corner1 = sorted_corners[x]
        corner2 = sorted_corners[x + 1]

        distance_012 = (
            lab_distance(corner1[0].lab, corner2[0].lab)
            + lab_distance(corner1[1].lab, corner2[1].lab)
            + lab_distance(corner1[2].lab, corner2[2].lab)
        )

        distance_201 = (
            lab_distance(corner1[0].lab, corner2[2].lab)
            + lab_distance(corner1[1].lab, corner2[0].lab)
            + lab_distance(corner1[2].lab, corner2[1].lab)
        )

        distance_120 = (
            lab_distance(corner1[0].lab, corner2[1].lab)
            + lab_distance(corner1[1].lab, corner2[2].lab)
            + lab_distance(corner1[2].lab, corner2[0].lab)
        )

        distance = min(distance_012, distance_201, distance_120)

        if distance == distance_012:
            pass

        elif distance == distance_201:
            sorted_corners[x + 1] = (corner2[2], corner2[0], corner2[1])

        elif distance == distance_120:
            sorted_corners[x + 1] = (corner2[1], corner2[2], corner2[0])

        else:
            raise ValueError(distance)

    while True:
        max_delta = 0
        max_delta_corners_to_swap = None

        for x in range(0, len(sorted_corners), 2):
            corner1 = sorted_corners[x]
            corner2 = sorted_corners[x + 1]
            distance12 = tsp_corner_distance(corner1, corner2)

            for y in range(x + 2, len(sorted_corners), 2):
                corner3 = sorted_corners[y]
                corner4 = sorted_corners[y + 1]
                distance34 = tsp_corner_distance(corner3, corner4)

                # If we were to swap corner2 with corner4, what would that do to the corner1->corner2 distance plus the corner3->corner4 distance?  # noqa: E501
                distance14 = tsp_corner_distance(corner1, corner4)
                distance32 = tsp_corner_distance(corner3, corner2)

                if distance14 + distance32 < distance12 + distance34:
                    delta = (distance12 + distance34) - (distance14 + distance32)

                    if delta > max_delta:
                        max_delta = delta
                        max_delta_corners_to_swap = (x + 1, y + 1)

        if max_delta_corners_to_swap:
            (x, y) = max_delta_corners_to_swap
            orig_x = sorted_corners[x]
            sorted_corners[x] = sorted_corners[y]
            sorted_corners[y] = orig_x

        else:
            break

    return sorted_corners


def tsp_matrix_edge_pairs(edge_pairs: List[Tuple[Square, Square]]) -> List[List[int]]:
    len_edge_pairs = len(edge_pairs)

    # build a full matrix of color to color distances
    # init the 2d list with 0s
    matrix = [x[:] for x in [[0] * len_edge_pairs] * len_edge_pairs]

    for x in range(len_edge_pairs):
        x_edge_pair = edge_pairs[x]

        for y in range(x + 1, len_edge_pairs):
            y_edge_pair = edge_pairs[y]

            if x_edge_pair[0].via_color_box == y_edge_pair[0].via_color_box:
                distance = 9999
            else:
                distance_01 = lab_distance(x_edge_pair[0].lab, y_edge_pair[0].lab) + lab_distance(
                    x_edge_pair[1].lab, y_edge_pair[1].lab
                )
                distance_10 = lab_distance(x_edge_pair[0].lab, y_edge_pair[1].lab) + lab_distance(
                    x_edge_pair[1].lab, y_edge_pair[0].lab
                )
                distance = min(distance_01, distance_10)

            matrix[x][y] = distance
            matrix[y][x] = distance

    return matrix


def edge_pair_distance(pair1: Tuple[Square, Square], pair2: Tuple[Square, Square], normal: bool) -> int:
    if normal:
        return lab_distance(pair1[0].lab, pair2[0].lab) + lab_distance(pair1[1].lab, pair2[1].lab)
    else:
        return lab_distance(pair1[0].lab, pair2[1].lab) + lab_distance(pair1[1].lab, pair2[0].lab)


def traveling_salesman_edge_pairs(edge_pairs: List[Tuple[Square, Square]], desc: str) -> List[Tuple[Square, Square]]:
    matrix = tsp_matrix_edge_pairs(edge_pairs)
    path = solve_tsp(matrix)
    sorted_edge_pairs = [edge_pairs[x] for x in path]

    for x in range(0, len(sorted_edge_pairs), 2):
        pair1 = sorted_edge_pairs[x]
        pair2 = sorted_edge_pairs[x + 1]
        distance_01 = edge_pair_distance(pair1, pair2, normal=True)
        distance_10 = edge_pair_distance(pair1, pair2, normal=False)

        if distance_10 < distance_01:
            sorted_edge_pairs[x + 1] = (
                sorted_edge_pairs[x + 1][1],
                sorted_edge_pairs[x + 1][0],
            )

    while True:
        max_delta = 0
        max_delta_edges_to_swap = None

        for x in range(0, len(sorted_edge_pairs), 2):
            pair1 = sorted_edge_pairs[x]
            pair2 = sorted_edge_pairs[x + 1]
            distance12 = edge_pair_distance(pair1, pair2, True)

            for y in range(x + 2, len(sorted_edge_pairs), 2):
                pair3 = sorted_edge_pairs[y]
                pair4 = sorted_edge_pairs[y + 1]
                distance34 = edge_pair_distance(pair3, pair4, True)

                # If we were to swap pair2 with pair4, what would that do to the pair1->pair2 distance plus the pair3->pair4 distance?  # noqa: E501
                distance14 = edge_pair_distance(pair1, pair4, True)
                distance32 = edge_pair_distance(pair3, pair2, True)

                if distance14 + distance32 < distance12 + distance34:
                    delta = (distance12 + distance34) - (distance14 + distance32)

                    if delta > max_delta:
                        max_delta = delta
                        max_delta_edges_to_swap = (x + 1, y + 1)

        if max_delta_edges_to_swap:
            (x, y) = max_delta_edges_to_swap
            orig_x = sorted_edge_pairs[x]
            sorted_edge_pairs[x] = sorted_edge_pairs[y]
            sorted_edge_pairs[y] = orig_x

        else:
            break

    return sorted_edge_pairs


def tsp_matrix(squares: List[Square]) -> Tuple[Tuple[float]]:
    len_squares = len(squares)
    r_len_squares = range(len_squares)

    # build a full matrix of color to color distances
    # init the 2d list with 0s
    matrix = [x[:] for x in [[0] * len_squares] * len_squares]

    for x in r_len_squares:
        x_lab = squares[x].lab

        for y in range(x + 1, len_squares):
            y_lab = squares[y].lab

            distance = lab_distance(x_lab, y_lab)
            matrix[x][y] = distance
            matrix[y][x] = distance

    # convert to tuple of tuples
    for (row_index, row) in enumerate(matrix):
        matrix[row_index] = tuple(row)

    matrix = tuple(matrix)

    return matrix


def traveling_salesman(squares: List[Square]) -> List[Square]:
    matrix = tsp_matrix(squares)
    path = solve_tsp(matrix)
    return [squares[x] for x in path]


def get_important_square_indexes(size):
    squares_per_side = size * size
    max_square = squares_per_side * 6
    first_squares = []
    last_squares = []

    for index in range(1, max_square + 1):
        if (index - 1) % squares_per_side == 0:
            first_squares.append(index)
        elif index % squares_per_side == 0:
            last_squares.append(index)

    last_UBD_squares = (last_squares[0], last_squares[4], last_squares[5])
    return (first_squares, last_squares, last_UBD_squares)


def hex_to_rgb(rgb_string):
    """
    Takes #112233 and returns the RGB values in decimal
    """
    if rgb_string.startswith("#"):
        rgb_string = rgb_string[1:]

    red = int(rgb_string[0:2], 16)
    green = int(rgb_string[2:4], 16)
    blue = int(rgb_string[4:6], 16)
    return (red, green, blue)


def hashtag_rgb_to_labcolor(rgb_string):
    (red, green, blue) = hex_to_rgb(rgb_string)
    # lab = rgb2lab((red, green, blue))
    # print("LabColor({}, {}, {}, {}, {}, {}),".format(lab.L, lab.a, lab.b, lab.red, lab.green, lab.blue))
    # return lab
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
    # "Wh": hashtag_rgb_to_labcolor("#FFFFFF"),
    # "Gr": hashtag_rgb_to_labcolor("#14694a"),
    # "Ye": hashtag_rgb_to_labcolor("#FFFF00"),
    # "OR": hashtag_rgb_to_labcolor("#943509"),
    # "Bu": hashtag_rgb_to_labcolor("#163967"),
    # "Rd": hashtag_rgb_to_labcolor("#680402"),
    "Wh": LabColor(100.0, 0.00526049995830391, -0.01040818452526793, 255, 255, 255),
    "Gr": LabColor(39.14982168015123, -32.45052099773829, 10.60519920674466, 20, 105, 74),
    "Ye": LabColor(97.13824698129729, -21.55590833483229, 94.48248544644462, 255, 255, 0),
    "OR": LabColor(35.71689493804023, 38.18518746791636, 43.98251678431012, 148, 53, 9),
    "Bu": LabColor(23.92144819784853, 5.28400492805528, -30.63998357385018, 22, 57, 103),
    "Rd": LabColor(20.18063311070288, 40.48184409611946, 29.94038922869042, 104, 4, 2),
}


def get_row_color_distances(squares, row_baseline_lab):
    """
    'colors' is list if (index, (red, green, blue)) tuples
    'row_baseline_lab' is a list of Lab colors, one for each row of colors

    Return the total distance of the colors in a row vs their baseline
    """
    results = []
    squares_per_row = int(len(squares) / 6)
    count = 0
    row_index = 0
    distance = 0
    baseline_lab = row_baseline_lab[row_index]

    for square in squares:
        baseline_lab = row_baseline_lab[row_index]
        distance += lab_distance(baseline_lab, square.lab)
        count += 1

        if count % squares_per_row == 0:
            results.append(int(distance))
            row_index += 1
            distance = 0

    return results


def get_squares_for_row(squares, target_row_index):
    results = []
    squares_per_row = int(len(squares) / 6)
    count = 0
    row_index = 0

    for square in squares:
        if row_index == target_row_index:
            results.append(square)
        count += 1

        if count % squares_per_row == 0:
            row_index += 1

    return results


def square_list_to_lab(squares: List[Square]) -> LabColor:
    reds = array.array("B")
    greens = array.array("B")
    blues = array.array("B")

    for square in squares:
        (red, green, blue) = (square.lab.red, square.lab.green, square.lab.blue)
        reds.append(red)
        greens.append(green)
        blues.append(blue)

    median_red = int(median(reds))
    median_green = int(median(greens))
    median_blue = int(median(blues))

    return rgb2lab((median_red, median_green, median_blue))


def open_mode(filename):
    if os.path.exists(HTML_FILENAME):
        return "a"
    else:
        return "w"


class RubiksColorSolverGeneric(RubiksColorSolverGenericBase):
    def www_header(self):
        """
        Write the <head> including css
        """
        side_margin = 10
        square_size = 40
        size = self.width  # 3 for 3x3x3, etc

        with open(HTML_FILENAME, open_mode(HTML_FILENAME)) as fh:
            fh.write(
                """<!DOCTYPE html>
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

"""
                % side_margin
            )

            for x in range(1, size - 1):
                fh.write("div.col%d,\n" % x)

            fh.write(
                """div.col%d {
    float: left;
}

div.col%d {
    margin-left: %dpx;
}
div#upper,
div#down {
    margin-left: %dpx;
}
"""
                % (
                    size - 1,
                    size,
                    (size - 1) * square_size,
                    (size * square_size) + (3 * side_margin),
                )
            )

            fh.write(
                """
span.half_square {
    width: %dpx;
    height: %dpx;
    white-space-collapsing: discard;
    display: inline-block;
    color: black;
    font-weight: bold;
    line-height: %dpx;
    text-align: center;
}

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

div#bottom {
    cursor: pointer;
}

div#bottom div.initial_rgb_values {
    display: none;
}
</style>

<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>
<script>
$(document).ready(function()
{
    $("div#bottom").click(function(event)
    {
        if ($("div#bottom div.final_cube").is(":visible")) {
            $("div#bottom div.initial_rgb_values").show();
            $("div#bottom div.final_cube").hide();
        } else {
            $("div#bottom div.initial_rgb_values").hide();
            $("div#bottom div.final_cube").show();
        }
    })
});
</script>


<title>Rubiks Cube Color Resolver</title>
</head>
<body>
"""
                % (
                    int(square_size / 2),
                    square_size,
                    square_size,
                    square_size,
                    square_size,
                    square_size,
                    square_size,
                    square_size,
                    square_size,
                )
            )

    def write_color_corners(self, desc, corners):
        with open(HTML_FILENAME, open_mode(HTML_FILENAME)) as fh:
            fh.write("<div class='clear colors'>\n")
            fh.write("<h2>%s</h2>\n" % desc)

            for row_index in range(3):
                for (index, (corner0, corner1, corner2)) in enumerate(corners):

                    if row_index == 0:
                        square = corner0
                    elif row_index == 1:
                        square = corner1
                    elif row_index == 2:
                        square = corner2
                    else:
                        raise ValueError(row_index)

                    (red, green, blue) = (
                        square.lab.red,
                        square.lab.green,
                        square.lab.blue,
                    )

                    if index and index % 2 == 0:
                        fh.write("<span class='half_square'></span>")

                    fh.write(
                        "<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s, side %s'>%s</span>\n"  # noqa: E501
                        % (
                            red,
                            green,
                            blue,
                            red,
                            green,
                            blue,
                            int(square.lab.L),
                            int(square.lab.a),
                            int(square.lab.b),
                            square.color_name,
                            square.side_name,
                            square.position,
                        )
                    )
                fh.write("<br>")
            fh.write("</div>\n")

    def write_color_edge_pairs(self, desc, square_pairs):
        with open(HTML_FILENAME, open_mode(HTML_FILENAME)) as fh:
            fh.write("<div class='clear colors'>\n")
            fh.write("<h2>%s</h2>\n" % desc)

            for use_square1 in (True, False):
                for (index, (square1, square2)) in enumerate(square_pairs):

                    if use_square1:
                        square = square1
                    else:
                        square = square2

                    (red, green, blue) = (
                        square.lab.red,
                        square.lab.green,
                        square.lab.blue,
                    )

                    if index and index % 2 == 0:
                        fh.write("<span class='half_square'></span>")

                    fh.write(
                        "<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s, side %s'>%s</span>\n"  # noqa: E501
                        % (
                            red,
                            green,
                            blue,
                            red,
                            green,
                            blue,
                            int(square.lab.L),
                            int(square.lab.a),
                            int(square.lab.b),
                            square.color_name,
                            square.side_name,
                            square.position,
                        )
                    )
                fh.write("<br>")
            fh.write("</div>\n")

    def write_colors(self, desc, squares):
        with open(HTML_FILENAME, open_mode(HTML_FILENAME)) as fh:
            squares_per_row = int(len(squares) / 6)
            fh.write("<div class='clear colors'>\n")
            fh.write("<h2>%s</h2>\n" % desc)

            count = 0
            for square in squares:
                (red, green, blue) = (square.lab.red, square.lab.green, square.lab.blue)
                fh.write(
                    "<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s, side %s'>%d</span>\n"  # noqa: E501
                    % (
                        red,
                        green,
                        blue,
                        red,
                        green,
                        blue,
                        int(square.lab.L),
                        int(square.lab.a),
                        int(square.lab.b),
                        square.color_name,
                        square.side_name,
                        square.position,
                    )
                )

                count += 1

                if count % squares_per_row == 0:
                    fh.write("<br>")
            fh.write("</div>\n")

    def www_footer(self):
        with open(HTML_FILENAME, open_mode(HTML_FILENAME)) as fh:
            fh.write(
                """
</body>
</html>
"""
            )

    def enter_scan_data(self, scan_data: Dict[int, List[int]]) -> None:

        for (position, (red, green, blue)) in scan_data.items():
            position = int(position)
            side = self.pos2side[position]
            side.set_square(position, red, green, blue)

        if self.write_debug_file:
            self.www_header()

            with open(HTML_FILENAME, open_mode(HTML_FILENAME)) as fh:
                fh.write("<h1>RGB Input</h1>\n")
                fh.write("<pre>{}</pre>\n".format(scan_data))

        self.calculate_pos2square()

    def html_cube(self, desc, use_html_colors, div_class):
        cube = ["dummy"]

        for side in (
            self.sideU,
            self.sideL,
            self.sideF,
            self.sideR,
            self.sideB,
            self.sideD,
        ):
            for position in range(side.min_pos, side.max_pos + 1):
                square = side.squares[position]

                if use_html_colors:
                    red = html_color[square.color_name]["red"]
                    green = html_color[square.color_name]["green"]
                    blue = html_color[square.color_name]["blue"]
                else:
                    red = square.lab.red
                    green = square.lab.green
                    blue = square.lab.blue

                cube.append((red, green, blue, square.color_name, square.lab))

        col = 1
        squares_per_side = self.width * self.width
        max_square = squares_per_side * 6

        sides = ("upper", "left", "front", "right", "back", "down")
        side_index = -1
        (first_squares, last_squares, last_UBD_squares) = get_important_square_indexes(self.width)

        html = []
        html.append("<div class='cube {}'>".format(div_class))
        html.append("<h1>%s</h1>\n" % desc)
        for index in range(1, max_square + 1):
            if index in first_squares:
                side_index += 1
                html.append("<div class='side' id='%s'>\n" % sides[side_index])

            (red, green, blue, color_name, lab) = cube[index]

            html.append(
                "    <div class='square col%d' title='RGB (%d, %d, %d), Lab (%s, %s, %s), "
                "color %s' style='background-color: #%02x%02x%02x;'><span>%02d</span></div>\n"
                % (
                    col,
                    red,
                    green,
                    blue,
                    int(lab.L),
                    int(lab.a),
                    int(lab.b),
                    color_name,
                    red,
                    green,
                    blue,
                    index,
                )
            )

            if index in last_squares:
                html.append("</div>\n")

                if index in last_UBD_squares:
                    html.append("<div class='clear'></div>\n")

            col += 1

            if col == self.width + 1:
                col = 1

        html.append("</div>")
        return "".join(html)

    def write_html(self, html):
        with open(HTML_FILENAME, open_mode(HTML_FILENAME)) as fh:
            fh.write(html)

    def _write_colors(self, desc, box):
        with open(HTML_FILENAME, open_mode(HTML_FILENAME)) as fh:
            fh.write("<div class='clear colors'>\n")
            fh.write("<h2>{}</h2>\n".format(desc))

            for color_name in ("Wh", "Ye", "Gr", "Bu", "OR", "Rd"):
                lab = box[color_name]

                fh.write(
                    "<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%s</span>\n"  # noqa: E501
                    % (
                        lab.red,
                        lab.green,
                        lab.blue,
                        lab.red,
                        lab.green,
                        lab.blue,
                        int(lab.L),
                        int(lab.a),
                        int(lab.b),
                        color_name,
                        color_name,
                    )
                )
            fh.write("<br>")
            fh.write("</div>\n")

    def write_crayola_colors(self):
        self._write_colors("crayola box", crayola_colors)

    def write_color_box(self):
        self._write_colors("color_box", self.color_box)

    def set_state(self) -> None:
        self.state = []

        # odd cube
        if self.sideU.mid_pos is not None:

            # Assign a color name to each center square. Compute
            # which naming scheme results in the least total color distance in
            # terms of the assigned color name vs. the colors in crayola_colors.
            min_distance = None
            min_distance_permutation = None

            # Build a list of all center squares
            center_squares = []
            for side in (
                self.sideU,
                self.sideL,
                self.sideF,
                self.sideR,
                self.sideB,
                self.sideD,
            ):
                square = side.squares[side.mid_pos]
                center_squares.append(square)
            # desc = "middle center"
            # logger.info("center_squares: %s".format(center_squares))

            for permutation in odd_cube_center_color_permutations:
                distance = 0

                for (index, center_square) in enumerate(center_squares):
                    color_name = permutation[index]
                    color_obj = crayola_colors[color_name]
                    distance += lab_distance(center_square.lab, color_obj)

                if min_distance is None or distance < min_distance:
                    min_distance = distance
                    min_distance_permutation = permutation
                    """
                    logger.info("{} PERMUTATION {}, DISTANCE {:,} (NEW MIN)".format(desc, permutation, int(distance)))
                else:
                    logger.info("{} PERMUTATION {}, DISTANCE {}".format(desc, permutation, distance))
                    """

            self.color_to_side_name = {
                min_distance_permutation[0]: "U",
                min_distance_permutation[1]: "L",
                min_distance_permutation[2]: "F",
                min_distance_permutation[3]: "R",
                min_distance_permutation[4]: "B",
                min_distance_permutation[5]: "D",
            }
            # logger.info("{} FINAL PERMUTATION {}".format(desc, min_distance_permutation))

        # even cube
        else:
            self.color_to_side_name = {
                "Wh": "U",
                "OR": "L",
                "Gr": "F",
                "Rd": "R",
                "Bu": "B",
                "Ye": "D",
            }

        for side in (
            self.sideU,
            self.sideR,
            self.sideF,
            self.sideD,
            self.sideL,
            self.sideB,
        ):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]

                if square.color_name is None:
                    raise Exception(f"{square} does not have a color_name")

                square.side_name = self.color_to_side_name[square.color_name]

    def cube_for_json(self):
        """
        Return a dictionary of the cube data so that we can json dump it
        """
        data = {}
        data["kociemba"] = "".join(self.cube_for_kociemba_strict())
        data["sides"] = {}
        data["squares"] = {}

        for side in (
            self.sideU,
            self.sideR,
            self.sideF,
            self.sideD,
            self.sideL,
            self.sideB,
        ):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]
                color = square.color_name
                side_name = self.color_to_side_name[color]

                if side_name not in data["sides"]:
                    data["sides"][side_name] = {}
                    data["sides"][side_name]["colorName"] = color
                    data["sides"][side_name]["colorHTML"] = {}
                    data["sides"][side_name]["colorHTML"]["red"] = html_color[color]["red"]
                    data["sides"][side_name]["colorHTML"]["green"] = html_color[color]["green"]
                    data["sides"][side_name]["colorHTML"]["blue"] = html_color[color]["blue"]

                data["squares"][square.position] = {"finalSide": side_name}

        return data

    def assign_color_names(
        self, desc: str, squares_lists_all: List[Square], color_permutations: str, color_box: Dict[str, LabColor]
    ) -> None:
        """
        Assign a color name to each square in each squares_list. Compute
        which naming scheme results in the least total color distance in
        terms of the assigned color name vs. the colors in color_box.
        """
        ref_even_cube_center_color_permutations = even_cube_center_color_permutations
        # print("\n\n\n")
        # print("assign_color_names '{}' via {}".format(desc, color_permutations))

        def get_even_cube_center_color_permutation(permutation_index):
            LINE_LENGTH = 18
            start = permutation_index * LINE_LENGTH
            end = start + LINE_LENGTH
            return ref_even_cube_center_color_permutations[start:end].split()

        ref_ALL_COLORS = ALL_COLORS

        # squares_lists_all is sorted by color. Split that list into 6 even buckets (squares_lists).
        squares_per_row = int(len(squares_lists_all) / 6)
        squares_lists = []
        square_list = []

        # logger.info(f"squares_list_all {squares_lists_all}")
        # logger.info(f"squares_per_row {squares_per_row}")

        for square in squares_lists_all:
            square_list.append(square)

            if len(square_list) == squares_per_row:
                squares_lists.append(tuple(square_list))
                square_list = []

        # logger.info(f"squares_list10 {squares_lists}")

        # Compute the distance for each color in the color_box vs each squares_list
        # in squares_lists. Store this in distances_of_square_list_per_color
        distances_of_square_list_per_color = {}

        for color_name in ref_ALL_COLORS:
            color_lab = color_box[color_name]
            distances_of_square_list_per_color[color_name] = []

            for (index, square_list) in enumerate(squares_lists):
                distance = 0
                for square in square_list:
                    distance += lab_distance(square.lab, color_lab)
                distances_of_square_list_per_color[color_name].append(int(distance))
            distances_of_square_list_per_color[color_name] = distances_of_square_list_per_color[color_name]

        min_distance = 99999
        min_distance_permutation = None

        if color_permutations == "even_cube_center_color_permutations":

            # before sorting
            """
            print("\n".join(map(str, squares_lists)))
            for color_name in ref_ALL_COLORS:
                print("pre  distances_of_square_list_per_color {} : {}".format(color_name, distances_of_square_list_per_color[color_name]))  # noqa: E501
            print("")
            """

            # Move the squares_list row that is closest to Bu to the front, then Gr, OR, Rd, Wh, Ye.
            # This will allow us to skip many more entries later.
            for (insert_index, color_name) in enumerate(ref_ALL_COLORS):
                min_color_name_distance = 99999
                min_color_name_distance_index = None

                for (index, distance) in enumerate(distances_of_square_list_per_color[color_name]):
                    if distance < min_color_name_distance:
                        min_color_name_distance = distance
                        min_color_name_distance_index = index

                tmp_square_list = squares_lists[min_color_name_distance_index]
                squares_lists.pop(min_color_name_distance_index)
                squares_lists.insert(insert_index, tmp_square_list)

                for color_name in ref_ALL_COLORS:
                    blue_distance = distances_of_square_list_per_color[color_name][min_color_name_distance_index]
                    distances_of_square_list_per_color[color_name].pop(min_color_name_distance_index)
                    distances_of_square_list_per_color[color_name].insert(insert_index, blue_distance)

            # after sorting
            """
            print("\n".join(map(str, squares_lists)))
            for color_name in ref_ALL_COLORS:
                print("post distances_of_square_list_per_color {} : {}".format(color_name, distances_of_square_list_per_color[color_name]))  # noqa: E501
            print("")
            """

            permutation_len = len_even_cube_center_color_permutations
            permutation_index = 0
            # total = 0
            # skip_total = 0
            r = range(6)

            while permutation_index < permutation_len:
                permutation = get_even_cube_center_color_permutation(permutation_index)
                distance = 0
                skip_by = 0

                for x in r:
                    distance += distances_of_square_list_per_color[permutation[x]][x]

                    if distance > min_distance:

                        if x == 0:
                            skip_by = 120
                        elif x == 1:
                            skip_by = 24
                        elif x == 2:
                            skip_by = 6
                        elif x == 3:
                            skip_by = 2

                        # if skip_by:
                        #    print("{} PERMUTATION {} - {}, x {} distance {:,} > min {}, skip_by {}".format(
                        #        desc, permutation_index, permutation, x, distance, min_distance, skip_by))
                        break

                if skip_by:
                    permutation_index += skip_by
                    # skip_total += skip_by
                    continue

                if distance < min_distance:
                    # print("{} PERMUTATION {} - {}, DISTANCE {:,} vs min {} (NEW MIN)".format(desc, permutation_index, permutation, distance, min_distance))  # noqa: E501
                    # logger.info("{} PERMUTATION {}, DISTANCE {:,} (NEW MIN)".format(desc, permutation, int(distance)))
                    min_distance = distance
                    min_distance_permutation = permutation
                # else:
                #    print("{} PERMUTATION {} - {}, DISTANCE {} vs min {}".format(desc, permutation_index, permutation, distance, min_distance))  # noqa: E501
                #    #logger.info("{} PERMUTATION {}, DISTANCE {}".format(desc, permutation, distance))

                # total += 1
                permutation_index += 1

            # print("total {}".format(total))
            # print("skip total {}".format(skip_total))
            # print("")

        elif color_permutations == "odd_cube_center_color_permutations":
            for permutation in odd_cube_center_color_permutations:
                distance = (
                    distances_of_square_list_per_color[permutation[0]][0]
                    + distances_of_square_list_per_color[permutation[1]][1]
                    + distances_of_square_list_per_color[permutation[2]][2]
                    + distances_of_square_list_per_color[permutation[3]][3]
                    + distances_of_square_list_per_color[permutation[4]][4]
                    + distances_of_square_list_per_color[permutation[5]][5]
                )

                if distance < min_distance:
                    min_distance = distance
                    min_distance_permutation = permutation

        # Assign the color name to the Square object
        for (index, square_list) in enumerate(squares_lists):
            color_name = min_distance_permutation[index]

            for square in square_list:
                square.color_name = color_name

    def get_squares_by_color_name(
        self,
    ) -> Tuple[List[Square], List[Square], List[Square], List[Square], List[Square], List[Square]]:
        white_squares = []
        yellow_squares = []
        orange_squares = []
        red_squares = []
        green_squares = []
        blue_squares = []

        for side in (
            self.sideU,
            self.sideR,
            self.sideF,
            self.sideD,
            self.sideL,
            self.sideB,
        ):
            for square in side.center_squares + side.corner_squares + side.edge_squares:
                if square.color_name == "Wh":
                    white_squares.append(square)
                elif square.color_name == "Ye":
                    yellow_squares.append(square)
                elif square.color_name == "OR":
                    orange_squares.append(square)
                elif square.color_name == "Rd":
                    red_squares.append(square)
                elif square.color_name == "Gr":
                    green_squares.append(square)
                elif square.color_name == "Bu":
                    blue_squares.append(square)

        return (
            white_squares,
            yellow_squares,
            orange_squares,
            red_squares,
            green_squares,
            blue_squares,
        )

    def resolve_color_box(self) -> None:
        """
        Temporarily assign names to all squares, use crayola colors as reference point.

        We use these name assignments to build our "color_box" which will be our
        references Wh, Ye, OR, Rd, Gr, Bu colors for assigning color names to edge
        and center squares.
        """

        # Save CPU cycles by only using the corner squares to create the color box
        corner_squares = []

        for side in (
            self.sideU,
            self.sideR,
            self.sideF,
            self.sideD,
            self.sideL,
            self.sideB,
        ):
            for square in side.corner_squares:
                corner_squares.append(square)

        sorted_corner_squares = traveling_salesman(corner_squares)

        self.assign_color_names(
            "corner squares for color_box",
            sorted_corner_squares,
            "even_cube_center_color_permutations",
            crayola_colors,
        )

        if self.write_debug_file:
            self.write_colors("corners for color_box", sorted_corner_squares)

        (
            white_squares,
            yellow_squares,
            orange_squares,
            red_squares,
            green_squares,
            blue_squares,
        ) = self.get_squares_by_color_name()
        self.color_box = {}
        self.color_box["Wh"] = square_list_to_lab(white_squares)
        self.color_box["Ye"] = square_list_to_lab(yellow_squares)
        self.color_box["OR"] = square_list_to_lab(orange_squares)
        self.color_box["Rd"] = square_list_to_lab(red_squares)
        self.color_box["Gr"] = square_list_to_lab(green_squares)
        self.color_box["Bu"] = square_list_to_lab(blue_squares)

        self.orange_baseline = self.color_box["OR"]
        self.red_baseline = self.color_box["Rd"]

        # Nuke all color names (they were temporary)
        for side in (
            self.sideU,
            self.sideR,
            self.sideF,
            self.sideD,
            self.sideL,
            self.sideB,
        ):
            for square in side.center_squares + side.corner_squares + side.edge_squares:
                square.color_name = None

        if self.write_debug_file:
            self.write_color_box()

    def squares_from_color_box(self) -> Tuple[Square, Square, Square, Square, Square, Square]:
        white = Square(
            None,
            self.color_box["Wh"].red,
            self.color_box["Wh"].green,
            self.color_box["Wh"].blue,
            color_name="Wh",
            via_color_box=True,
        )
        yellow = Square(
            None,
            self.color_box["Ye"].red,
            self.color_box["Ye"].green,
            self.color_box["Ye"].blue,
            color_name="Ye",
            via_color_box=True,
        )
        orange = Square(
            None,
            self.color_box["OR"].red,
            self.color_box["OR"].green,
            self.color_box["OR"].blue,
            color_name="OR",
            via_color_box=True,
        )
        red = Square(
            None,
            self.color_box["Rd"].red,
            self.color_box["Rd"].green,
            self.color_box["Rd"].blue,
            color_name="Rd",
            via_color_box=True,
        )
        green = Square(
            None,
            self.color_box["Gr"].red,
            self.color_box["Gr"].green,
            self.color_box["Gr"].blue,
            color_name="Gr",
            via_color_box=True,
        )
        blue = Square(
            None,
            self.color_box["Bu"].red,
            self.color_box["Bu"].green,
            self.color_box["Bu"].blue,
            color_name="Bu",
            via_color_box=True,
        )

        return (white, yellow, orange, red, green, blue)

    def resolve_corner_squares(self) -> None:
        """
        Assign names to the corner squares
        """
        if self.width == 2:
            # rubiks cube libraries
            from rubikscolorresolver.cube_222 import corner_tuples
        elif self.width == 3:
            # rubiks cube libraries
            from rubikscolorresolver.cube_333 import corner_tuples
        elif self.width == 4:
            # rubiks cube libraries
            from rubikscolorresolver.cube_444 import corner_tuples
        elif self.width == 5:
            # rubiks cube libraries
            from rubikscolorresolver.cube_555 import corner_tuples
        elif self.width == 6:
            # rubiks cube libraries
            from rubikscolorresolver.cube_666 import corner_tuples
        elif self.width == 7:
            # rubiks cube libraries
            from rubikscolorresolver.cube_777 import corner_tuples

        (white, yellow, orange, red, green, blue) = self.squares_from_color_box()
        target_corners = [
            (white, green, orange),
            (white, red, green),
            (white, orange, blue),
            (white, blue, red),
            (yellow, orange, green),
            (yellow, green, red),
            (yellow, blue, orange),
            (yellow, red, blue),
        ]
        corners = []

        for corner_tuple in corner_tuples:
            corners.append(
                (
                    self.pos2square[corner_tuple[0]],
                    self.pos2square[corner_tuple[1]],
                    self.pos2square[corner_tuple[2]],
                )
            )

        sorted_corners = traveling_salesman_corners(target_corners + corners, "corners")
        # logger.info(f"sorted_corners\n{pformat(sorted_corners)}")

        if sorted_corners[0][0].position is None:
            target_first = True
        else:
            target_first = False

        # assign color names
        for x in range(0, len(sorted_corners), 2):
            corner1 = sorted_corners[x]
            corner2 = sorted_corners[x + 1]

            if target_first:
                corner2[0].color_name = corner1[0].color_name
                corner2[1].color_name = corner1[1].color_name
                corner2[2].color_name = corner1[2].color_name
            else:
                corner1[0].color_name = corner2[0].color_name
                corner1[1].color_name = corner2[1].color_name
                corner1[2].color_name = corner2[2].color_name

        if self.write_debug_file:
            self.write_color_corners("corners", sorted_corners)

    def resolve_edge_squares(self) -> None:
        """
        Use traveling salesman algorithm to sort the colors
        """
        # Nothing to be done for 2x2x2
        if self.width == 2:
            return
        elif self.width == 3:
            # rubiks cube libraries
            from rubikscolorresolver.cube_333 import edge_orbit_id
        elif self.width == 4:
            # rubiks cube libraries
            from rubikscolorresolver.cube_444 import edge_orbit_id
        elif self.width == 5:
            # rubiks cube libraries
            from rubikscolorresolver.cube_555 import edge_orbit_id
        elif self.width == 6:
            # rubiks cube libraries
            from rubikscolorresolver.cube_666 import edge_orbit_id
        elif self.width == 7:
            # rubiks cube libraries
            from rubikscolorresolver.cube_777 import edge_orbit_id

        (white, yellow, orange, red, green, blue) = self.squares_from_color_box()

        for target_orbit_id in range(self.orbits):
            edge_pairs = []

            for side in (self.sideU, self.sideD, self.sideL, self.sideR):
                for square in side.edge_squares:
                    orbit_id = edge_orbit_id[square.position]

                    if orbit_id == target_orbit_id:
                        partner_index = side.get_wing_partner(square.position)
                        partner = self.pos2square[partner_index]
                        edge_pair = (square, partner)

                        if edge_pair not in edge_pairs and (edge_pair[1], edge_pair[0]) not in edge_pairs:
                            edge_pairs.append(edge_pair)

            if len(edge_pairs) == 12:
                target_edge_pairs = [
                    (white, orange),
                    (white, red),
                    (white, green),
                    (white, blue),
                    (green, orange),
                    (green, red),
                    (blue, orange),
                    (blue, red),
                    (yellow, orange),
                    (yellow, red),
                    (yellow, green),
                    (yellow, blue),
                ]
            elif len(edge_pairs) == 24:
                target_edge_pairs = [
                    (white, orange),
                    (white, orange),
                    (white, red),
                    (white, red),
                    (white, green),
                    (white, green),
                    (white, blue),
                    (white, blue),
                    (green, orange),
                    (green, orange),
                    (green, red),
                    (green, red),
                    (blue, orange),
                    (blue, orange),
                    (blue, red),
                    (blue, red),
                    (yellow, orange),
                    (yellow, orange),
                    (yellow, red),
                    (yellow, red),
                    (yellow, green),
                    (yellow, green),
                    (yellow, blue),
                    (yellow, blue),
                ]
            else:
                raise ValueError("found {} edge pairs".format(len(edge_pairs)))

            sorted_edge_pairs = traveling_salesman_edge_pairs(target_edge_pairs + edge_pairs, "edge pairs")
            # logger.info(f"sorted_edge_pairs\n{pformat(sorted_edge_pairs)}")

            if sorted_edge_pairs[0][0].position is None:
                target_first = True
            else:
                target_first = False

            # assign color names
            for x in range(0, len(sorted_edge_pairs), 2):
                pair1 = sorted_edge_pairs[x]
                pair2 = sorted_edge_pairs[x + 1]

                if target_first:
                    pair2[0].color_name = pair1[0].color_name
                    pair2[1].color_name = pair1[1].color_name
                else:
                    pair1[0].color_name = pair2[0].color_name
                    pair1[1].color_name = pair2[1].color_name

            if self.write_debug_file:
                self.write_color_edge_pairs("edges - orbit %d" % target_orbit_id, sorted_edge_pairs)

    def resolve_center_squares(self) -> None:
        """
        Use traveling salesman algorithm to sort the squares by color
        """

        if self.width == 2:
            return
        elif self.width == 3:
            # rubiks cube libraries
            from rubikscolorresolver.cube_333 import center_groups
        elif self.width == 4:
            # rubiks cube libraries
            from rubikscolorresolver.cube_444 import center_groups
        elif self.width == 5:
            # rubiks cube libraries
            from rubikscolorresolver.cube_555 import center_groups
        elif self.width == 6:
            # rubiks cube libraries
            from rubikscolorresolver.cube_666 import center_groups
        elif self.width == 7:
            # rubiks cube libraries
            from rubikscolorresolver.cube_777 import center_groups

        for (desc, centers_squares) in center_groups:
            # logger.debug("\n\n\n\n")
            # logger.info("Resolve {}".format(desc))
            center_squares = []

            for position in centers_squares:
                square = self.pos2square[position]
                center_squares.append(square)

            if desc == "centers":
                sorted_center_squares = center_squares[:]
                permutations = "odd_cube_center_color_permutations"
            else:
                sorted_center_squares = traveling_salesman(center_squares)
                permutations = "even_cube_center_color_permutations"

            self.assign_color_names(desc, sorted_center_squares, permutations, self.color_box)

            if self.write_debug_file:
                self.write_colors(desc, sorted_center_squares)

    def crunch_colors(self) -> None:
        if self.write_debug_file:
            html_init_cube = self.html_cube("Initial RGB values", False, "initial_rgb_values")
            self.write_html(html_init_cube)
            self.write_crayola_colors()

        self.resolve_color_box()

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

        if self.write_debug_file:
            html_final_cube = self.html_cube("Final Cube", True, "final_cube")
            html = "<div id='bottom'>{}{}</div>".format(html_init_cube, html_final_cube)

            self.write_html(html)
            self.www_footer()

    def print_profile_data(self):
        # print_profile_data()
        pass


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
        with open(filename, "r") as fh:
            rgb = "".join(fh.readlines())
    elif rgb:
        pass
    else:
        print("ERROR: Neither --filename or --rgb was specified")
        sys.exit(1)

    argv = None
    scan_data = eval(rgb)

    for key, value in scan_data.items():
        scan_data[key] = tuple(value)

    square_count = len(list(scan_data.keys()))
    square_count_per_side = int(square_count / 6)
    width = int(sqrt(square_count_per_side))

    cube = RubiksColorSolverGeneric(width)
    cube.write_debug_file = True
    cube.enter_scan_data(scan_data)
    cube.crunch_colors()
    cube.print_profile_data()
    cube.print_cube()

    if use_json:
        # standard libraries
        from json import dumps as json_dumps

        result = json_dumps(cube.cube_for_json(), indent=4, sort_keys=True)
    else:
        result = "".join(cube.cube_for_kociemba_strict())

    print(result)
    return result
