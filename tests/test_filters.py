from iceberg import Bounds, Colors
from iceberg.primitives import Blank, Image, Blur
from .scene_tester import check_render

import os


def test_image():
    blank = Blank(Bounds(size=(512, 512)), Colors.GREEN)
    image = Image(os.path.join("tests", "testdata", "logo.png"))
    scene = blank.add_centered(image)
    check_render(scene, "image.png")


def test_blurred_image():
    blank = Blank(Bounds(size=(512, 512)), Colors.GREEN)
    image = Blur(Image(os.path.join("tests", "testdata", "logo.png")), sigma=10)
    scene = blank.add_centered(image)
    check_render(scene, "blurred_image.png")
