from iceberg import Bounds, Colors
from iceberg.primitives import Blank
from .scene_tester import check_render


def test_blank_bounds():
    blank = Blank(Bounds(10, 10, 100, 100))
    assert blank.rectangle.left == 10
    assert blank.rectangle.top == 10
    assert blank.rectangle.right == 100
    assert blank.rectangle.bottom == 100


def test_blank_image():
    blank = Blank(Bounds(10, 10, 100, 100), Colors.RED)
    check_render(blank, "blank.png")
