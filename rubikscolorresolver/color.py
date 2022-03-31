# standard libraries
from math import atan2, cos, degrees, exp, radians, sin, sqrt

try:
    # standard libraries
    from typing import Tuple
except ImportError:
    # this will barf for micropython...ignore it
    pass


html_color = {
    "Gr": {"red": 0, "green": 102, "blue": 0},
    "Bu": {"red": 0, "green": 0, "blue": 153},
    "OR": {"red": 255, "green": 153, "blue": 0},
    "Rd": {"red": 204, "green": 51, "blue": 0},
    "Wh": {"red": 255, "green": 255, "blue": 255},
    "Ye": {"red": 255, "green": 255, "blue": 0},
}


def hex_to_rgb(rgb_string: str) -> Tuple[int, int, int]:
    """
    Takes #112233 and returns the RGB values in decimal
    """
    if rgb_string.startswith("#"):
        rgb_string = rgb_string[1:]

    red = int(rgb_string[0:2], 16)
    green = int(rgb_string[2:4], 16)
    blue = int(rgb_string[4:6], 16)
    return (red, green, blue)


class LabColor(object):
    def __init__(self, L: float, a: float, b: float, red: int, green: int, blue: int) -> None:
        assert isinstance(L, float)
        assert isinstance(a, float)
        assert isinstance(b, float)
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

    def __hash__(self):
        return hash((self.L, self.a, self.b))

    def __eq__(self, other) -> bool:
        return bool(self.L == other.L and self.a == other.a and self.b == other.b)

    def __lt__(self, other) -> bool:
        if self.L != other.L:
            return self.L < other.L

        if self.a != other.a:
            return self.a < other.a

        return self.b < other.b


def rgb2lab(inputColor: Tuple[int, int, int]) -> LabColor:
    """
    Given a tuple of red, green, blue values return the corresponding LabColor object
    """
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
    """
    Given a tuple of red, green, blue values return the corresponding HSV values
    """
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


cie2000_cache = {}


def lab_distance_cie2000(lab1, lab2):
    """
    delta CIE 2000

    Ported from this php implementation
    https://github.com/renasboy/php-color-difference/blob/master/lib/color_difference.class.php
    """
    global cie2000_cache
    l1 = lab1.L
    a1 = lab1.a
    b1 = lab1.b

    l2 = lab2.L
    a2 = lab2.a
    b2 = lab2.b

    delta_e = cie2000_cache.get((l1, a1, b1, l2, a2, b2))

    if delta_e is not None:
        return delta_e

    delta_e = cie2000_cache.get((l2, a2, b2, l1, a1, b1))

    if delta_e is not None:
        return delta_e

    avg_lp = (l1 + l2) / 2.0
    c1 = sqrt(a1**2 + b1**2)
    c2 = sqrt(a2**2 + b2**2)
    avg_c = (c1 + c2) / 2.0
    g = (1 - sqrt(avg_c**7 / (avg_c**7 + 25**7))) / 2.0
    a1p = a1 * (1 + g)
    a2p = a2 * (1 + g)
    c1p = sqrt(a1p**2 + b1**2)
    c2p = sqrt(a2p**2 + b2**2)
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

    r_c = 2 * sqrt((avg_cp**7) / ((avg_cp**7) + (25**7)))
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

    cie2000_cache[(l1, a1, b1, l2, a2, b2)] = delta_e
    cie2000_cache[(l2, a2, b2, l1, a1, b1)] = delta_e

    return delta_e


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
    return int(sqrt(((lab1.L - lab2.L) ** 2) + ((lab1.a - lab2.a) ** 2) + ((lab1.b - lab2.b) ** 2)))
    # return lab_distance_cie2000(lab1, lab2)


def hashtag_rgb_to_labcolor(rgb_string: str) -> LabColor:
    """
    Given a string like #AABBCC return the corresponding LabColor object
    """
    (red, green, blue) = hex_to_rgb(rgb_string)
    return rgb2lab((red, green, blue))
