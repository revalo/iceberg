import iceberg as ice
from .scene_tester import check_render

import os
import numpy as np


def test_image():
    blank = ice.Blank(ice.Bounds.from_size(512, 512), ice.Colors.GREEN)
    image = ice.Image(filename=os.path.join("tests", "testdata", "logo.png"))
    scene = blank.add_centered(image)
    check_render(scene, "image.png")


def test_np_image():
    blank = ice.Blank(ice.Bounds.from_size(256, 256), ice.Colors.GREEN)
    array = np.zeros((128, 128))
    array[:, :64] = 1.0
    image = ice.Image(image=array)
    scene = blank.add_centered(image)
    check_render(scene, "np_image.png")


def test_blurred_image():
    blank = ice.Blank(ice.Bounds.from_size(512, 512), ice.Colors.GREEN)
    image = ice.Blur(
        child=ice.Image(filename=os.path.join("tests", "testdata", "logo.png")),
        sigma=10,
    )
    scene = blank.add_centered(image)
    check_render(scene, "blurred_image.png")


def test_opacity():
    blank = ice.Blank(ice.Bounds(size=(512, 512)), ice.Colors.GREEN)
    image = ice.Opacity(
        child=ice.Image(os.path.join("tests", "testdata", "logo.png")), opacity=0.5
    )
    line = ice.Opacity(
        child=ice.Line((10, 10), (500, 500), ice.PathStyle(ice.Colors.BLACK, 20)),
        opacity=0.2,
    )
    scene = blank.add_centered(image).add_centered(line)
    check_render(scene, "opacity_image.png")
