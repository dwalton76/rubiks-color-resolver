# standard libraries
import logging
import sys
from math import ceil

try:
    # standard libraries
    from typing import Dict, List, Set, Tuple
except ImportError:
    # this will barf for micropython...ignore it
    pass

# rubiks cube libraries
from rubikscolorresolver.color import html_color, lab_distance, rgb2lab
from rubikscolorresolver.side import Side
from rubikscolorresolver.square import Square

logger = logging.getLogger(__name__)


class ListMissingValue(Exception):
    pass


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
            "U": Side(self.width, "U"),
            "L": Side(self.width, "L"),
            "F": Side(self.width, "F"),
            "R": Side(self.width, "R"),
            "B": Side(self.width, "B"),
            "D": Side(self.width, "D"),
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
            for (pos1, pos2) in self.all_edge_positions:
                if pos1 >= side.min_pos and pos1 <= side.max_pos:
                    side.wing_partner[pos1] = pos2
                elif pos2 >= side.min_pos and pos2 <= side.max_pos:
                    side.wing_partner[pos2] = pos1

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
            partner_index = side.wing_partner[square_index]
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
                partner_position = side.wing_partner[square.position]
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
