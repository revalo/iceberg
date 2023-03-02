from absl import app
from absl import flags

from iceberg import Renderer, Color, Bounds
from iceberg.primitives import Rectangle, Transform, Padding, Compose, Grid
from iceberg.primitives.rectangle import BorderPosition

FLAGS = flags.FLAGS


def main(argv):
    grid_size_x = 5
    grid_size_y = 3

    # items = []

    # for x in range(grid_size_x):
    #     for y in range(grid_size_y):
    #         rect = Rectangle(
    #             rectangle=Bounds(0, 0, 100, 100),
    #             border_color=Color(1, 0, 1, 1),
    #             fill_color=Color(1, 1, 0, 1),
    #             border_thickness=10,
    #             border_position=BorderPosition.INSIDE,
    #         )

    #         items.append(rect)

    matrix = [
        [
            Rectangle(
                rectangle=Bounds(0, 0, 100, 100),
                border_color=Color(1, 0, 1, 1),
                fill_color=Color(1, 1, 0, 1),
                border_thickness=10,
                border_position=BorderPosition.INSIDE,
            )
            for _ in range(grid_size_x)
        ]
        for _ in range(grid_size_y)
    ]

    scene = Grid(matrix, gap=20)

    # rect = Rectangle(
    #     rectangle=Bounds(0, 0, 100, 100),
    #     border_color=Color(1, 0, 1, 1),
    #     fill_color=Color(1, 1, 0, 1),
    #     border_thickness=10,
    # )

    # rect = Padding(
    #     child=rect,
    #     padding=20,
    # )

    # items = [rect]
    Renderer(scene).save("test.png")


if __name__ == "__main__":
    app.run(main)
