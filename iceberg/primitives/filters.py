from typing import Sequence

import skia

from iceberg import Bounds, Drawable, DrawableWithChild


class Filter(Drawable):
    """Base class for filters."""

    def set_paint(self, child: Drawable, paint: skia.Paint) -> None:
        """Set the paint of the child.

        Args:
            child: The child to set the paint of.
            paint: The paint to set.
        """

        self._paint = paint
        self._child = child

        picture_recorder = skia.PictureRecorder()
        fake_canvas = picture_recorder.beginRecording(self._child.bounds.to_skia())

        self._child.draw(fake_canvas)
        self._skia_picture = picture_recorder.finishRecordingAsPicture()

    @property
    def children(self) -> Sequence[Drawable]:
        return [self._child]

    @property
    def bounds(self) -> Bounds:
        return self._child.bounds

    def draw(self, canvas: skia.Canvas) -> None:
        canvas.drawPicture(self._skia_picture, paint=self._paint)


class Blur(Filter):
    """Blur the child by sigma.

    Args:
        child: The child to blur.
        sigma: The sigma of the blur.
        sigma_y: The sigma of the blur in the y direction. If None, sigma is used.
    """

    child: Drawable
    sigma: float
    sigma_y: float = None

    def setup(self):
        paint = skia.Paint(
            ImageFilter=skia.ImageFilters.Blur(
                self.sigma, self.sigma if self.sigma_y is None else self.sigma_y
            )
        )
        self.set_paint(self.child, paint)


class Opacity(Filter):
    """Set the opacity of the child.

    Warning: As of now this only works for images, in general this should be
    implemented using a shader, which we haven't done yet.

    Args:
        child: The child to set the opacity of.
        opacity: The opacity of the child.
    """

    child: Drawable
    opacity: float

    def setup(self):
        paint = skia.Paint(Color4f=skia.Color4f(0, 0, 0, self.opacity))
        self.set_paint(self.child, paint)


class Hidden(DrawableWithChild):
    """Hide the child.

    Args:
        child: The child to hide.
        hidden: Whether the child is hidden.
    """

    child: Drawable
    hidden: bool = True

    @property
    def bounds(self) -> Bounds:
        return self.child.bounds

    def draw(self, canvas: skia.Canvas) -> None:
        if not self.hidden:
            self.child.draw(canvas)
