from iceberg import (
    Renderer,
    Bounds,
    Colors,
    FontStyle,
    Corner,
    PathStyle,
    Color,
    Drawable,
)
from iceberg.primitives import (
    Ellipse,
    Rectangle,
    Arrange,
    Compose,
    Text,
    MathTex,
    Blank,
)
from iceberg.animation import animate
from iceberg.animation.scene import Scene
from iceberg.arrows import Arrow, LabelArrow


class Scene1(Scene):
    def __init__(self):
        super().__init__(duration=1.0, make_frame=self.make_frame)

    def make_frame(self, t: float) -> Drawable:
        blank = Blank(Bounds(size=(1920, 1080)), Colors.WHITE)

        rect = animate(
            Rectangle(
                Bounds(size=(500, 500)),
                fill_color=Colors.BLUE,
                border_radius=0,
            ).move(100, 100),
            Rectangle(
                Bounds(size=(500, 500)),
                fill_color=Colors.RED,
                border_radius=1000,
            ).move(1000, 100),
            t / self.duration,
        )

        return Compose([blank, rect])


if __name__ == "__main__":
    scene = Scene1()
    final = scene + scene.freeze(0.5) + scene.reverse()
    final.render("test.mp4", fps=60)
