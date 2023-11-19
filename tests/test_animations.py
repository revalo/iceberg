import iceberg as ice
from .scene_tester import check_animation
from .test_neural_net import NeuralNetwork

import os


def test_logo_float():
    class Anim(ice.Scene):
        def __init__(self):
            super().__init__(duration=1.0, make_frame=self.make_frame)

        def make_frame(self, t: float) -> ice.Drawable:
            progress = t / self.duration

            logo = ice.Image(os.path.join("tests", "testdata", "logo.png"))
            blank = ice.Blank(logo.bounds, ice.Colors.TRANSPARENT)

            dy = ice.tween(-10, 10, progress)

            scene = ice.Anchor([blank, logo.move(0, dy)])

            return scene

    check_animation(Anim(), "logo_float")


def test_nn_animated():
    class Anim(ice.Scene):
        def __init__(self):
            super().__init__(duration=1.0, make_frame=self.make_frame)

        def make_frame(self, t: float) -> ice.Drawable:
            progress = t / self.duration
            layer_gap = ice.tween(50, 200, progress)
            node_vertical_gap = ice.tween(20, 50, progress)

            network = NeuralNetwork(
                layer_node_counts=[3, 4, 4, 2],
                node_border_color=ice.Colors.BLACK,
                line_path_style=ice.PathStyle(ice.Colors.BLACK, thickness=3),
                layer_gap=layer_gap,
                node_vertical_gap=node_vertical_gap,
            )
            node = network.layer_nodes[1][0]
            node.border_color = ice.Colors.RED
            node.border_thickness = 5
            node.setup()

            canvas = ice.Blank(
                ice.Bounds(size=(1080, 720)), background_color=ice.Colors.WHITE
            )
            scene = canvas.add_centered(network)

            return scene

    check_animation(Anim(), "nn_animated")


def test_nn_compute():
    from typing import Tuple, Sequence, Union

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
                    ice.Rectangle(
                        ice.Bounds(
                            top=0,
                            left=0,
                            bottom=self.node_radius * 2,
                            right=self.node_radius * 2,
                        ),
                        self.node_border_color,
                        self.node_fill_color,
                        self.node_border_thickness,
                        border_radius=20,
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

            self._layer_lines = []

            for layer_a, layer_b in zip(self.layer_nodes[:-1], self.layer_nodes[1:]):
                self._layer_lines.append([])

                for circle_b in layer_b:
                    self._layer_lines[-1].append([])
                    for circle_a in layer_a:
                        start = nodes_arranged.child_bounds(circle_a).corners[
                            ice.Corner.MIDDLE_RIGHT
                        ]
                        end = nodes_arranged.child_bounds(circle_b).corners[
                            ice.Corner.MIDDLE_LEFT
                        ]

                        line = ice.Line(start, end, self._line_path_style)
                        self._lines.append(line)
                        self._layer_lines[-1][-1].append(line)

            # All the children in this composition.
            # Nodes are drawn on top of lines.
            children = self._lines.copy()
            children.append(nodes_arranged)

            self.set_child(ice.Compose(children))

        @property
        def layer_nodes(self) -> Sequence[Sequence[Union[ice.Drawable, ice.Ellipse]]]:
            return self._layer_nodes

    class Anim(ice.Playbook):
        def timeline(self):
            _GREY = ice.Color.from_hex("#151e25")
            _LIGHT_GREY = ice.Color.from_hex("#585f63")
            _LINE_GREY = ice.Color.from_hex("#2c3134")
            _LASER_COLOR = ice.Color.from_hex("#959fcc")

            background = ice.Blank(
                ice.Bounds(size=(1920, 1080)), ice.Color.from_hex("#0d1117")
            )
            network = NeuralNetwork(
                layer_node_counts=(3, 4, 4, 3),
                node_radius=70,
                layer_gap=300,
                node_vertical_gap=50,
                node_fill_color=_GREY,
                node_border_color=_LIGHT_GREY,
                node_border_thickness=5,
                line_path_style=ice.PathStyle(_LINE_GREY, thickness=3),
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
                            laser = ice.Line(
                                line.start,
                                line.end,
                                ice.PathStyle(_LASER_COLOR, thickness=3),
                            )
                            laser_animated = ice.Animated(
                                [
                                    ice.PartialPath(laser, *starts),
                                    ice.PartialPath(laser, *ends),
                                ],
                                0.5,
                                start_time=0.1 * node_index + 0.2 * line_index,
                                ease_types=ice.EaseType.EASE_OUT_CUBIC,
                            )
                            animated_lasers.append(laser_animated)
                    animated_network = ice.Compose([network, *animated_lasers])
                    scene = background.add_centered(animated_network).scale(0.5)
                    self.play(scene)

    check_animation(Anim().combined_scene, "nn_compute")


def test_animation_within_animation():
    class Anim(ice.Playbook):
        def timeline(self):
            background = ice.Blank(ice.Bounds.from_size(256, 256), ice.Colors.WHITE)
            square = ice.Rectangle(
                ice.Bounds.from_size(128, 128),
                ice.Colors.BLACK,
                border_thickness=2,
                dont_modify_bounds=True,
            )
            point = ice.Ellipse(
                rectangle=ice.Bounds.from_size(32, 32),
                fill_color=ice.Colors.RED.with_alpha(1),
            )

            scene = square
            with square:
                for corner_i, corner in enumerate(
                    [
                        ice.Corner.TOP_LEFT,
                        ice.Corner.TOP_RIGHT,
                        ice.Corner.BOTTOM_LEFT,
                        ice.Corner.BOTTOM_RIGHT,
                    ]
                ):
                    current_point = point.move_to(
                        *square.relative_bounds.corners[corner],
                        corner=ice.Corner.CENTER
                    )
                    st = corner_i * 0.1 + 0.1
                    point_anim = ice.Animated(
                        [
                            current_point.scale(0.1),
                            current_point.scale(1.1),
                            current_point.scale(1),
                        ],
                        durations=[0.4, 0.1],
                        start_time=st,
                    )

                    scene = scene + point_anim

            tex = ice.MathTex("x^2 + y^2 = 1").scale(1.7)
            scene = scene.add_centered(tex)

            square = scene.move(100, 20)

            square = ice.Animated(
                [
                    square.scale(0.1),
                    square.scale(1.1),
                    square.scale(1),
                    square.scale(1),
                ],
                durations=[0.4, 0.2, 1],
            )

            self.play(background + square)

    check_animation(Anim().combined_scene, "animation_within_animation")
