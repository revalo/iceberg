import skia

from iceberg import Drawable, Bounds, Color
from dataclasses import dataclass
from enum import Enum


class BorderPosition(Enum):
    CENTER = "center"
    INSIDE = "inside"
    OUTSIDE = "outside"


@dataclass
class Rectangle(Drawable):
    rectangle: Bounds
    border_color: Color = None
    fill_color: Color = None
    border_thickness: float = 1.0
    anti_alias: bool = True
    border_position: BorderPosition = BorderPosition.CENTER

    def __post_init__(
        self,
    ) -> None:
        self._border_paint = (
            skia.Paint(
                Style=skia.Paint.kStroke_Style,
                AntiAlias=self.anti_alias,
                StrokeWidth=self.border_thickness,
                Color4f=self.border_color.to_skia(),
            )
            if self.border_color
            else None
        )

        self._fill_paint = (
            skia.Paint(
                Style=skia.Paint.kFill_Style,
                AntiAlias=self.anti_alias,
                Color4f=self.fill_color.to_skia(),
            )
            if self.fill_color
            else None
        )

        self._bounds = self.rectangle
        self._skia_rect = self.rectangle.to_skia()
        self._border_skia_rect = self.rectangle.inset(
            self.border_thickness / 2, self.border_thickness / 2
        ).to_skia()

        # Increase the bounds to account for the border.
        if self.border_position == BorderPosition.CENTER:
            self._bounds = self._bounds.inset(
                -self.border_thickness / 2, -self.border_thickness / 2
            )
            self._border_skia_rect = self.rectangle.to_skia()
        elif self.border_position == BorderPosition.OUTSIDE:
            self._bounds = self._bounds.inset(
                -self.border_thickness, -self.border_thickness
            )
            self._border_skia_rect = self.rectangle.inset(
                -self.border_thickness / 2, -self.border_thickness / 2
            ).to_skia()

    @property
    def bounds(self) -> Bounds:
        return self._bounds

    def draw(self, canvas):
        canvas.drawRect(self._skia_rect, self._fill_paint)
        canvas.drawRect(self._border_skia_rect, self._border_paint)
