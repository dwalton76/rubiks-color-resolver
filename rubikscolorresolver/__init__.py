
import array
import gc
from math import atan2, ceil, cos, degrees, exp, radians, sin, sqrt
from rubikscolorresolver.tsp_solver_greedy import solve_tsp  # takes about 7k
import sys
import utime

if sys.version_info < (3, 4):
    raise SystemError("Must be using Python 3.4 or higher")


def is_micropython():
    return sys.implementation.name == "micropython"


profile_stats_time = {}
profile_stats_calls = {}


def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]

    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)

        if myname not in profile_stats_time:
            profile_stats_time[myname] = 0
            profile_stats_calls[myname] = 0

        profile_stats_time[myname] += utime.ticks_diff(utime.ticks_us(), t)
        profile_stats_calls[myname] += 1

        return result

    return new_func


if is_micropython():
    from ucollections import OrderedDict
    from ujson import dumps as json_dumps
    from ujson import loads as json_loads

    use_cie2000_cache = False

    @timed_function
    def get_lab_distance(lab1, lab2):
        """
        http://www.w3resource.com/python-exercises/math/python-math-exercise-79.php

        In mathematics, the Euclidean distance or Euclidean metric is the "ordinary"
        (i.e. straight-line) distance between two points in Euclidean space. With this
        distance, Euclidean space becomes a metric space. The associated norm is called
        the Euclidean norm.
        """
        return sqrt(((lab1.L - lab2.L) ** 2) + ((lab1.a - lab2.a) ** 2) + ((lab1.b - lab2.b) ** 2))

else:
    from collections import OrderedDict
    from json import dumps as json_dumps
    from json import loads as json_loads

    use_cie2000_cache = True

    @timed_function
    def get_lab_distance(lab1, lab2):
        """
        delta CIE 2000

        Ported from this php implementation
        https://github.com/renasboy/php-color-difference/blob/master/lib/color_difference.class.php
        """
        l1 = lab1.L
        a1 = lab1.a
        b1 = lab1.b

        l2 = lab2.L
        a2 = lab2.a
        b2 = lab2.b

        if use_cie2000_cache:
            delta_e = cie2000_cache.get((l1, a1, b1, l2, a2, b2))

            if delta_e is not None:
                return delta_e

            delta_e = cie2000_cache.get((l2, a2, b2, l1, a1, b1))

            if delta_e is not None:
                return delta_e

        avg_lp = (l1 + l2) / 2.0
        c1 = sqrt(a1 ** 2 + b1 ** 2)
        c2 = sqrt(a2 ** 2 + b2 ** 2)
        avg_c = (c1 + c2) / 2.0
        g = (1 - sqrt(avg_c ** 7 / (avg_c ** 7 + 25 ** 7))) / 2.0
        a1p = a1 * (1 + g)
        a2p = a2 * (1 + g)
        c1p = sqrt(a1p ** 2 + b1 ** 2)
        c2p = sqrt(a2p ** 2 + b2 ** 2)
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

        t = (
            1
            - 0.17 * cos(radians(avg_hp - 30))
            + 0.24 * cos(radians(2 * avg_hp))
            + 0.32 * cos(radians(3 * avg_hp + 6))
            - 0.2 * cos(radians(4 * avg_hp - 63))
        )
        delta_hp = h2p - h1p

        if abs(delta_hp) > 180:
            if h2p <= h1p:
                delta_hp += 360
            else:
                delta_hp -= 360

        delta_lp = l2 - l1
        delta_cp = c2p - c1p
        delta_hp = 2 * sqrt(c1p * c2p) * sin(radians(delta_hp) / 2.0)
        s_l = 1 + ((0.015 * ((avg_lp - 50) ** 2)) / sqrt(20 + ((avg_lp - 50) ** 2)))
        s_c = 1 + 0.045 * avg_cp
        s_h = 1 + 0.015 * avg_cp * t

        delta_ro = 30 * exp(-((((avg_hp - 275) / 25.0) ** 2)))

        r_c = 2 * sqrt((avg_cp ** 7) / ((avg_cp ** 7) + (25 ** 7)))
        r_t = -r_c * sin(2 * radians(delta_ro))
        kl = 1.0
        kc = 1.0
        kh = 1.0
        delta_e = sqrt(
            ((delta_lp / (s_l * kl)) ** 2)
            + ((delta_cp / (s_c * kc)) ** 2)
            + ((delta_hp / (s_h * kh)) ** 2)
            + r_t * (delta_cp / (s_c * kc)) * (delta_hp / (s_h * kh))
        )

        if use_cie2000_cache:
            cie2000_cache[(l1, a1, b1, l2, a2, b2)] = delta_e
            cie2000_cache[(l2, a2, b2, l1, a1, b1)] = delta_e

        # I used this once to build some test cases for TestDeltaCIE2000
        '''
        with open("/tmp/foobar.txt", "a") as fh:
            fh.write("""
            def test_%d_%d_%d_vs_%d_%d_%d(self):
                lab1 = rgb2lab((%d, %d, %d))
                lab2 = rgb2lab((%d, %d, %d))
                delta_e = delta_e_cie2000(lab1, lab2)
                self.assertEqual(delta_e, %s)
    """ % ( lab1.red, lab1.green, lab1.blue,
            lab2.red, lab2.green, lab2.blue,
            lab1.red, lab1.green, lab1.blue,
            lab2.red, lab2.green, lab2.blue,
            delta_e))
        '''

        return delta_e


cie2000_cache = {}

html_color = {
    "Gr": {"red": 0, "green": 102, "blue": 0},
    "Bu": {"red": 0, "green": 0, "blue": 153},
    "OR": {"red": 255, "green": 102, "blue": 0},
    "Rd": {"red": 204, "green": 0, "blue": 0},
    "Wh": {"red": 255, "green": 255, "blue": 255},
    "Ye": {"red": 255, "green": 204, "blue": 0},
}

odd_cube_center_color_permutations = (
    ("Wh", "OR", "Gr", "Rd", "Bu", "Ye"),
    ("Wh", "Gr", "Rd", "Bu", "OR", "Ye"),
    ("Wh", "Bu", "OR", "Gr", "Rd", "Ye"),
    ("Wh", "Rd", "Bu", "OR", "Gr", "Ye"),
    ("Ye", "Bu", "Rd", "Gr", "OR", "Wh"),
    ("Ye", "Gr", "OR", "Bu", "Rd", "Wh"),
    ("Ye", "Rd", "Gr", "OR", "Bu", "Wh"),
    ("Ye", "OR", "Bu", "Rd", "Gr", "Wh"),
    ("OR", "Ye", "Gr", "Wh", "Bu", "Rd"),
    ("OR", "Wh", "Bu", "Ye", "Gr", "Rd"),
    ("OR", "Gr", "Wh", "Bu", "Ye", "Rd"),
    ("OR", "Bu", "Ye", "Gr", "Wh", "Rd"),
    ("Gr", "Ye", "Rd", "Wh", "OR", "Bu"),
    ("Gr", "Wh", "OR", "Ye", "Rd", "Bu"),
    ("Gr", "Rd", "Wh", "OR", "Ye", "Bu"),
    ("Gr", "OR", "Ye", "Rd", "Wh", "Bu"),
    ("Rd", "Ye", "Bu", "Wh", "Gr", "OR"),
    ("Rd", "Wh", "Gr", "Ye", "Bu", "OR"),
    ("Rd", "Bu", "Wh", "Gr", "Ye", "OR"),
    ("Rd", "Gr", "Ye", "Bu", "Wh", "OR"),
    ("Bu", "Wh", "Rd", "Ye", "OR", "Gr"),
    ("Bu", "Ye", "OR", "Wh", "Rd", "Gr"),
    ("Bu", "Rd", "Ye", "OR", "Wh", "Gr"),
    ("Bu", "OR", "Wh", "Rd", "Ye", "Gr"),
)


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


SIDES_COUNT = 6
HTML_DIRECTORY = "/tmp/rubiks-color-resolver/"
#HTML_FILENAME = HTML_DIRECTORY + "index.html"
HTML_FILENAME = "rubiks-color-resolver.html"


def print_mem_stats(desc):
    print('{} free: {} allocated: {}'.format(desc, gc.mem_free(), gc.mem_alloc()))


class ListMissingValue(Exception):
    pass


def permutations(iterable, r=None):
    """
    From https://github.com/python/cpython/blob/master/Modules/itertoolsmodule.c
    """
    pool = tuple(iterable)
    n = len(pool)
    r = n if r is None else r
    indices = list(range(n))
    cycles = list(range(n-r+1, n+1))[::-1]
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(list(range(r))):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i+1:] + indices[i:i+1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                break
        else:
            return


@timed_function
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


@timed_function
def find_index_for_value(list_foo, target, min_index):
    for (index, value) in enumerate(list_foo):
        if value == target and index >= min_index:
            return index
    raise ListMissingValue("Did not find %s in list %s".format(target, list_foo))


@timed_function
def get_swap_count(listA, listB, debug=False):
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


@timed_function
def traveling_salesman(squares):
    ref_get_lab_distance = get_lab_distance

    # build a full matrix of color to color distances
    len_squares = len(squares)
    matrix = [[0 for i in range(len_squares)] for j in range(len_squares)]
    r_len_squares = range(len_squares)

    for x in r_len_squares:
        x_square = squares[x]
        (x_red, x_green, x_blue) = x_square.rgb
        x_lab = x_square.lab

        for y in r_len_squares:

            if x == y:
                matrix[x][y] = 0
                matrix[y][x] = 0
                continue

            if matrix[x][y] or matrix[y][x]:
                continue

            y_square = squares[y]
            (y_red, y_green, y_blue) = y_square.rgb
            y_lab = y_square.lab

            distance = ref_get_lab_distance(x_lab, y_lab)
            matrix[x][y] = distance
            matrix[y][x] = distance

    if use_cie2000_cache:
        global cie2000_cache
        cie2000_cache = {}
        gc.collect()

    path = solve_tsp(matrix)
    return [squares[x] for x in path]


@timed_function
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


class LabColor(object):

    @timed_function
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


@timed_function
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


@timed_function
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


@timed_function
def hashtag_rgb_to_labcolor(rgb_string):
    (red, green, blue) = hex_to_rgb(rgb_string)
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
    "Wh": hashtag_rgb_to_labcolor("#FFFFFF"),
    "Gr": hashtag_rgb_to_labcolor("#14694a"),
    "Ye": hashtag_rgb_to_labcolor("#FFFF00"),
    "OR": hashtag_rgb_to_labcolor("#943509"),
    "Bu": hashtag_rgb_to_labcolor("#163967"),
    "Rd": hashtag_rgb_to_labcolor("#680402"),
}


@timed_function
def get_row_color_distances(squares, row_baseline_lab):
    """
    'colors' is list if (index, (red, green, blue)) tuples
    'row_baseline_lab' is a list of Lab colors, one for each row of colors

    Return the total distance of the colors in a row vs their baseline
    """
    ref_get_lab_distance = get_lab_distance
    results = []
    squares_per_row = int(len(squares) / 6)
    count = 0
    row_index = 0
    distance = 0
    baseline_lab = row_baseline_lab[row_index]

    for square in squares:
        baseline_lab = row_baseline_lab[row_index]
        distance += ref_get_lab_distance(baseline_lab, square.lab)
        count += 1

        if count % squares_per_row == 0:
            results.append(int(distance))
            row_index += 1
            distance = 0

    return results


@timed_function
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


@timed_function
def rgb_list_to_lab(rgbs):
    reds = array.array("B")
    greens = array.array("B")
    blues = array.array("B")

    for (red, green, blue) in rgbs:
        reds.append(red)
        greens.append(green)
        blues.append(blue)

    median_red = int(median(reds))
    median_green = int(median(greens))
    median_blue = int(median(blues))

    return rgb2lab((median_red, median_green, median_blue))


class Square(object):

    def __init__(self, side, cube, position, red, green, blue):
        #self.cube = cube
        self.side = side
        self.position = position
        self.rgb = (red, green, blue)
        self.lab = rgb2lab((red, green, blue))
        self.color_name = None
        self.side_name = None  # ULFRBD

    def __str__(self):
        return "%s%d" % (self.side, self.position)

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
            self.mid_pos = (self.min_pos + self.max_pos) / 2

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
        return "side-" + self.name

    def __repr__(self):
        return self.__str__()

    @timed_function
    def set_square(self, position, red, green, blue):
        self.squares[position] = Square(self, self.cube, position, red, green, blue)

        if position in self.center_pos:
            self.center_squares.append(self.squares[position])

        elif position in self.edge_pos:
            self.edge_squares.append(self.squares[position])

        elif position in self.corner_pos:
            self.corner_squares.append(self.squares[position])

        else:
            raise Exception("Could not determine egde vs corner vs center")

    @timed_function
    def calculate_wing_partners(self):
        for (pos1, pos2) in self.cube.all_edge_positions:
            if pos1 >= self.min_pos and pos1 <= self.max_pos:
                self.wing_partner[pos1] = pos2
            elif pos2 >= self.min_pos and pos2 <= self.max_pos:
                self.wing_partner[pos2] = pos1

    @timed_function
    def get_wing_partner(self, wing_index):
        try:
            return self.wing_partner[wing_index]
        except KeyError:
            #log.info("wing_partner\n%s\n".format(self.wing_partner))
            raise


class RubiksColorSolverGeneric(object):

    def __init__(self, width):
        self.width = width
        self.height = width
        self.squares_per_side = self.width * self.width
        self.orbits = int(ceil((self.width - 2) / 2.0))
        self.state = []
        self.orange_baseline = None
        self.red_baseline = None
        self.white_squares = []
        self.all_edge_positions = []

        if self.width % 2 == 0:
            self.even = True
            self.odd = False
        else:
            self.even = False
            self.odd = True

        #if not os.path.exists(HTML_DIRECTORY):
        #    os.makedirs(HTML_DIRECTORY)

        with open(HTML_FILENAME, "w"):
            pass

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

        # U and B
        for (pos1, pos2) in zip(
            self.sideU.edge_north_pos, reversed(self.sideB.edge_north_pos)
        ):
            self.all_edge_positions.append((pos1, pos2))

        # U and L
        for (pos1, pos2) in zip(self.sideU.edge_west_pos, self.sideL.edge_north_pos):
            self.all_edge_positions.append((pos1, pos2))

        # U and F
        for (pos1, pos2) in zip(self.sideU.edge_south_pos, self.sideF.edge_north_pos):
            self.all_edge_positions.append((pos1, pos2))

        # U and R
        for (pos1, pos2) in zip(
            self.sideU.edge_east_pos, reversed(self.sideR.edge_north_pos)
        ):
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
        for (pos1, pos2) in zip(
            self.sideL.edge_south_pos, reversed(self.sideD.edge_west_pos)
        ):
            self.all_edge_positions.append((pos1, pos2))

        # R and D
        for (pos1, pos2) in zip(self.sideR.edge_south_pos, self.sideD.edge_east_pos):
            self.all_edge_positions.append((pos1, pos2))

        # R and B
        for (pos1, pos2) in zip(self.sideR.edge_east_pos, self.sideB.edge_west_pos):
            self.all_edge_positions.append((pos1, pos2))

        # B and D
        for (pos1, pos2) in zip(
            reversed(self.sideB.edge_south_pos), self.sideD.edge_south_pos
        ):
            self.all_edge_positions.append((pos1, pos2))

        for side in self.sides.values():
            side.calculate_wing_partners()

        self.www_header()

    @timed_function
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
"""
                % (
                    square_size,
                    square_size,
                    square_size,
                    square_size,
                    square_size,
                    square_size,
                )
            )

    @timed_function
    def write_colors(self, desc, squares):
        with open(HTML_FILENAME, "a") as fh:
            squares_per_row = int(len(squares) / 6)
            fh.write("<h2>%s</h2>\n" % desc)
            fh.write("<div class='clear colors'>\n")

            count = 0
            for square in squares:
                (red, green, blue) = square.rgb
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

    @timed_function
    def www_footer(self):
        with open(HTML_FILENAME, "a") as fh:
            fh.write(
                """
</body>
</html>
"""
            )

    @timed_function
    def get_side(self, position):
        """
        Given a position on the cube return the Side object
        that contians that position
        """
        for side in self.sides.values():
            if position >= side.min_pos and position <= side.max_pos:
                return side
        raise Exception("Could not find side for %d" % position)

    @timed_function
    def get_square(self, position):
        side = self.get_side(position)
        return side.squares[position]

    @timed_function
    def enter_scan_data(self, scan_data):

        for (position, (red, green, blue)) in scan_data.items():
            # dwalton I do not think this int() is needed
            position = int(position)
            side = self.get_side(position)
            side.set_square(position, red, green, blue)

        with open(HTML_FILENAME, "a") as fh:
            fh.write("<h1>JSON Input</h1>\n")
            fh.write("<pre>%s</pre>\n" % json_dumps(scan_data))

    @timed_function
    def write_cube(self, desc, use_html_colors):
        # TODO clean this up...should not need the 'cube' var
        cube = ["dummy"]

        for side in (self.sideU, self.sideL, self.sideF, self.sideR, self.sideB, self.sideD):
            for position in range(side.min_pos, side.max_pos + 1):
                square = side.squares[position]

                if use_html_colors:
                    red = html_color[square.color_name]["red"]
                    green = html_color[square.color_name]["green"]
                    blue = html_color[square.color_name]["blue"]
                else:
                    red = square.rgb[0]
                    green = square.rgb[1]
                    blue = square.rgb[2]

                cube.append((red, green, blue, square.color_name))

        col = 1
        squares_per_side = self.width * self.width
        max_square = squares_per_side * 6

        sides = ("upper", "left", "front", "right", "back", "down")
        side_index = -1
        (first_squares, last_squares, last_UBD_squares) = get_important_square_indexes(
            self.width
        )

        with open(HTML_FILENAME, "a") as fh:
            fh.write("<h1>%s</h1>\n" % desc)
            for index in range(1, max_square + 1):
                if index in first_squares:
                    side_index += 1
                    fh.write("<div class='side' id='%s'>\n" % sides[side_index])

                (red, green, blue, color_name) = cube[index]
                lab = rgb2lab((red, green, blue))

                fh.write(
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
                    fh.write("</div>\n")

                    if index in last_UBD_squares:
                        fh.write("<div class='clear'></div>\n")

                col += 1

                if col == self.width + 1:
                    col = 1

    @timed_function
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

        #log.info("Cube\n\n%s\n" % "\n".join(output))

    @timed_function
    def write_color_box(self):
        with open(HTML_FILENAME, "a") as fh:
            fh.write("<h2>color_box</h2>\n")
            fh.write("<div class='clear colors'>\n")
            for color_name in ("Wh", "Ye", "Gr", "Bu", "OR", "Rd"):
                lab = self.color_box[color_name]

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

    @timed_function
    def set_state(self):
        self.state = []
        ref_get_lab_distance = get_lab_distance

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
                    distance += ref_get_lab_distance(center_square.lab, color_obj)

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

    @timed_function
    def cube_for_kociemba_strict(self):
        #log.info("color_to_side_name:\n{}\n".format(self.color_to_side_name))
        data = []
        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]
                data.append(square.side_name)

        return data

    @timed_function
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
                data["squares"][square.position] = {
                    "finalSide": self.color_to_side_name[color]
                }

        return data

    @timed_function
    def assign_color_names(self, desc, squares_lists_all, color_permutations, color_box):
        assert color_permutations
        assert color_box
        ref_get_lab_distance = get_lab_distance

        # log.info(f"assign_color_names for '{desc}'")
        # log.info(f"squares_lists_all {squares_lists_all}")
        # log.info(f"color_permutations {color_permutations}")
        # log.info(f"color_box {color_box}")

        # split squares_lists_all up into 6 evenly sized lists
        squares_per_row = int(len(squares_lists_all) / 6)
        squares_lists = []
        square_list = []

        # squares_lists_all is sorted by color. Split that list into 6 even buckets (squares_lists).
        for square in squares_lists_all:
            square_list.append(square)

            if len(square_list) == squares_per_row:
                squares_lists.append(tuple(square_list))
                square_list = []

        #print("squares_lists\n    {}\n".format("\n    ".join(map(str, squares_lists))))
        # Assign a color name to each squares in each square_list. Compute
        # which naming scheme results in the least total color distance in
        # terms of the assigned color name vs. the colors in color_box.
        min_distance = 99999
        min_distance_permutation = None
        distances_of_square_list_per_color = {}

        for color_name in ("Wh", "Ye", "OR", "Rd", "Gr", "Bu"):
            color_lab = color_box[color_name]
            distances_of_square_list_per_color[color_name] = []

            for (index, squares_list) in enumerate(squares_lists):
                distance = 0
                for square in squares_list:
                    distance += ref_get_lab_distance(square.lab, color_lab)
                distances_of_square_list_per_color[color_name].append(int(distance))
            distances_of_square_list_per_color[color_name] = tuple(distances_of_square_list_per_color[color_name])

        #for color_name in (Wh, Ye, OR, Rd, Gr, Bu):
        #    print("distances_of_square_list_per_color {} : {}".format(color_name, distances_of_square_list_per_color[color_name]))

        if color_permutations == "even_cube_center_color_permutations":

            #for (permutation_index, permutation) in enumerate(permutations((Wh, Ye, OR, Rd, Gr, Bu))):
            for permutation in permutations(("Wh", "Ye", "OR", "Rd", "Gr", "Bu")):
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
                #    log.info("{} PERMUTATION {}, DISTANCE {}".format(desc, permutation, distance))

        elif color_permutations == "odd_cube_center_color_permutations":

            #for (permutation_index, permutation) in enumerate(odd_cube_center_color_permutations):
            for permutation in odd_cube_center_color_permutations:
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
                #    log.info("{} PERMUTATION {}, DISTANCE {}".format(desc, permutation, distance))

        # Assign the color name to the Square object
        for (index, squares_list) in enumerate(squares_lists):
            color_name = min_distance_permutation[index]

            for square in squares_list:
                square.color_name = color_name

    @timed_function
    def resolve_color_box(self):
        """
        Assign names to the corner squares, use crayola colors as reference point.

        We use these name assignments to build our "color_box" which will be our
        references Wh, Ye, OR, Rd, Gr, Bu colors for assigning color names to edge
        and center squares.
        """
        #log.debug("\n\n\n\n")
        #log.info("Resolve color_box")
        corner_squares = []

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for square in side.corner_squares:
                corner_squares.append(square)

        sorted_corner_squares = traveling_salesman(corner_squares)
        self.assign_color_names(
            "corners",
            sorted_corner_squares,
            "even_cube_center_color_permutations",
            crayola_colors,
        )
        self.sanity_check_corner_squares()
        self.write_colors("color_box corners", sorted_corner_squares)

        # Build a color_box dictionary from the centers
        self.color_box = {}

        white_corners = []
        yellow_corners = []
        orange_corners = []
        red_corners = []
        green_corners = []
        blue_corners = []

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for square in side.corner_squares:
                if square.color_name == "Wh":
                    white_corners.append(square.rgb)
                elif square.color_name == "Ye":
                    yellow_corners.append(square.rgb)
                elif square.color_name == "OR":
                    orange_corners.append(square.rgb)
                elif square.color_name == "Rd":
                    red_corners.append(square.rgb)
                elif square.color_name == "Gr":
                    green_corners.append(square.rgb)
                elif square.color_name == "Bu":
                    blue_corners.append(square.rgb)

        self.color_box["Wh"] = rgb_list_to_lab(white_corners)
        self.color_box["Ye"] = rgb_list_to_lab(yellow_corners)
        self.color_box["OR"] = rgb_list_to_lab(orange_corners)
        self.color_box["Rd"] = rgb_list_to_lab(red_corners)
        self.color_box["Gr"] = rgb_list_to_lab(green_corners)
        self.color_box["Bu"] = rgb_list_to_lab(blue_corners)
        # log.info(f"self.color_box: {self.color_box}")

        self.orange_baseline = self.color_box["OR"]
        self.red_baseline = self.color_box["Rd"]

    @timed_function
    def resolve_corner_squares(self):
        """
        Assign names to the corner squares
        """
        #log.debug("\n\n\n\n")
        #log.info("Resolve corners")
        corner_squares = []

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for square in side.corner_squares:
                corner_squares.append(square)

        # corner_squares.extend(self.color_box_squares)

        sorted_corner_squares = traveling_salesman(corner_squares)
        self.assign_color_names(
            "corners",
            sorted_corner_squares,
            "even_cube_center_color_permutations",
            self.color_box,
        )
        self.sanity_check_corner_squares()
        self.write_colors("corners", sorted_corner_squares)

    @timed_function
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
            square1 = self.get_square(square1_position)
            square2 = self.get_square(square2_position)
            wing_pair_string = ", ".join(
                sorted([square1.color_name, square2.color_name])
            )
            # log.info("orbit {}: ({}, {}) is ({})".format(orbit_id, square1_position, square2_position, wing_pair_string))

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

        #if not valid:
        #    log.info("wing_pair_counts:\n{}\n".format(wing_pair_counts))
        #    log.warning("valid: {}".format(valid))

        # assert valid, "Cube is invalid"
        return valid

    @timed_function
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
                square = self.get_square(position)
                # log.info("square %s is %s" % (square, square.color_name))
                corner_colors.append(square.color_name)

            if "Gr" in corner_colors and "Wh" in corner_colors:
                # log.info("%s is Gr/Wh corner" % " ".join(map(str, corner_tuple)))
                green_white_corners.append(corner_tuple)

            elif "Gr" in corner_colors and "Ye" in corner_colors:
                # log.info("%s is Gr/Ye corner" % " ".join(map(str, corner_tuple)))
                green_yellow_corners.append(corner_tuple)

            elif "Bu" in corner_colors and "Wh" in corner_colors:
                # log.info("%s is Bu/Wh corner" % " ".join(map(str, corner_tuple)))
                blue_white_corners.append(corner_tuple)

            elif "Bu" in corner_colors and "Ye" in corner_colors:
                # log.info("%s is Bu/Ye corner" % " ".join(map(str, corner_tuple)))
                blue_yellow_corners.append(corner_tuple)

        return (
            green_white_corners,
            green_yellow_corners,
            blue_white_corners,
            blue_yellow_corners,
        )

    @timed_function
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
            square = self.get_square(square_index)
            partner = self.get_square(partner_index)

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

    @timed_function
    def sanity_check_edges_red_orange_count_for_orbit(self, target_orbit_id):
        ref_get_lab_distance = get_lab_distance

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
                        distance += ref_get_lab_distance(
                            partner_square.lab, self.orange_baseline
                        )
                    elif red_orange == "Rd":
                        distance += ref_get_lab_distance(
                            partner_square.lab, self.red_baseline
                        )
                    else:
                        raise Exception(red_orange)

                    partner_square.color_name = red_orange
                    partner_square.side_name = self.color_to_side_name[partner_square.color_name]

                if (self.width == 4 or self.width == 6 or (self.width == 5 and target_orbit_id == 0)):

                    for (index, (target_color_square, partner_square)) in enumerate(
                        target_color_red_or_orange_edges
                    ):
                        red_orange = red_orange_permutation[index]
                        high_low_edge_per_color = self.get_high_low_per_edge_color(
                            target_orbit_id
                        )
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

            for (index, (target_color_square, partner_square)) in enumerate(
                target_color_red_or_orange_edges
            ):
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
        #log.info(
        #    "orbit %s green_red_or_orange_edges %s"
        #    % (target_orbit_id, green_red_or_orange_edges)
        #)
        fix_orange_vs_red_for_color("green", green_red_or_orange_edges)

        #log.info(
        #    "orbit %s blue_red_or_orange_edges %s"
        #    % (target_orbit_id, blue_red_or_orange_edges)
        #)
        fix_orange_vs_red_for_color("blue", blue_red_or_orange_edges)

        #log.info(
        #    "orbit %s white_red_or_orange_edges %s"
        #    % (target_orbit_id, white_red_or_orange_edges)
        #)
        fix_orange_vs_red_for_color("white", white_red_or_orange_edges)

        #log.info(
        #    "orbit %s yellow_red_or_orange_edges %s"
        #    % (target_orbit_id, yellow_red_or_orange_edges)
        #)
        fix_orange_vs_red_for_color("yellow", yellow_red_or_orange_edges)

        self.validate_edge_orbit(target_orbit_id)

    @timed_function
    def get_high_low_per_edge_color(self, target_orbit_id):

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
            square = self.get_square(square_index)
            partner = self.get_square(partner_index)

            if self.width == 6:
                from rubikscolorresolver.cube_666 import highlow_edge_values
                highlow = highlow_edge_values[(square_index, partner_index, square.side_name, partner.side_name)]
            elif self.width == 5:
                from rubikscolorresolver.cube_555 import highlow_edge_values
                highlow = highlow_edge_values[(square_index, partner_index, square.side_name, partner.side_name)]
            elif self.width == 4:
                from rubikscolorresolver.cube_444 import highlow_edge_values
                highlow = highlow_edge_values[(square_index, partner_index, square.side_name, partner.side_name)]
            else:
                raise Exception("Add support for %sx%sx%s" % (self.width, self.width, self.width))

            edge_color_pair = edge_color_pair_map["%s/%s" % (square.color_name, partner.color_name)]
            high_low_per_edge_color[edge_color_pair].add(highlow)

        # log.info("high_low_per_edge_color for orbit %d\n%s" % (target_orbit_id, high_low_per_edge_color))
        # log.info("")
        return high_low_per_edge_color

    @timed_function
    def sanity_check_edge_squares(self):
        for orbit_id in range(self.orbits):
            self.sanity_check_edges_red_orange_count_for_orbit(orbit_id)

    @timed_function
    def resolve_edge_squares(self):
        """
        Use traveling salesman algorithm to sort the colors
        """

        # Nothing to be done for 2x2x2
        if self.width == 2:
            return True
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

        for target_orbit_id in range(self.orbits):
            #log.debug("\n\n\n\n")
            #log.info("Resolve edges for orbit %d" % target_orbit_id)
            edge_squares = []

            for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
                for square in side.edge_squares:
                    orbit_id = edge_orbit_id[square.position]
                    # log.info("{}: {}, position {}, orbit_id {}".format(self.width, square, square.position, orbit_id))

                    if orbit_id == target_orbit_id:
                        edge_squares.append(square)

            # edge_squares.extend(self.color_box_squares)
            sorted_edge_squares = traveling_salesman(edge_squares)
            self.assign_color_names(
                "edge orbit %d" % target_orbit_id,
                sorted_edge_squares,
                "even_cube_center_color_permutations",
                self.color_box,
            )
            self.write_colors("edges - orbit %d" % target_orbit_id, sorted_edge_squares)

    @timed_function
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
            corner1 = self.get_square(corner1_index)
            corner2 = self.get_square(corner2_index)
            corner3 = self.get_square(corner3_index)
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

    @timed_function
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
            corner1 = self.get_square(corner1_index)
            corner2 = self.get_square(corner2_index)
            corner3 = self.get_square(corner3_index)
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

    @timed_function
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
            corner1 = self.get_square(corner1_index)
            corner2 = self.get_square(corner2_index)
            corner3 = self.get_square(corner3_index)
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

    @timed_function
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
            corner1 = self.get_square(corner1_index)
            corner2 = self.get_square(corner2_index)
            corner3 = self.get_square(corner3_index)
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

    @timed_function
    def sanity_check_corner_squares(self):
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

    @timed_function
    def resolve_center_squares(self):
        """
        Use traveling salesman algorithm to sort the squares by color
        """

        if self.width == 2:
            from rubikscolorresolver.cube_222 import center_groups
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
                square = self.get_square(position)
                center_squares.append(square)

            if desc == "centers":
                sorted_center_squares = center_squares[:]
                permutations = "odd_cube_center_color_permutations"
            else:
                sorted_center_squares = traveling_salesman(center_squares)
                permutations = "even_cube_center_color_permutations"

            self.assign_color_names(
                desc, sorted_center_squares, permutations, self.color_box
            )
            self.write_colors(desc, sorted_center_squares)

    @timed_function
    def get_corner_swap_count(self, debug=False):

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
            square1 = self.get_square(square_index1)
            square2 = self.get_square(square_index2)
            square3 = self.get_square(square_index3)
            corner_str = "".join(
                sorted([square1.side_name, square2.side_name, square3.side_name])
            )
            current_corners.append(corner_str)

        if debug:
            #log.info("to_check:\n%s".format(to_check))
            to_check_str = ""
            for (a, b, c) in to_check:
                to_check_str += "%4s" % a

            #log.info("to_check       :%s" % to_check_str)
            #log.info("needed corners : %s" % " ".join(needed_corners))
            #log.info("currnet corners: %s" % " ".join(current_corners))
            #log.info("")

        return get_swap_count(needed_corners, current_corners, debug)

    @timed_function
    def corner_swaps_even(self, debug=False):
        if self.get_corner_swap_count(debug) % 2 == 0:
            return True
        return False

    @timed_function
    def corner_swaps_odd(self, debug=False):
        if self.get_corner_swap_count(debug) % 2 == 1:
            return True
        return False

    @timed_function
    def get_edge_swap_count(self, orbit, debug=False):
        needed_edges = []
        to_check = []

        # Upper
        for (edge_index, square_index) in enumerate(self.sideU.edge_north_pos):
            to_check.append(square_index)
            needed_edges.append("UB")
            break

        for (edge_index, square_index) in enumerate(reversed(self.sideU.edge_west_pos)):
            to_check.append(square_index)
            needed_edges.append("UL")
            break

        for (edge_index, square_index) in enumerate(
            reversed(self.sideU.edge_south_pos)
        ):
            to_check.append(square_index)
            needed_edges.append("UF")
            break

        for (edge_index, square_index) in enumerate(self.sideU.edge_east_pos):
            to_check.append(square_index)
            needed_edges.append("UR")
            break

        # Left
        for (edge_index, square_index) in enumerate(reversed(self.sideL.edge_west_pos)):
            to_check.append(square_index)
            needed_edges.append("LB")
            break

        for (edge_index, square_index) in enumerate(self.sideL.edge_east_pos):
            to_check.append(square_index)
            needed_edges.append("LF")
            break

        # Right
        for (edge_index, square_index) in enumerate(reversed(self.sideR.edge_west_pos)):
            to_check.append(square_index)
            needed_edges.append("RF")
            break

        for (edge_index, square_index) in enumerate(self.sideR.edge_east_pos):
            to_check.append(square_index)
            needed_edges.append("RB")
            break

        # Down
        for (edge_index, square_index) in enumerate(self.sideD.edge_north_pos):
            to_check.append(square_index)
            needed_edges.append("DF")
            break

        for (edge_index, square_index) in enumerate(reversed(self.sideD.edge_west_pos)):
            to_check.append(square_index)
            needed_edges.append("DL")
            break

        for (edge_index, square_index) in enumerate(
            reversed(self.sideD.edge_south_pos)
        ):
            to_check.append(square_index)
            needed_edges.append("DB")
            break

        for (edge_index, square_index) in enumerate(self.sideD.edge_east_pos):
            to_check.append(square_index)
            needed_edges.append("DR")
            break

        if debug:
            to_check_str = ""

            for x in to_check:
                to_check_str += "%3s" % x

            #log.info("to_check     :%s" % to_check_str)
            #log.info("needed edges : %s" % " ".join(needed_edges))

        current_edges = []

        for square_index in to_check:
            side = self.get_side(square_index)
            partner_index = side.get_wing_partner(square_index)
            square1 = self.get_square(square_index)
            square2 = self.get_square(partner_index)

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

        #if debug:
        #    log.info("current edges: %s" % " ".join(current_edges))

        return get_swap_count(needed_edges, current_edges, debug)

    @timed_function
    def edge_swaps_even(self, orbit, debug):
        if self.get_edge_swap_count(orbit, debug) % 2 == 0:
            return True
        return False

    @timed_function
    def edge_swaps_odd(self, orbit, debug):
        if self.get_edge_swap_count(orbit, debug) % 2 == 1:
            return True
        return False

    @timed_function
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
            square1 = self.get_square(square_index1)
            square2 = self.get_square(square_index2)
            square3 = self.get_square(square_index3)
            corner_str = "".join(
                sorted([square1.side_name, square2.side_name, square3.side_name])
            )
            current_corners.append(corner_str)

        # We need a way to validate all of the needed_corners are present and
        # if not, what do we flip so that we do have all of the needed corners?
        for corner in needed_corners:
            if corner not in current_corners:
                raise Exception("corner %s is missing".format(corner))

    @timed_function
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
        ref_get_lab_distance = get_lab_distance

        try:
            edges_even = self.edge_swaps_even(None, debug)
            corners_even = self.corner_swaps_even(debug)

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
                partner = self.get_square(partner_position)

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

        square_green_orange = self.get_square(green_orange_position)
        square_green_red = self.get_square(green_red_position)
        square_blue_orange = self.get_square(blue_orange_position)
        square_blue_red = self.get_square(blue_red_position)

        # To correct the parity we can swap orange/red for the green edges or
        # we can swap orange/red for the blue edges. Which will result in the
        # lowest color distance with our orange/red baselines?
        distance_swap_green_edge = 0
        distance_swap_green_edge += ref_get_lab_distance(
            square_blue_orange.lab, self.orange_baseline
        )
        distance_swap_green_edge += ref_get_lab_distance(
            square_blue_red.lab, self.red_baseline
        )
        distance_swap_green_edge += ref_get_lab_distance(
            square_green_orange.lab, self.red_baseline
        )
        distance_swap_green_edge += ref_get_lab_distance(
            square_green_red.lab, self.orange_baseline
        )

        distance_swap_blue_edge = 0
        distance_swap_blue_edge += ref_get_lab_distance(
            square_green_orange.lab, self.orange_baseline
        )
        distance_swap_blue_edge += ref_get_lab_distance(
            square_green_red.lab, self.red_baseline
        )
        distance_swap_blue_edge += ref_get_lab_distance(
            square_blue_orange.lab, self.red_baseline
        )
        distance_swap_blue_edge += ref_get_lab_distance(
            square_blue_red.lab, self.orange_baseline
        )

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
            square_green_orange.side_name = self.color_to_side_name[
                square_green_orange.color_name
            ]
            square_green_red.side_name = self.color_to_side_name[
                square_green_red.color_name
            ]
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
            square_blue_orange.side_name = self.color_to_side_name[
                square_blue_orange.color_name
            ]
            square_blue_red.side_name = self.color_to_side_name[
                square_blue_red.color_name
            ]

        edges_even = self.edge_swaps_even(None, debug)
        corners_even = self.corner_swaps_even(debug)
        assert edges_even == corners_even, (
            "parity is still broken, edges_even %s, corners_even %s"
            % (edges_even, corners_even)
        )

    @timed_function
    def crunch_colors(self):
        self.write_cube("Initial RGB values", False)

        self.resolve_color_box()
        self.write_color_box()

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

        self.write_cube("Final Cube", True)
        self.print_cube()
        self.www_footer()

    def print_profile_data(self):
        print("                     function      calls  time(ms)")
        print("==============================  ========  ========")
        for function in profile_stats_calls.keys():
            print("{:>30}  {:>8}  {:>8.2f}".format(function, profile_stats_calls[function], profile_stats_time[function] / 1000))


@timed_function
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

    scan_data = eval(rgb)

    square_count = len(list(scan_data.keys()))
    square_count_per_side = int(square_count / 6)
    width = int(sqrt(square_count_per_side))

    cube = RubiksColorSolverGeneric(width)
    cube.enter_scan_data(scan_data)
    cube.crunch_colors()
    cube.print_profile_data()

    if use_json:
        result = json_dumps(cube.cube_for_json(), indent=4, sort_keys=True)
    else:
        result = "".join(cube.cube_for_kociemba_strict())

    print(result)
    return result
