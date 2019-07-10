
import array
import gc
from math import sqrt
from rubikscolorresolver.base import (
    LabColor,
    RubiksColorSolverGenericBase,
    rgb2lab,
)
from rubikscolorresolver.tsp_solver_greedy import solve_tsp
#from rubikscolorresolver.profile import timed_function, print_profile_data
import sys

if sys.version_info < (3, 4):
    raise SystemError("Must be using Python 3.4 or higher")


def is_micropython():
    return sys.implementation.name == "micropython"


if is_micropython():
    from ucollections import OrderedDict

else:
    from collections import OrderedDict


'''
from math import atan2, ceil, cos, degrees, exp, radians, sin, sqrt

# @timed_function
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

    return delta_e
'''


cie2000_cache = {}

ALL_COLORS = ("Bu", "Gr", "OR", "Rd", "Wh", "Ye")

html_color = {
    "Gr": {"red": 0, "green": 102, "blue": 0},
    "Bu": {"red": 0, "green": 0, "blue": 153},
    "OR": {"red": 255, "green": 102, "blue": 0},
    "Rd": {"red": 204, "green": 0, "blue": 0},
    "Wh": {"red": 255, "green": 255, "blue": 255},
    "Ye": {"red": 255, "green": 204, "blue": 0},
}


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

#even_cube_center_color_permutations = list(sorted(permutations(ALL_COLORS)))
even_cube_center_color_permutations = """Bu Gr OR Rd Wh Ye
Bu Gr OR Rd Ye Wh
Bu Gr OR Wh Rd Ye
Bu Gr OR Wh Ye Rd
Bu Gr OR Ye Rd Wh
Bu Gr OR Ye Wh Rd
Bu Gr Rd OR Wh Ye
Bu Gr Rd OR Ye Wh
Bu Gr Rd Wh OR Ye
Bu Gr Rd Wh Ye OR
Bu Gr Rd Ye OR Wh
Bu Gr Rd Ye Wh OR
Bu Gr Wh OR Rd Ye
Bu Gr Wh OR Ye Rd
Bu Gr Wh Rd OR Ye
Bu Gr Wh Rd Ye OR
Bu Gr Wh Ye OR Rd
Bu Gr Wh Ye Rd OR
Bu Gr Ye OR Rd Wh
Bu Gr Ye OR Wh Rd
Bu Gr Ye Rd OR Wh
Bu Gr Ye Rd Wh OR
Bu Gr Ye Wh OR Rd
Bu Gr Ye Wh Rd OR
Bu OR Gr Rd Wh Ye
Bu OR Gr Rd Ye Wh
Bu OR Gr Wh Rd Ye
Bu OR Gr Wh Ye Rd
Bu OR Gr Ye Rd Wh
Bu OR Gr Ye Wh Rd
Bu OR Rd Gr Wh Ye
Bu OR Rd Gr Ye Wh
Bu OR Rd Wh Gr Ye
Bu OR Rd Wh Ye Gr
Bu OR Rd Ye Gr Wh
Bu OR Rd Ye Wh Gr
Bu OR Wh Gr Rd Ye
Bu OR Wh Gr Ye Rd
Bu OR Wh Rd Gr Ye
Bu OR Wh Rd Ye Gr
Bu OR Wh Ye Gr Rd
Bu OR Wh Ye Rd Gr
Bu OR Ye Gr Rd Wh
Bu OR Ye Gr Wh Rd
Bu OR Ye Rd Gr Wh
Bu OR Ye Rd Wh Gr
Bu OR Ye Wh Gr Rd
Bu OR Ye Wh Rd Gr
Bu Rd Gr OR Wh Ye
Bu Rd Gr OR Ye Wh
Bu Rd Gr Wh OR Ye
Bu Rd Gr Wh Ye OR
Bu Rd Gr Ye OR Wh
Bu Rd Gr Ye Wh OR
Bu Rd OR Gr Wh Ye
Bu Rd OR Gr Ye Wh
Bu Rd OR Wh Gr Ye
Bu Rd OR Wh Ye Gr
Bu Rd OR Ye Gr Wh
Bu Rd OR Ye Wh Gr
Bu Rd Wh Gr OR Ye
Bu Rd Wh Gr Ye OR
Bu Rd Wh OR Gr Ye
Bu Rd Wh OR Ye Gr
Bu Rd Wh Ye Gr OR
Bu Rd Wh Ye OR Gr
Bu Rd Ye Gr OR Wh
Bu Rd Ye Gr Wh OR
Bu Rd Ye OR Gr Wh
Bu Rd Ye OR Wh Gr
Bu Rd Ye Wh Gr OR
Bu Rd Ye Wh OR Gr
Bu Wh Gr OR Rd Ye
Bu Wh Gr OR Ye Rd
Bu Wh Gr Rd OR Ye
Bu Wh Gr Rd Ye OR
Bu Wh Gr Ye OR Rd
Bu Wh Gr Ye Rd OR
Bu Wh OR Gr Rd Ye
Bu Wh OR Gr Ye Rd
Bu Wh OR Rd Gr Ye
Bu Wh OR Rd Ye Gr
Bu Wh OR Ye Gr Rd
Bu Wh OR Ye Rd Gr
Bu Wh Rd Gr OR Ye
Bu Wh Rd Gr Ye OR
Bu Wh Rd OR Gr Ye
Bu Wh Rd OR Ye Gr
Bu Wh Rd Ye Gr OR
Bu Wh Rd Ye OR Gr
Bu Wh Ye Gr OR Rd
Bu Wh Ye Gr Rd OR
Bu Wh Ye OR Gr Rd
Bu Wh Ye OR Rd Gr
Bu Wh Ye Rd Gr OR
Bu Wh Ye Rd OR Gr
Bu Ye Gr OR Rd Wh
Bu Ye Gr OR Wh Rd
Bu Ye Gr Rd OR Wh
Bu Ye Gr Rd Wh OR
Bu Ye Gr Wh OR Rd
Bu Ye Gr Wh Rd OR
Bu Ye OR Gr Rd Wh
Bu Ye OR Gr Wh Rd
Bu Ye OR Rd Gr Wh
Bu Ye OR Rd Wh Gr
Bu Ye OR Wh Gr Rd
Bu Ye OR Wh Rd Gr
Bu Ye Rd Gr OR Wh
Bu Ye Rd Gr Wh OR
Bu Ye Rd OR Gr Wh
Bu Ye Rd OR Wh Gr
Bu Ye Rd Wh Gr OR
Bu Ye Rd Wh OR Gr
Bu Ye Wh Gr OR Rd
Bu Ye Wh Gr Rd OR
Bu Ye Wh OR Gr Rd
Bu Ye Wh OR Rd Gr
Bu Ye Wh Rd Gr OR
Bu Ye Wh Rd OR Gr
Gr Bu OR Rd Wh Ye
Gr Bu OR Rd Ye Wh
Gr Bu OR Wh Rd Ye
Gr Bu OR Wh Ye Rd
Gr Bu OR Ye Rd Wh
Gr Bu OR Ye Wh Rd
Gr Bu Rd OR Wh Ye
Gr Bu Rd OR Ye Wh
Gr Bu Rd Wh OR Ye
Gr Bu Rd Wh Ye OR
Gr Bu Rd Ye OR Wh
Gr Bu Rd Ye Wh OR
Gr Bu Wh OR Rd Ye
Gr Bu Wh OR Ye Rd
Gr Bu Wh Rd OR Ye
Gr Bu Wh Rd Ye OR
Gr Bu Wh Ye OR Rd
Gr Bu Wh Ye Rd OR
Gr Bu Ye OR Rd Wh
Gr Bu Ye OR Wh Rd
Gr Bu Ye Rd OR Wh
Gr Bu Ye Rd Wh OR
Gr Bu Ye Wh OR Rd
Gr Bu Ye Wh Rd OR
Gr OR Bu Rd Wh Ye
Gr OR Bu Rd Ye Wh
Gr OR Bu Wh Rd Ye
Gr OR Bu Wh Ye Rd
Gr OR Bu Ye Rd Wh
Gr OR Bu Ye Wh Rd
Gr OR Rd Bu Wh Ye
Gr OR Rd Bu Ye Wh
Gr OR Rd Wh Bu Ye
Gr OR Rd Wh Ye Bu
Gr OR Rd Ye Bu Wh
Gr OR Rd Ye Wh Bu
Gr OR Wh Bu Rd Ye
Gr OR Wh Bu Ye Rd
Gr OR Wh Rd Bu Ye
Gr OR Wh Rd Ye Bu
Gr OR Wh Ye Bu Rd
Gr OR Wh Ye Rd Bu
Gr OR Ye Bu Rd Wh
Gr OR Ye Bu Wh Rd
Gr OR Ye Rd Bu Wh
Gr OR Ye Rd Wh Bu
Gr OR Ye Wh Bu Rd
Gr OR Ye Wh Rd Bu
Gr Rd Bu OR Wh Ye
Gr Rd Bu OR Ye Wh
Gr Rd Bu Wh OR Ye
Gr Rd Bu Wh Ye OR
Gr Rd Bu Ye OR Wh
Gr Rd Bu Ye Wh OR
Gr Rd OR Bu Wh Ye
Gr Rd OR Bu Ye Wh
Gr Rd OR Wh Bu Ye
Gr Rd OR Wh Ye Bu
Gr Rd OR Ye Bu Wh
Gr Rd OR Ye Wh Bu
Gr Rd Wh Bu OR Ye
Gr Rd Wh Bu Ye OR
Gr Rd Wh OR Bu Ye
Gr Rd Wh OR Ye Bu
Gr Rd Wh Ye Bu OR
Gr Rd Wh Ye OR Bu
Gr Rd Ye Bu OR Wh
Gr Rd Ye Bu Wh OR
Gr Rd Ye OR Bu Wh
Gr Rd Ye OR Wh Bu
Gr Rd Ye Wh Bu OR
Gr Rd Ye Wh OR Bu
Gr Wh Bu OR Rd Ye
Gr Wh Bu OR Ye Rd
Gr Wh Bu Rd OR Ye
Gr Wh Bu Rd Ye OR
Gr Wh Bu Ye OR Rd
Gr Wh Bu Ye Rd OR
Gr Wh OR Bu Rd Ye
Gr Wh OR Bu Ye Rd
Gr Wh OR Rd Bu Ye
Gr Wh OR Rd Ye Bu
Gr Wh OR Ye Bu Rd
Gr Wh OR Ye Rd Bu
Gr Wh Rd Bu OR Ye
Gr Wh Rd Bu Ye OR
Gr Wh Rd OR Bu Ye
Gr Wh Rd OR Ye Bu
Gr Wh Rd Ye Bu OR
Gr Wh Rd Ye OR Bu
Gr Wh Ye Bu OR Rd
Gr Wh Ye Bu Rd OR
Gr Wh Ye OR Bu Rd
Gr Wh Ye OR Rd Bu
Gr Wh Ye Rd Bu OR
Gr Wh Ye Rd OR Bu
Gr Ye Bu OR Rd Wh
Gr Ye Bu OR Wh Rd
Gr Ye Bu Rd OR Wh
Gr Ye Bu Rd Wh OR
Gr Ye Bu Wh OR Rd
Gr Ye Bu Wh Rd OR
Gr Ye OR Bu Rd Wh
Gr Ye OR Bu Wh Rd
Gr Ye OR Rd Bu Wh
Gr Ye OR Rd Wh Bu
Gr Ye OR Wh Bu Rd
Gr Ye OR Wh Rd Bu
Gr Ye Rd Bu OR Wh
Gr Ye Rd Bu Wh OR
Gr Ye Rd OR Bu Wh
Gr Ye Rd OR Wh Bu
Gr Ye Rd Wh Bu OR
Gr Ye Rd Wh OR Bu
Gr Ye Wh Bu OR Rd
Gr Ye Wh Bu Rd OR
Gr Ye Wh OR Bu Rd
Gr Ye Wh OR Rd Bu
Gr Ye Wh Rd Bu OR
Gr Ye Wh Rd OR Bu
OR Bu Gr Rd Wh Ye
OR Bu Gr Rd Ye Wh
OR Bu Gr Wh Rd Ye
OR Bu Gr Wh Ye Rd
OR Bu Gr Ye Rd Wh
OR Bu Gr Ye Wh Rd
OR Bu Rd Gr Wh Ye
OR Bu Rd Gr Ye Wh
OR Bu Rd Wh Gr Ye
OR Bu Rd Wh Ye Gr
OR Bu Rd Ye Gr Wh
OR Bu Rd Ye Wh Gr
OR Bu Wh Gr Rd Ye
OR Bu Wh Gr Ye Rd
OR Bu Wh Rd Gr Ye
OR Bu Wh Rd Ye Gr
OR Bu Wh Ye Gr Rd
OR Bu Wh Ye Rd Gr
OR Bu Ye Gr Rd Wh
OR Bu Ye Gr Wh Rd
OR Bu Ye Rd Gr Wh
OR Bu Ye Rd Wh Gr
OR Bu Ye Wh Gr Rd
OR Bu Ye Wh Rd Gr
OR Gr Bu Rd Wh Ye
OR Gr Bu Rd Ye Wh
OR Gr Bu Wh Rd Ye
OR Gr Bu Wh Ye Rd
OR Gr Bu Ye Rd Wh
OR Gr Bu Ye Wh Rd
OR Gr Rd Bu Wh Ye
OR Gr Rd Bu Ye Wh
OR Gr Rd Wh Bu Ye
OR Gr Rd Wh Ye Bu
OR Gr Rd Ye Bu Wh
OR Gr Rd Ye Wh Bu
OR Gr Wh Bu Rd Ye
OR Gr Wh Bu Ye Rd
OR Gr Wh Rd Bu Ye
OR Gr Wh Rd Ye Bu
OR Gr Wh Ye Bu Rd
OR Gr Wh Ye Rd Bu
OR Gr Ye Bu Rd Wh
OR Gr Ye Bu Wh Rd
OR Gr Ye Rd Bu Wh
OR Gr Ye Rd Wh Bu
OR Gr Ye Wh Bu Rd
OR Gr Ye Wh Rd Bu
OR Rd Bu Gr Wh Ye
OR Rd Bu Gr Ye Wh
OR Rd Bu Wh Gr Ye
OR Rd Bu Wh Ye Gr
OR Rd Bu Ye Gr Wh
OR Rd Bu Ye Wh Gr
OR Rd Gr Bu Wh Ye
OR Rd Gr Bu Ye Wh
OR Rd Gr Wh Bu Ye
OR Rd Gr Wh Ye Bu
OR Rd Gr Ye Bu Wh
OR Rd Gr Ye Wh Bu
OR Rd Wh Bu Gr Ye
OR Rd Wh Bu Ye Gr
OR Rd Wh Gr Bu Ye
OR Rd Wh Gr Ye Bu
OR Rd Wh Ye Bu Gr
OR Rd Wh Ye Gr Bu
OR Rd Ye Bu Gr Wh
OR Rd Ye Bu Wh Gr
OR Rd Ye Gr Bu Wh
OR Rd Ye Gr Wh Bu
OR Rd Ye Wh Bu Gr
OR Rd Ye Wh Gr Bu
OR Wh Bu Gr Rd Ye
OR Wh Bu Gr Ye Rd
OR Wh Bu Rd Gr Ye
OR Wh Bu Rd Ye Gr
OR Wh Bu Ye Gr Rd
OR Wh Bu Ye Rd Gr
OR Wh Gr Bu Rd Ye
OR Wh Gr Bu Ye Rd
OR Wh Gr Rd Bu Ye
OR Wh Gr Rd Ye Bu
OR Wh Gr Ye Bu Rd
OR Wh Gr Ye Rd Bu
OR Wh Rd Bu Gr Ye
OR Wh Rd Bu Ye Gr
OR Wh Rd Gr Bu Ye
OR Wh Rd Gr Ye Bu
OR Wh Rd Ye Bu Gr
OR Wh Rd Ye Gr Bu
OR Wh Ye Bu Gr Rd
OR Wh Ye Bu Rd Gr
OR Wh Ye Gr Bu Rd
OR Wh Ye Gr Rd Bu
OR Wh Ye Rd Bu Gr
OR Wh Ye Rd Gr Bu
OR Ye Bu Gr Rd Wh
OR Ye Bu Gr Wh Rd
OR Ye Bu Rd Gr Wh
OR Ye Bu Rd Wh Gr
OR Ye Bu Wh Gr Rd
OR Ye Bu Wh Rd Gr
OR Ye Gr Bu Rd Wh
OR Ye Gr Bu Wh Rd
OR Ye Gr Rd Bu Wh
OR Ye Gr Rd Wh Bu
OR Ye Gr Wh Bu Rd
OR Ye Gr Wh Rd Bu
OR Ye Rd Bu Gr Wh
OR Ye Rd Bu Wh Gr
OR Ye Rd Gr Bu Wh
OR Ye Rd Gr Wh Bu
OR Ye Rd Wh Bu Gr
OR Ye Rd Wh Gr Bu
OR Ye Wh Bu Gr Rd
OR Ye Wh Bu Rd Gr
OR Ye Wh Gr Bu Rd
OR Ye Wh Gr Rd Bu
OR Ye Wh Rd Bu Gr
OR Ye Wh Rd Gr Bu
Rd Bu Gr OR Wh Ye
Rd Bu Gr OR Ye Wh
Rd Bu Gr Wh OR Ye
Rd Bu Gr Wh Ye OR
Rd Bu Gr Ye OR Wh
Rd Bu Gr Ye Wh OR
Rd Bu OR Gr Wh Ye
Rd Bu OR Gr Ye Wh
Rd Bu OR Wh Gr Ye
Rd Bu OR Wh Ye Gr
Rd Bu OR Ye Gr Wh
Rd Bu OR Ye Wh Gr
Rd Bu Wh Gr OR Ye
Rd Bu Wh Gr Ye OR
Rd Bu Wh OR Gr Ye
Rd Bu Wh OR Ye Gr
Rd Bu Wh Ye Gr OR
Rd Bu Wh Ye OR Gr
Rd Bu Ye Gr OR Wh
Rd Bu Ye Gr Wh OR
Rd Bu Ye OR Gr Wh
Rd Bu Ye OR Wh Gr
Rd Bu Ye Wh Gr OR
Rd Bu Ye Wh OR Gr
Rd Gr Bu OR Wh Ye
Rd Gr Bu OR Ye Wh
Rd Gr Bu Wh OR Ye
Rd Gr Bu Wh Ye OR
Rd Gr Bu Ye OR Wh
Rd Gr Bu Ye Wh OR
Rd Gr OR Bu Wh Ye
Rd Gr OR Bu Ye Wh
Rd Gr OR Wh Bu Ye
Rd Gr OR Wh Ye Bu
Rd Gr OR Ye Bu Wh
Rd Gr OR Ye Wh Bu
Rd Gr Wh Bu OR Ye
Rd Gr Wh Bu Ye OR
Rd Gr Wh OR Bu Ye
Rd Gr Wh OR Ye Bu
Rd Gr Wh Ye Bu OR
Rd Gr Wh Ye OR Bu
Rd Gr Ye Bu OR Wh
Rd Gr Ye Bu Wh OR
Rd Gr Ye OR Bu Wh
Rd Gr Ye OR Wh Bu
Rd Gr Ye Wh Bu OR
Rd Gr Ye Wh OR Bu
Rd OR Bu Gr Wh Ye
Rd OR Bu Gr Ye Wh
Rd OR Bu Wh Gr Ye
Rd OR Bu Wh Ye Gr
Rd OR Bu Ye Gr Wh
Rd OR Bu Ye Wh Gr
Rd OR Gr Bu Wh Ye
Rd OR Gr Bu Ye Wh
Rd OR Gr Wh Bu Ye
Rd OR Gr Wh Ye Bu
Rd OR Gr Ye Bu Wh
Rd OR Gr Ye Wh Bu
Rd OR Wh Bu Gr Ye
Rd OR Wh Bu Ye Gr
Rd OR Wh Gr Bu Ye
Rd OR Wh Gr Ye Bu
Rd OR Wh Ye Bu Gr
Rd OR Wh Ye Gr Bu
Rd OR Ye Bu Gr Wh
Rd OR Ye Bu Wh Gr
Rd OR Ye Gr Bu Wh
Rd OR Ye Gr Wh Bu
Rd OR Ye Wh Bu Gr
Rd OR Ye Wh Gr Bu
Rd Wh Bu Gr OR Ye
Rd Wh Bu Gr Ye OR
Rd Wh Bu OR Gr Ye
Rd Wh Bu OR Ye Gr
Rd Wh Bu Ye Gr OR
Rd Wh Bu Ye OR Gr
Rd Wh Gr Bu OR Ye
Rd Wh Gr Bu Ye OR
Rd Wh Gr OR Bu Ye
Rd Wh Gr OR Ye Bu
Rd Wh Gr Ye Bu OR
Rd Wh Gr Ye OR Bu
Rd Wh OR Bu Gr Ye
Rd Wh OR Bu Ye Gr
Rd Wh OR Gr Bu Ye
Rd Wh OR Gr Ye Bu
Rd Wh OR Ye Bu Gr
Rd Wh OR Ye Gr Bu
Rd Wh Ye Bu Gr OR
Rd Wh Ye Bu OR Gr
Rd Wh Ye Gr Bu OR
Rd Wh Ye Gr OR Bu
Rd Wh Ye OR Bu Gr
Rd Wh Ye OR Gr Bu
Rd Ye Bu Gr OR Wh
Rd Ye Bu Gr Wh OR
Rd Ye Bu OR Gr Wh
Rd Ye Bu OR Wh Gr
Rd Ye Bu Wh Gr OR
Rd Ye Bu Wh OR Gr
Rd Ye Gr Bu OR Wh
Rd Ye Gr Bu Wh OR
Rd Ye Gr OR Bu Wh
Rd Ye Gr OR Wh Bu
Rd Ye Gr Wh Bu OR
Rd Ye Gr Wh OR Bu
Rd Ye OR Bu Gr Wh
Rd Ye OR Bu Wh Gr
Rd Ye OR Gr Bu Wh
Rd Ye OR Gr Wh Bu
Rd Ye OR Wh Bu Gr
Rd Ye OR Wh Gr Bu
Rd Ye Wh Bu Gr OR
Rd Ye Wh Bu OR Gr
Rd Ye Wh Gr Bu OR
Rd Ye Wh Gr OR Bu
Rd Ye Wh OR Bu Gr
Rd Ye Wh OR Gr Bu
Wh Bu Gr OR Rd Ye
Wh Bu Gr OR Ye Rd
Wh Bu Gr Rd OR Ye
Wh Bu Gr Rd Ye OR
Wh Bu Gr Ye OR Rd
Wh Bu Gr Ye Rd OR
Wh Bu OR Gr Rd Ye
Wh Bu OR Gr Ye Rd
Wh Bu OR Rd Gr Ye
Wh Bu OR Rd Ye Gr
Wh Bu OR Ye Gr Rd
Wh Bu OR Ye Rd Gr
Wh Bu Rd Gr OR Ye
Wh Bu Rd Gr Ye OR
Wh Bu Rd OR Gr Ye
Wh Bu Rd OR Ye Gr
Wh Bu Rd Ye Gr OR
Wh Bu Rd Ye OR Gr
Wh Bu Ye Gr OR Rd
Wh Bu Ye Gr Rd OR
Wh Bu Ye OR Gr Rd
Wh Bu Ye OR Rd Gr
Wh Bu Ye Rd Gr OR
Wh Bu Ye Rd OR Gr
Wh Gr Bu OR Rd Ye
Wh Gr Bu OR Ye Rd
Wh Gr Bu Rd OR Ye
Wh Gr Bu Rd Ye OR
Wh Gr Bu Ye OR Rd
Wh Gr Bu Ye Rd OR
Wh Gr OR Bu Rd Ye
Wh Gr OR Bu Ye Rd
Wh Gr OR Rd Bu Ye
Wh Gr OR Rd Ye Bu
Wh Gr OR Ye Bu Rd
Wh Gr OR Ye Rd Bu
Wh Gr Rd Bu OR Ye
Wh Gr Rd Bu Ye OR
Wh Gr Rd OR Bu Ye
Wh Gr Rd OR Ye Bu
Wh Gr Rd Ye Bu OR
Wh Gr Rd Ye OR Bu
Wh Gr Ye Bu OR Rd
Wh Gr Ye Bu Rd OR
Wh Gr Ye OR Bu Rd
Wh Gr Ye OR Rd Bu
Wh Gr Ye Rd Bu OR
Wh Gr Ye Rd OR Bu
Wh OR Bu Gr Rd Ye
Wh OR Bu Gr Ye Rd
Wh OR Bu Rd Gr Ye
Wh OR Bu Rd Ye Gr
Wh OR Bu Ye Gr Rd
Wh OR Bu Ye Rd Gr
Wh OR Gr Bu Rd Ye
Wh OR Gr Bu Ye Rd
Wh OR Gr Rd Bu Ye
Wh OR Gr Rd Ye Bu
Wh OR Gr Ye Bu Rd
Wh OR Gr Ye Rd Bu
Wh OR Rd Bu Gr Ye
Wh OR Rd Bu Ye Gr
Wh OR Rd Gr Bu Ye
Wh OR Rd Gr Ye Bu
Wh OR Rd Ye Bu Gr
Wh OR Rd Ye Gr Bu
Wh OR Ye Bu Gr Rd
Wh OR Ye Bu Rd Gr
Wh OR Ye Gr Bu Rd
Wh OR Ye Gr Rd Bu
Wh OR Ye Rd Bu Gr
Wh OR Ye Rd Gr Bu
Wh Rd Bu Gr OR Ye
Wh Rd Bu Gr Ye OR
Wh Rd Bu OR Gr Ye
Wh Rd Bu OR Ye Gr
Wh Rd Bu Ye Gr OR
Wh Rd Bu Ye OR Gr
Wh Rd Gr Bu OR Ye
Wh Rd Gr Bu Ye OR
Wh Rd Gr OR Bu Ye
Wh Rd Gr OR Ye Bu
Wh Rd Gr Ye Bu OR
Wh Rd Gr Ye OR Bu
Wh Rd OR Bu Gr Ye
Wh Rd OR Bu Ye Gr
Wh Rd OR Gr Bu Ye
Wh Rd OR Gr Ye Bu
Wh Rd OR Ye Bu Gr
Wh Rd OR Ye Gr Bu
Wh Rd Ye Bu Gr OR
Wh Rd Ye Bu OR Gr
Wh Rd Ye Gr Bu OR
Wh Rd Ye Gr OR Bu
Wh Rd Ye OR Bu Gr
Wh Rd Ye OR Gr Bu
Wh Ye Bu Gr OR Rd
Wh Ye Bu Gr Rd OR
Wh Ye Bu OR Gr Rd
Wh Ye Bu OR Rd Gr
Wh Ye Bu Rd Gr OR
Wh Ye Bu Rd OR Gr
Wh Ye Gr Bu OR Rd
Wh Ye Gr Bu Rd OR
Wh Ye Gr OR Bu Rd
Wh Ye Gr OR Rd Bu
Wh Ye Gr Rd Bu OR
Wh Ye Gr Rd OR Bu
Wh Ye OR Bu Gr Rd
Wh Ye OR Bu Rd Gr
Wh Ye OR Gr Bu Rd
Wh Ye OR Gr Rd Bu
Wh Ye OR Rd Bu Gr
Wh Ye OR Rd Gr Bu
Wh Ye Rd Bu Gr OR
Wh Ye Rd Bu OR Gr
Wh Ye Rd Gr Bu OR
Wh Ye Rd Gr OR Bu
Wh Ye Rd OR Bu Gr
Wh Ye Rd OR Gr Bu
Ye Bu Gr OR Rd Wh
Ye Bu Gr OR Wh Rd
Ye Bu Gr Rd OR Wh
Ye Bu Gr Rd Wh OR
Ye Bu Gr Wh OR Rd
Ye Bu Gr Wh Rd OR
Ye Bu OR Gr Rd Wh
Ye Bu OR Gr Wh Rd
Ye Bu OR Rd Gr Wh
Ye Bu OR Rd Wh Gr
Ye Bu OR Wh Gr Rd
Ye Bu OR Wh Rd Gr
Ye Bu Rd Gr OR Wh
Ye Bu Rd Gr Wh OR
Ye Bu Rd OR Gr Wh
Ye Bu Rd OR Wh Gr
Ye Bu Rd Wh Gr OR
Ye Bu Rd Wh OR Gr
Ye Bu Wh Gr OR Rd
Ye Bu Wh Gr Rd OR
Ye Bu Wh OR Gr Rd
Ye Bu Wh OR Rd Gr
Ye Bu Wh Rd Gr OR
Ye Bu Wh Rd OR Gr
Ye Gr Bu OR Rd Wh
Ye Gr Bu OR Wh Rd
Ye Gr Bu Rd OR Wh
Ye Gr Bu Rd Wh OR
Ye Gr Bu Wh OR Rd
Ye Gr Bu Wh Rd OR
Ye Gr OR Bu Rd Wh
Ye Gr OR Bu Wh Rd
Ye Gr OR Rd Bu Wh
Ye Gr OR Rd Wh Bu
Ye Gr OR Wh Bu Rd
Ye Gr OR Wh Rd Bu
Ye Gr Rd Bu OR Wh
Ye Gr Rd Bu Wh OR
Ye Gr Rd OR Bu Wh
Ye Gr Rd OR Wh Bu
Ye Gr Rd Wh Bu OR
Ye Gr Rd Wh OR Bu
Ye Gr Wh Bu OR Rd
Ye Gr Wh Bu Rd OR
Ye Gr Wh OR Bu Rd
Ye Gr Wh OR Rd Bu
Ye Gr Wh Rd Bu OR
Ye Gr Wh Rd OR Bu
Ye OR Bu Gr Rd Wh
Ye OR Bu Gr Wh Rd
Ye OR Bu Rd Gr Wh
Ye OR Bu Rd Wh Gr
Ye OR Bu Wh Gr Rd
Ye OR Bu Wh Rd Gr
Ye OR Gr Bu Rd Wh
Ye OR Gr Bu Wh Rd
Ye OR Gr Rd Bu Wh
Ye OR Gr Rd Wh Bu
Ye OR Gr Wh Bu Rd
Ye OR Gr Wh Rd Bu
Ye OR Rd Bu Gr Wh
Ye OR Rd Bu Wh Gr
Ye OR Rd Gr Bu Wh
Ye OR Rd Gr Wh Bu
Ye OR Rd Wh Bu Gr
Ye OR Rd Wh Gr Bu
Ye OR Wh Bu Gr Rd
Ye OR Wh Bu Rd Gr
Ye OR Wh Gr Bu Rd
Ye OR Wh Gr Rd Bu
Ye OR Wh Rd Bu Gr
Ye OR Wh Rd Gr Bu
Ye Rd Bu Gr OR Wh
Ye Rd Bu Gr Wh OR
Ye Rd Bu OR Gr Wh
Ye Rd Bu OR Wh Gr
Ye Rd Bu Wh Gr OR
Ye Rd Bu Wh OR Gr
Ye Rd Gr Bu OR Wh
Ye Rd Gr Bu Wh OR
Ye Rd Gr OR Bu Wh
Ye Rd Gr OR Wh Bu
Ye Rd Gr Wh Bu OR
Ye Rd Gr Wh OR Bu
Ye Rd OR Bu Gr Wh
Ye Rd OR Bu Wh Gr
Ye Rd OR Gr Bu Wh
Ye Rd OR Gr Wh Bu
Ye Rd OR Wh Bu Gr
Ye Rd OR Wh Gr Bu
Ye Rd Wh Bu Gr OR
Ye Rd Wh Bu OR Gr
Ye Rd Wh Gr Bu OR
Ye Rd Wh Gr OR Bu
Ye Rd Wh OR Bu Gr
Ye Rd Wh OR Gr Bu
Ye Wh Bu Gr OR Rd
Ye Wh Bu Gr Rd OR
Ye Wh Bu OR Gr Rd
Ye Wh Bu OR Rd Gr
Ye Wh Bu Rd Gr OR
Ye Wh Bu Rd OR Gr
Ye Wh Gr Bu OR Rd
Ye Wh Gr Bu Rd OR
Ye Wh Gr OR Bu Rd
Ye Wh Gr OR Rd Bu
Ye Wh Gr Rd Bu OR
Ye Wh Gr Rd OR Bu
Ye Wh OR Bu Gr Rd
Ye Wh OR Bu Rd Gr
Ye Wh OR Gr Bu Rd
Ye Wh OR Gr Rd Bu
Ye Wh OR Rd Bu Gr
Ye Wh OR Rd Gr Bu
Ye Wh Rd Bu Gr OR
Ye Wh Rd Bu OR Gr
Ye Wh Rd Gr Bu OR
Ye Wh Rd Gr OR Bu
Ye Wh Rd OR Bu Gr
Ye Wh Rd OR Gr Bu"""
len_even_cube_center_color_permutations = 720


SIDES_COUNT = 6
HTML_DIRECTORY = "/tmp/rubiks-color-resolver/"
#HTML_FILENAME = HTML_DIRECTORY + "index.html"
HTML_FILENAME = "rubiks-color-resolver.html"


def print_mem_stats(desc):
    print('{} free: {} allocated: {}'.format(desc, gc.mem_free(), gc.mem_alloc()))


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


# @timed_function
def traveling_salesman(squares, endpoints=None):
    len_squares = len(squares)
    r_len_squares = range(len_squares)

    # build a full matrix of color to color distances
    # init the 2d list with 0s
    matrix = [x[:] for x in [[0] * len_squares] * len_squares]

    for x in r_len_squares:
        x_lab = squares[x].lab

        for y in range(x+1, len_squares):
            y_lab = squares[y].lab

            distance = sqrt(((x_lab.L - y_lab.L) ** 2) + ((x_lab.a - y_lab.a) ** 2) + ((x_lab.b - y_lab.b) ** 2))
            matrix[x][y] = distance
            matrix[y][x] = distance

    path = solve_tsp(matrix, optim_steps=0, endpoints=endpoints)
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
        distance += sqrt(((baseline_lab.L - square.lab.L) ** 2) + ((baseline_lab.a - square.lab.a) ** 2) + ((baseline_lab.b - square.lab.b) ** 2))
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

    # @timed_function
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
    def write_cube(self, desc, use_html_colors):
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

                cube.append((red, green, blue, square.color_name, square.lab))

        col = 1
        squares_per_side = self.width * self.width
        max_square = squares_per_side * 6

        sides = ("upper", "left", "front", "right", "back", "down")
        side_index = -1
        (first_squares, last_squares, last_UBD_squares) = get_important_square_indexes(self.width)

        with open(HTML_FILENAME, "a") as fh:
            fh.write("<h1>%s</h1>\n" % desc)
            for index in range(1, max_square + 1):
                if index in first_squares:
                    side_index += 1
                    fh.write("<div class='side' id='%s'>\n" % sides[side_index])

                (red, green, blue, color_name, lab) = cube[index]

                fh.write(
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
                    fh.write("</div>\n")

                    if index in last_UBD_squares:
                        fh.write("<div class='clear'></div>\n")

                col += 1

                if col == self.width + 1:
                    col = 1

    def _write_colors(self, desc, box):
        with open(HTML_FILENAME, "a") as fh:
            fh.write("<h2>{}</h2>\n".format(desc))
            fh.write("<div class='clear colors'>\n")

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
                    distance += sqrt(((center_square.lab.L - color_obj.L) ** 2) + ((center_square.lab.a - color_obj.a) ** 2) + ((center_square.lab.b - color_obj.b) ** 2))

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
                data["squares"][square.position] = {
                    "finalSide": self.color_to_side_name[color]
                }

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
                    distance += sqrt(((square.lab.L - color_lab.L) ** 2) + ((square.lab.a - color_lab.a) ** 2) + ((square.lab.b - color_lab.b) ** 2))
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
                min_color_name_distance = 9999
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

            #for (permutation_index, permutation) in enumerate(odd_cube_center_color_permutations):
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

    # @timed_function
    def set_sorted_corner_squares(self):
        corner_squares = []

        for side in (self.sideU, self.sideR, self.sideF, self.sideD, self.sideL, self.sideB):
            for square in side.corner_squares:
                corner_squares.append(square)

        self.sorted_corner_squares = traveling_salesman(corner_squares)

    # @timed_function
    def resolve_color_box(self):
        """
        Assign names to the corner squares, use crayola colors as reference point.

        For odd cubes another option here would be to only use the 6 center squares.
        This ends up being less reliable though because in that scenario we only have
        one square for each color where if we use the corners we have 4 squares for
        each color and can take the median to get a more accurate color.

        We use these name assignments to build our "color_box" which will be our
        references Wh, Ye, OR, Rd, Gr, Bu colors for assigning color names to edge
        and center squares.
        """
        self.assign_color_names(
            "corners for color_box",
            self.sorted_corner_squares,
            "even_cube_center_color_permutations",
            crayola_colors,
        )
        self.sanity_check_corner_squares()

        if self.write_debug_file:
            self.write_colors("color_box corners", self.sorted_corner_squares)

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

    # @timed_function
    def resolve_corner_squares(self):
        """
        Assign names to the corner squares
        """
        self.assign_color_names(
            "corners",
            self.sorted_corner_squares,
            "even_cube_center_color_permutations",
            self.color_box,
        )
        self.sanity_check_corner_squares()

        if self.write_debug_file:
            self.write_colors("corners", self.sorted_corner_squares)

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

            sorted_edge_squares = traveling_salesman(edge_squares)

            self.assign_color_names(
                "edge orbit %d" % target_orbit_id,
                sorted_edge_squares,
                "even_cube_center_color_permutations",
                self.color_box,
            )

            if self.write_debug_file:
                self.write_colors("edges - orbit %d" % target_orbit_id, sorted_edge_squares)

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
                sorted_center_squares = traveling_salesman(center_squares)
                permutations = "even_cube_center_color_permutations"

            self.assign_color_names(desc, sorted_center_squares, permutations, self.color_box)

            if self.write_debug_file:
                self.write_colors(desc, sorted_center_squares)

    # @timed_function
    def crunch_colors(self):
        if self.write_debug_file:
            self.write_cube("Initial RGB values", False)
            self.write_crayola_colors()

        self.set_sorted_corner_squares()
        self.resolve_color_box()

        if self.write_debug_file:
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

        if self.write_debug_file:
            self.write_cube("Final Cube", True)
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

    scan_data = eval(rgb)

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
        result = json_dumps(cube.cube_for_json(), indent=4, sort_keys=True)
    else:
        result = "".join(cube.cube_for_kociemba_strict())

    print(result)
    return result
