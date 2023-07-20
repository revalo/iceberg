import numpy as np
from iceberg import (
    Renderer,
    Bounds,
    Colors,
    FontStyle,
    PathStyle,
    Corner,
    Drawable,
    SplineType,
)
from iceberg.primitives import (
    Rectangle,
    Compose,
    Blank,
    SimpleText,
    PartialPath,
    MathTex,
)
from iceberg.arrows import MultiArrow, AutoArrow, LabelArrowPath
from iceberg.animation import tween
from iceberg.animation.scene import Scene


class Scene1(Scene):
    def __init__(self):
        super().__init__(duration=1.0, make_frame=self.make_frame)

    def make_frame(self, t: float) -> Drawable:
        progress = t / self.duration
        # What font?
        _FONT_FAMILY = "Arial"

        box = Rectangle(
            Bounds(size=(40, 40)),
            Colors.BLACK,
            border_thickness=3,
        )
        label_a = SimpleText(
            text="A",
            font_style=FontStyle(
                family=_FONT_FAMILY,
                size=28,
                color=Colors.BLACK,
            ),
        )
        label_b = SimpleText(
            text="B",
            font_style=FontStyle(
                family=_FONT_FAMILY,
                size=28,
                color=Colors.BLACK,
            ),
        )

        box_a = box.add_centered(label_a)
        box_b = box.add_centered(label_b)

        boxes = Compose((box_a, box_b.move(200, 200)))

        path = AutoArrow(
            box_a,
            box_b,
            "lurdrdl",
            PathStyle(Colors.BLACK, thickness=3),
            x_padding=40,
            y_padding=60,
            context=boxes,
            arrow_head_end=True,
            head_length=12,
            corner_radius=20,
            partial_end=tween(0, 1, progress),
            subdivide_increment=0.01,
        )
        label1 = MathTex("\int_0^\infty e^{-x^2} \,dx", scale=1.5)

        path = LabelArrowPath(path, label1, Corner.BOTTOM_MIDDLE, t=0.65, distance=10)

        with boxes:
            path2 = MultiArrow(
                [
                    box_a.relative_bounds.corners[Corner.BOTTOM_MIDDLE],
                    # (-70, 200),
                    tween(np.array([-70, 200]), np.array([100, 200]), progress),
                    (100, 140),
                    box_b.relative_bounds.corners[Corner.MIDDLE_LEFT],
                ],
                PathStyle(Colors.BLACK, thickness=3, dashed=True),
                arrow_path_style=PathStyle(Colors.BLACK, thickness=3),
                arrow_head_start=True,
                arrow_head_end=True,
                partial_end=tween(0, 1, progress),
                head_length=12,
                spline=SplineType.CUBIC,
                subdivide_increment=0.1,
            )
            label2 = SimpleText(
                text="Lorem ipsum",
                font_style=FontStyle(
                    family=_FONT_FAMILY,
                    size=18,
                    color=Colors.BLACK,
                ),
            )

            path2 = LabelArrowPath(
                path2, label2, Corner.BOTTOM_MIDDLE, t=0.75, distance=10, rotated=True
            )

        scene = Compose((boxes, path, path2))
        blank = Blank(Bounds(size=(400, 400)), background=Colors.WHITE)
        scene = blank.add_centered(scene)

        return scene


if __name__ == "__main__":
    scene = Scene1()
    final = scene + scene.freeze(0.1) + scene.reverse()
    final.render("test.gif", fps=60)
    renderer = Renderer()
    renderer.render(scene.make_frame(1).scale(4))
    renderer.save_rendered_image("test.png")
