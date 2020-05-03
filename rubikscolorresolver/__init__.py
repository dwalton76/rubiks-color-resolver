
import array
import gc
import os
from math import sqrt
from rubikscolorresolver.base import (
    LabColor,
    RubiksColorSolverGenericBase,
    Square,
    lab_distance,
    html_color,
    rgb2lab,
)
from rubikscolorresolver.tsp_solver_greedy import solve_tsp
from rubikscolorresolver.permutations import (
    even_cube_center_color_permutations,
    len_even_cube_center_color_permutations,
    odd_cube_center_color_permutations,
)
#from rubikscolorresolver.profile import timed_function, print_profile_data
import sys

if sys.version_info < (3, 4):
    raise SystemError("Must be using Python 3.4 or higher")


def is_micropython():
    return sys.implementation.name == "micropython"

ALL_COLORS = ("Bu", "Gr", "OR", "Rd", "Wh", "Ye")
SIDES_COUNT = 6

if is_micropython():
    from ucollections import OrderedDict
    HTML_FILENAME = "rubiks-color-resolver.html"
else:
    from collections import OrderedDict
    HTML_FILENAME = "/tmp/rubiks-color-resolver.html"

try:
    os.unlink(HTML_FILENAME)
except Exception:
    pass


# @timed_function
def median(list_foo):
    list_foo = sorted(list_foo)
    list_foo_len = len(list_foo)

    if list_foo_len < 1:
        return None

    # Even number of entries
    if list_foo_len % 2 == 0:
        return (
            list_foo[int((list_foo_len - 1) / 2)]
            + list_foo[int((list_foo_len + 1) / 2)]
        ) / 2.0

    # Odd number of entries
    else:
        return list_foo[int((list_foo_len - 1) / 2)]


def tsp_matrix_corners(corners):
    len_corners = len(corners)

    # build a full matrix of color to color distances
    # init the 2d list with 0s
    matrix = [x[:] for x in [[0] * len_corners] * len_corners]
    color_names = set(("Wh", "Ye", "OR", "Rd", "Bu", "Gr"))

    for x in range(len_corners):
        x_corner = corners[x]

        for y in range(x+1, len_corners):
            y_corner = corners[y]

            if x_corner[0].position in color_names and y_corner[0].position in color_names:
                distance = 999

            elif x_corner[0].position not in color_names and y_corner[0].position not in color_names:
                distance = 999

            else:
                distance_012 = (
                    lab_distance(x_corner[0].lab, y_corner[0].lab) +
                    lab_distance(x_corner[1].lab, y_corner[1].lab) +
                    lab_distance(x_corner[2].lab, y_corner[2].lab)
                )

                distance_201 = (
                    lab_distance(x_corner[0].lab, y_corner[2].lab) +
                    lab_distance(x_corner[1].lab, y_corner[0].lab) +
                    lab_distance(x_corner[2].lab, y_corner[1].lab)
                )

                distance_120 = (
                    lab_distance(x_corner[0].lab, y_corner[1].lab) +
                    lab_distance(x_corner[1].lab, y_corner[2].lab) +
                    lab_distance(x_corner[2].lab, y_corner[0].lab)
                )

                distance = min(distance_012, distance_201, distance_120)

            matrix[x][y] = distance
            matrix[y][x] = distance

    # print("corners matrix")
    # for row in matrix:
    #     print(row)

    return matrix


def corner_distance(corner1, corner2):
    return (
        lab_distance(corner1[0].lab, corner2[0].lab) +
        lab_distance(corner1[1].lab, corner2[1].lab) +
        lab_distance(corner1[2].lab, corner2[2].lab)
    )

def traveling_salesman_corners(corners, desc):
    matrix = tsp_matrix_corners(corners)
    path = solve_tsp(matrix, desc=desc)
    sorted_corners = [corners[x] for x in path]

    for x in range(0, len(sorted_corners), 2):
        corner1 = sorted_corners[x]
        corner2 = sorted_corners[x+1]

        distance_012 = (
            lab_distance(corner1[0].lab, corner2[0].lab) +
            lab_distance(corner1[1].lab, corner2[1].lab) +
            lab_distance(corner1[2].lab, corner2[2].lab)
        )

        distance_201 = (
            lab_distance(corner1[0].lab, corner2[2].lab) +
            lab_distance(corner1[1].lab, corner2[0].lab) +
            lab_distance(corner1[2].lab, corner2[1].lab)
        )

        distance_120 = (
            lab_distance(corner1[0].lab, corner2[1].lab) +
            lab_distance(corner1[1].lab, corner2[2].lab) +
            lab_distance(corner1[2].lab, corner2[0].lab)
        )

        distance = min(distance_012, distance_201, distance_120)

        if distance == distance_012:
            pass

        elif distance == distance_201:
            sorted_corners[x+1] = (corner2[2], corner2[0], corner2[1])

        elif distance == distance_120:
            sorted_corners[x+1] = (corner2[1], corner2[2], corner2[0])

        else:
            raise ValueError(distance)

    while True:
        max_delta = 0
        max_delta_corners_to_swap = None

        for x in range(0, len(sorted_corners), 2):
            corner1 = sorted_corners[x]
            corner2 = sorted_corners[x+1]
            distance12 = corner_distance(corner1, corner2)

            for y in range(x+2, len(sorted_corners), 2):
                corner3 = sorted_corners[y]
                corner4 = sorted_corners[y+1]
                distance34 = corner_distance(corner3, corner4)

                # If we were to swap corner2 with corner4, what would that do to the corner1->corner2 distance plus the corner3->corner4 distance?
                distance14 = corner_distance(corner1, corner4)
                distance32 = corner_distance(corner3, corner2)

                if distance14 + distance32 < distance12 + distance34:
                    delta = (distance12 + distance34) - (distance14 + distance32)

                    if delta > max_delta:
                        max_delta = delta
                        max_delta_corners_to_swap = (x+1, y+1)
                    #    print(f"corner swap ({x}, {y}) would reduce distance {int(delta)} from {int(distance12 + distance34)} to {int(distance14 + distance32)} (NEW MAX)")
                    #else:
                    #    print(f"corner swap ({x}, {y}) would reduce distance {int(delta)} from {int(distance12 + distance34)} to {int(distance14 + distance32)}")

        if max_delta_corners_to_swap:
            (x, y) = max_delta_corners_to_swap
            orig_x = sorted_corners[x]
            sorted_corners[x] = sorted_corners[y]
            sorted_corners[y] = orig_x
            # print("")

        else:
            break

    return sorted_corners


def tsp_matrix_edge_pairs(edge_pairs):
    len_edge_pairs = len(edge_pairs)

    # build a full matrix of color to color distances
    # init the 2d list with 0s
    matrix = [x[:] for x in [[0] * len_edge_pairs] * len_edge_pairs]
    color_names = set(("Wh", "Ye", "OR", "Rd", "Bu", "Gr"))

    for x in range(len_edge_pairs):
        x_edge_pair = edge_pairs[x]

        for y in range(x+1, len_edge_pairs):
            y_edge_pair = edge_pairs[y]

            if x_edge_pair[0].position in color_names and y_edge_pair[0].position in color_names:
                distance = 999

            elif x_edge_pair[0].position not in color_names and y_edge_pair[0].position not in color_names:
                distance = 999

            else:
                distance_01 = (
                    lab_distance(x_edge_pair[0].lab, y_edge_pair[0].lab) +
                    lab_distance(x_edge_pair[1].lab, y_edge_pair[1].lab)
                )
                distance_10 = (
                    lab_distance(x_edge_pair[0].lab, y_edge_pair[1].lab) +
                    lab_distance(x_edge_pair[1].lab, y_edge_pair[0].lab)
                )

                distance = min(distance_01, distance_10)

            matrix[x][y] = distance
            matrix[y][x] = distance

    return matrix


def edge_pair_distance(pair1, pair2, normal):
    if normal:
        return (
            lab_distance(pair1[0].lab, pair2[0].lab) +
            lab_distance(pair1[1].lab, pair2[1].lab)
        )
    else:
        return (
            lab_distance(pair1[0].lab, pair2[1].lab) +
            lab_distance(pair1[1].lab, pair2[0].lab)
        )

def traveling_salesman_edge_pairs(edge_pairs, desc):
    matrix = tsp_matrix_edge_pairs(edge_pairs)
    path = solve_tsp(matrix, desc=desc)
    sorted_edge_pairs = [edge_pairs[x] for x in path]

    for x in range(0, len(sorted_edge_pairs), 2):
        pair1 = sorted_edge_pairs[x]
        pair2 = sorted_edge_pairs[x+1]
        distance_01 = edge_pair_distance(pair1, pair2, normal=True)
        distance_10 = edge_pair_distance(pair1, pair2, normal=False)

        if distance_10 < distance_01:
            sorted_edge_pairs[x+1] = (sorted_edge_pairs[x+1][1], sorted_edge_pairs[x+1][0])

        distance = min(distance_01, distance_10)

    while True:
        max_delta = 0
        max_delta_edges_to_swap = None

        for x in range(0, len(sorted_edge_pairs), 2):
            pair1 = sorted_edge_pairs[x]
            pair2 = sorted_edge_pairs[x+1]
            distance12 = edge_pair_distance(pair1, pair2, True)

            for y in range(x+2, len(sorted_edge_pairs), 2):
                pair3 = sorted_edge_pairs[y]
                pair4 = sorted_edge_pairs[y+1]
                distance34 = edge_pair_distance(pair3, pair4, True)

                # If we were to swap pair2 with pair4, what would that do to the pair1->pair2 distance plus the pair3->pair4 distance?
                distance14 = edge_pair_distance(pair1, pair4, True)
                distance32 = edge_pair_distance(pair3, pair2, True)

                if distance14 + distance32 < distance12 + distance34:
                    delta = (distance12 + distance34) - (distance14 + distance32)

                    if delta > max_delta:
                        max_delta = delta
                        max_delta_edges_to_swap = (x+1, y+1)
                    #    print(f"edge swap ({x}, {y}) would reduce distance {int(delta)} from {int(distance12 + distance34)} to {int(distance14 + distance32)} (NEW MAX)")
                    #else:
                    #    print(f"edge swap ({x}, {y}) would reduce distance {int(delta)} from {int(distance12 + distance34)} to {int(distance14 + distance32)}")
                #else:
                #    delta = (distance14 + distance32) - (distance12 + distance34)
                #    print(f"edge swap ({x}, {y}) would increase distance {int(delta)} from {int(distance12 + distance34)} to {int(distance14 + distance32)}")

        if max_delta_edges_to_swap:
            (x, y) = max_delta_edges_to_swap
            orig_x = sorted_edge_pairs[x]
            sorted_edge_pairs[x] = sorted_edge_pairs[y]
            sorted_edge_pairs[y] = orig_x
            #print("")

        else:
            break

    return sorted_edge_pairs


"""
def path_streak_cost(squares):

    if len(squares) <= 1:
        return 0

    cost = 0
    prev_square = squares[0]

    for square in squares[1:]:
        cost += lab_distance(prev_square.lab, square.lab)
        prev_square = square

    return cost


def best_path_streak(sorted_squares, streak_length, middle_squares, edge_pairs, corners):
    max_cost_start = len(sorted_squares) - streak_length
    min_cost = 999
    min_cost_start = None
    # print(middle_squares)
    len_edge_pairs = len(edge_pairs)

    if len_edge_pairs == 0:
        pass
    elif len_edge_pairs == 12:
        target_edges_in_streak = 4
    else:
        raise ValueError(len_edge_pairs)

    for x in range(0, max_cost_start):
        squares_for_streak = sorted_squares[x:x + streak_length]
        cost = path_streak_cost(squares_for_streak)
        valid = True

        if middle_squares:
            middle_squares_in_streak = [square for square in squares_for_streak if square in middle_squares]
            valid = bool(len(middle_squares_in_streak) == 1)
            # print(middle_squares_in_streak)

        '''
        if valid and edge_pairs:
            for edge_pair in edge_pairs:
                edges_in_pair_in_streak = [square for square in squares_for_streak if square in edge_pair]
                valid = bool(len(edges_in_pair_in_streak) == target_edges_in_streak)
        '''

        if valid and corners:
            # print(f"corners {corners}")
            corners_in_streak = []

            for corner in corners:
                corner_in_streak = [square for square in squares_for_streak if square in corner]
                corners_in_streak.extend(corner_in_streak)
                # print(f"corner_in_streak {len(corner_in_streak)}")
                valid = bool(len(corner_in_streak) <= 1)

                if not valid:
                    break

            if valid:
                valid = bool(len(corners_in_streak) == 4)
            # print(f"corners_in_streak {len(corners_in_streak)}")

        if valid and cost < min_cost:
            min_cost = cost
            min_cost_start = x

    return sorted_squares[min_cost_start : min_cost_start + streak_length]
"""


def tsp_matrix(squares):
    len_squares = len(squares)
    r_len_squares = range(len_squares)

    # build a full matrix of color to color distances
    # init the 2d list with 0s
    matrix = [x[:] for x in [[0] * len_squares] * len_squares]

    for x in r_len_squares:
        x_lab = squares[x].lab

        for y in range(x+1, len_squares):
            y_lab = squares[y].lab

            distance = lab_distance(x_lab, y_lab)
            matrix[x][y] = distance
            matrix[y][x] = distance

    # convert to tuple of tuples
    for (row_index, row) in enumerate(matrix):
        matrix[row_index] = tuple(row)

    matrix = tuple(matrix)

    return matrix


# @timed_function
def traveling_salesman(squares, desc, middle_squares=[], edge_pairs=[], corners=[]):
    '''
    SQUARES_PER_ROW = int(len(squares) / SIDES_COUNT)
    results = []
    _squares = squares[:]

    for x in range(SIDES_COUNT - 1):
        if x == 4:
            matrix = tsp_matrix(_squares)
            path = solve_tsp(matrix, desc=desc)
            path_squares = [_squares[x] for x in path]
            results.extend(path_squares)
        else:
            matrix = tsp_matrix(_squares)
            path = solve_tsp(matrix, desc=desc)
            path_squares = [_squares[x] for x in path]
            results.extend(best_path_streak(path_squares, SQUARES_PER_ROW, middle_squares, edge_pairs, corners))
            _squares = [square for square in squares if square not in results]

    return results
    '''
    matrix = tsp_matrix(squares)
    path = solve_tsp(matrix, desc=desc)
    return [squares[x] for x in path]


def traveling_salesman_two_colors(squares, endpoints=None, desc=None):
    matrix = tsp_matrix(squares)

    if endpoints:
        start_index = squares.index(endpoints[0])
        end_index = squares.index(endpoints[1])
        endpoints = (start_index, end_index)
    path = solve_tsp(matrix, endpoints=endpoints, desc=desc)
    return [squares[x] for x in path]


# @timed_function
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


# @timed_function
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


# @timed_function
def hashtag_rgb_to_labcolor(rgb_string):
    (red, green, blue) = hex_to_rgb(rgb_string)
    #lab = rgb2lab((red, green, blue))
    #print("LabColor({}, {}, {}, {}, {}, {}),".format(lab.L, lab.a, lab.b, lab.red, lab.green, lab.blue))
    #return lab
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
    #"Wh": hashtag_rgb_to_labcolor("#FFFFFF"),
    #"Gr": hashtag_rgb_to_labcolor("#14694a"),
    #"Ye": hashtag_rgb_to_labcolor("#FFFF00"),
    #"OR": hashtag_rgb_to_labcolor("#943509"),
    #"Bu": hashtag_rgb_to_labcolor("#163967"),
    #"Rd": hashtag_rgb_to_labcolor("#680402"),
    "Wh" : LabColor(100.0, 0.00526049995830391, -0.01040818452526793, 255, 255, 255),
    "Gr" : LabColor(39.14982168015123, -32.45052099773829, 10.60519920674466, 20, 105, 74),
    "Ye" : LabColor(97.13824698129729, -21.55590833483229, 94.48248544644462, 255, 255, 0),
    "OR" : LabColor(35.71689493804023, 38.18518746791636, 43.98251678431012, 148, 53, 9),
    "Bu" : LabColor(23.92144819784853, 5.28400492805528, -30.63998357385018, 22, 57, 103),
    "Rd" : LabColor(20.18063311070288, 40.48184409611946, 29.94038922869042, 104, 4, 2),
}


# @timed_function
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


# @timed_function
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


# @timed_function
def square_list_to_lab(squares):
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


class RubiksColorSolverGeneric(RubiksColorSolverGenericBase):

    # @timed_function
    def www_header(self):
        """
        Write the <head> including css
        """
        side_margin = 10
        square_size = 40
        size = self.width  # 3 for 3x3x3, etc

        with open(HTML_FILENAME, "a") as fh:
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
        with open(HTML_FILENAME, "a") as fh:
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

                    (red, green, blue) = (square.lab.red, square.lab.green, square.lab.blue)

                    if index and index % 2 == 0:
                        fh.write("<span class='half_square'></span>")

                    fh.write(
                        "<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s, side %s'>%s</span>\n"
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
        with open(HTML_FILENAME, "a") as fh:
            fh.write("<div class='clear colors'>\n")
            fh.write("<h2>%s</h2>\n" % desc)

            for use_square1 in (True, False):
                for (index, (square1, square2)) in enumerate(square_pairs):

                    if use_square1:
                        square = square1
                    else:
                        square = square2

                    (red, green, blue) = (square.lab.red, square.lab.green, square.lab.blue)

                    if index and index % 2 == 0:
                        fh.write("<span class='half_square'></span>")

                    fh.write(
                        "<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s, side %s'>%s</span>\n"
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

    # @timed_function
    def write_colors(self, desc, squares):
        with open(HTML_FILENAME, "a") as fh:
            squares_per_row = int(len(squares) / 6)
            fh.write("<div class='clear colors'>\n")
            fh.write("<h2>%s</h2>\n" % desc)

            count = 0
            for square in squares:
                (red, green, blue) = (square.lab.red, square.lab.green, square.lab.blue)
                fh.write(
                    "<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s, side %s'>%d</span>\n"
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

    # @timed_function
    def www_footer(self):
        with open(HTML_FILENAME, "a") as fh:
            fh.write("""
</body>
</html>
""")

    # @timed_function
    def enter_scan_data(self, scan_data):

        for (position, (red, green, blue)) in scan_data.items():
            position = int(position)
            side = self.pos2side[position]
            side.set_square(position, red, green, blue)

        if self.write_debug_file:
            self.www_header()

            with open(HTML_FILENAME, "a") as fh:
                fh.write("<h1>RGB Input</h1>\n")
                fh.write("<pre>{}</pre>\n".format(scan_data))

        self.calculate_pos2square()

    # @timed_function
    def html_cube(self, desc, use_html_colors, div_class):
        cube = ["dummy"]

        for side in (self.sideU, self.sideL, self.sideF, self.sideR, self.sideB, self.sideD):
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
                % (col,
                   red, green, blue,
                   int(lab.L), int(lab.a), int(lab.b),
                   color_name,
                   red, green, blue,
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
        with open(HTML_FILENAME, "a") as fh:
            fh.write(html)

    def _write_colors(self, desc, box):
        with open(HTML_FILENAME, "a") as fh:
            fh.write("<div class='clear colors'>\n")
            fh.write("<h2>{}</h2>\n".format(desc))

            for color_name in ("Wh", "Ye", "Gr", "Bu", "OR", "Rd"):
                lab = box[color_name]

                fh.write(
                    "<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%s</span>\n"
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

    # @timed_function
    def write_crayola_colors(self):
        self._write_colors("crayola box", crayola_colors)

    # @timed_function
    def write_color_box(self):
        self._write_colors("color_box", self.color_box)

    # @timed_function
    def set_state(self):
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
            for side in (self.sideU, self.sideL, self.sideF, self.sideR, self.sideB, self.sideD):
                square = side.squares[side.mid_pos]
                center_squares.append(square)
            # desc = "middle center"
            # log.info("center_squares: %s".format(center_squares))

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
                    log.info("{} PERMUTATION {}, DISTANCE {:,} (NEW MIN)".format(desc, permutation, int(distance)))
                else:
                    log.info("{} PERMUTATION {}, DISTANCE {}".format(desc, permutation, distance))
                    """

            self.color_to_side_name = {
                min_distance_permutation[0]: "U",
                min_distance_permutation[1]: "L",
                min_distance_permutation[2]: "F",
                min_distance_permutation[3]: "R",
                min_distance_permutation[4]: "B",
                min_distance_permutation[5]: "D",
            }
            # log.info("{} FINAL PERMUTATION {}".format(desc, min_distance_permutation))

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

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]
                square.side_name = self.color_to_side_name[square.color_name]

    # @timed_function
    def cube_for_json(self):
        """
        Return a dictionary of the cube data so that we can json dump it
        """
        data = {}
        data["kociemba"] = "".join(self.cube_for_kociemba_strict())
        data["sides"] = {}
        data["squares"] = {}

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
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

                data["squares"][square.position] = {"finalSide": side_name }

        return data

    # @timed_function
    def assign_color_names(self, desc, squares_lists_all, color_permutations, color_box):
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

            for (index, squares_list) in enumerate(squares_lists):
                distance = 0
                for square in squares_list:
                    distance += lab_distance(square.lab, color_lab)
                distances_of_square_list_per_color[color_name].append(int(distance))
            distances_of_square_list_per_color[color_name] = distances_of_square_list_per_color[color_name]

        min_distance = 99999
        min_distance_permutation = None

        if color_permutations == "even_cube_center_color_permutations":

            # before sorting
            '''
            print("\n".join(map(str, squares_lists)))
            for color_name in ref_ALL_COLORS:
                print("pre  distances_of_square_list_per_color {} : {}".format(color_name, distances_of_square_list_per_color[color_name]))
            print("")
            '''

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
            '''
            print("\n".join(map(str, squares_lists)))
            for color_name in ref_ALL_COLORS:
                print("post distances_of_square_list_per_color {} : {}".format(color_name, distances_of_square_list_per_color[color_name]))
            print("")
            '''

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

                        #if skip_by:
                        #    print("{} PERMUTATION {} - {}, x {} distance {:,} > min {}, skip_by {}".format(
                        #        desc, permutation_index, permutation, x, distance, min_distance, skip_by))
                        break

                if skip_by:
                    permutation_index += skip_by
                    # skip_total += skip_by
                    continue

                if distance < min_distance:
                    #print("{} PERMUTATION {} - {}, DISTANCE {:,} vs min {} (NEW MIN)".format(desc, permutation_index, permutation, distance, min_distance))
                    #log.info("{} PERMUTATION {}, DISTANCE {:,} (NEW MIN)".format(desc, permutation, int(distance)))
                    min_distance = distance
                    min_distance_permutation = permutation
                #else:
                #    print("{} PERMUTATION {} - {}, DISTANCE {} vs min {}".format(desc, permutation_index, permutation, distance, min_distance))
                #    #log.info("{} PERMUTATION {}, DISTANCE {}".format(desc, permutation, distance))

                # total += 1
                permutation_index += 1

            #print("total {}".format(total))
            #print("skip total {}".format(skip_total))
            #print("")

        elif color_permutations == "odd_cube_center_color_permutations":
            p = odd_cube_center_color_permutations

            for permutation in p:
                distance = (
                    distances_of_square_list_per_color[permutation[0]][0] +
                    distances_of_square_list_per_color[permutation[1]][1] +
                    distances_of_square_list_per_color[permutation[2]][2] +
                    distances_of_square_list_per_color[permutation[3]][3] +
                    distances_of_square_list_per_color[permutation[4]][4] +
                    distances_of_square_list_per_color[permutation[5]][5]
                )

                if distance < min_distance:
                    min_distance = distance
                    min_distance_permutation = permutation
                #    print("{} PERMUTATION {} -  {}, DISTANCE {:,} (NEW MIN)".format(desc, permutation_index, permutation, int(distance)))
                #    log.info("{} PERMUTATION {}, DISTANCE {:,} (NEW MIN)".format(desc, permutation, int(distance)))
                # else:
                #    print("{} PERMUTATION {}, DISTANCE {}".format(desc, permutation, distance))
                #    log.info("{} PERMUTATION {}, DISTANCE {}".format(desc, permutation, distance))

        # Assign the color name to the Square object
        for (index, squares_list) in enumerate(squares_lists):
            color_name = min_distance_permutation[index]

            for square in squares_list:
                square.color_name = color_name

    def get_squares_by_color_name(self):
        white_squares = []
        yellow_squares = []
        orange_squares = []
        red_squares = []
        green_squares = []
        blue_squares = []

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
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

    # @timed_function
    def resolve_color_box(self):
        """
        Temporarily assign names to all squares, use crayola colors as reference point.

        We use these name assignments to build our "color_box" which will be our
        references Wh, Ye, OR, Rd, Gr, Bu colors for assigning color names to edge
        and center squares.
        """

        # Only works on odd cubes and can cause problems if the scan of the center square happens
        # to be much brighter/darker than all squares of the same color
        use_center_squares = False
        use_corner_squares = False
        use_all_squares = False

        # LEGO SPIKE (micropython) has very little memory so only do TSP on the corners
        if is_micropython():
            use_corner_squares = True
        else:
            use_all_squares = True

        if use_center_squares:
            center_squares = []

            for side in (self.sideU, self.sideL, self.sideF, self.sideR, self.sideB, self.sideD):
                for square in side.center_squares:
                    center_squares.append(square)

            self.assign_color_names(
                "center squares for color_box",
                center_squares,
                "odd_cube_center_color_permutations",
                crayola_colors,
            )

            if self.write_debug_file:
                self.write_colors("centers for color_box", center_squares)

        elif use_corner_squares:
            corner_squares = []

            for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
                for square in side.corner_squares:
                    corner_squares.append(square)

            sorted_corner_squares = traveling_salesman(corner_squares, "corner")

            self.assign_color_names(
                "corner squares for color_box",
                sorted_corner_squares,
                "even_cube_center_color_permutations",
                crayola_colors,
            )

            if self.write_debug_file:
                self.write_colors("corners for color_box", sorted_corner_squares)

        elif use_all_squares:
            all_squares = []
            middle_squares = []

            for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
                for square in side.center_squares + side.corner_squares + side.edge_squares:
                    all_squares.append(square)

                if side.mid_pos:
                    middle_squares.append(side.squares[side.mid_pos])

            edge_pairs = []

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

            corners = []

            for corner_tuple in corner_tuples:
                corners.append((
                    self.pos2square[corner_tuple[0]],
                    self.pos2square[corner_tuple[1]],
                    self.pos2square[corner_tuple[2]],
                ))

            # ======
            # pass 1
            # ======
            sorted_all_squares = traveling_salesman(all_squares, "all", middle_squares, edge_pairs, corners)

            self.assign_color_names(
                "squares for color_box (pass 1)",
                sorted_all_squares,
                "even_cube_center_color_permutations",
                crayola_colors,
            )

            if self.write_debug_file:
                self.write_colors("squares for color_box (pass 1)", sorted_all_squares)

            # ======
            # pass 2
            # ======
            (white_squares, yellow_squares, orange_squares, red_squares, green_squares, blue_squares) = self.get_squares_by_color_name()
            green_blue_endpoints = None
            white_yellow_endpoints = None
            red_orange_endpoints = None

            # odd cube
            if self.width % 2 == 1:
                white_center = None
                yellow_center = None
                orange_center = None
                red_center = None
                green_center = None
                blue_center = None

                for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
                    square = self.pos2square[side.mid_pos]

                    if square.color_name == "Wh":
                        white_center = square
                    elif square.color_name == "Ye":
                        yellow_center = square
                    elif square.color_name == "OR":
                        orange_center = square
                    elif square.color_name == "Rd":
                        red_center = square
                    elif square.color_name == "Gr":
                        green_center = square
                    elif square.color_name == "Bu":
                        blue_center = square

                if white_center and yellow_center:
                    white_yellow_endpoints = (white_center, yellow_center)

                if green_center and blue_center:
                    green_blue_endpoints = (green_center, blue_center)

                if red_center and orange_center:
                    red_orange_endpoints = (red_center, orange_center)

            # Nuke all color names (they were temporary)
            for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
                for square in side.center_squares + side.corner_squares + side.edge_squares:
                    square.color_name = None

            sorted_green_blue = traveling_salesman_two_colors(green_squares + blue_squares, endpoints=green_blue_endpoints, desc="green blue")
            sorted_white_yellow = traveling_salesman_two_colors(white_squares + yellow_squares, endpoints=white_yellow_endpoints, desc="white yellow")
            sorted_red_orange = traveling_salesman_two_colors(red_squares + orange_squares, endpoints=red_orange_endpoints, desc="white yellow")
            sorted_all_squares = sorted_green_blue + sorted_white_yellow + sorted_red_orange

            self.assign_color_names(
                "squares for color_box (pass 2)",
                sorted_all_squares,
                "even_cube_center_color_permutations",
                crayola_colors,
            )

            if self.write_debug_file:
                self.write_colors("squares for color_box (pass 2)", sorted_all_squares)

        else:
            raise Exception()

        (white_squares, yellow_squares, orange_squares, red_squares, green_squares, blue_squares) = self.get_squares_by_color_name()
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
        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for square in side.center_squares + side.corner_squares + side.edge_squares:
                square.color_name = None

        if self.write_debug_file:
            self.write_color_box()

    # @timed_function
    def resolve_corner_squares(self):
        """
        Assign names to the corner squares
        """
        white = Square(None, "Wh", self.color_box["Wh"].red, self.color_box["Wh"].green, self.color_box["Wh"].blue)
        yellow = Square(None, "Ye", self.color_box["Ye"].red, self.color_box["Ye"].green, self.color_box["Ye"].blue)
        orange = Square(None, "OR", self.color_box["OR"].red, self.color_box["OR"].green, self.color_box["OR"].blue)
        red = Square(None, "Rd", self.color_box["Rd"].red, self.color_box["Rd"].green, self.color_box["Rd"].blue)
        green = Square(None, "Gr", self.color_box["Gr"].red, self.color_box["Gr"].green, self.color_box["Gr"].blue)
        blue = Square(None, "Bu", self.color_box["Bu"].red, self.color_box["Bu"].green, self.color_box["Bu"].blue)

        white.color_name = "Wh"
        yellow.color_name = "Ye"
        orange.color_name = "OR"
        red.color_name = "Rd"
        green.color_name = "Gr"
        blue.color_name = "Bu"

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

        corners = []

        for corner_tuple in corner_tuples:
            corners.append([
                self.pos2square[corner_tuple[0]],
                self.pos2square[corner_tuple[1]],
                self.pos2square[corner_tuple[2]],
            ])

        sorted_corners = traveling_salesman_corners(target_corners + corners, "corners")

        # assign color names
        for x in range(0, len(sorted_corners), 2):
            corner1 = sorted_corners[x]
            corner2 = sorted_corners[x+1]
            corner2[0].color_name = corner1[0].position
            corner2[1].color_name = corner1[1].position
            corner2[2].color_name = corner1[2].position

        if self.write_debug_file:
            self.write_color_corners("corners" , sorted_corners)

    # @timed_function
    def resolve_edge_squares(self):
        """
        Use traveling salesman algorithm to sort the colors
        """

        # Nothing to be done for 2x2x2
        if self.width == 2:
            return
        elif self.width == 3:
            from rubikscolorresolver.cube_333 import edge_orbit_id
        elif self.width == 4:
            from rubikscolorresolver.cube_444 import edge_orbit_id
        elif self.width == 5:
            from rubikscolorresolver.cube_555 import edge_orbit_id
        elif self.width == 6:
            from rubikscolorresolver.cube_666 import edge_orbit_id
        elif self.width == 7:
            from rubikscolorresolver.cube_777 import edge_orbit_id

        white = Square(None, "Wh", self.color_box["Wh"].red, self.color_box["Wh"].green, self.color_box["Wh"].blue)
        yellow = Square(None, "Ye", self.color_box["Ye"].red, self.color_box["Ye"].green, self.color_box["Ye"].blue)
        orange = Square(None, "OR", self.color_box["OR"].red, self.color_box["OR"].green, self.color_box["OR"].blue)
        red = Square(None, "Rd", self.color_box["Rd"].red, self.color_box["Rd"].green, self.color_box["Rd"].blue)
        green = Square(None, "Gr", self.color_box["Gr"].red, self.color_box["Gr"].green, self.color_box["Gr"].blue)
        blue = Square(None, "Bu", self.color_box["Bu"].red, self.color_box["Bu"].green, self.color_box["Bu"].blue)

        white.color_name = "Wh"
        yellow.color_name = "Ye"
        orange.color_name = "OR"
        red.color_name = "Rd"
        green.color_name = "Gr"
        blue.color_name = "Bu"

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

            # assign color names
            for x in range(0, len(sorted_edge_pairs), 2):
                pair1 = sorted_edge_pairs[x]
                pair2 = sorted_edge_pairs[x+1]
                pair2[0].color_name = pair1[0].position
                pair2[1].color_name = pair1[1].position

            if self.write_debug_file:
                self.write_color_edge_pairs("edges - orbit %d" % target_orbit_id, sorted_edge_pairs)

    # @timed_function
    def resolve_center_squares(self):
        """
        Use traveling salesman algorithm to sort the squares by color
        """

        if self.width == 2:
            return
        elif self.width == 3:
            from rubikscolorresolver.cube_333 import center_groups
        elif self.width == 4:
            from rubikscolorresolver.cube_444 import center_groups
        elif self.width == 5:
            from rubikscolorresolver.cube_555 import center_groups
        elif self.width == 6:
            from rubikscolorresolver.cube_666 import center_groups
        elif self.width == 7:
            from rubikscolorresolver.cube_777 import center_groups

        for (desc, centers_squares) in center_groups:
            #log.debug("\n\n\n\n")
            #log.info("Resolve {}".format(desc))
            center_squares = []

            for position in centers_squares:
                square = self.pos2square[position]
                center_squares.append(square)

            if desc == "centers":
                sorted_center_squares = center_squares[:]
                permutations = "odd_cube_center_color_permutations"
            else:
                sorted_center_squares = traveling_salesman(center_squares, desc)
                permutations = "even_cube_center_color_permutations"

            self.assign_color_names(desc, sorted_center_squares, permutations, self.color_box)

            if self.write_debug_file:
                self.write_colors(desc, sorted_center_squares)

    # @timed_function
    def crunch_colors(self):
        if self.write_debug_file:
            html_init_cube = self.html_cube("Initial RGB values", False, "initial_rgb_values")
            self.write_html(html_init_cube)
            self.write_crayola_colors()

        gc.collect()
        self.resolve_color_box()

        # corners
        gc.collect()
        self.resolve_corner_squares()

        # centers
        gc.collect()
        self.resolve_center_squares()

        # edges
        gc.collect()
        self.resolve_edge_squares()
        gc.collect()
        self.set_state()
        gc.collect()
        self.sanity_check_edge_squares()
        gc.collect()
        self.validate_all_corners_found()
        gc.collect()
        self.validate_odd_cube_midge_vs_corner_parity()
        gc.collect()

        if self.write_debug_file:
            html_final_cube = self.html_cube("Final Cube", True, "final_cube")
            html = "<div id='bottom'>{}{}</div>".format(html_init_cube, html_final_cube)

            self.write_html(html)
            self.www_footer()

    def print_profile_data(self):
        #print_profile_data()
        pass


# @timed_function
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
        from json import dumps as json_dumps
        result = json_dumps(cube.cube_for_json(), indent=4, sort_keys=True)
    else:
        result = "".join(cube.cube_for_kociemba_strict())

    print(result)
    return result
