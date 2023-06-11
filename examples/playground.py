from absl import app
from absl import flags

from iceberg import Renderer, Color, Bounds
from iceberg.core.properties import Colors, Corner, FontStyle, PathStyle
from iceberg.primitives import (
    Rectangle,
    Transform,
    Padding,
    Compose,
    Grid,
    Ellipse,
    Line,
    Blank,
    Text,
)
from iceberg.primitives.layout import Align, Directions
from iceberg.primitives.shapes import BorderPosition

FLAGS = flags.FLAGS


def main(argv):
    # scene = Line(
    #     start=(0, 0),
    #     end=(0, 200),
    #     path_style=PathStyle(
    #         color=Color(1, 0, 0),
    #         thickness=5,
    #     ),
    # )
    # print(scene.bounds)

    matrix = [
        [
            Rectangle(
                rectangle=Bounds(0, 0, 100, 100),
                border_color=Color(0.2, 0.2, 1, 0.8),
                border_thickness=1,
                border_position=BorderPosition.INSIDE,
            )
            for _ in range(5)
        ]
        for _ in range(3)
    ]
    matrix = Grid(matrix, gap=10)

    _FONT_FAMILY = "IBM Plex Sans"

    canvas = Blank(Bounds(size=(1080, 720)))

    rectangle = Rectangle(
        Bounds(size=(500, 100)),
        Colors.WHITE,
        border_thickness=3,
    )
    text = Text(
        text="Hello, World!",
        font_style=FontStyle(
            family=_FONT_FAMILY,
            size=28,
            color=Colors.WHITE,
        ),
    )

    rectangle_and_text = rectangle.next_to(text, Directions.DOWN * 10)
    scene = canvas.center_to(rectangle_and_text).center_to(matrix)

    Renderer(scene).save("test.png")


if __name__ == "__main__":
    app.run(main)
