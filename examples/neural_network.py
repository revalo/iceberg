from typing import Tuple, Sequence, Union

from absl import app
from absl import flags

from iceberg import (
    Renderer,
    Color,
    Bounds,
    Drawable,
    Colors,
    Corner,
    PathStyle,
)
from iceberg.primitives import (
    Compose,
    Ellipse,
    Line,
    Blank,
    Arrange,
)
from iceberg.primitives.layout import Transform

FLAGS = flags.FLAGS


class NeuralNetwork(Compose):
    def __init__(
        self,
        layer_node_counts: Tuple[int, ...],
        node_radius: float = 30,
        node_vertical_gap: float = 30,
        layer_gap: float = 150,
        node_border_color: Color = Colors.WHITE,
        node_fill_color: Color = None,
        node_border_thickness: float = 3,
        line_path_style: PathStyle = PathStyle(Colors.WHITE, thickness=3),
    ):
        # [layer_index, node_index]
        self._layer_nodes = [
            [
                Ellipse(
                    Bounds(
                        top=0,
                        left=0,
                        bottom=node_radius * 2,
                        right=node_radius * 2,
                    ),
                    node_border_color,
                    node_fill_color,
                    node_border_thickness,
                )
                for _ in range(layer_node_count)
            ]
            for layer_node_count in layer_node_counts
        ]

        self._node_vertical_gap = node_vertical_gap
        self._layer_gap = layer_gap
        self._line_path_style = line_path_style

        self._initialize_based_on_nodes()

    def _initialize_based_on_nodes(self):
        # Arrange the circles.
        nodes_arranged = Arrange(
            [
                Arrange(
                    circles,
                    Arrange.Direction.VERTICAL,
                    gap=self._node_vertical_gap,
                )
                for circles in self.layer_nodes
            ],
            Arrange.Direction.HORIZONTAL,
            gap=self._layer_gap,
        )

        # Draw the lines.
        self._lines = []
        for layer_a, layer_b in zip(self.layer_nodes[:-1], self.layer_nodes[1:]):
            for circle_a in layer_a:
                for circle_b in layer_b:
                    start = nodes_arranged.child_bounds(circle_a).corners[
                        Corner.MIDDLE_RIGHT
                    ]
                    end = nodes_arranged.child_bounds(circle_b).corners[
                        Corner.MIDDLE_LEFT
                    ]

                    line = Line(start, end, self._line_path_style)
                    self._lines.append(line)

        # All the children in this composition.
        children = [nodes_arranged]
        children.extend(self._lines)

        super().__init__(children)

    @property
    def layer_nodes(self) -> Sequence[Sequence[Union[Drawable, Ellipse]]]:
        return self._layer_nodes


def main(argv):
    network = NeuralNetwork(
        [3, 4, 4, 2],
        node_border_color=Colors.BLACK,
        line_path_style=PathStyle(Colors.BLACK, thickness=3),
    )
    node = network.layer_nodes[1][0]
    node.border_color = Colors.RED
    node.border_thickness = 5

    canvas = Blank(Bounds(size=(1080, 720)), background=Colors.WHITE)
    scene = canvas.center_to(network)

    Renderer(scene).save("test.png")


if __name__ == "__main__":
    app.run(main)
