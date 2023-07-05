from iceberg import Bounds, Colors, PathStyle
from iceberg.primitives import Blank, Line, Compose
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
