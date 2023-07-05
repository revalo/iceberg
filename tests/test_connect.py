from iceberg import (
    Bounds,
    Colors,
    FontStyle,
    Corner,
    PathStyle,
    Color,
)
from iceberg.primitives import (
    Ellipse,
    Arrange,
    Compose,
    Text,
    MathTex,
)
from iceberg.arrows import Arrow, LabelArrow

from .scene_tester import check_render
import os


def test_connect():
    # What font?
    _CIRCLE_WIDTH = 100
    _BORDER_THICKNESS = 8
    _CIRCLE_PAD = 20

    left_ellipse = Ellipse(
        Bounds(size=(_CIRCLE_WIDTH, _CIRCLE_WIDTH)),
        border_color=Color.from_hex("#d63031"),
        border_thickness=_BORDER_THICKNESS,
        fill_color=Color.from_hex("#ff7675"),
    ).pad(_CIRCLE_PAD)

    right_ellipse = Ellipse(
        Bounds(size=(_CIRCLE_WIDTH, _CIRCLE_WIDTH)),
        border_color=Color.from_hex("#0984e3"),
        border_thickness=_BORDER_THICKNESS,
        fill_color=Color.from_hex("#74b9ff"),
    ).pad(_CIRCLE_PAD)

    ellipses = Arrange(
        [left_ellipse, right_ellipse],
        gap=500,
    )

    with ellipses:
        # Within this context, we can use `relative_bounds` to get the bounds of the
        # `left_ellipse` and `right_ellipse` relative to the `ellipses` object.
        arrow = Arrow(
            left_ellipse.relative_bounds.corners[Corner.MIDDLE_RIGHT],
            right_ellipse.relative_bounds.corners[Corner.MIDDLE_LEFT],
            line_path_style=PathStyle(
                color=Colors.BLACK,
                thickness=3,
            ),
        )

    arrow_label = MathTex("f(x) = x^2", scale=4)
    arrow = LabelArrow(
        arrow,
        arrow_label,
        Corner.BOTTOM_MIDDLE,
        distance=20,
    )
    connection = Compose([ellipses, arrow])

    text_block = Text(
        "This is some really long text, and it's going to wrap around at some point, because it's so long and I spent a lot of time.",
        font_style=FontStyle(
            filename=os.path.join("tests", "testdata", "OpenSans-Regular.ttf"),
            size=28,
            color=Colors.BLACK,
        ),
        width=connection.bounds.width,
    )

    scene = Arrange(
        [connection, text_block],
        gap=10,
        arrange_direction=Arrange.Direction.VERTICAL,
    )

    scene = scene.pad(20).scale(2)

    check_render(scene, "connect.png")
