# standard libraries
import sys
from math import ceil

# rubiks cube libraries
from rubikscolorresolver.side import Side


class RubiksCube:
    def __init__(self, width: int) -> None:
        self.width = width
        self.squares_per_side = self.width * self.width
        self.orbits = int(ceil((self.width - 2) / 2.0))
        self.write_debug_file = False

        self.sides = {
            "U": Side(self.width, "U"),
            "L": Side(self.width, "L"),
            "F": Side(self.width, "F"),
            "R": Side(self.width, "R"),
            "B": Side(self.width, "B"),
            "D": Side(self.width, "D"),
        }

        self.sideU = self.sides["U"]
        self.sideL = self.sides["L"]
        self.sideF = self.sides["F"]
        self.sideR = self.sides["R"]
        self.sideB = self.sides["B"]
        self.sideD = self.sides["D"]
        self.side_order = ("U", "L", "F", "R", "B", "D")
        self.pos2side = {}
        self.pos2square = {}
        all_edge_positions = []

        # U and B
        for (pos1, pos2) in zip(self.sideU.edge_north_pos, reversed(self.sideB.edge_north_pos)):
            all_edge_positions.append((pos1, pos2))

        # U and L
        for (pos1, pos2) in zip(self.sideU.edge_west_pos, self.sideL.edge_north_pos):
            all_edge_positions.append((pos1, pos2))

        # U and F
        for (pos1, pos2) in zip(self.sideU.edge_south_pos, self.sideF.edge_north_pos):
            all_edge_positions.append((pos1, pos2))

        # U and R
        for (pos1, pos2) in zip(self.sideU.edge_east_pos, reversed(self.sideR.edge_north_pos)):
            all_edge_positions.append((pos1, pos2))

        # F and L
        for (pos1, pos2) in zip(self.sideF.edge_west_pos, self.sideL.edge_east_pos):
            all_edge_positions.append((pos1, pos2))

        # F and R
        for (pos1, pos2) in zip(self.sideF.edge_east_pos, self.sideR.edge_west_pos):
            all_edge_positions.append((pos1, pos2))

        # F and D
        for (pos1, pos2) in zip(self.sideF.edge_south_pos, self.sideD.edge_north_pos):
            all_edge_positions.append((pos1, pos2))

        # L and B
        for (pos1, pos2) in zip(self.sideL.edge_west_pos, self.sideB.edge_east_pos):
            all_edge_positions.append((pos1, pos2))

        # L and D
        for (pos1, pos2) in zip(self.sideL.edge_south_pos, reversed(self.sideD.edge_west_pos)):
            all_edge_positions.append((pos1, pos2))

        # R and D
        for (pos1, pos2) in zip(self.sideR.edge_south_pos, self.sideD.edge_east_pos):
            all_edge_positions.append((pos1, pos2))

        # R and B
        for (pos1, pos2) in zip(self.sideR.edge_east_pos, self.sideB.edge_west_pos):
            all_edge_positions.append((pos1, pos2))

        # B and D
        for (pos1, pos2) in zip(reversed(self.sideB.edge_south_pos), self.sideD.edge_south_pos):
            all_edge_positions.append((pos1, pos2))

        for side in self.sides.values():
            for (pos1, pos2) in all_edge_positions:
                if pos1 >= side.min_pos and pos1 <= side.max_pos:
                    side.wing_partner[pos1] = pos2
                elif pos2 >= side.min_pos and pos2 <= side.max_pos:
                    side.wing_partner[pos2] = pos1

        self.calculate_pos2side()

    def calculate_pos2side(self) -> None:
        for side in self.sides.values():
            for x in range(side.min_pos, side.max_pos + 1):
                self.pos2side[x] = side

    def calculate_pos2square(self) -> None:
        for side in self.sides.values():
            for (position, square) in side.squares.items():
                self.pos2square[position] = square

    def print_cube(self) -> None:
        data = []
        for x in range(3 * self.width):
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
                    color_name = side.squares[side.min_pos + (y * self.width) + x].color_name
                    color_code = color_codes.get(color_name)

                    if color_name is None:
                        color_code = 97
                        data[line_number].append("\033[%dmFo\033[0m" % color_code)
                    else:
                        data[line_number].append("\033[%dm%s\033[0m" % (color_code, color_name))
                line_number += 1

        output = []
        for row in data:
            output.append(" ".join(row))

        sys.stderr.write("Cube\n\n%s\n" % "\n".join(output))

    def cube_for_kociemba_strict(self):
        data = []

        for side in (
            self.sideU,
            self.sideR,
            self.sideF,
            self.sideD,
            self.sideL,
            self.sideB,
        ):
            for x in range(side.min_pos, side.max_pos + 1):
                square = side.squares[x]
                data.append(square.side_name)

        return data

    def is_even(self) -> bool:
        return bool(self.width % 2 == 0)

    def is_odd(self) -> bool:
        return not self.is_even()
