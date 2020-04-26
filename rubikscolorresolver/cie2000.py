from math import atan2, ceil, cos, degrees, exp, radians, sin, sqrt

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

    cie2000_cache[(l1, a1, b1, l2, a2, b2)] = delta_e
    cie2000_cache[(l2, a2, b2, l1, a1, b1)] = delta_e

    return delta_e