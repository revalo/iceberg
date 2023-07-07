"""Inspired by https://www.modular.com/mojo.
"""

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
from iceberg.animation.ease import EaseType
from iceberg.animation.scene import Animated, Playbook
from iceberg.primitives import (
    Compose,
    Ellipse,
    Line,
    Blank,
    Arrange,
    Rectangle,
)
from iceberg.primitives.layout import Transform
from iceberg.primitives.shapes import PartialPath

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
                Rectangle(
                    Bounds(
                        top=0,
                        left=0,
                        bottom=node_radius * 2,
                        right=node_radius * 2,
                    ),
                    node_border_color,
                    node_fill_color,
                    node_border_thickness,
                    border_radius=20,
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

        self._layer_lines = []

        for layer_a, layer_b in zip(self.layer_nodes[:-1], self.layer_nodes[1:]):
            self._layer_lines.append([])

            for circle_b in layer_b:
                self._layer_lines[-1].append([])
                for circle_a in layer_a:
                    start = nodes_arranged.child_bounds(circle_a).corners[
                        Corner.MIDDLE_RIGHT
                    ]
                    end = nodes_arranged.child_bounds(circle_b).corners[
                        Corner.MIDDLE_LEFT
                    ]

                    line = Line(start, end, self._line_path_style)
                    self._lines.append(line)
                    self._layer_lines[-1][-1].append(line)

        # All the children in this composition.
        # Nodes are drawn on top of lines.
        children = self._lines.copy()
        children.append(nodes_arranged)

        super().__init__(children)

    @property
    def layer_nodes(self) -> Sequence[Sequence[Union[Drawable, Ellipse]]]:
        return self._layer_nodes


class Play(Playbook):
    def timeline(self):
        _GREY = Color.from_hex("#151e25")
        _LIGHT_GREY = Color.from_hex("#585f63")
        _LINE_GREY = Color.from_hex("#2c3134")
        _LASER_COLOR = Color.from_hex("#959fcc")

        background = Blank(Bounds(size=(1920, 1080)), Colors.TRANSPARENT)
        network = NeuralNetwork(
            (3, 4, 4, 3),
            node_radius=70,
            layer_gap=300,
            node_vertical_gap=50,
            node_fill_color=_GREY,
            node_border_color=_LIGHT_GREY,
            node_border_thickness=5,
            line_path_style=PathStyle(_LINE_GREY, thickness=3),
        )

        for layer in network._layer_lines:
            for phase in range(2):
                if phase == 0:
                    starts = (0, 0)
                    ends = (0, 1)
                else:
                    starts = (0, 1)
                    ends = (1, 1)

                animated_lasers = []
                for node_index, node in enumerate(layer):
                    for line_index, line in enumerate(node):
                        laser = Line(
                            line.start,
                            line.end,
                            PathStyle(_LASER_COLOR, thickness=3),
                        )
                        laser_animated = Animated(
                            [PartialPath(laser, *starts), PartialPath(laser, *ends)],
                            0.5,
                            start_time=0.1 * node_index + 0.2 * line_index,
                            ease_types=EaseType.EASE_OUT_CUBIC,
                        )
                        animated_lasers.append(laser_animated)
                animated_network = Compose([network, *animated_lasers])
                scene = background.add_centered(animated_network)
                self.play(scene)


def main(argv):
    Play().combined_scene.render("test.mp4")


if __name__ == "__main__":
    app.run(main)
