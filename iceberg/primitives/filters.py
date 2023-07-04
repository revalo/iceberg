from typing import Sequence
import skia

from iceberg import Drawable, Bounds, Color
from iceberg.core import Bounds
from iceberg.core.drawable import Drawable


class Filter(Drawable):
    def __init__(self, child: Drawable, paint: skia.Paint = None) -> None:
        self._paint = paint
        self._child = child
        picture_recorder = skia.PictureRecorder()
        fake_canvas = picture_recorder.beginRecording(
            child.native_bounds.width, child.native_bounds.height
        )
        child.draw(fake_canvas)
        self._skia_picture = picture_recorder.finishRecordingAsPicture()

    @property
    def children(self) -> Sequence[Drawable]:
        return [self._child]

    @property
    def native_bounds(self) -> Bounds:
        return self._child.native_bounds

    def draw(self, canvas: skia.Canvas) -> None:
        canvas.drawPicture(self._skia_picture, paint=self._paint)


class Blur(Filter):
    def __init__(self, child: Drawable, sigma: float) -> None:
        paint = skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma, sigma))
        super().__init__(child=child, paint=paint)
