from iceberg import (
    Bounds,
    Colors,
    PathStyle,
    Drawable,
)
from iceberg.primitives import (
    Blank,
)
from iceberg.animation import tween
from iceberg.animation.scene import Scene
from iceberg.primitives.shapes import CurvedCubicLine, PartialPath
from neural_network import NeuralNetwork


class Scene1(Scene):
    def __init__(self):
        super().__init__(duration=1.0, make_frame=self.make_frame)

    def make_frame(self, t: float) -> Drawable:
        progress = t / self.duration
        layer_gap = tween(50, 200, progress)
        node_vertical_gap = tween(20, 50, progress)

        network = NeuralNetwork(
            [3, 4, 4, 2],
            node_border_color=Colors.BLACK,
            line_path_style=PathStyle(Colors.BLACK, thickness=3),
            layer_gap=layer_gap,
            node_vertical_gap=node_vertical_gap,
        )
        node = network.layer_nodes[1][0]
        node.border_color = Colors.RED
        node.border_thickness = 5

        canvas = Blank(Bounds(size=(1080, 720)), background=Colors.WHITE)
        scene = canvas.add_centered(network)

        return scene


if __name__ == "__main__":
    scene = Scene1()
    final = scene + scene.freeze(0.1) + scene.reverse()
    final.render("test.gif", fps=60)
