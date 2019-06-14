#!/usr/bin/env python3

"""
print(the output of colormath's cie2000 vs our cie2000.  This was
used once upon a time to verify that our cie2000 is working.
"""

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_diff import delta_e_cie2000, delta_e_cie1994, delta_e_cie1976
from colormath.color_conversions import convert_color
from rubikscolorresolver import delta_e_cie2000 as my_delta_e_cie2000
from rubikscolorresolver import rgb2lab


def rgb_to_labcolor(red, green, blue):
    rgb_obj = sRGBColor(red, green, blue)
    return convert_color(rgb_obj, LabColor)


# red = (30, 12, 6)
# blue = (6, 19, 20)
# white = (60, 100, 70)
# green = (6, 35, 13)
# yellow = (34, 43, 8)
# orange = (40, 20, 6)

my_white = rgb2lab((232, 232, 236))
my_green = rgb2lab((41, 202, 121))
my_white2 = rgb2lab((217, 233, 247))

print("my_white     : %s" % my_white)
print("my_green     : %s" % my_green)
print("my_white2    : %s" % my_white2)
print("my cie2000 white->green : %s" % my_delta_e_cie2000(my_white, my_green))
print("my cie2000 white->white2: %s\n\n" % my_delta_e_cie2000(my_white, my_white2))

white = rgb_to_labcolor(232, 232, 236)
green = rgb_to_labcolor(41, 202, 121)
white2 = rgb_to_labcolor(217, 233, 247)
distance = delta_e_cie2000(white, green)

print("white        : %s" % white)
print("green        : %s" % green)
print("white2       : %s" % white2)
print("cie2000 white->green : %s" % delta_e_cie2000(white, green))
print("cie2000 white->white2: %s\n" % delta_e_cie2000(white, white2))
print("cie1994 white->green : %s" % delta_e_cie1994(white, green))
print("cie1994 white->white2: %s\n" % delta_e_cie1994(white, white2))
print("cie1976 white->green : %s" % delta_e_cie1976(white, green))
print("cie1976 white->white2: %s\n" % delta_e_cie1976(white, white2))
