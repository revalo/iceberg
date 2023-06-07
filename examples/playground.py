from absl import app
from absl import flags

from iceberg import Renderer, Color, Bounds
from iceberg.core.properties import PathStyle
from iceberg.primitives import (
    Rectangle,
    Transform,
    Padding,
    Compose,
    Grid,
    Ellipse,
    Line,
)
from iceberg.primitives.shapes import BorderPosition

FLAGS = flags.FLAGS


def main(argv):
    scene = Line(
        start=(0, 0),
        end=(0, 200),
        path_style=PathStyle(
            color=Color(1, 0, 0),
            thickness=5,
        ),
    )
    print(scene.bounds)

    # matrix = [
    #     [
    #         Rectangle(
    #             rectangle=Bounds(0, 0, 100, 100),
    #             border_color=Color(1, 1, 1, 1),
    #             border_thickness=1,
    #             border_position=BorderPosition.INSIDE,
    #         )
    #         for _ in range(5)
    #     ]
    #     for _ in range(3)
    # ]
    # scene = Grid(matrix, gap=10)

    Renderer(scene).save("test.png")


if __name__ == "__main__":
    app.run(main)
