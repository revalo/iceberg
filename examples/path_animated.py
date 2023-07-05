from iceberg import (
    Bounds,
    Colors,
    PathStyle,
    Drawable,
)
from iceberg.primitives import (
    Blank,
)
from iceberg.animation import animate
from iceberg.animation.scene import Scene
from iceberg.primitives.shapes import CurvedCubicLine, PartialPath


class Scene1(Scene):
    def __init__(self):
        super().__init__(duration=1.0, make_frame=self.make_frame)

    def make_frame(self, t: float) -> Drawable:
        blank = Blank(Bounds(size=(512, 512)), Colors.WHITE)
        line = CurvedCubicLine(
            [
                (10, 10),
                (256, 10),
                (256, 256),
                (256, 500),
                (500, 500),
            ],
            PathStyle(
                Colors.BLUE,
                thickness=5,
                dashed=True,
                dash_intervals=[20.0, 10.0],
                dash_phase=0.0,
            ),
        )
        partial_line = animate(
            PartialPath(line, 0, 0.01),
            PartialPath(line, 0, 1),
            t / self.duration,
        )
        scene = blank.add_centered(partial_line)

        return scene


if __name__ == "__main__":
    scene = Scene1()
    final = scene + scene.freeze(0.5) + scene.reverse()
    final.render("test.gif", fps=60)
