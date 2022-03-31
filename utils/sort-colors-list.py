#!/usr/bin/env python3

# standard libraries
import colorsys
import json
import math
import random
import subprocess
from collections import defaultdict
from math import sqrt
from random import uniform

# third party libraries
import matplotlib.pyplot as plt

# rubiks cube libraries
from rubikscolorresolver.color import hashtag_rgb_to_labcolor, lab_distance_cie2000, rgb2lab
from rubikscolorresolver.tsp_solver_greedy import solve_tsp

lego_colors = []

if False:
    with open("tests/test-data/6x6x6-random-03.txt", "r") as fh:
        lego_colors.extend(list(json.load(fh).values()))

else:
    colors_length = 200
    random.seed(1234)

    for i in range(colors_length):
        lego_colors.append((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))


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
    # 'Ye': hashtag_rgb_to_labcolor('#FFFF00'),
    "Ye": hashtag_rgb_to_labcolor("#f9d62e"),
    # 'OR': hashtag_rgb_to_labcolor('#943509'),
    "OR": hashtag_rgb_to_labcolor("#e09864"),
    "Bu": hashtag_rgb_to_labcolor("#163967"),
    # 'Rd': hashtag_rgb_to_labcolor('#680402')
    "Rd": hashtag_rgb_to_labcolor("#c4281b"),
}


def step1(r, g, b, repetitions=1):
    lum = math.sqrt(0.241 * r + 0.691 * g + 0.068 * b)

    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    h2 = int(h * repetitions)
    # lum2 = int(lum * repetitions)
    v2 = int(v * repetitions)

    return (h2, lum, v2)


def step2(r, g, b, repetitions=1):
    lum = math.sqrt(0.241 * r + 0.691 * g + 0.068 * b)

    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    h2 = int(h * repetitions)
    # lum2 = int(lum * repetitions)
    v2 = int(v * repetitions)

    if h2 % 2 == 1:
        v2 = repetitions - v2
        lum = repetitions - lum

    return (h2, lum, v2)


def write_colors(title, colors_to_write):
    fh.write("<h2>{}</h2>\n".format(title))
    fh.write("<div class='clear colors'>\n")
    for (red, green, blue) in colors_to_write:
        lab = rgb2lab((red, green, blue))
        hsv = colorsys.rgb_to_hsv(red / 255.0, green / 255.0, blue / 255.0)
        hls = colorsys.rgb_to_hls(red / 255.0, green / 255.0, blue / 255.0)

        fh.write(
            "<span class='square' style='background-color: #%02x%02x%02x;' "
            "title='RGB (%d, %d, %d)) Lab (%s, %s, %s), HSV (%s, %s, %s), HLS (%s, %s, %s)'></span>"
            % (
                red,
                green,
                blue,
                red,
                green,
                blue,
                int(lab.L),
                int(lab.a),
                int(lab.b),
                *hsv,
                *hls,
            )
        )

    fh.write("<br></div>")


def get_euclidean_lab_distance(lab1, lab2):
    """
    http://www.w3resource.com/python-exercises/math/python-math-exercise-79.php

    In mathematics, the Euclidean distance or Euclidean metric is the "ordinary"
    (i.e. straight-line) distance between two points in Euclidean space. With this
    distance, Euclidean space becomes a metric space. The associated norm is called
    the Euclidean norm.
    """
    lab1_tuple = (lab1.L, lab1.a, lab1.b)
    lab2_tuple = (lab2.L, lab2.a, lab2.b)
    return math.sqrt(sum([(a - b) ** 2 for a, b in zip(lab1_tuple, lab2_tuple)]))


def get_euclidean_distance(rgb1):
    # rgb2 = (255, 255, 255) # sort from light to dark
    rgb2 = (0, 0, 0)  # sort from dark to light
    return math.sqrt(sum([(a - b) ** 2 for a, b in zip(rgb1, rgb2)]))


def get_euclidean_distance_two_points(rgb1, rgb2):
    return math.sqrt(sum([(a - b) ** 2 for a, b in zip(rgb1, rgb2)]))


def get_vector_endpoints(length, angle_degrees, start_x=0, start_y=0):
    x = start_x + length * math.cos((math.pi * angle_degrees) / 180)
    y = start_y + length * math.sin((math.pi * angle_degrees) / 180)
    return (x, y)


def get_hsv_distance(hsv_A, hsv_B):
    """
    H is a percentage of 360 degrees as a float
    S is a percentage as a float
    V is a percentage as a float
    """
    hue_A = hsv_A[0] * 360
    saturation_A = hsv_A[1]
    value_A = hsv_A[2]

    hue_B = hsv_B[0] * 360
    saturation_B = hsv_B[1]
    value_B = hsv_B[2]

    # https://gamedev.stackexchange.com/questions/31936/3d-vector-end-point-calculation-for-procedural-vector-graphics
    (vector_A_x, vector_A_y) = get_vector_endpoints(saturation_A, hue_A)
    vector_A_z = value_A

    (vector_B_x, vector_B_y) = get_vector_endpoints(saturation_B, hue_B)
    vector_B_z = value_B

    distance = get_euclidean_distance_two_points(
        (vector_A_x, vector_A_y, vector_A_z), (vector_B_x, vector_B_y, vector_B_z)
    )
    return distance


def get_hls_distance(hls_A, hls_B):
    """
    https://www.rapidtables.com/convert/color/rgb-to-hsl.html
    H is a percentage of 360 degrees as a float
    L is a percentage as a float
    S is a percentage as a float
    """
    hue_A = hls_A[0] * 360
    lum_A = hls_A[1]
    saturation_A = hls_A[2]

    hue_B = hls_B[0] * 360
    lum_B = hls_B[1]
    saturation_B = hls_B[2]

    # https://gamedev.stackexchange.com/questions/31936/3d-vector-end-point-calculation-for-procedural-vector-graphics
    (vector_A_x, vector_A_y) = get_vector_endpoints(saturation_A, hue_A)
    vector_A_z = lum_A

    (vector_B_x, vector_B_y) = get_vector_endpoints(saturation_B, hue_B)
    vector_B_z = lum_B

    distance = get_euclidean_distance_two_points(
        (vector_A_x, vector_A_y, vector_A_z), (vector_B_x, vector_B_y, vector_B_z)
    )
    return distance


def point_avg(points):
    """
    Accepts a list of points, each with the same number of dimensions.
    NB. points can have more dimensions than 2

    Returns a new point which is the center of all the points.
    """
    dimensions = len(points[0])

    new_center = []

    for dimension in range(dimensions):
        dim_sum = 0  # dimension sum
        for p in points:
            dim_sum += p[dimension]

        # average of each dimension
        new_center.append(dim_sum / float(len(points)))

    return new_center


def update_centers(data_set, assignments):
    """
    Accepts a dataset and a list of assignments; the indexes
    of both lists correspond to each other.
    Compute the center for each of the assigned groups.
    Return `k` centers where `k` is the number of unique assignments.
    """
    new_means = defaultdict(list)
    centers = []
    for assignment, point in zip(assignments, data_set):
        new_means[assignment].append(point)

    for points in new_means.values():
        centers.append(point_avg(points))

    return centers


def assign_points(data_points, centers):
    """
    Given a data set and a list of points betweeen other points,
    assign each point to an index that corresponds to the index
    of the center point on it's proximity to that point.
    Return a an array of indexes of centers that correspond to
    an index in the data set; that is, if there are N points
    in `data_set` the list we return will have N elements. Also
    If there are Y points in `centers` there will be Y unique
    possible values within the returned list.
    """
    assignments = []
    for point in data_points:
        shortest = None  # positive infinity
        shortest_index = 0
        for i in range(len(centers)):
            val = lab_distance_cie2000(rgb2lab(point), rgb2lab(centers[i]))
            if shortest is None or val < shortest:
                shortest = val
                shortest_index = i
        assignments.append(shortest_index)
    return assignments


def distance(a, b):
    dimensions = len(a)

    _sum = 0
    for dimension in range(dimensions):
        difference_sq = (a[dimension] - b[dimension]) ** 2
        _sum += difference_sq
    return sqrt(_sum)


def generate_k(data_set, k):
    """
    Given `data_set`, which is an array of arrays,
    find the minimum and maximum for each coordinate, a range.
    Generate `k` random points between the ranges.
    Return an array of the random points within the ranges.
    """
    centers = []
    dimensions = len(data_set[0])
    min_max = defaultdict(int)

    for point in data_set:
        for i in range(dimensions):
            val = point[i]
            min_key = "min_%d" % i
            max_key = "max_%d" % i
            if min_key not in min_max or val < min_max[min_key]:
                min_max[min_key] = val
            if max_key not in min_max or val > min_max[max_key]:
                min_max[max_key] = val

    for _k in range(k):
        rand_point = []
        for i in range(dimensions):
            min_val = min_max["min_%d" % i]
            max_val = min_max["max_%d" % i]

            rand_point.append(uniform(min_val, max_val))

        centers.append(rand_point)

    return centers


def k_means(dataset, k):
    k_points = generate_k(dataset, k)
    assignments = assign_points(dataset, k_points)
    old_assignments = None
    while assignments != old_assignments:
        new_centers = update_centers(dataset, assignments)
        old_assignments = assignments
        assignments = assign_points(dataset, new_centers)
    print("assignements:\n{}\n".format(assignments))
    print("dataset:\n{}\n".format(dataset))
    # for x in zip(assignments, dataset):
    #    print(x)
    return zip(assignments, dataset)


def get_closest_cie2000_match(rgb, colors):
    (red, green, blue) = rgb
    lab = rgb2lab((red, green, blue))
    min_distance = None
    min_rgb = None

    for (x_red, x_green, x_blue) in colors:
        if x_red == red and x_green == green and x_blue == blue:
            continue

        x_lab = rgb2lab((x_red, x_green, x_blue))
        distance = lab_distance_cie2000(lab, x_lab)

        if min_distance is None or distance < min_distance:
            min_distance = distance
            min_rgb = (x_red, x_green, x_blue)

    return (min_distance, min_rgb)


def get_total_cie2000_distance(rgb_list):

    if len(rgb_list) <= 1:
        return 0

    prev_lab = rgb2lab(rgb_list[0])
    total = 0

    for rgb in rgb_list[1:]:
        lab = rgb2lab(rgb)

        total += lab_distance_cie2000(lab, prev_lab)
        prev_lab = lab

    return total


def traveling_salesman(colors, alg):

    # build a full matrix of cie2000 distances
    len_colors = len(colors)
    matrix = [[0 for i in range(len_colors)] for j in range(len_colors)]

    for x in range(len_colors):
        (x_red, x_green, x_blue) = colors[x]
        x_rgb = colors[x]
        x_lab = rgb2lab((x_red, x_green, x_blue))
        x_hsv = colorsys.rgb_to_hsv(x_red / 255.0, x_green / 255.0, x_blue / 255.0)
        x_hls = colorsys.rgb_to_hls(x_red / 255.0, x_green / 255.0, x_blue / 255.0)

        for y in range(len_colors):

            if x == y:
                matrix[x][y] = 0
                matrix[y][x] = 0
                continue

            if matrix[x][y] or matrix[y][x]:
                continue

            (y_red, y_green, y_blue) = colors[y]
            y_rgb = colors[y]

            if alg == "cie2000":
                y_lab = rgb2lab((y_red, y_green, y_blue))
                distance = lab_distance_cie2000(x_lab, y_lab)

            elif alg == "HSV":
                y_hsv = colorsys.rgb_to_hsv(y_red / 255.0, y_green / 255.0, y_blue / 255.0)
                distance = get_hsv_distance(x_hsv, y_hsv)

            elif alg == "HLS":
                y_hls = colorsys.rgb_to_hls(y_red / 255.0, y_green / 255.0, y_blue / 255.0)
                distance = get_hls_distance(x_hls, y_hls)

            elif alg == "Lab":
                y_lab = rgb2lab((y_red, y_green, y_blue))
                distance = get_euclidean_lab_distance(x_lab, y_lab)

            elif alg == "RGB":
                distance = get_euclidean_distance_two_points(x_rgb, y_rgb)

            else:
                raise Exception("Implement {}".format(alg))

            matrix[x][y] = distance
            matrix[y][x] = distance

    # path = solve_tsp(matrix, endpoints=(0, -1))
    path = solve_tsp(matrix)
    return [colors[x] for x in path]


def my_rgb_to_hls(red, green, blue):
    return colorsys.rgb_to_hls(red / 255.0, green / 255.0, blue / 255.0)


def _plot_animated_gif(color_space, x_values, y_values, z_values, colors, x_label, y_label, z_label):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_zlabel(z_label)

    # Only works for RGB right now
    for i in range(len(x_values)):
        ax.scatter(x_values[i], y_values[i], z_values[i], c=colors[i])

    for i in range(len(x_values)):
        filename = "image%03d-%s.png" % (i, color_space)
        print(filename)
        plt.plot(x_values[i : i + 2], y_values[i : i + 2], z_values[i : i + 2], "ro-")
        plt.savefig(filename, dpi=200, bbox_inches="tight")

    subprocess.check_output(
        "convert -delay 20 -loop 0 image*%s*.png image-final-%s.gif" % (color_space, color_space),
        shell=True,
    )


def _plot_show_or_save(show, desc, x_values, y_values, z_values, colors, x_label, y_label, z_label):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_zlabel(z_label)

    for i in range(len(x_values)):
        ax.scatter(x_values[i], y_values[i], z_values[i], c=colors[i])
        plt.plot(x_values[i : i + 2], y_values[i : i + 2], z_values[i : i + 2], "ro-")

    if show:
        plt.show()
    else:
        filename = f"image-{desc}.png"
        plt.savefig(filename, dpi=300, bbox_inches="tight")


def _plot_show(desc, x_values, y_values, z_values, colors, x_label, y_label, z_label):
    _plot_show_or_save(True, desc, x_values, y_values, z_values, colors, x_label, y_label, z_label)


def _plot_save(desc, x_values, y_values, z_values, colors, x_label, y_label, z_label):
    _plot_show_or_save(False, desc, x_values, y_values, z_values, colors, x_label, y_label, z_label)


def plot(plot_type, color_space, lego_colors):
    xs = []
    ys = []
    zs = []
    colors = []

    if color_space == "RGB":
        for (red, green, blue) in lego_colors:
            xs.append(red)
            ys.append(green)
            zs.append(blue)

        x_label = "Red"
        y_label = "Green"
        z_label = "Blue"

    elif color_space == "HSV":
        for (red, green, blue) in lego_colors:
            (h, s, v) = colorsys.rgb_to_hsv(red / 255.0, green / 255.0, blue / 255.0)
            h *= 360
            (x, y) = get_vector_endpoints(s, h)
            z = v

            xs.append(x)
            ys.append(y)
            zs.append(z)

        x_label = "X"
        y_label = "Y"
        z_label = "Z"

    elif color_space == "Lab":
        for (red, green, blue) in lego_colors:
            lab = rgb2lab((red, green, blue))
            xs.append(lab.L)
            ys.append(lab.a)
            zs.append(lab.b)

        x_label = "L"
        y_label = "a"
        z_label = "b"

    else:
        raise Exception(f"Implement {color_space}")

    for (red, green, blue) in lego_colors:
        colors.append("#%02x%02x%02x" % (red, green, blue))

    if plot_type == "show":
        _plot_show(color_space, xs, ys, zs, colors, x_label, y_label, z_label)
    elif plot_type == "animated-gif":
        _plot_animated_gif(color_space, xs, ys, zs, colors, x_label, y_label, z_label)
    elif plot_type == "save":
        _plot_save(color_space, xs, ys, zs, colors, x_label, y_label, z_label)
    else:
        raise Exception(f"Invalid plot_type {plot_type}")


if __name__ == "__main__":
    random.seed(1234)

    with open("foo.html", "w") as fh:
        fh.write(
            """
<!DOCTYPE html>
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
    margin: 10px;
    float: left;
}

div.col1,
div.col2,
div.col3 {
    float: left;
}

div.col4 {
    margin-left: 120px;
}
div#upper,
div#down {
    margin-left: 190px;
}

span.square {
    width: 6px;
    height: 40px;
    padding: 0px;
    margin: 0px;
    display: inline-block;
    color: black;
    font-weight: bold;
    line-height: 40px;
    text-align: center;
}

div.square {
    width: 40px;
    height: 40px;
    color: black;
    font-weight: bold;
    line-height: 40px;
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

div#anchorsquares {
    margin-left: 350px;
}

</style>
<title>Color Sorting</title>
</head>
<body>
"""
        )

        # shuffle(lego_colors)
        # print(lego_colors)
        # write_colors("Random", lego_colors)
        lego_colors_original = lego_colors[:]

        # lego_colors.sort()
        # write_colors("RGB", lego_colors)

        # CLUSTERS = 8
        # lego_colors = lego_colors_original[:]
        # lego_colors.sort(key=lambda rgb: step1(*rgb, CLUSTERS))
        # write_colors("Step1", lego_colors)

        # lego_colors = lego_colors_original[:]
        # lego_colors.sort(key=lambda rgb: step2(*rgb, CLUSTERS))
        # write_colors("Step2", lego_colors)

        lego_colors = lego_colors_original[:]
        lego_colors = traveling_salesman(lego_colors, "RGB")
        write_colors("traveling salesman - RGB", lego_colors)
        plot("save", "RGB", lego_colors)
        # plot("show", "RGB", lego_colors)
        # plot("animated-gif", "RGB", lego_colors)

        lego_colors = lego_colors_original[:]
        lego_colors.sort(key=lambda rgb: colorsys.rgb_to_hsv(*rgb))
        write_colors("HSV", lego_colors)

        lego_colors = lego_colors_original[:]
        lego_colors = traveling_salesman(lego_colors, "HSV")
        write_colors("traveling salesman - HSV", lego_colors)
        # plot("show", "HSV", lego_colors)

        lego_colors = lego_colors_original[:]
        lego_colors.sort(key=lambda rgb: my_rgb_to_hls(*rgb))
        write_colors("HLS", lego_colors)

        lego_colors = lego_colors_original[:]
        lego_colors = traveling_salesman(lego_colors, "HLS")
        write_colors("traveling salesman - HLS", lego_colors)

        lego_colors = lego_colors_original[:]
        lego_colors = traveling_salesman(lego_colors, "cie2000")
        write_colors("traveling salesman - Lab cie2000", lego_colors)
        # plot("show", "Lab", lego_colors)

        lego_colors = lego_colors_original[:]
        lego_colors = traveling_salesman(lego_colors, "Lab")
        write_colors("traveling salesman - Lab", lego_colors)
        # plot("show", "Lab", lego_colors)

        # print("{} lego colors".format(len(lego_colors)))
        fh.write(
            """
<div class='clear'></div>

</body>
</html>
"""
        )


# Was sanity checking get_vector_endpoints
"""
for (length, angle) in (
        (10, 0),
        (10, 45),
        (10, 90),
        (10, 135),
        (10, 180),
        (10, 225),
        (10, 270),
        (10, 315),
        (10, 360)):
    (x, y) = get_vector_endpoints(length, angle)
    print(f"vector ({length}, {angle}) endpoint ({x}, {y})")
"""
