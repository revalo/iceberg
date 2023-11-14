from pathlib import Path
from typing import Union
from .drawable import Drawable
from .properties import Color

import skia
import glfw
import re
import os

import numpy as np


def get_skia_surface(width, height):
    """Creates a Skia surface for rendering to on the GPU.

    Args:
        width: The width of the canvas.
        height: The height of the canvas.

    Returns:
        A SkSurface with the given dimensions.
    """

    if not glfw.init():
        raise RuntimeError("glfw.init() failed")

    # Round up width and height to the nearest integer.
    width = int(width + 0.5)
    height = int(height + 0.5)

    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    glfw.window_hint(glfw.STENCIL_BITS, 8)
    window = glfw.create_window(width, height, "", None, None)
    glfw.make_context_current(window)

    context = skia.GrDirectContext.MakeGL()
    info = skia.ImageInfo.MakeN32Premul(width, height)
    surface = skia.Surface.MakeRenderTarget(context, skia.Budgeted.kNo, info)

    return surface


def _canvas_draw_commands(canvas, drawable: Drawable, background_color: Color = None):
    if background_color is not None:
        canvas.clear(background_color.to_skia())
    else:
        canvas.clear(skia.Color4f(1, 0, 0, 1))

    canvas.save()
    canvas.translate(-drawable.bounds.left, -drawable.bounds.top)
    drawable.draw(canvas)
    canvas.restore()


class Renderer(object):
    def __init__(self, gpu: bool = False, skia_surface=None):
        """Creates a new Renderer.

        Args:
            gpu: Whether to use the GPU for rendering.
            skia_surface: A Skia surface to render to. If None, a new surface will be created.

        Returns:
            A new Renderer.
        """

        self._gpu = gpu
        self._skia_surface = skia_surface
        self._bounds = None
        self._drawable = None

    def _try_create_skia_surface(self, drawable: Drawable):
        self._drawable = drawable
        if self._skia_surface is None or self._bounds != drawable.bounds:
            self._bounds = drawable.bounds
            if self._gpu:
                self._skia_surface = self._create_gpu_surface()
            else:
                self._skia_surface = self._create_cpu_surface()

    def render(self, drawable: Drawable, background_color: Color = None):
        """Renders the given Drawable to the surface.

        Note that calling this again and again with a differently sized Drawable will
        incur a performance penalty, as the surface will be resized to fit the Drawable.

        It is best called repeatedly with Drawables of the same size.

        This method does not return anything. To get the rendered image, call
        `get_rendered_image()`. To save the rendered image, call `save_rendered_image()`.

        Args:
            drawable: The Drawable to render.
            background_color: The background color to use. If None, the background will be transparent.
        """

        self._try_create_skia_surface(drawable)

        with self._skia_surface as canvas:
            _canvas_draw_commands(canvas, drawable, background_color)

    def get_rendered_image(self) -> np.ndarray:
        """Returns the rendered image as a numpy array.

        Returns:
            The rendered image as a numpy array.
        """

        # TODO(revalo): Convert BGR to RGB via Skia.
        image = self._skia_surface.makeImageSnapshot()
        array = image.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)

        return array

    def save_rendered_image(self, path: Union[str, Path]):
        """Saves the rendered image to the given path.

        Args:
            path: The path to save the image to.
        """

        path = Path(path)

        if not path.parent.exists():
            raise RuntimeError(
                f"Destination directory {path.parent} does not exist. Please create it first."
            )

        image = self._skia_surface.makeImageSnapshot()
        image.save(str(path))

    def _create_gpu_surface(self):
        return get_skia_surface(self._bounds.width, self._bounds.height)

    def _create_cpu_surface(self):
        return skia.Surface(
            int(self._bounds.width + 0.5), int(self._bounds.height + 0.5)
        )


def _svg_postprocess(svg: str) -> str:
    # Skia adds a trailing comma to `y="0"`, which is invalid SVG.
    # While Chrome can render it, Firefox cannot.

    # Replace `y="<number>, "` with `y="<number>"`.
    svg = re.sub(r'y="(\d+\.?\d*), "', r'y="\1"', svg)

    return svg


def render_svg(
    drawable: Drawable,
    filename: str,
    background_color: Color = None,
    run_postprocess: bool = True,
):
    assert filename.endswith(".svg")

    stream = skia.FILEWStream(filename)
    canvas = skia.SVGCanvas.Make(
        (drawable.bounds.width, drawable.bounds.height), stream
    )

    _canvas_draw_commands(canvas, drawable, background_color)

    del canvas
    stream.flush()

    if run_postprocess:
        with open(filename, "r") as f:
            svg = f.read()
        svg = _svg_postprocess(svg)
        with open(filename, "w") as f:
            f.write(svg)
