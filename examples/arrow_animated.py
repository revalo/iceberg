import numpy as np
from iceberg import (
    Bounds,
    Colors,
    PathStyle,
    Drawable,
    Color,
    Corner,
    SplineType,
)
from iceberg.primitives import (
    Blank,
    Anchor,
    Ellipse,
    PointAlign,
    MathTex,
    Line,
    Compose,
    GridOverlay,
)
from iceberg.arrows import MultiArrow, Arrow, ArrowHeadStyle, ArrowPath
from iceberg.animation import tween
from iceberg.animation.scene import Playbook, Animated, Frozen, Scene
from iceberg.primitives.shapes import GeneralLine


class TangentArrow(Compose):
    def __init__(self, t: float, *args, **kwargs):
        arrow = MultiArrow(*args, **kwargs)
        pos, tan = arrow.point_and_tangent_at(t)
        pos = np.array(pos)
        tan = np.array(tan)

        point = Ellipse(
            Bounds(center=pos, size=(3, 3)), fill_color=Colors.RED, border_thickness=0
        )
        tangent = Arrow(
            pos,
            pos + 10 * tan,
            PathStyle(Colors.RED, thickness=1),
            head_length=4,
            arrow_head_style=ArrowHeadStyle.FILLED_TRIANGLE,
        )

        super().__init__((arrow, point, tangent))


class MovingArrow(Scene):
    def __init__(self, arrow1: ArrowPath, arrow2: ArrowPath, duration: float = 1.0):
        self.arrow1 = arrow1
        self.arrow2 = arrow2
        self._duration = duration

    def make_frame(self, t: float) -> Drawable:
        blank = Blank(Bounds(size=(150, 150), center=(50, 0)), Colors.WHITE)
        arrow = tween(self.arrow1, self.arrow2, t / self._duration)
        pos, tan = arrow.point_and_tangent_at(t)
        pos = np.array(pos)
        tan = np.array(tan)

        point = Ellipse(
            Bounds(center=pos, size=(3, 3)), fill_color=Colors.RED, border_thickness=0
        )
        tangent = Arrow(
            pos, pos + 20 * tan, PathStyle(Colors.RED, thickness=1), head_length=8
        )

        scene = Anchor((arrow, point, tangent))
        return Compose((blank, scene)).scale(10)


# class Play(Playbook):
#     animated_line = Animated(
#         [
#             TangentArrow(0.3, points_1, path_style, smooth=True),
#             TangentArrow(0.7, points_2, path_style, smooth=True),
#         ],
#         0.5,
#     )
#     scene = blank.add_centered(animated_line).scale(10)

#     self.play(scene)


if __name__ == "__main__":
    # scene = Play().combined_scene
    path_style = PathStyle(
        Colors.BLACK,
        thickness=1,
    )

    points_1 = [
        (0, 0),
        (33, -25),
        (67, -25),
        (100, 0),
    ]
    points_2 = [
        (0, 0),
        (33, 25),
        (67, 25),
        (100, 0),
    ]
    curve1 = GeneralLine(points_1, path_style, spline=SplineType.CUBIC)
    curve2 = GeneralLine(points_2, path_style, spline=SplineType.CUBIC)
    arrow_1 = ArrowPath(
        curve1,
        arrow_head_end=True,
        head_length=4,
        arrow_head_style=ArrowHeadStyle.FILLED_TRIANGLE,
    )
    arrow_2 = ArrowPath(
        curve2,
        arrow_head_end=True,
        head_length=4,
        arrow_head_style=ArrowHeadStyle.FILLED_TRIANGLE,
    )
    scene = MovingArrow(arrow_1, arrow_2, duration=1.0)
    scene = scene + scene.reverse()
    scene.render("test.gif")
