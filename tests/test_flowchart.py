from iceberg import Renderer, Bounds, Colors, FontStyle, PathStyle, Corner, render_svg
from iceberg.primitives import (
    Rectangle,
    Compose,
    Blank,
    SimpleText,
    Directions,
)
from iceberg.arrows import MultiArrow, AutoArrow, ArrowHeadStyle

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
        subdivide_increment=0.001,
    )

    with boxes:
        path2 = MultiArrow(
            [
                box_a.relative_bounds.corners[Corner.BOTTOM_MIDDLE],
                (-70, 200),
                (100, 140),
                box_b.relative_bounds.corners[Corner.MIDDLE_LEFT],
            ],
            PathStyle(Colors.BLACK, thickness=3, dashed=True),
            arrow_path_style=PathStyle(Colors.BLACK, thickness=3),
            arrow_head_start=True,
            arrow_head_end=True,
            arrow_head_style=ArrowHeadStyle.FILLED_TRIANGLE,
            head_length=12,
            smooth=True,
        )

    scene = Compose((boxes, path, path2)).scale(2)
    blank = Blank(Bounds(size=(1000, 1000)), background=Colors.WHITE)
    scene = blank.add_centered(scene)

    check_render(scene, "flow_chart.png")
