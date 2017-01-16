#!/usr/bin/env python

"""
Print the output of colormath's cie2000 vs our cie2000.  This was
used once upon a time to verify that our cie2000 is working.
"""

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_diff import delta_e_cie2000
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

my_red = rgb2lab((30, 12, 6))
my_blue = rgb2lab((6, 19, 20))
my_orange = rgb2lab((40, 20, 6))

print "my_red      : %s" % my_red
print "my_blue     : %s" % my_blue
print "my_orange   : %s" % my_orange
print "red->blue   : %s" % my_delta_e_cie2000(my_red, my_blue)
print "red->orange : %s\n\n" % my_delta_e_cie2000(my_red, my_orange)

red = rgb_to_labcolor(30, 12, 6)
blue = rgb_to_labcolor(6, 19, 20)
orange = rgb_to_labcolor(40, 20, 6)
distance = delta_e_cie2000(red, blue)

print "red         : %s" % red
print "blue        : %s" % blue
print "orange      : %s" % my_orange
print "red->blue   : %s" % delta_e_cie2000(red, blue)
print "red->orange : %s" % delta_e_cie2000(red, orange)
