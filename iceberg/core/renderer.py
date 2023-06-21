from .drawable import Drawable

import skia
import glfw

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


class Renderer(object):
    def __init__(self, drawable: Drawable, gpu: bool = True, skia_surface=None):
        self._drawable = drawable
        self._skia_surface = skia_surface
        self._bounds = self._drawable.bounds

        if self._skia_surface is None:
            if gpu:
                self._skia_surface = self._create_gpu_surface()
            else:
                self._skia_surface = self._create_cpu_surface()

        self.render()

    def render(self):
        with self._skia_surface as canvas:
            canvas.clear(skia.Color4f(0, 0, 0, 0))
            canvas.save()
            canvas.translate(-self._bounds.left, -self._bounds.top)
            self._drawable.draw(canvas)
            canvas.restore()

    def get_rendered_image(self) -> np.ndarray:
        image = self._skia_surface.makeImageSnapshot()
        return image.toarray()[:, :, :3][:, :, ::-1]

    def save(self, path: str):
        image = self._skia_surface.makeImageSnapshot()
        image.save(path)

    def _create_gpu_surface(self):
        return get_skia_surface(self._bounds.width, self._bounds.height)

    def _create_cpu_surface(self):
        return skia.Surface(
            int(self._bounds.width + 0.5), int(self._bounds.height + 0.5)
        )
