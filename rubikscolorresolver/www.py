# standard libraries
import logging
import os
import sys

# rubiks cube libraries
from rubikscolorresolver.color import LabColor, html_color

logger = logging.getLogger(__name__)

ALL_COLORS = ("Bu", "Gr", "OR", "Rd", "Wh", "Ye")

if sys.implementation.name == "micropython":
    HTML_FILENAME = "rubiks-color-resolver.html"
else:
    HTML_FILENAME = "/tmp/rubiks-color-resolver.html"

try:
    os.unlink(HTML_FILENAME)
except Exception:
    pass


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
    "Wh": LabColor(100.0, 0.00526049995830391, -0.01040818452526793, 255, 255, 255),
    "OR": LabColor(35.71689493804023, 38.18518746791636, 43.98251678431012, 148, 53, 9),
    "Gr": LabColor(39.14982168015123, -32.45052099773829, 10.60519920674466, 20, 105, 74),
    "Rd": LabColor(20.18063311070288, 40.48184409611946, 29.94038922869042, 104, 4, 2),
    "Bu": LabColor(23.92144819784853, 5.28400492805528, -30.63998357385018, 22, 57, 103),
    "Ye": LabColor(97.13824698129729, -21.55590833483229, 94.48248544644462, 255, 255, 0),
}


def open_mode(filename):
    if os.path.exists(HTML_FILENAME):
        return "a"
    else:
        return "w"


class WwwMixin:
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

                    if square.position:
                        desc = square.position
                    else:
                        desc = square.color_name

                    fh.write(
                        "<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%s</span>\n"  # noqa: E501
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
                            desc,
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

                    if square.position:
                        desc = square.position
                    else:
                        desc = square.color_name

                    fh.write(
                        "<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%s</span>\n"  # noqa: E501
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
                            desc,
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
                    "<span class='square' style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), Lab (%s, %s, %s), color %s'>%d</span>\n"  # noqa: E501
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

    def html_cube(self, desc, use_html_colors, div_class):
        cube = ["dummy"]

        for side in self.sides.values():
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

            for color_name, lab in box.items():
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
