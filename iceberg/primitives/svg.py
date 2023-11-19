import skia
import hashlib
import os

from iceberg import Drawable, Bounds, Color
from iceberg.core import Bounds
from iceberg.utils import temp_directory


class SVG(Drawable):
    """Initialize the SVG drawable.

    Args:
        svg_filename: The filename of the SVG file to load.
        color: The color to use for the SVG. If not specified, the SVG will be drawn as-is.
    """

    svg_filename: str = None
    raw_svg: str = None
    color: Color = None

    def setup(self):
        if self.svg_filename is None and self.raw_svg is None:
            raise ValueError("Must specify either svg_filename or raw_svg")

        if self.svg_filename is not None and self.raw_svg is not None:
            raise ValueError("Cannot specify both svg_filename and raw_svg")

        if self.raw_svg is not None:
            encoded_svg = self.raw_svg.encode("utf-8")
            filename = hashlib.sha1(encoded_svg).hexdigest()
            self._svg_filename = os.path.join(temp_directory(), filename + ".svg")

            with open(self._svg_filename, "wb") as f:
                f.write(encoded_svg)
        else:
            self._svg_filename = self.svg_filename

        self._color = self.color
        self._paint = None

        if self._color is not None:
            self._paint = skia.Paint(
                ColorFilter=skia.ColorFilters.Blend(
                    self.color.to_blend_int(), skia.BlendMode.kSrcIn
                )
            )

        skia_stream = skia.FILEStream.Make(self._svg_filename)
        self._skia_svg = skia.SVGDOM.MakeFromStream(skia_stream)

        container_size = self._skia_svg.containerSize()

        if container_size.isEmpty():
            container_size = skia.Size(100, 100)
            self._skia_svg.setContainerSize(container_size)

        self._bounds = Bounds(
            left=0,
            top=0,
            right=container_size.width(),
            bottom=container_size.height(),
        )

        picture_recorder = skia.PictureRecorder()
        fake_canvas = picture_recorder.beginRecording(
            self._bounds.width, self._bounds.height
        )
        self._skia_svg.render(fake_canvas)
        self._skia_picture = picture_recorder.finishRecordingAsPicture()

        super().__init__()

    @property
    def bounds(self) -> Bounds:
        return self._bounds

    def draw(self, canvas: skia.Canvas) -> None:
        canvas.drawPicture(self._skia_picture, paint=self._paint)
