#!/usr/bin/env python3

"""
Experiment with the algorithms from:
http://www.alanzucconi.com/2015/09/30/colour-sorting/

Against Rubiks cube RGB values
I skipped hilbert, that one was more trouble than it was worth
"""

from rubikscolorresolver import k_means_colors_dictionary
from sklearn.cluster import KMeans
from copy import deepcopy
from scipy.spatial import distance
import numpy as np
import colorsys
import json
import logging
import math
import sys


def convert_key_strings_to_int(data):
    """
    Convert keys that are strings of integers to integers
    """
    result = {}
    for (key, value) in data.items():

        if isinstance(value, list):
            value = tuple(value)

        if key.isdigit():
            result[int(key)] = value
        else:
            result[key] = value
    return result


def write_header(fh):
    fh.write(
        """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
div.clear {
    clear: both;
}

div.colors span {
    width: 40px;
    height: 40px;
    white-space-collapsing: discard;
    display: inline-block;
}
</style>
<title>Python Color Sorter</title>
</head>
<body>
"""
    )


def write_colors(fh, algorithm, colors):
    # squares_per_side = int(len(colors) / 6)
    fh.write("<h2>%s</h2>\n" % algorithm)
    fh.write("<div class='clear colors'>\n")
    for (index, (red, green, blue)) in enumerate(colors):

        if red is None and green is None and blue is None:
            fh.write("<br>")
            continue

        # to use python coloursys convertion we have to rescale to range 0-1
        (H, S, V) = colorsys.rgb_to_hsv(
            float(red / 255), float(green / 255), float(blue / 255)
        )

        # rescale H to 360 degrees and S, V to percent of 100%
        H = int(H * 360)
        S = int(S * 100)
        V = int(V * 100)
        # log.info("%3d: RGB (%3d, %3d, %3d) -> HSV (%3d, %3d, %3d)" % (index+1, red, green, blue, H, S, V))
        fh.write(
            "<span style='background-color:#%02x%02x%02x' title='RGB (%s, %s, %s), HSV (%s, %s, %s)'>&nbsp;</span>\n"
            % (red, green, blue, red, green, blue, H, S, V)
        )
        # if (index+1) % squares_per_side == 0:
        #    log.info('')

    fh.write("</div>\n")
    log.info("\n\n")


def write_footer(fh):
    fh.write("</body>\n")
    fh.write("</html>\n")


def lum(r, g, b):
    return math.sqrt(0.241 * r + 0.691 * g + 0.068 * b)


def step(r, g, b, repetitions=1):
    lum = math.sqrt(0.241 * r + 0.691 * g + 0.068 * b)

    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    h2 = int(h * repetitions)
    # lum2 = int(lum * repetitions)
    v2 = int(v * repetitions)

    return (h2, lum, v2)


def NN(A, start):
    """
    http://stackoverflow.com/questions/17493494/nearest-neighbour-algorithm

    NEAREST NEIGHBOUR ALGORITHM
    ---------------------------
    The algorithm takes two arguments. The first one is an array, with elements
    being lists/column-vectors from the given complete incidensmatrix. The second
    argument is an integer which represents the startingnode where 1 is the
    smallest. The program will only make sense, if the triangle inequality is satisfied.
    Furthermore, diagonal elements needs to be inf. The pseudocode is listed below:


    1. - stand on an arbitrary vertex as current vertex.
    2. - find out the shortest edge connecting current vertex and an unvisited vertex V.
    3. - set current vertex to V.
    4. - mark V as visited.
    5. - if all the vertices in domain are visited, then terminate.
    6. - Go to step 2.

    The sequence of the visited vertices is the output of the algorithm

    Remark - infinity is entered as np.inf
    """

    start = start - 1  # To compensate for the python index starting at 0.
    n = len(A)
    path = [start]
    costList = []
    tmp = deepcopy(start)
    B = deepcopy(A)

    # This block eliminates the startingnode, by setting it equal to inf.
    for h in range(n):
        B[h][start] = np.inf

    for i in range(n):

        # This block appends the visited nodes to the path, and appends
        # the cost of the path.
        for j in range(n):
            if B[tmp][j] == min(B[tmp]):
                costList.append(B[tmp][j])
                path.append(j)
                tmp = j
                break

        # This block sets the current node to inf, so it can't be visited again.
        for k in range(n):
            B[k][tmp] = np.inf

    # The last term adds the weight of the edge connecting the start - and endnote.
    # cost = sum([i for i in costList if i < np.inf]) + A[path[len(path) - 2]][start]

    # The last element needs to be popped, because it is equal to inf.
    path.pop(n)

    # Because we want to return to start, we append this node as the last element.
    path.insert(n, start)

    # Prints the path with original indicies.
    path = [i + 1 for i in path]

    # print "The path is: ", path
    # print "The cost is: ", cost
    return path


def travelling_salesman(colors):
    colors_length = len(colors)

    # Distance matrix
    A = np.zeros([colors_length, colors_length])
    for x in range(0, colors_length - 1):
        for y in range(0, colors_length - 1):
            A[x, y] = distance.euclidean(colors[x], colors[y])

    # Nearest neighbour algorithm
    path = NN(A, 0)

    # Final array
    colors_nn = []
    for i in path:
        colors_nn.append(colors[i])

    return colors_nn


if __name__ == "__main__":

    # logging.basicConfig(filename='rubiks.log',
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(filename)12s %(levelname)8s: %(message)s",
    )
    log = logging.getLogger(__name__)

    filename = sys.argv[1]

    with open(filename, "r") as fh:
        data = convert_key_strings_to_int(json.load(fh))
        # pprint(data)

    colors = sorted(list(data.values()))

    with open("foo.html", "w") as fh:
        write_header(fh)
        # for algorithm in ('none', 'rgb', 'hsv', 'hls', 'luminosity', 'step', 'travelling-salesman'):
        # for algorithm in ('none', 'hsv', 'step', 'kmeans'):
        # for algorithm in ('none', 'hsv', 'kmeans'):
        for algorithm in ("kmeans", "kmeans2"):

            if algorithm == "none":
                tmp_colors = colors

            elif algorithm == "rgb":
                tmp_colors = sorted(colors)

            elif algorithm == "hsv":
                tmp_colors = deepcopy(colors)
                tmp_colors.sort(key=lambda rgb: colorsys.rgb_to_hsv(*rgb))

            elif algorithm == "hls":
                tmp_colors = deepcopy(colors)
                tmp_colors.sort(key=lambda rgb: colorsys.rgb_to_hls(*rgb))

            elif algorithm == "luminosity":
                tmp_colors = deepcopy(colors)
                tmp_colors.sort(key=lambda rgb: lum(*rgb))

            elif algorithm == "step":
                tmp_colors = deepcopy(colors)
                tmp_colors.sort(key=lambda rgb: step(*rgb, 6))

            elif algorithm == "travelling-salesman":
                tmp_colors = travelling_salesman(deepcopy(colors))

            elif algorithm == "kmeans":
                # http://www.pyimagesearch.com/2014/05/26/opencv-python-k-means-color-clustering/
                clt = KMeans(n_clusters=6)
                clt.fit(deepcopy(colors))

                tmp_colors = []
                for target_cluster in range(6):
                    for (index, cluster) in enumerate(clt.labels_):
                        if cluster == target_cluster:
                            tmp_colors.append(colors[index])
                    tmp_colors.append((None, None, None))

            elif algorithm == "kmeans2":
                tmp_colors = []
                # for rgb_list in k_means_colors_dictionary(deepcopy(data), (13, 38, 63, 88, 113, 138)):
                for rgb_list in k_means_colors_dictionary(
                    deepcopy(data), (31, 42, 73, 108, 139, 186)
                ):
                    for rgb in rgb_list:
                        tmp_colors.append(rgb)
                    tmp_colors.append((None, None, None))

            else:
                log.warning("Implement %s" % algorithm)
                continue

            write_colors(fh, algorithm, tmp_colors)

        write_footer(fh)
