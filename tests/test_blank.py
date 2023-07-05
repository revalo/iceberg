from iceberg import Bounds, Colors
from iceberg.primitives import Blank
from .scene_tester import check_render


def test_blank_bounds():
    blank = Blank(Bounds(10, 10, 100, 100))
    assert blank.bounds.left == 10
    assert blank.bounds.top == 10
    assert blank.bounds.right == 100
    assert blank.bounds.bottom == 100


def test_blank_image():
    blank = Blank(Bounds(10, 10, 100, 100), Colors.RED)
    check_render(blank, "blank.png")
