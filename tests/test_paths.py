from iceberg import Bounds, Colors, PathStyle
from iceberg.primitives import Blank, Line, Compose, CurvedCubicLine
from .scene_tester import check_render


def test_dashed():
    blank = Blank(Bounds(size=(512, 512)), Colors.WHITE)
    line = Line(
        (10, 10),
        (500, 500),
        PathStyle(
            Colors.BLUE,
            thickness=5,
            dashed=True,
            dash_intervals=[20.0, 10.0],
            dash_phase=0.0,
        ),
    )
    scene = Compose([blank, line])
    check_render(scene, "dashed.png")


def test_cubic():
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
    ).scale(0.5)
    scene = blank.add_centered(line)
    check_render(scene, "cubic.png")
