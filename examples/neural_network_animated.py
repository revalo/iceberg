import iceberg as ice
from neural_network import NeuralNetwork


class Scene1(ice.Scene):
    def __init__(self):
        super().__init__(duration=1.0, make_frame=self.make_frame)

    def make_frame(self, t: float) -> ice.Drawable:
        progress = t / self.duration
        layer_gap = ice.tween(50, 200, progress)
        node_vertical_gap = ice.tween(20, 50, progress)

        network = NeuralNetwork(
            [3, 4, 4, 2],
            node_border_color=ice.Colors.BLACK,
            line_path_style=ice.PathStyle(ice.Colors.BLACK, thickness=3),
            layer_gap=layer_gap,
            node_vertical_gap=node_vertical_gap,
        )
        node = network.layer_nodes[1][0]
        node.border_color = ice.Colors.RED
        node.border_thickness = 5

        canvas = ice.Blank(ice.Bounds(size=(1080, 720)), background=ice.Colors.WHITE)
        scene = canvas.add_centered(network)

        return scene


if __name__ == "__main__":
    scene = Scene1()
    final = scene + scene.freeze(0.1) + scene.reverse()
    final.render("test.gif", fps=60)
