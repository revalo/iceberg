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
