from typing import List, Optional, Sequence, Tuple, Union
import skia

from iceberg import Drawable, Bounds, Color, FontStyle, Corner, Colors
from iceberg.animation import Animatable
from iceberg.animation.animatable import AnimatableSequence
from iceberg.core import Bounds
from iceberg.core.drawable import Drawable
from iceberg.core.properties import PathStyle
from iceberg.geometry import get_transform, apply_transform
from .layout import Compose
from .text import SimpleText
from dataclasses import dataclass
from abc import ABC, abstractmethod, abstractproperty
from enum import Enum

import math


class BorderPosition(Enum):
    CENTER = "center"
    INSIDE = "inside"
    OUTSIDE = "outside"


@dataclass
class Rectangle(Drawable, Animatable):
    rectangle: Bounds
    border_color: Color = None
    fill_color: Color = None
    border_thickness: float = 1.0
    anti_alias: bool = True
    border_position: BorderPosition = BorderPosition.CENTER
    border_radius: Union[float, Tuple[float, float]] = 0.0

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

    @property
    def border_radius_tuple(self) -> Tuple[float, float]:
        if isinstance(self.border_radius, tuple):
            rx, ry = self.border_radius
        else:
            rx = ry = self.border_radius

        return rx, ry

    def draw(self, canvas):
        self.__post_init__()

        rx, ry = self.border_radius_tuple

        if self._fill_paint:
            canvas.drawRoundRect(self._skia_rect, rx, ry, self._fill_paint)

        if self._border_paint:
            canvas.drawRoundRect(self._border_skia_rect, rx, ry, self._border_paint)

    @property
    def animatables(self) -> AnimatableSequence:
        rx, ry = self.border_radius_tuple
        return [
            self.rectangle,
            self.border_color,
            self.fill_color,
            self.border_thickness,
            rx,
            ry,
        ]

    def copy_with_animatables(self, animatables: AnimatableSequence):
        rectangle, border_color, fill_color, border_thickness, rx, ry = animatables

        return self.__class__(
            rectangle=rectangle,
            border_color=border_color,
            fill_color=fill_color,
            border_thickness=border_thickness,
            anti_alias=self.anti_alias,
            border_position=self.border_position,
            border_radius=(rx, ry),
        )


@dataclass
class Ellipse(Rectangle):
    def draw(self, canvas):
        self.__post_init__()

        if self._fill_paint:
            canvas.drawOval(self._skia_rect, self._fill_paint)

        if self._border_paint:
            canvas.drawOval(self._border_skia_rect, self._border_paint)


class Path(Drawable, ABC):
    def __init__(self, skia_path: skia.Path, path_style: PathStyle):
        super().__init__()

        self._path = skia_path
        self._path_style = path_style
        self._fill_path = skia.Path()
        self._path_style.skia_paint.getFillPath(self._path, self._fill_path)
        self._bounds = Bounds.from_skia(self._fill_path.computeTightBounds())

    @property
    def bounds(self) -> Bounds:
        return self._bounds

    @property
    def skia_path(self) -> skia.Path:
        return self._path

    def draw(self, canvas):
        canvas.drawPath(self._path, self._path_style.skia_paint)


class PartialPath(Drawable, Animatable):
    def __init__(
        self,
        child_path: Path,
        start: float = 0,
        end: float = 1,
        subdivide_increment: float = 0.01,
    ):
        super().__init__()

        assert (
            0 <= start <= end <= 1
        ), f"Start and end must be between 0 and 1, got {start} and {end}."

        self._child_path = child_path
        self._start = start
        self._end = end

        self._path_measure = skia.PathMeasure(self._child_path.skia_path, False)
        self._total_length = self._path_measure.getLength()

        self._points = []
        self._tangents = []

        # Subdivide the path and store the points and tangents.
        current_t = start

        while current_t < end:
            current_distance = self._total_length * current_t

            point, tangent = self._path_measure.getPosTan(current_distance)

            self._points.append(point)
            self._tangents.append(tangent)

            current_t += subdivide_increment

        # Add the end point.
        point, tangent = self._path_measure.getPosTan(self._total_length * end)

        self._points.append(point)
        self._tangents.append(tangent)

        self._points = [tuple(point) for point in self._points]
        self._tangents = [tuple(tangent) for tangent in self._tangents]

        self._partial_path = skia.Path()
        self._partial_path.moveTo(*self._points[0])

        for point in self._points[1:]:
            self._partial_path.lineTo(*point)

    def draw(self, canvas: skia.Canvas):
        canvas.drawPath(self._partial_path, self._child_path._path_style.skia_paint)

    @property
    def tangents(self) -> Sequence[Tuple[float, float]]:
        return self._tangents

    @property
    def points(self) -> Sequence[Tuple[float, float]]:
        return self._points

    @property
    def children(self) -> Sequence[Drawable]:
        return [self._child_path]

    @property
    def bounds(self) -> Bounds:
        return self._child_path.bounds

    @property
    def animatables(self) -> AnimatableSequence:
        return [self._start, self._end]

    @property
    def total_length(self) -> float:
        return self._total_length

    def copy_with_animatables(self, animatables: AnimatableSequence):
        start, end = animatables
        return PartialPath(self._child_path, start, end)


@dataclass
class Line(Path):
    start: Tuple[float, float]
    end: Tuple[float, float]
    path_style: PathStyle

    def __post_init__(self):
        path = skia.Path()
        path.moveTo(*self.start)
        path.lineTo(*self.end)

        super().__init__(path, self.path_style)


@dataclass
class CurvedCubicLine(Path):
    points: List[Tuple[float, float]]
    path_style: PathStyle

    def __post_init__(self):
        assert len(self.points) >= 3, "A cubic line requires at least 3 points."

        path = skia.Path()
        path.moveTo(*self.points[0])

        # Take points in groups of 3 and draw a cubic line.
        for i in range(0, len(self.points) - 2, 2):
            path.cubicTo(*self.points[i], *self.points[i + 1], *self.points[i + 2])

        super().__init__(path, self.path_style)


class GridOverlay(Compose):
    """Overlays a grid on top of a scene, for debugging and design."""

    def __init__(
        self,
        scene: Drawable,
        spacing: float = 20,
        label_every: int = 5,
        color: Color = Colors.BLACK,
    ):
        x_lower, x_upper = scene.bounds.left, scene.bounds.right
        y_lower, y_upper = scene.bounds.top, scene.bounds.bottom

        # Round the lower bounds to the previous multiple of the spacing.
        x_lower = math.floor(x_lower / spacing) * spacing
        y_lower = math.floor(y_lower / spacing) * spacing

        # Number of horizontal and vertical lines
        num_verticals = math.floor((x_upper - x_lower) / spacing)
        num_horizontals = math.floor((y_upper - y_lower) / spacing)

        # Line positions
        xs = [x_lower + spacing * i for i in range(num_verticals + 1)]
        ys = [y_lower + spacing * i for i in range(num_horizontals + 1)]

        # Extend the lines a bit to make the grid look nicer
        x_lower -= spacing / 2
        y_lower -= spacing / 2
        x_upper = max(x_upper, xs[-1] + spacing / 2)
        y_upper = max(y_upper, ys[-1] + spacing / 2)

        style = PathStyle(Color(color.r, color.g, color.b, 0.3), 1)
        important_style = PathStyle(Color(color.r, color.g, color.b, 0.85), 1)

        # Index of the zero line, to figure out which lines to bold and label.
        x_offset_index = xs.index(0) % label_every
        y_offset_index = ys.index(0) % label_every

        vertical_lines = [
            Line(
                (x, y_lower),
                (x, y_upper),
                important_style if i % label_every == x_offset_index else style,
            )
            for i, x in enumerate(xs)
        ]
        horizontal_lines = [
            Line(
                (x_lower, y),
                (x_upper, y),
                important_style if i % label_every == y_offset_index else style,
            )
            for i, y in enumerate(ys)
        ]

        labels = []
        font_style = FontStyle(
            family="Arial",
            size=12,
            color=color,
        )

        for i, x in enumerate(xs):
            if i % label_every == x_offset_index:
                labels.append(
                    SimpleText(
                        str(round(x)),
                        font_style,
                    ).move(x, y_lower - 5, corner=Corner.BOTTOM_MIDDLE)
                )

        for i, y in enumerate(ys):
            if i % label_every == y_offset_index:
                labels.append(
                    SimpleText(
                        str(round(y)),
                        font_style,
                    ).move(x_lower - 5, y, corner=Corner.MIDDLE_RIGHT)
                )

        super().__init__([scene] + vertical_lines + horizontal_lines + labels)
