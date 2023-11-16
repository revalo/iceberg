import iceberg as ice
from .scene_tester import check_render


def test_dashed():
    blank = ice.Blank(ice.Bounds(size=(512, 512)), ice.Colors.WHITE)
    line = ice.Line(
        (10, 10),
        (500, 500),
        ice.PathStyle(
            ice.Colors.BLUE,
            thickness=5,
            dashed=True,
            dash_intervals=[20.0, 10.0],
            dash_phase=0.0,
        ),
    )
    scene = ice.Compose([blank, line])
    check_render(scene, "dashed.png")


def test_cubic():
    blank = ice.Blank(ice.Bounds(size=(512, 512)), ice.Colors.WHITE)
    line = ice.CurvedCubicLine(
        points=[
            (10, 10),
            (256, 10),
            (256, 256),
            (256, 500),
            (500, 500),
        ],
        path_style=ice.PathStyle(
            ice.Colors.BLUE,
            thickness=5,
            dashed=True,
            dash_intervals=[20.0, 10.0],
            dash_phase=0.0,
        ),
    ).scale(0.5)
    scene = blank.add_centered(line)
    check_render(scene, "cubic.png")


def test_partial():
    blank = ice.Blank(ice.Bounds(size=(512, 512)), ice.Colors.WHITE)
    line = ice.CurvedCubicLine(
        points=[
            (10, 10),
            (256, 10),
            (256, 256),
            (256, 500),
            (500, 500),
        ],
        path_style=ice.PathStyle(
            ice.Colors.BLUE,
            thickness=5,
            dashed=True,
            dash_intervals=[20.0, 10.0],
            dash_phase=0.0,
        ),
    )
    partial_line = ice.PartialPath(line, 0, 0.8)
    scene = blank.add_centered(partial_line)
    check_render(scene, "partial_path.png")
