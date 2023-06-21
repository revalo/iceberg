from typing import Tuple
import skia

from iceberg import Drawable, Bounds, Color
from iceberg.core import Bounds
from iceberg.core.properties import FontStyle

from dataclasses import dataclass
from enum import Enum


@dataclass
class SimpleText(Drawable):
    text: str
    font_style: FontStyle

    def __post_init__(self) -> None:
        self._skia_font = self.font_style.get_skia_font()
        self._skia_paint = self.font_style.get_skia_paint()
        self._height = self.font_style.size
        self._width = self._skia_font.measureText(self.text, paint=self._skia_paint)

        self._bounds = Bounds(
            left=0,
            top=0,
            right=self._width,
            bottom=self._height,
        )

    @property
    def bounds(self) -> Bounds:
        return self._bounds

    def draw(self, canvas: skia.Canvas) -> None:
        canvas.drawString(self.text, 0, self._height, self._skia_font, self._skia_paint)


# @dataclass
# class Text(Drawable):
#     class Alignment(Enum):
#         LEFT = 0
#         CENTER = 1
#         RIGHT = 2

#     text: str = None
#     markup: str = None
#     font_style: FontStyle = None
#     width: int = None
#     height: int = None
#     alignment: Alignment = Alignment.LEFT
#     justify: bool = False

#     def __post_init__(self) -> None:
#         self._layout = Layout(
#             text=self.text,
#             markup=self.markup,
#             width=self.width,
#             height=self.height,
#             justify=self.justify,
#         )

#         x, y, w, h = self._layout.get_bounding_box()
#         svg_path = "test.svg"
#         renderer = SVGRenderer(w, h, self._layout, svg_path)
#         renderer.render()

#         skia_stream = skia.FILEStream.Make(svg_path)
#         self._skia_svg = skia.SVGDOM.MakeFromStream(skia_stream)

#         self._bounds = Bounds(
#             left=x,
#             top=y,
#             right=x + w,
#             bottom=y + h,
#         )

#     @property
#     def bounds(self) -> Bounds:
#         return self._bounds

#     def draw(self, canvas: skia.Canvas) -> None:
#         self._skia_svg.render(canvas)
