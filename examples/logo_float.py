from iceberg import (
    Bounds,
    Colors,
    PathStyle,
    Drawable,
)
from iceberg.primitives import (
    Blank,
    Image,
    Anchor,
)
from iceberg.animation import tween
from iceberg.animation.scene import Scene
from iceberg.primitives.shapes import CurvedCubicLine, PartialPath

import os


class Scene1(Scene):
    def __init__(self):
        super().__init__(duration=1.0, make_frame=self.make_frame)

    def make_frame(self, t: float) -> Drawable:
        progress = t / self.duration

        logo = Image(os.path.join("images", "logo.png"))
        blank = Blank(logo.bounds, Colors.TRANSPARENT)

        dy = tween(-10, 10, progress)

        scene = Anchor([blank, logo.move(0, dy)])

        return scene


if __name__ == "__main__":
    scene = Scene1()
    final = scene + scene.freeze(0.1) + scene.reverse()
    final.render("test.gif", fps=60)
