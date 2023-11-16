from typing import Tuple, Sequence, Union

from absl import app
from absl import flags

import iceberg as ice

FLAGS = flags.FLAGS


class NeuralNetwork(ice.DrawableWithChild):
    layer_node_counts: Tuple[int, ...]
    node_radius: float = 30
    node_vertical_gap: float = 30
    layer_gap: float = 150
    node_border_color: ice.Color = ice.Colors.WHITE
    node_fill_color: ice.Color = None
    node_border_thickness: float = 3
    line_path_style: ice.PathStyle = ice.PathStyle(ice.Colors.WHITE, thickness=3)

    def setup(self):
        # [layer_index, node_index]
        self._layer_nodes = [
            [
                ice.Ellipse(
                    rectangle=ice.Bounds(
                        top=0,
                        left=0,
                        bottom=self.node_radius * 2,
                        right=self.node_radius * 2,
                    ),
                    border_color=self.node_border_color,
                    fill_color=self.node_fill_color,
                    border_thickness=self.node_border_thickness,
                )
                for _ in range(layer_node_count)
            ]
            for layer_node_count in self.layer_node_counts
        ]

        self._node_vertical_gap = self.node_vertical_gap
        self._layer_gap = self.layer_gap
        self._line_path_style = self.line_path_style

        self._initialize_based_on_nodes()

    def _initialize_based_on_nodes(self):
        # Arrange the circles.
        nodes_arranged = ice.Arrange(
            [
                ice.Arrange(
                    circles,
                    arrange_direction=ice.Arrange.Direction.VERTICAL,
                    gap=self._node_vertical_gap,
                )
                for circles in self.layer_nodes
            ],
            arrange_direction=ice.Arrange.Direction.HORIZONTAL,
            gap=self._layer_gap,
        )

        # Draw the lines.
        self._lines = []
        for layer_a, layer_b in zip(self.layer_nodes[:-1], self.layer_nodes[1:]):
            for circle_a in layer_a:
                for circle_b in layer_b:
                    start = nodes_arranged.child_bounds(circle_a).corners[
                        ice.Corner.MIDDLE_RIGHT
                    ]
                    end = nodes_arranged.child_bounds(circle_b).corners[
                        ice.Corner.MIDDLE_LEFT
                    ]

                    line = ice.Line(start, end, self._line_path_style)
                    self._lines.append(line)

        # All the children in this composition.
        # Nodes are drawn on top of lines.
        children = self._lines
        children.append(nodes_arranged)

        self.set_child(ice.Compose(children))

    @property
    def layer_nodes(self) -> Sequence[Sequence[Union[ice.Drawable, ice.Ellipse]]]:
        return self._layer_nodes


def main(argv):
    network = NeuralNetwork(
        layer_node_counts=[3, 4, 4, 2],
        node_border_color=ice.Colors.BLACK,
        line_path_style=ice.PathStyle(ice.Colors.BLACK, thickness=3),
    )
    node = network.layer_nodes[1][0]
    node.border_color = ice.Colors.RED
    node.border_thickness = 5
    node.setup()

    canvas = ice.Blank(ice.Bounds(size=(1080, 720)), background_color=ice.Colors.WHITE)
    scene = canvas.add_centered(network)

    renderer = ice.Renderer()
    renderer.render(scene)
    renderer.save_rendered_image("test.png")


if __name__ == "__main__":
    app.run(main)
