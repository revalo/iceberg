import skia

from iceberg import Drawable, Bounds, Color
from iceberg.core import Bounds


class SVG(Drawable):
    """Initialize the SVG drawable.

    Args:
        svg_filename: The filename of the SVG file to load.
        color: The color to use for the SVG. If not specified, the SVG will be drawn as-is.
    """

    svg_filename: str
    color: Color = None

    def setup(self):
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
