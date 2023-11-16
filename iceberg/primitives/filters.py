from typing import Sequence
import skia

from iceberg import Drawable, Bounds
from iceberg.core import Bounds
from iceberg.core.drawable import Drawable, DrawableWithChild


class Filter(Drawable):
    child: Drawable
    paint: skia.Paint = None

    def __init__(self, child: Drawable, paint: skia.Paint = None):
        self.init_from_fields(child=child, paint=paint)

    def setup(self) -> None:
        self._paint = self.paint
        self._child = self.child
        picture_recorder = skia.PictureRecorder()
        fake_canvas = picture_recorder.beginRecording(
            self.child.bounds.width, self.child.bounds.height
        )
        self.child.draw(fake_canvas)
        self._skia_picture = picture_recorder.finishRecordingAsPicture()

        super().__init__()

    @property
    def children(self) -> Sequence[Drawable]:
        return [self._child]

    @property
    def bounds(self) -> Bounds:
        return self._child.bounds

    def draw(self, canvas: skia.Canvas) -> None:
        canvas.drawPicture(self._skia_picture, paint=self._paint)


class Blur(DrawableWithChild):
    child: Drawable
    sigma: float

    def setup(self):
        paint = skia.Paint(ImageFilter=skia.ImageFilters.Blur(self.sigma, self.sigma))
        self.set_child(Filter(self.child, paint))


class Opacity(DrawableWithChild):
    child: Drawable
    opacity: float

    def setup(self):
        paint = skia.Paint(Color4f=skia.Color4f(0, 0, 0, self.opacity))
        self.set_child(Filter(self.child, paint))
