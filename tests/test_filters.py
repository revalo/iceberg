from iceberg import Bounds, Colors, PathStyle
from iceberg.primitives import Blank, Image, Blur, Opacity, Line
from .scene_tester import check_render

import os
import numpy as np


def test_image():
    blank = Blank(Bounds(size=(512, 512)), Colors.GREEN)
    image = Image(os.path.join("tests", "testdata", "logo.png"))
    scene = blank.add_centered(image)
    check_render(scene, "image.png")


def test_np_image():
    blank = Blank(Bounds(size=(256, 256)), Colors.GREEN)
    array = np.zeros((128, 128))
    array[:, :64] = 1.0
    image = Image(image=array)
    scene = blank.add_centered(image)
    check_render(scene, "np_image.png")


def test_blurred_image():
    blank = Blank(Bounds(size=(512, 512)), Colors.GREEN)
    image = Blur(Image(os.path.join("tests", "testdata", "logo.png")), sigma=10)
    scene = blank.add_centered(image)
    check_render(scene, "blurred_image.png")


def test_opacity():
    blank = Blank(Bounds(size=(512, 512)), Colors.GREEN)
    image = Opacity(Image(os.path.join("tests", "testdata", "logo.png")), 0.5)
    line = Opacity(Line((10, 10), (500, 500), PathStyle(Colors.BLACK, 20)), 0.2)
    scene = blank.add_centered(image).add_centered(line)
    check_render(scene, "opacity_image.png")
