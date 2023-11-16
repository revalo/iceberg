from typing import Sequence
import skia

from iceberg import Drawable, Bounds
from iceberg.core import Bounds
from iceberg.core.drawable import Drawable, DrawableWithChild


class Filter(Drawable):
    def set_paint(self, child: Drawable, paint: skia.Paint) -> None:
        self._paint = paint
        self._child = child

        picture_recorder = skia.PictureRecorder()
        fake_canvas = picture_recorder.beginRecording(
            self._child.bounds.width, self._child.bounds.height
        )
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
    child: Drawable
    sigma: float

    def setup(self):
        paint = skia.Paint(ImageFilter=skia.ImageFilters.Blur(self.sigma, self.sigma))
        self.set_paint(self.child, paint)


class Opacity(Filter):
    child: Drawable
    opacity: float

    def setup(self):
        paint = skia.Paint(Color4f=skia.Color4f(0, 0, 0, self.opacity))
        self.set_paint(self.child, paint)
