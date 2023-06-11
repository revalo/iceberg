from typing import Tuple, Sequence

from absl import app
from absl import flags

from iceberg import Renderer, Color, Bounds
from iceberg.core.drawable import Drawable
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

        stacks = [
            Grid([[c] for c in circles], gap=node_vertical_gap)
            for circles in self.layer_nodes
        ]
        nodes_composed = stacks[0]
        for stack in stacks[1:]:
            nodes_composed = nodes_composed.next_to(stack, Directions.RIGHT * layer_gap)

        # Draw lines.
        lines = []

        for layer_a, layer_b in zip(self.layer_nodes[:-1], self.layer_nodes[1:]):
            for circle_a in layer_a:
                for circle_b in layer_b:
                    start = nodes_composed.child_bounds(circle_a).corners[
                        Corner.MIDDLE_RIGHT
                    ]
                    end = nodes_composed.child_bounds(circle_b).corners[
                        Corner.MIDDLE_LEFT
                    ]

                    lines.append(Line(start, end, line_path_style))

        children = [nodes_composed]
        children.extend(lines)

        super().__init__(children)

    @property
    def layer_nodes(self) -> Sequence[Sequence[Drawable]]:
        return self._layer_nodes


def main(argv):
    network = NeuralNetwork([3, 4, 4, 2])
    canvas = Blank(Bounds(size=(1080, 720)))

    scene = canvas.center_to(network)
    Renderer(scene).save("test.png")


if __name__ == "__main__":
    app.run(main)
