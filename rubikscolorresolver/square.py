# rubiks cube libraries
from rubikscolorresolver.color import rgb2lab


class Square(object):
    def __init__(
        self,
        position: int,
        red: int,
        green: int,
        blue: int,
        side_name: None = None,
        color_name: None = None,
        via_color_box: bool = False,
    ) -> None:
        assert position is None or isinstance(position, int)
        assert isinstance(red, int)
        assert isinstance(green, int)
        assert isinstance(blue, int)
        assert side_name is None or isinstance(side_name, str)
        assert color_name is None or isinstance(color_name, str)

        if side_name is not None:
            assert side_name in ("U", "L", "F", "R", "B", "D")

        if color_name is not None:
            assert color_name in ("Wh", "Ye", "OR", "Rd", "Gr", "Bu")

        self.position = position
        self.lab = rgb2lab((red, green, blue))
        self.side_name = side_name  # ULFRBD
        self.color_name = color_name
        self.via_color_box = via_color_box

    def __str__(self) -> str:
        return "{}{}-{}".format(self.side_name, self.position, self.color_name)

    def __repr__(self) -> str:
        return self.__str__()

    def __lt__(self, other) -> bool:
        return self.position < other.position
