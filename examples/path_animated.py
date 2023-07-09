from iceberg import (
    Bounds,
    Colors,
    PathStyle,
    Drawable,
    Color,
    Corner,
)
from iceberg.primitives import (
    Blank,
    Anchor,
    Ellipse,
    PointAlign,
    MathTex,
    Line,
)
from iceberg.animation import tween
from iceberg.animation.scene import Playbook, Animated, Frozen
from iceberg.primitives.shapes import CurvedCubicLine, PartialPath


class Play(Playbook):
    def timeline(self) -> Drawable:
        blank = Blank(Bounds(size=(512, 512)), Colors.WHITE)

        path_style = PathStyle(
            Colors.BLUE,
            thickness=5,
            dashed=True,
            dash_intervals=[20.0, 10.0],
            dash_phase=10.0,
        )

        line = CurvedCubicLine(
            [
                (10, 10),
                (256, 10),
                (256, 256),
            ],
            path_style,
        )
        animated_line = Animated(
            [
                PartialPath(line, 0, 0.01),
                PartialPath(line, 0, 1),
            ],
            0.5,
        )

        frozen_line = animated_line.frozen()
        label = MathTex("x^3").scale(4)
        circle = (
            Ellipse(
                Bounds(size=(100, 100)),
                border_color=Color.from_hex("#d63031"),
                border_thickness=8,
                fill_color=Color.from_hex("#ff7675"),
            )
            .pad(5)
            .anchor(Corner.CENTER)
        ).add_centered(label)
        container = Blank(Bounds(size=circle.bounds.size), Colors.TRANSPARENT)
        container = PointAlign(
            frozen_line.points[-1],
            container,
            Corner.TOP_MIDDLE,
        )

        animated_circle = Animated(
            [circle.scale(0), circle.scale(1.1), circle.scale(1)],
            [0.3, 0.1],
            start_time=0.3,
        )
        container = container.add_centered(animated_circle)

        scene = Anchor([blank, animated_line, container])
        self.play(scene)

        with scene:
            new_line = Line(
                container.relative_bounds.corners[Corner.BOTTOM_MIDDLE],
                (container.relative_bounds.corners[Corner.BOTTOM_MIDDLE][0], 500),
                path_style,
            )

        animated_line = Animated(
            [
                PartialPath(new_line, 0, 0.01),
                PartialPath(new_line, 0, 1),
            ],
            0.3,
        )
        scene = Anchor([blank, frozen_line, Frozen(container), animated_line])
        self.play(scene)


if __name__ == "__main__":
    scene = Play().combined_scene
    scene = scene + scene.reverse()
    scene.render("test.gif")
