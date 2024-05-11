import skia
import hashlib
import os

from iceberg import Drawable, Bounds, Color, Colors
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


def _svg_path_to_skia(svg_path_string: str) -> skia.Path:
    import svgelements as se

    skia_path = skia.Path()
    path = se.Path(svg_path_string)

    for command in path:
        if isinstance(command, se.Move):
            skia_path.moveTo(command.end.x, command.end.y)
        elif isinstance(command, se.Line):
            skia_path.lineTo(command.end.x, command.end.y)
        elif isinstance(command, se.CubicBezier):
            skia_path.cubicTo(
                command.control1.x,
                command.control1.y,
                command.control2.x,
                command.control2.y,
                command.end.x,
                command.end.y,
            )
        elif isinstance(command, se.Close):
            skia_path.close()
        else:
            raise ValueError(f"Unknown command: {command}")

    return skia_path


class SVGPath(Drawable):
    svg_path_string: str
    fill_color: Color = Colors.BLACK
    stroke_color: Color = None

    def __init__(
        self,
        svg_path_string: str,
        fill_color: Color = Colors.BLACK,
        stroke_color: Color = None,
    ):
        self.init_from_fields(
            svg_path_string=svg_path_string,
            fill_color=fill_color,
            stroke_color=stroke_color,
        )

    def setup(self):
        self._skia_path = _svg_path_to_skia(self.svg_path_string)
        self._stroke_paint = (
            skia.Paint(
                AntiAlias=True,
                Color=self.stroke_color.to_skia(),
                Style=skia.Paint.kStroke_Style,
            )
            if self.stroke_color
            else None
        )
        self._fill_paint = (
            skia.Paint(
                AntiAlias=True,
                Color=self.fill_color.to_skia(),
                Style=skia.Paint.kFill_Style,
            )
            if self.fill_color
            else None
        )

        if self._stroke_paint:
            self._fill_path = skia.Path()
            self._stroke_paint.getFillPath(self._skia_path, self._fill_path)
            self._bounds = Bounds.from_skia(self._fill_path.computeTightBounds())
        elif self._fill_paint:
            self._fill_path = skia.Path()
            self._fill_paint.getFillPath(self._skia_path, self._fill_path)
            self._bounds = Bounds.from_skia(self._fill_path.computeTightBounds())
        else:
            raise ValueError("Either fill or stroke must be set")

    def draw(self, canvas: skia.Canvas):
        if self._fill_paint:
            canvas.drawPath(self._skia_path, self._fill_paint)
        if self._stroke_paint:
            canvas.drawPath(self._skia_path, self._stroke_paint)

    @property
    def bounds(self) -> Bounds:
        return self._bounds
