from iceberg import Renderer, Bounds, Colors, FontStyle, PathStyle, Corner, render_svg
from iceberg.primitives import (
    Rectangle,
    Compose,
    Blank,
    SimpleText,
    Directions,
    MultiLine,
    AutoLine,
)

from .scene_tester import check_render


def test_flow_chart():
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

    path = AutoLine(
        box_a,
        box_b,
        "lurdrdrul",
        PathStyle(Colors.BLACK, thickness=3),
        x_padding=20,
        y_padding=40,
        context=boxes,
        arrow_head_end=True,
        head_length=15,
        corner_radius=10,
    )

    with boxes:
        path2 = MultiLine(
            [
                box_a.relative_bounds.corners[Corner.BOTTOM_MIDDLE],
                (-70, 150),
                (0, 140),
                (0, 200),
            ],
            PathStyle(Colors.BLACK, thickness=3),
            arrow_head_start=True,
            arrow_head_end=True,
            smooth=True,
        )

    scene = Compose((boxes, path, path2))
    scene = scene.pad(10)

    check_render(scene, "flow_chart.png")
