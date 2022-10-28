# standard libraries
import array
import logging
import sys
from math import sqrt

try:
    # standard libraries
    from typing import Dict, List, Tuple, Union
except ImportError:
    # this will barf for micropython...ignore it
    pass

# rubiks cube libraries
from rubikscolorresolver.color import LabColor, html_color, lab_distance, rgb2lab
from rubikscolorresolver.cube import RubiksCube
from rubikscolorresolver.permutations import (
    even_cube_center_color_permutations,
    len_even_cube_center_color_permutations,
    odd_cube_center_color_permutations,
)
from rubikscolorresolver.square import Square
from rubikscolorresolver.tsp_solver_greedy import solve_tsp
from rubikscolorresolver.www import HTML_FILENAME, WwwMixin, crayola_colors, open_mode

logger = logging.getLogger(__name__)

ALL_COLORS = ("Bu", "Gr", "OR", "Rd", "Wh", "Ye")


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


class RubiksColorSolverGeneric(RubiksCube, WwwMixin):
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

    def set_state(self) -> None:

        # odd cube
        if self.sideU.mid_pos is not None:

            # Assign a color name to each center square. Compute
            # which naming scheme results in the least total color distance in
            # terms of the assigned color name vs. the colors in crayola_colors.
            min_distance = None
            min_distance_permutation = None

            # Build a list of all center squares
            center_squares = []
            for side in self.sides.values():
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

        for side in self.sides.values():
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

        for square in squares_lists_all:
            square_list.append(square)

            if len(square_list) == squares_per_row:
                squares_lists.append(tuple(square_list))
                square_list = []

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

        min_distance = 99999
        min_distance_permutation = None

        if color_permutations == "even_cube_center_color_permutations":

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

            permutation_len = len_even_cube_center_color_permutations
            permutation_index = 0
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

                        break

                if skip_by:
                    permutation_index += skip_by
                    continue

                if distance < min_distance:
                    min_distance = distance
                    min_distance_permutation = permutation

                permutation_index += 1

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
                    logger.debug(f"permutation {permutation} distance {distance} (NEW MIN)")
                    min_distance = distance
                    min_distance_permutation = permutation
                else:
                    logger.debug(f"permutation {permutation} distance {distance}")

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

        for side in self.sides.values():
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

        # For odd cubes use the dead center squares to define the color box
        # For even cubes use the corner squares to define the color box
        squares_for_color_box = []

        if self.is_odd():
            for side in self.sides.values():
                squares_for_color_box.append(side.squares[side.mid_pos])

            desc = "dead center squares for color_box"
            color_permutations = "odd_cube_center_color_permutations"

        else:
            for side in self.sides.values():
                for square in side.corner_squares:
                    squares_for_color_box.append(square)

            desc = "corner squares for color_box"
            color_permutations = "even_cube_center_color_permutations"
            squares_for_color_box = traveling_salesman(squares_for_color_box)

        self.assign_color_names(
            desc,
            squares_for_color_box,
            color_permutations,
            crayola_colors,
        )

        if self.write_debug_file:
            self.write_colors(desc, squares_for_color_box)

        (
            white_squares,
            yellow_squares,
            orange_squares,
            red_squares,
            green_squares,
            blue_squares,
        ) = self.get_squares_by_color_name()

        # The order here is important, use the very first odd_cube_center_color_permutations
        # which is ("Wh", "OR", "Gr", "Rd", "Bu", "Ye")
        self.color_box = {
            "Wh": square_list_to_lab(white_squares),
            "OR": square_list_to_lab(orange_squares),
            "Gr": square_list_to_lab(green_squares),
            "Rd": square_list_to_lab(red_squares),
            "Bu": square_list_to_lab(blue_squares),
            "Ye": square_list_to_lab(yellow_squares),
        }

        # Nuke all color names (they were temporary)
        for side in self.sides.values():
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
                        partner_index = side.wing_partner[square.position]
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
                self.assign_color_names(desc, sorted_center_squares, permutations, self.color_box)
            else:
                sorted_center_squares = traveling_salesman(center_squares)
                permutations = "even_cube_center_color_permutations"
                self.assign_color_names(desc, sorted_center_squares, permutations, self.color_box)

                # resort sorted_center_squares so that we display them consistently
                sorted_center_squares = sorted(sorted_center_squares, key=lambda x: x.color_name)

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
