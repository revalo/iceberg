from iceberg import (
    Bounds,
    Colors,
    Drawable,
)
from iceberg.primitives import (
    Rectangle,
    Compose,
    Blank,
)
from iceberg.animation import tween
from iceberg.animation.scene import Scene
from iceberg.arrows import Arrow, LabelArrow


class Scene1(Scene):
    def __init__(self):
        super().__init__(duration=1.0, make_frame=self.make_frame)

    def make_frame(self, t: float) -> Drawable:
        blank = Blank(Bounds(size=(1920, 1080)), Colors.WHITE)

        _SIZE = 500
        _DISPLACEMENT = 600
        y = blank.bounds.height / 2 - _SIZE / 2
        start_x = blank.bounds.width / 2 - _SIZE / 2 - _DISPLACEMENT
        end_x = blank.bounds.width / 2 - _SIZE / 2 + _DISPLACEMENT

        rect = tween(
            Rectangle(
                Bounds(size=(_SIZE, _SIZE)),
                fill_color=Colors.BLUE,
                border_radius=0,
            ).move(start_x, y),
            Rectangle(
                Bounds(size=(_SIZE, _SIZE)),
                fill_color=Colors.RED,
                border_radius=1000,
            ).move(end_x, y),
            t / self.duration,
        )

        return Compose([blank, rect])


if __name__ == "__main__":
    scene = Scene1()
    final = scene + scene.freeze(0.5) + scene.reverse()
    final.render("test.gif", fps=60)
