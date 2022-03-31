"""
Full credit to this code from:
https://github.com/dmishin/tsp-solver/blob/master/tsp_solver/greedy.py
"""

# standard libraries
from array import array as pyarray

try:
    # standard libraries
    from typing import List, Tuple
except ImportError:
    # this will barf for micropython...ignore it
    pass


def optimize_solution(distances, connections, endpoints) -> Tuple:
    """
    Tries to optimize solution, found by the greedy algorithm
    """
    N = len(connections)
    path = restore_path(connections, endpoints)

    def ds(i, j):  # distance between ith and jth points of path
        pi = path[i]
        pj = path[j]

        if pi < pj:
            return distances[pj][pi]
        else:
            return distances[pi][pj]

    d_total = 0.0
    optimizations = 0

    for a in range(N - 1):
        b = a + 1

        for c in range(b + 2, N - 1):
            d = c + 1
            delta_d = ds(a, b) + ds(c, d) - (ds(a, c) + ds(b, d))

            if delta_d > 0:
                d_total += delta_d
                optimizations += 1
                connections[path[a]].remove(path[b])
                connections[path[a]].append(path[c])
                connections[path[b]].remove(path[a])
                connections[path[b]].append(path[d])

                connections[path[c]].remove(path[d])
                connections[path[c]].append(path[a])
                connections[path[d]].remove(path[c])
                connections[path[d]].append(path[b])
                path[:] = restore_path(connections, endpoints)

    return (optimizations, d_total)


def restore_path(connections: List[List[int]], endpoints: Tuple[int, int]) -> List[int]:
    """
    Takes array of connections and returns a path.
    Connections is array of lists with 1 or 2 elements.
    These elements are indices of teh vertices, connected to this vertex
    Guarantees that first index < last index
    """
    if endpoints is None:
        # there are 2 nodes with valency 1 - start and end. Get them.
        (start, end) = [idx for idx, conn in enumerate(connections) if len(conn) == 1]
    else:
        (start, end) = endpoints

    path = [start]
    prev_point = None
    cur_point = start

    while True:
        next_points = [pnt for pnt in connections[cur_point] if pnt != prev_point]

        if not next_points:
            break

        next_point = next_points[0]
        path.append(next_point)
        (prev_point, cur_point) = (cur_point, next_point)

    return path


def pairs_by_dist(N: int, distances) -> Tuple[Tuple[int, int]]:
    """
    returns list of coordinate pairs (i,j), sorted by distances; such that i < j
    """

    # sort coordinate pairs by distance
    indices = []

    for i in range(N):
        for j in range(i):
            indices.append(i * N + j)

    indices.sort(key=lambda ij: distances[ij // N][ij % N])
    return ((ij // N, ij % N) for ij in indices)


def calc_path_cost(distances, path) -> float:
    """
    Calculate the total for each row (if there are 24 squares, 6 sides of a cube then
    there are 4 squares per row) and total all of those together. We do this because
    we do not care about the cost from square at the end of one row to the square at
    the start of the next row.
    """
    cost = 0
    row_cost = 0
    prev_x = None
    ROW_SIZE = len(path) / 6

    for (index, x) in enumerate(path):
        if prev_x is not None:

            if (index + 1) % ROW_SIZE == 0:
                row_cost += distances[prev_x][x]
                cost += row_cost
                row_cost = 0

            elif (index + 1) % (ROW_SIZE + 1) == 0:
                pass

            else:
                row_cost += distances[prev_x][x]

        prev_x = x

    return cost


def solve_tsp(distances, optim_steps: int = 0, endpoints: Tuple[int, int] = None) -> List[int]:
    """
    Given a distance matrix, finds a solution for the TSP problem.
    Returns list of vertex indices.
    Guarantees that the first index is lower than the last

    :arg: distances : left-triangular matrix of distances. array of arrays
    :arg: optim_steps (int) number of additional optimization steps, allows to improve solution but costly.
    :arg: pairs_by_dist (function) an implementtion of the pairs_by_dist function. for optimization purposes.
    :arg: endpoinds : None or pair (int,int)
    """
    N = len(distances)

    if N == 0:
        return []

    if N == 1:
        return [0]

    if N == 2:
        return [0, 1]

    # State of the TSP solver algorithm.
    node_valency = pyarray("i", [2] * N)  # Initially, each node has 2 sticky ends

    if endpoints is not None:
        start, end = endpoints

        if start == end:
            raise ValueError("start=end is not supported")

        node_valency[start] = 1
        node_valency[end] = 1

    # for each node, stores 1 or 2 connected nodes
    connections = [[] for i in range(N)]

    def join_segments(sorted_pairs):
        # segments of nodes. Initially, each segment contains only 1 node
        segments = [[i] for i in range(N)]

        def possible_edges():
            # Generate sequence of graph edges, that are possible and connect different segments.
            for ij in sorted_pairs:
                (i, j) = ij

                # if both start and end could have connections and both nodes connect to a different segments
                if node_valency[i] and node_valency[j] and (segments[i] is not segments[j]):
                    yield ij

        def connect_vertices(i, j):
            node_valency[i] -= 1
            node_valency[j] -= 1
            connections[i].append(j)
            connections[j].append(i)

            # Merge segment J into segment I.
            seg_i = segments[i]
            seg_j = segments[j]

            if len(seg_j) > len(seg_i):
                (seg_i, seg_j) = (seg_j, seg_i)
                (i, j) = (j, i)

            for node_idx in seg_j:
                segments[node_idx] = seg_i

            seg_i.extend(seg_j)

        def edge_connects_endpoint_segments(i, j):
            # return True, if given ede merges 2 segments that have endpoints in them
            (si, sj) = (segments[i], segments[j])
            (ss, se) = (segments[start], segments[end])
            return (si is ss) and (sj is se) or (sj is ss) and (si is se)

        # Take first N-1 possible edge. they are already sorted by distance
        edges_left = N - 1

        for (i, j) in possible_edges():
            if endpoints and edges_left != 1 and edge_connects_endpoint_segments(i, j):
                continue  # don't allow premature path termination

            connect_vertices(i, j)
            edges_left -= 1

            if edges_left == 0:
                break

    # invoke main greedy algorithm
    join_segments(pairs_by_dist(N, distances))

    # now call additional optiomization procedure.
    for passn in range(optim_steps):
        (nopt, dtotal) = optimize_solution(distances, connections, endpoints)

        if nopt == 0:
            break

    # restore path from the connections map (graph) and return it
    return restore_path(connections, endpoints=endpoints)
