# rubiks cube libraries
from rubikscolorresolver.square import Square


class Side(object):
    def __init__(self, width: int, name: str) -> None:
        self.name = name  # U, L, etc
        self.color = None
        self.squares = {}
        self.width = width
        self.squares_per_side = width * width
        self.center_squares = []
        self.edge_squares = []
        self.corner_squares = []

        # our wing_partners will be populated by RubiksColorSolverGenericBase
        self.wing_partner = {}

        if self.name == "U":
            index = 0
        elif self.name == "L":
            index = 1
        elif self.name == "F":
            index = 2
        elif self.name == "R":
            index = 3
        elif self.name == "B":
            index = 4
        elif self.name == "D":
            index = 5

        self.min_pos = (index * self.squares_per_side) + 1
        self.max_pos = (index * self.squares_per_side) + self.squares_per_side

        # If this is a cube of odd width (3x3x3) then define a mid_pos
        if self.width % 2 == 0:
            self.mid_pos = None
        else:
            self.mid_pos = int((self.min_pos + self.max_pos) / 2)

        self.corner_pos = (
            self.min_pos,
            self.min_pos + self.width - 1,
            self.max_pos - self.width + 1,
            self.max_pos,
        )
        self.edge_pos = []
        self.edge_north_pos = []
        self.edge_west_pos = []
        self.edge_south_pos = []
        self.edge_east_pos = []
        self.center_pos = []

        for position in range(self.min_pos, self.max_pos):
            if position in self.corner_pos:
                pass

            # Edges at the north
            elif position > self.corner_pos[0] and position < self.corner_pos[1]:
                self.edge_pos.append(position)
                self.edge_north_pos.append(position)

            # Edges at the south
            elif position > self.corner_pos[2] and position < self.corner_pos[3]:
                self.edge_pos.append(position)
                self.edge_south_pos.append(position)

            elif (position - 1) % self.width == 0:
                west_edge = position
                east_edge = west_edge + self.width - 1

                # Edges on the west
                self.edge_pos.append(west_edge)
                self.edge_west_pos.append(west_edge)

                # Edges on the east
                self.edge_pos.append(east_edge)
                self.edge_east_pos.append(east_edge)

                # Center squares
                for x in range(west_edge + 1, east_edge):
                    self.center_pos.append(x)

    def __str__(self) -> str:
        return "side-{}".format(self.name)

    def __repr__(self) -> str:
        return self.__str__()

    def set_square(
        self, position: int, red: int, green: int, blue: int, side_name: None = None, color_name: None = None
    ) -> None:
        self.squares[position] = Square(position, red, green, blue, side_name=side_name, color_name=color_name)

        if position in self.center_pos:
            self.center_squares.append(self.squares[position])

        elif position in self.edge_pos:
            self.edge_squares.append(self.squares[position])

        elif position in self.corner_pos:
            self.corner_squares.append(self.squares[position])

        else:
            raise Exception("Could not determine egde vs corner vs center")
